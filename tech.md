# Doomsday Pager: Technical Audit and Improvement Plan

- **Review date:** October 24, 2026
- **Target deadline:** Sunday, October 25, 2026, 18:00, Europe/Belgrade
- **Status:** Source-based audit and proposed work. Findings below are not fixes already delivered.
- **Setup documentation:** [README.md](README.md)

## Review summary

The MVP implements a coherent incident workflow through a FastAPI API, PostgreSQL persistence, a React Control Plane, and a Kotlin Android client. Backend authentication, role checks, ownership checks, transactional audit records, and conditional claiming provide a useful foundation. No Critical issue or unauthorized ownership takeover was confirmed in this review.

The largest risks for the demonstration are Android alert delivery, stale client state, development-only API configuration, and the absence of live database/device validation. The recommended work preserves the existing architecture and concentrates on these gaps.

This audit covers the current source and local changes prepared for review. File locations refer to the reviewed version; line numbers can move after edits. Secrets and populated environment files are deliberately excluded. The original specification is removed in this review snapshot; implemented behavior is documented in the README and this audit.

## Scope and evidence

Reviewed areas:

- Backend application, authentication, JWT decoding, role dependencies, routers, schemas, incident service, configuration, and account setup helpers.
- SQLAlchemy models and all four Alembic revisions, including foreign keys, uniqueness, response-state migration, and locking strategy.
- React entry point, session handling, API wrapper, incident actions, pages, components, styles, and npm/Vite configuration.
- Android activity, API client, repositories, models, manifest, Gradle configuration, alarm playback, polling, and example tests.
- Root documentation, ignore rules, dependency/build declarations, environment-template availability, and Git working state.

Evidence labels:

- **Confirmed defect:** reproducible behavior or a deterministic code path that produces an incorrect result.
- **Confirmed limitation/gap:** a capability or protection is absent; absence does not imply an exploit occurred.
- **Potential risk:** impact depends on deployment, workload, access policy, or device behavior not established here.

Severity reflects impact on this MVP and its planned demonstration. Public exposure can increase the importance of a finding.

## Verification results

| Check | Result | Limits |
| --- | --- | --- |
| Backend suite | 41 passed | Used isolated placeholder settings and an in-memory SQLite engine URL. Service tests mock database calls; no PostgreSQL workflow was exercised. |
| Web lint | Passed with one warning | `control-plane/src/App.jsx:87`, synchronous state update in an effect. |
| Web compilation | Vite production compilation passed in memory | Used the same React plugin with output writing disabled; not a clean installation or a normal artifact-producing release build. |
| JWT expiry requirement | Correctly signed token without `exp` accepted | Synthetic token and audit-only signing material; does not demonstrate signature bypass. |
| Alembic URL interpolation | Percent-encoded URL rejected at configuration assignment | Synthetic URL; no real database credentials or connection used. |
| Live migrations and concurrent requests | Not run | Must use a disposable PostgreSQL database. |
| Android compilation, installation, sound, lifecycle | Not run | Requires the Android toolchain and actual device/emulator validation. |
| Clean dependency installation | Not run | Python manifest is absent; existing local dependencies were used. |

Backend verification used `python -B -m pytest -p no:cacheprovider tests -q` with bytecode writes disabled and process-only placeholder configuration. Web lint used `npm.cmd run lint`. No audit result should be interpreted as proof of production readiness or guaranteed alert delivery.

## Confirmed strengths

- Incident endpoints require authentication. Privileged actions require `SYSTEM_ADMIN` or `ADMIN` in `backend/routers/incidents.py`.
- Resolution and help requests check ownership in `backend/services/incident_service.py:445` and `:540`.
- Claiming uses a conditional `UPDATE ... RETURNING` in `backend/services/incident_service.py:199`. A second claimant cannot simply overwrite the first owner.
- Response, join, help, and resolution operations acquire an incident row lock through `get_locked_incident()` at `backend/services/incident_service.py:21`.
- Response records and responder membership enforce incident/user uniqueness in `backend/models.py:148` and `:251` and corresponding migrations.
- Workflow changes and audit events are committed in the same service transaction; failures roll back.
- Password hashing uses `pwdlib`; JWT decoding restricts the configured algorithm; authenticated requests reload the user and role from the database.
- Non-admin requests receive an empty audit history through backend enforcement, independently of web rendering.
- The migration chain is linear: `1d0df4dc4584` -> `5659d7fe732e` -> `520b7e528e38` -> `d2756d494e1b`. The last revision preserves older acknowledgements before making response columns mandatory.
- No endpoint naming mismatch was found between the current clients and backend routes.

## High severity findings

| ID | Evidence and location | Explanation and impact | Proposed solution |
| --- | --- | --- | --- |
| H1 | **Confirmed limitation.** `android-app/app/src/main/java/com/doomsdaypager/app/MainActivity.kt:64-71,108-152`; `android-app/app/src/main/AndroidManifest.xml:5-30` | Polling belongs to the activity composition; sound stops in `onStop()`. No notification service, push receiver, or persistent delivery mechanism exists. Background and locked-device delivery cannot be guaranteed. A Compose coroutine is not a lifecycle-aware foreground monitoring service. | Scope the immediate demo to visible foreground monitoring; show monitoring state, handle lifecycle transitions deliberately, and test the actual device. Estimate push delivery separately. |
| H2 | **Confirmed defect.** `android-app/app/src/main/java/com/doomsdaypager/app/MainActivity.kt:37-38,99-105,128-145,236-241` | Active/queued alarms hold incident snapshots. Polling replaces the overview but does not reconcile alarms. A remotely claimed or resolved incident can retain obsolete actions or continue sounding. | Queue IDs/event keys, reconcile with latest data, remove resolved entries, and refresh/revalidate before actions. |
| H3 | **Confirmed configuration; potential interception/connectivity impact.** `android-app/app/src/main/java/com/doomsdaypager/app/data/remote/ApiClient.kt:14`; `android-app/app/src/main/AndroidManifest.xml:16`; `control-plane/src/api/client.js:1-2` | Android hardcodes a development HTTP URL; web defaults to loopback HTTP. HTTP exposes credentials/tokens to interception where the network permits it. Device access depends on a reachable development machine. | Use a stable HTTPS test API; configure both clients consistently; move Android URL selection to build configuration. Restrict cleartext to development if retained. |
| H4 | **Confirmed defect.** `control-plane/src/App.jsx:118-124,161-175,225-231,253-254` | Only the incident list polls. An open detail screen can retain old ownership, comments, responses, and status after another client acts. | Poll the selected detail with identity/cancellation guards and refresh after conflict responses. |
| H5 | **Confirmed setup defect.** `backend/migrations/env.py:21-26` | The URL goes directly into interpolated Alembic configuration. Percent-encoded credentials can raise an interpolation error before migration connection. | Escape `%` to `%%` at the configuration boundary, or avoid interpolation for the URL. Preserve correct URL encoding and add a regression test. |
| H6 | **Confirmed readiness gap.** No `backend/requirements.txt` or `pyproject.toml`; `backend/tests/test_incident_workflow.py:4-27`; `backend/tests/test_routes.py:29-69`; `android-app/app/src/test/java/com/doomsdaypager/app/ExampleUnitTest.kt:14`; `android-app/app/src/androidTest/java/com/doomsdaypager/app/ExampleInstrumentedTest.kt:17` | A clean backend install is not reproducible from a manifest. Mocked service tests and route inspection do not exercise migrations, PostgreSQL locking, HTTP integration, or device alerts. Android tests are template checks. | Record a minimal tested dependency set; verify fresh migrations, real concurrent HTTP requests, and the demonstration APK/device. |
| H7 | **Confirmed omission; potential abuse when public.** `backend/routers/auth.py:18-37`; `backend/auth.py:6-16`; `backend/main.py:12-23` | No application login throttling is implemented. Hosting-level protection is unverified. Public requests can repeatedly attempt passwords and consume password-hashing resources. | Add a tested edge/application login limit before unrestricted public exposure. Use dedicated demonstration accounts and bounded request sizes. |

## Medium severity findings

| ID | Evidence and location | Explanation and impact | Proposed solution |
| --- | --- | --- | --- |
| M1 | **Confirmed UI defect.** `control-plane/src/components/IncidentActions.jsx:10-27,74-93`; `backend/routers/incidents.py:60-76` | `canRespond` omits the privileged-role condition. `L2` can see buttons that the API correctly rejects with 403. This is not a backend authorization bypass. | Include `canManage` in response eligibility. |
| M2 | **Confirmed client/API inconsistency.** `control-plane/src/components/IncidentActions.jsx:27,55-56`; `android-app/app/src/main/java/com/doomsdaypager/app/MainActivity.kt:240-241`; `backend/services/incident_service.py:259-310` | Web removes response actions after claim although the API permits responses until resolution. Android disables acknowledgement after `UNAVAILABLE` although the backend permits that transition. Existing mobile overview cards do not open a full detail/response screen. | Align client eligibility with backend rules and provide a small response entry point where needed. |
| M3 | **Confirmed UX/error-handling defect.** `control-plane/src/App.jsx:70-82,346-348`; `control-plane/src/api/client.js:23-34`; `android-app/app/src/main/java/com/doomsdaypager/app/MainActivity.kt:147-150` | Quiet web polls suppress failures while the header always says online; the API wrapper discards HTTP status. Android keeps retrying after authentication failures. Users can mistake stale data for current state. | Preserve status codes, handle 401 centrally, and show last successful sync plus stale/offline/session-expired state. |
| M4 | **Confirmed race condition in client code; runtime occurrence depends on timing.** `control-plane/src/App.jsx:161-175,209-279` | In-flight requests lack selected-ID/session guards. A response for incident A can overwrite detail state after navigation to B. | Cancel obsolete requests or use request-generation/identity checks; ignore results from previous sessions. |
| M5 | **Confirmed hardening gap; exploitability conditional.** `backend/jwt_handler.py:27-32` | `exp` is verified only when present. Correctly signed tokens without expiry are accepted. Normal login creates expiry, and an attacker still needs a valid signature. | Require `exp` and `sub` at decode; test absent/expired claims, malformed subjects, and tampered signatures. |
| M6 | **Confirmed inefficient polling and incomplete fallback.** `android-app/app/src/main/java/com/doomsdaypager/app/MainActivity.kt:114-124,150`; `android-app/app/src/main/java/com/doomsdaypager/app/data/repository/IncidentRepository.kt:14-20`; `backend/services/incident_service.py:405-414` | Each Android cycle fetches every incident's details sequentially, including resolved incidents, then waits eight seconds. Failed detail reads silently produce summary objects missing owner/help/response details. Latency grows with data and failures can conceal useful state. | Avoid unnecessary detail requests; retain last known details on partial failure; expose partial/stale status. Consider a small list-summary extension rather than a new transport. |
| M7 | **Confirmed schema hardening gap; potential integrity risk.** `backend/models.py:87-121,274-287`; `backend/migrations/versions/5659d7fe732e_add_incident_workflow_tabels.py:24-37`; `backend/migrations/versions/d2756d494e1b_add_incident_response_state.py:64-68` | Most state/owner/timestamp invariants are enforced only in service code. The response-value CHECK exists in migration SQL but is absent from model metadata. No corrupted rows were demonstrated. | Mirror the existing response CHECK in metadata. Defer broader state constraints unless integration tests reveal an immediate problem; do not rewrite existing revisions. |
| M8 | **Confirmed configuration gap.** `backend/config.py:18-46`; `backend/seed.py:41-50`; missing `backend/.env.example` and `control-plane/.env.example` | Setup relies on README snippets. JWT settings are checked for presence rather than full suitability. Seed checks a missing password but permits an empty value. | Add placeholder-only templates; validate blank bootstrap passwords and supported JWT configuration; document the tested runtime. |
| M9 | **Confirmed demonstration gap.** `backend/services/incident_service.py:146-155,194-196`; `control-plane/src/pages/IncidentDetailsPage.jsx:62-132` | The API returns team responses/timestamps, but the detail page does not display the collection. Response coordination is difficult to demonstrate. | Add a live response panel using existing fields. Keep ownership, acknowledgement, and joined membership distinct. |

## Low severity findings

| ID | Evidence and location | Explanation and impact | Proposed solution |
| --- | --- | --- | --- |
| L1 | **Confirmed.** `backend/create_test_user.py:29`; `android-app/app/src/main/java/com/doomsdaypager/app/MainActivity.kt:83-86,202-223` | Helper passwords echo through `input()`; Android retains its entered password after successful login. | Use `getpass()` and clear the mobile password after login. |
| L2 | **Confirmed maintainability issue.** `control-plane/components/IncidentBoard.jsx:1`; `control-plane/src/components/IncidentBoard.jsx:1`; `control-plane/src/App.jsx:2-7`; `control-plane/src/styles/operations.css:154`; `control-plane/src/styles/final-touches.css:2` | Duplicate components outside `src` and overlapping styles complicate maintenance. The application uses the `src` components. | Defer consolidation unless a specific defect requires it. |
| L3 | **Potential performance risk.** `backend/models.py:160-167,187-194,219-225`; `backend/services/incident_service.py:80-90,138-142,407-414` | Unbounded incident lists, growing comments/history, and limited supporting indexes can increase query and polling costs. | Keep demonstration data modest; measure before adding pagination/indexes after submission. |
| L4 | **Release checkpoint.** Current review snapshot and Git staging | The review must include the matching application source, both root documents, and required style assets. An incomplete commit can make a remote checkout differ from the documented local version. | Review staged paths and secret checks before commit; verify the pushed branch. Include the explicitly authorized specification deletion. |

## Behaviors that are not automatically security bugs

All authenticated users currently see all incidents. Comments remain allowed after resolution. Logout clears client state but does not revoke issued access tokens. Help can be requested only once per incident. No narrower visibility policy, revocation requirement, or repeated-help workflow is implemented.

These are scope decisions/limitations to document. They should not be changed solely because a different product could use different rules. CORS is browser-origin control, not a replacement for authentication or role checks.

## Prioritized improvement plan

Estimates assume one developer familiar with the repository and working hosting/toolchain access. They are estimates rather than delivery guarantees. Implementing every row is not a realistic pre-deadline commitment.

| Priority | Improvement | Benefit | Estimate | Regression risk | Dependencies |
| --- | --- | --- | --- | --- | --- |
| P0 | Tested Python dependencies, environment examples, Alembic URL fix | Reproducible setup and migrations | 45-75 min | Low | Working local environment |
| P0 | Stable HTTPS API and matching client configuration | Reliable cross-device access and encrypted traffic | 1.5-2.5 h | Medium | Hosting, PostgreSQL, secrets, APK build |
| P0 | Reconcile Android alarms and expose monitoring state | Removes obsolete alerts and actions | 1-2 h | Medium | Device/emulator |
| P0 | Web detail synchronization, request guards, offline/401 handling | Correct collaboration and visible failures | 1-1.5 h | Medium | Existing API |
| P0 | PostgreSQL integration and two-client rehearsal | Evidence beyond mocked tests | 1.5-2 h | Low to code | Disposable database, test accounts, device |
| P1 | Required JWT claims, login throttling, bootstrap validation | Safer public test exposure | 45-90 min | Low-medium | Edge rate limit or small implementation |
| P1 | Align response UI permissions/transitions | Removes avoidable 403s and blocked actions | 30-45 min | Low | Agreed existing response rules |
| P1 | Live responder response panel | Visible coordination for the demo | 45-75 min | Low | Detail refresh |
| P2 | Foreground notification support | Better monitoring visibility | 2-4 h | Medium | Permission/channel handling, device tests |
| Defer | FCM background delivery | Foundation for alerts outside the activity | 6-12+ h | High under deadline | Firebase, registration, backend sending, delivery tests |

Required JWT claims and login throttling should be addressed before unrestricted public exposure. If the core workflow is not validated, drop the optional feature rather than borrowing from the final testing window.

## Best demonstration feature

Build a **live responder response panel** in incident details. Display username, recorded response, response timestamp, and totals for acknowledged/unavailable users, using the existing `responses` field. Show owner and joined responders separately.

No migration is required. Do not display a percentage or identify users who have not responded: the API has no confirmed recipient roster. This feature is proposed, not currently implemented.

## Proposed HTTPS deployment

Use a Render Python Web Service, managed PostgreSQL, and a static deployment of the Control Plane. This fits the current application without adding a container platform. No deployment is performed or claimed by this document.

1. Add a minimal, tested Python dependency manifest and select a compatible Python version.
2. Set the backend service root to `backend/` and install from that manifest.
3. Provide database and JWT settings through hosting configuration, never committed files. Select the SQLAlchemy driver URL that matches the installed driver.
4. Run `python -m alembic upgrade head` once as a controlled deployment step after resolving H5. Avoid concurrent migration execution by multiple app workers.
5. Use `python -m uvicorn main:app --host 0.0.0.0 --port $PORT` as the Linux hosting start command, without reload.
6. Set exact HTTPS web origins in `CORS_ORIGINS`. Build the Control Plane with `VITE_API_BASE_URL` set to the HTTPS API URL and publish `dist/`.
7. Configure the Android build to use the same HTTPS URL, then build and install the APK.
8. Verify `/`, `/docs`, login, and protected operations from both clients. A future readiness check should verify database access; `/` currently does not.

An always-on service is preferable for the scheduled demo. Render documents idle sleep for free web services, so plan for cold starts if using free hosting. Account access, costs, deployment success, and regional availability have not been established here. If setup stalls, stop provider troubleshooting and use the rehearsed local-network fallback.

References: [Render FastAPI deployment](https://render.com/docs/deploy-fastapi), [Render free-service limitations](https://render.com/docs/free).

## Android delivery scope

For this deadline, prioritize accurate foreground monitoring and alarm state. Add visible monitoring/sync status, refresh stale entries, test sound, and document what happens on backgrounding, rotation, network loss, and token expiry.

Do not present a foreground service as an unlimited background-polling solution. Android 13+ notification permission handling and modern foreground-service restrictions must be considered. Android documents time limits for certain service types, including `dataSync`. A push-based implementation also needs device-token registration, backend event sending, retries, deduplication, notification handling, and tests; it is more than an SDK addition.

References: [notification permission](https://developer.android.com/develop/ui/compose/notifications/notification-permission), [foreground-service timeouts](https://developer.android.com/develop/background-work/services/fgs/timeout), [PyJWT required claims](https://pyjwt.readthedocs.io/en/latest/usage.html), [Alembic configuration](https://alembic.sqlalchemy.org/en/latest/tutorial.html).

## End-to-end acceptance checklist

Run against a disposable PostgreSQL database and the actual demonstration devices. These checks remain pending until executed and recorded.

- [ ] Fresh setup: install dependencies, apply all migrations, seed roles, provision accounts.
- [ ] Confirm L2 can create/read/comment but cannot claim/respond/join/request help/resolve.
- [ ] Log Android in, wait for the initial successful poll, create a new incident from web, and verify detection/sound.
- [ ] Submit two concurrent claims: exactly one succeeds; the other returns 409; ownership and audit history remain consistent.
- [ ] Repeat acknowledgement and verify no duplicate response or audit record; allow unavailable -> acknowledged; reject acknowledged -> unavailable.
- [ ] Claim an incident, request help as owner, observe help on another client, and join as another responder.
- [ ] Add comments and verify cross-client refresh without losing drafts or showing the wrong incident.
- [ ] Reject non-owner resolution with 403; resolve as owner; reject subsequent response/join/help actions and remove stale alarms.
- [ ] Confirm only ADMIN receives audit history, including when calling the API directly.
- [ ] Reject invalid/expired/missing-claim tokens; represent authentication failure clearly in both clients.
- [ ] Test network loss/recovery, partial detail failures, activity recreation, backgrounding, locking, and sound behavior.
- [ ] Restart API and clients; confirm persisted database state and documented client session behavior.
- [ ] Produce the frontend bundle and Android APK, install the exact APK, and run the final demonstration script.

## Execution schedule

All times below are Europe/Belgrade. This is a proposed schedule for Sunday, October 25, 2026; reserve the final three hours for validation and release preparation.

| Time | Work and completion criterion |
| --- | --- |
| Saturday preparation | Review current source, confirm hosting/device access, identify demonstration accounts, and attempt initial deployment. |
| 08:00-09:00 | Dependency manifest, environment examples, Alembic URL fix, JWT requirements, and focused checks. |
| 09:00-10:30 | Connect PostgreSQL/API/web/Android through HTTPS; time-box provider troubleshooting. |
| 10:30-12:00 | Fix stale mobile alarms and monitoring state; test remote claim/resolve changes. |
| 12:00-13:15 | Web detail refresh, request guards, role gating, and offline/session state. |
| 13:15-14:00 | Optional response panel only if the core flow is working; otherwise fix defects. |
| 14:00-15:00 | Regression checks and normal web/APK builds; freeze feature scope at 15:00. |
| 15:00-16:30 | Actual deployment/device rehearsal and release-blocking fixes only. |
| 16:30-17:00 | Update setup instructions, known limitations, and demonstration script. |
| 17:00-17:30 | Review final diff for secrets/unintended changes, commit/push, verify deployed revision and APK. |
| 17:30-18:00 | Buffer and final smoke test; keep the last working build available. |

## Top five priorities

1. Reproducible setup and correct Alembic URL handling.
2. One stable HTTPS API address for web and Android.
3. Android alarm reconciliation against current incident state.
4. Web detail synchronization and accurate connectivity/session feedback.
5. Live PostgreSQL concurrency and full multi-client workflow validation.

## Changes to avoid before the deadline

- Backend/service/ORM rewrites, a new web state-management framework, or a navigation redesign.
- Kubernetes, Redis, Celery, WebSockets, or a separate notification service.
- Rushed guarantees of permanent background or locked-device alert delivery.
- SSO, full user administration, multi-tenancy, or a large session redesign.
- Broad schema cleanup, editing applied migrations, or downgrading the working database.
- Toolchain major-version changes without a confirmed blocker.
- Unrelated component/style consolidation mixed into functional fixes.

## Reviewer handoff

Start with [README.md](README.md), then review H1-H7 and the acceptance checklist. Focus feedback on a reliable demonstration, small fixes, and the evidence still needed. This repository snapshot is an MVP under review, not a completed implementation of the proposed improvement plan.
