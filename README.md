# Doomsday Pager

Doomsday Pager is an internal incident response MVP for reporting operational problems, establishing ownership, coordinating responders, and retaining an incident history. It combines a FastAPI backend, a PostgreSQL database, a React Control Plane, and a Kotlin Android pager application.

The core workflow is **report → respond → claim → collaborate → resolve**. The web application provides the operational workspace; the Android application provides an incident overview and polling-based alarm screens for privileged responders.

This README describes the current implementation. For the source-based technical audit, known defects, validation results, and proposed improvement plan, see [tech.md](tech.md). Proposed improvements in that document have not been implemented.

## Reviewer guide

Start with the architecture and workflow below, then follow the setup instructions for the backend and Control Plane. The Android application requires a backend URL reachable from the test device. Local credentials and environment files are intentionally excluded from the repository.

The current validation baseline is 41 passing backend tests, a successful web lint check with one warning, and a successful Vite compilation in memory. Live PostgreSQL migrations/concurrency, a clean dependency installation, and Android device/build verification remain outstanding. See [verification scope](tech.md#verification-results) before interpreting these checks as end-to-end validation.

## Contents

- [Architecture and technology](#architecture-and-technology)
- [Features and incident workflow](#features-and-incident-workflow)
- [Repository structure](#repository-structure)
- [Prerequisites](#prerequisites)
- [Environment configuration](#environment-configuration)
- [Backend installation and startup](#backend-installation-and-startup)
- [PostgreSQL and Alembic setup](#postgresql-and-alembic-setup)
- [Control Plane setup](#control-plane-setup)
- [Android setup](#android-setup)
- [API documentation and authentication](#api-documentation-and-authentication)
- [Testing and builds](#testing-and-builds)
- [Current MVP limitations](#current-mvp-limitations)
- [Technical audit and review checklist](tech.md)

## Architecture and technology

```text
React / Vite Control Plane       Kotlin / Compose Android app
            |                                |
            +---------- JSON over HTTP ------+
                            |
                     FastAPI REST API
                 JWT authentication / roles
                   Incident service layer
                            |
                      SQLAlchemy ORM
                            |
                        PostgreSQL
                   Alembic schema migrations
```

Both clients use the same backend API and bearer authentication. Database access and workflow enforcement reside in the backend. There is no separate notification server or background worker in the current repository.

| Component      | Technologies confirmed in source                                                 |
| -------------- | -------------------------------------------------------------------------------- |
| Backend        | Python, FastAPI, Pydantic v2 APIs, SQLAlchemy 2 APIs                             |
| Database       | PostgreSQL, Alembic migrations                                                   |
| Authentication | PyJWT access tokens, `pwdlib` password hashing, FastAPI bearer dependencies      |
| Control Plane  | React 19, Vite 8, JavaScript, CSS, native Fetch API, Oxlint                      |
| Android        | Kotlin 2.2.10, Jetpack Compose, Material 3, OkHttp 4.12.0, coroutines            |
| Android build  | Android Gradle Plugin 9.4.1, Gradle wrapper 9.6.0                                |
| Tests          | pytest with mocked database sessions; Android JUnit and instrumentation examples |

## Features and incident workflow

### Incident information

Incidents contain a title, description, type, priority, creator, optional owner, status, creation timestamp, and optional resolution timestamp.

- **Types:** `NETWORK`, `SERVER`, `DATABASE`, `SECURITY`, `APPLICATION`, `OTHER`.
- **Priorities:** `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`.
- **Statuses:** `NEW`, `IN_PROGRESS`, `RESOLVED`.
- **Individual responses:** `ACKNOWLEDGED` or `UNAVAILABLE`, stored separately from ownership and incident status.

The API trims incident titles, descriptions, and comments and rejects empty text. Titles are limited to 200 characters; API comments are limited to 5,000 characters. The current web comment form imposes a stricter 2,000-character limit.

### Workflow rules

1. **Report:** an `L2`, `SYSTEM_ADMIN`, or `ADMIN` user creates an incident. It starts as `NEW` without an owner.
2. **Respond:** `SYSTEM_ADMIN` and `ADMIN` users can acknowledge an unresolved incident or mark themselves unavailable. Repeating the same response is idempotent. An unavailable response can become acknowledged; an acknowledged response cannot become unavailable. These responses do not claim the incident.
3. **Claim:** a privileged responder claims an unowned `NEW` incident. An atomic conditional database update assigns the owner and changes the status to `IN_PROGRESS`; conflicting claims return HTTP 409.
4. **Collaborate:** other privileged users can join an `IN_PROGRESS` incident once each. The owner cannot also join as an additional responder. Any authenticated user can add comments, including after resolution.
5. **Request help:** only the owner of an `IN_PROGRESS` incident can request additional help. This records an audit event and exposes `help_requested` in incident details. Only one help request is accepted per incident.
6. **Resolve:** only the owner, with a privileged role, can resolve an `IN_PROGRESS` incident. The backend records `resolved_at` and changes the status to `RESOLVED`.

Creation, claims, responses, joins, help requests, comments, and resolution produce audit events. Incident details return audit history only for `ADMIN`; other users receive an empty history list.

### Client capabilities

The **Control Plane** provides login, session restoration, logout, a three-column incident board, search by title or ID, incident creation and details, response and ownership actions, responder joining, help requests, comments, and administrator history. It refreshes the incident list every 12 seconds. Detail data refreshes when opened or after local actions; it is not independently polled.

The **Android app** provides login, logout, an incident overview, manual refresh, and queued alarm screens. For `SYSTEM_ADMIN` and `ADMIN`, an activity coroutine fetches the list and incident details, then waits eight seconds before repeating. Newly observed `NEW` incidents and help-request events can trigger a screen and device alarm sound. Existing incidents observed on the initial poll are marked as seen without sounding an alarm. Alarm screens offer assignment, acknowledgement, and unavailability actions; help-request alarms cannot assign an already owned incident.

## Repository structure

```text
.
├── README.md
├── tech.md                     # Technical audit and improvement plan
├── backend/
│   ├── main.py                  # FastAPI application and CORS
│   ├── config.py                # Environment loading and validation
│   ├── database.py              # Engine, ORM base, database sessions
│   ├── models.py                # Database entities and relationships
│   ├── schemas.py               # Request validation
│   ├── constants.py             # Roles, states, priorities, audit actions
│   ├── auth.py                  # Credential verification
│   ├── security.py              # Password hashing
│   ├── jwt_handler.py           # Access token creation and decoding
│   ├── dependencies.py          # Authentication and role checks
│   ├── routers/                 # Authentication and incident routes
│   ├── services/                # Incident workflow operations
│   ├── migrations/versions/     # Four ordered schema revisions
│   ├── alembic.ini
│   ├── seed.py                  # Role and initial administrator setup
│   ├── create_test_user.py      # Local SYSTEM_ADMIN account helper
│   └── tests/                   # Backend test suite
├── control-plane/
│   ├── package.json             # Dependencies and npm scripts
│   ├── vite.config.js
│   ├── public/
│   ├── components/              # Additional components outside src
│   └── src/
│       ├── App.jsx              # Session, navigation, workflow state
│       ├── api/                 # HTTP client and API functions
│       ├── pages/               # Login, dashboard, creation, details
│       ├── components/          # Components used by the application
│       └── styles/
└── android-app/
    ├── gradle/                  # Wrapper, version catalog, JVM criteria
    ├── gradlew / gradlew.bat
    └── app/src/
        ├── main/                # Manifest, resources, Kotlin app
        ├── test/                # Example local unit test
        └── androidTest/         # Example instrumentation test
```

Local environments, secrets, generated output, and backups are omitted from this tree. An empty local `mobile/` directory is not part of the tracked application; Android source is under `android-app/`.

## Prerequisites

- **Python 3.11 or newer:** required by the use of `enum.StrEnum`.
- **PostgreSQL:** a running server and an account permitted to create and migrate the application database. No server version is pinned.
- **Node.js and npm:** the inspected Vite 8 installation declares `^20.19.0 || >=22.12.0`. Use a compatible Node version and install the committed npm lockfile.
- **Android Studio and Android SDK:** a toolchain capable of loading the checked-in Android Gradle Plugin and Gradle versions, with SDK Platform 37 installed.
- **Android runtime:** an emulator or device with API 26 or newer. The application compiles and targets API 37.
- **Gradle JVM:** the checked-in daemon criteria request JDK 25. Java source and target compatibility are separately configured as Java 11.
- Network access for initial package downloads and connectivity from each client to the API.

Commands below use PowerShell unless identified otherwise. Start each component's instructions from the repository root, and use separate terminals for the API and web server.

## Environment configuration

Create `backend/.env` locally. All values below are placeholders; replace them before running commands. Do not commit populated environment files.

```dotenv
DATABASE_URL=postgresql+psycopg://<database-user>:<url-encoded-database-password>@<database-host>:<database-port>/<database-name>
JWT_SECRET_KEY=<private-signing-secret>
JWT_ALGORITHM=<supported-jwt-signing-algorithm>
ACCESS_TOKEN_EXPIRE_MINUTES=<positive-integer>
CORS_ORIGINS=<control-plane-origin>,<additional-allowed-origin>
INITIAL_ADMIN_PASSWORD=<initial-administrator-password>
```

| Variable                      | Purpose and requirements                                                                                                                   |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| `DATABASE_URL`                | Required SQLAlchemy connection URL. The example selects the Psycopg driver installed below. URL-encode reserved characters in credentials. |
| `JWT_SECRET_KEY`              | Required signing/verification secret or key material suitable for the selected algorithm.                                                  |
| `JWT_ALGORITHM`               | Required PyJWT algorithm name; no default is supplied by the application.                                                                  |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Required integer greater than zero.                                                                                                        |
| `CORS_ORIGINS`                | Optional comma-separated browser origins. Source defaults allow `http://localhost:5173` and `http://127.0.0.1:5173`.                       |
| `INITIAL_ADMIN_PASSWORD`      | Required by `seed.py`, including when rerunning the script; not required for normal API startup.                                           |

Configuration loads through `python-dotenv` and process environment variables. The four required API settings are validated at import time. Alembic imports the database module, so provide the complete API configuration before running migrations as well.

There are currently no checked-in `.env.example` files. The snippets here are templates only. Use a non-empty bootstrap password and signing material suitable for the selected JWT algorithm; the current application does not fully validate their strength or suitability.

For the web client, optionally create `control-plane/.env.local`:

```dotenv
VITE_API_BASE_URL=<api-base-url-without-trailing-slash>
```

`VITE_API_BASE_URL` is public client configuration, not a secret. Its source fallback is `http://127.0.0.1:8000`. Restart Vite after changing it, or rebuild for a production bundle. Android does not read this variable or `backend/.env`.

## Backend installation and startup

The repository currently has no `requirements.txt`, `pyproject.toml`, or Python lockfile. The following manual installation covers the libraries used by source imports, an ASGI server, the Psycopg driver selected in the example URL, and pytest. It is not a pinned, reproducible dependency specification.

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install fastapi "pydantic>=2" "sqlalchemy>=2" alembic python-dotenv PyJWT "pwdlib[argon2]" "psycopg[binary]" "uvicorn[standard]" pytest
```

On macOS/Linux, activate the environment with `source .venv/bin/activate` instead. Run backend commands from `backend/` because imports use that directory as the module root.

Complete the database setup below, then start the development API from the activated environment:

```powershell
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

The root endpoint at `http://127.0.0.1:8000/` returns an API-running message. It is not a database health check.

For access from another device, bind to all interfaces instead:

```powershell
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Use the development machine's reachable address in the client; `0.0.0.0` is a bind address. Allow the chosen port through the local firewall when using a physical Android device. These commands run a development server, not a production deployment.

## PostgreSQL and Alembic setup

### Create the database

Using PostgreSQL administration tools, create a dedicated login role and database owned by that role. Substitute your own values in this SQL template and execute it as a PostgreSQL administrator:

```sql
CREATE ROLE <database-user> WITH LOGIN PASSWORD '<database-password>';
CREATE DATABASE <database-name> OWNER <database-user>;
```

The angle-bracket placeholders are not executable SQL. Use valid PostgreSQL identifiers and securely supplied credentials. Point `DATABASE_URL` at the resulting database. Migrations create the schema; they do not create the PostgreSQL server, login role, or database.

### Apply existing migrations

From `backend/`, with the virtual environment active and configuration populated:

```powershell
python -m alembic upgrade head
python -m alembic current
```

`migrations/env.py` reads `DATABASE_URL` and overrides the sample URL in `alembic.ini`. The current migration chain is:

| Revision       | Schema change                                                                                                                                 |
| -------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| `1d0df4dc4584` | Creates `roles` and `users`.                                                                                                                  |
| `5659d7fe732e` | Creates `incidents`, `audit_logs`, `comments`, and `incident_responders`.                                                                     |
| `520b7e528e38` | Creates `incident_acknowledgements`.                                                                                                          |
| `d2756d494e1b` | Adds response state and response timestamp, preserves prior acknowledgements, and restricts response values with a database check constraint. |

Users reference roles; incidents reference their creator and optional owner. Responder memberships, comments, audit events, and response records reference their incident and user. Membership and response records each enforce uniqueness for an incident/user pair. The final schema stores timezone-aware timestamps. Alembic also tracks the applied revision in `alembic_version`.

The latest migration explicitly refuses to downgrade while `UNAVAILABLE` response records exist. Do not use schema downgrade as routine setup.

**Known setup defect:** the current URL assignment in `migrations/env.py` does not escape percent signs for Alembic's interpolated configuration. A URL containing percent-encoded credentials can fail before migrations connect. Keep proper URL encoding; the planned fix belongs at the Alembic configuration boundary. See finding H5 in [tech.md](tech.md#high-severity-findings).

### Initialize roles and an administrator

With `INITIAL_ADMIN_PASSWORD` configured, run:

```powershell
python seed.py
```

This creates missing `L2`, `SYSTEM_ADMIN`, and `ADMIN` roles and creates the initial administrator if its fixed username is absent. The administrator username and email are defined in `seed.py`; they are not environment settings. Inspect that script locally for the login identity. The script does not reset an existing administrator's password.

`create_test_user.py` is an additional local helper for a fixed `SYSTEM_ADMIN` account. Review its account and password handling locally before use; it is not a general account provisioning interface. There is no registration or user-management API/UI in the current implementation.

## Control Plane setup

From the repository root:

```powershell
cd control-plane
npm ci
npm run dev
```

Open the local URL printed by Vite and sign in with a provisioned backend account. The default development origin is normally `http://localhost:5173`; if Vite chooses another port, update backend `CORS_ORIGINS` to match the actual browser origin and restart the API.

If PowerShell blocks `npm.ps1`, use `npm.cmd ci` and `npm.cmd run dev`. No `npm start` script is configured.

The application uses `src/main.jsx` and `src/App.jsx`. Navigation is managed in React state rather than through URL routes. JWTs are stored under `pager_token` in browser `sessionStorage`, validated through `/me` during session restoration, and removed on logout.

## Android setup

1. Open **`android-app/`** in Android Studio and let Gradle sync.
2. Install the SDK and configure the Gradle JVM required by the checked-in build files. Android Studio can maintain the machine-specific SDK path in `local.properties`; this file is ignored by Git.
3. Configure the backend address in `app/src/main/java/com/doomsdaypager/app/data/remote/ApiClient.kt`. The application currently uses a hardcoded `BASE_URL` pointing to a developer-specific LAN address. Replace that constant locally with the API URL reachable from your emulator or device; there is no runtime settings screen or environment-variable override.
4. For the standard Android emulator, use the host-machine alias `10.0.2.2` with the API port. For a physical device, use the development machine's reachable LAN address, run the API with the all-interface bind shown above, and ensure both devices can communicate.
5. Run the `app` configuration on an API 26+ device/emulator. Sign in with a provisioned `SYSTEM_ADMIN` or `ADMIN` account to exercise polling alarms and response actions.

The manifest declares Internet access and permits cleartext HTTP. Keep the API running while testing. The current UI shows the incident overview and alarm responses; repository/API methods for joining, requesting help, resolving, and commenting exist but are not exposed as a full mobile incident-detail workflow.

For a foreground alarm demonstration, log in and wait for the initial successful monitoring poll before creating a new incident from the Control Plane. Initial incidents are treated as already seen. Stale queued alarms and response-action differences remain known defects documented in [tech.md](tech.md).

Android session state and event deduplication are held in Compose memory. Alarm playback is stopped in activity stop/destroy callbacks. This implementation does not guarantee delivery when the app is closed or the device is locked.

## API documentation and authentication

With the local backend running, FastAPI exposes:

- **Swagger UI:** `http://127.0.0.1:8000/docs`
- **ReDoc:** `http://127.0.0.1:8000/redoc`
- **OpenAPI schema:** `http://127.0.0.1:8000/openapi.json`

### Sign-in flow

Send JSON to `POST /login`:

```json
{
  "username": "<provisioned-username>",
  "password": "<account-password>"
}
```

A successful response contains `access_token` and `token_type: "bearer"`. Use the returned token on protected requests:

```http
Authorization: Bearer <access-token>
```

In Swagger UI, call `/login` and then enter the token through **Authorize**. Login accepts JSON, not an OAuth2 form. Tokens contain the user ID in `sub` and an expiry in `exp`; protected requests validate the token and load the user and role from the database. Missing, invalid, or expired credentials produce HTTP 401; insufficient role/ownership permissions produce HTTP 403.

### Implemented routes

All paths are relative to the API base URL. “Privileged” means `SYSTEM_ADMIN` or `ADMIN`.

| Method | Path                                    | Access / behavior                                                                      |
| ------ | --------------------------------------- | -------------------------------------------------------------------------------------- |
| GET    | `/`                                     | Public API-running message.                                                            |
| POST   | `/login`                                | Public credential verification and token issuance.                                     |
| GET    | `/me`                                   | Authenticated user's ID, username, email, and role.                                    |
| GET    | `/admin-only`                           | `ADMIN` role demonstration endpoint.                                                   |
| POST   | `/incidents`                            | `L2` or privileged; creates an incident, returns HTTP 201.                             |
| GET    | `/incidents`                            | Authenticated; returns all incidents, newest first.                                    |
| GET    | `/incidents/{incident_id}`              | Authenticated; details, responders, comments, responses, and admin-only audit history. |
| POST   | `/incidents/{incident_id}/claim`        | Privileged; claims an unowned `NEW` incident.                                          |
| POST   | `/incidents/{incident_id}/acknowledge`  | Privileged; acknowledges an unresolved incident.                                       |
| POST   | `/incidents/{incident_id}/unavailable`  | Privileged; records unavailability on an unresolved incident.                          |
| POST   | `/incidents/{incident_id}/join`         | Privileged; joins an `IN_PROGRESS` incident as an additional responder.                |
| POST   | `/incidents/{incident_id}/request-help` | Privileged owner; one help request per `IN_PROGRESS` incident.                         |
| POST   | `/incidents/{incident_id}/comments`     | Authenticated; adds a comment, returns HTTP 201.                                       |
| POST   | `/incidents/{incident_id}/resolve`      | Privileged owner; resolves an `IN_PROGRESS` incident.                                  |

Incident creation accepts `title`, `description`, `type`, and `priority`. Comment creation accepts `content`. Other incident action endpoints do not require a request body. Missing incidents return HTTP 404; workflow conflicts return HTTP 409; invalid request data produces FastAPI validation errors, normally HTTP 422.

## Testing and builds

### Backend

From `backend/`, with dependencies installed and required settings configured:

```powershell
python -m pytest tests
```

The suite checks route registration, authentication and role dependencies, acknowledgement behavior, claims, joins, help requests, and resolution. Database interactions in service tests use mocks; this is not a live PostgreSQL integration or migration test suite. Configuration is still required because test imports load application/database modules.

### Control Plane

From `control-plane/`:

```powershell
npm run lint
npm run build
npm run preview
```

The build writes to `control-plane/dist/`; preview serves the generated bundle locally. Use the URL printed by preview, and allow that origin in backend CORS if exercising the API. There is no frontend automated test script in `package.json`.

### Android

From `android-app/` on Windows:

```powershell
.\gradlew.bat :app:assembleDebug
.\gradlew.bat :app:testDebugUnitTest
.\gradlew.bat :app:connectedDebugAndroidTest
```

On macOS/Linux, use `./gradlew` instead of `.\gradlew.bat`. Connected instrumentation tests require a running emulator or attached device. The debug APK is generated under `app/build/outputs/apk/debug/`. The checked-in tests are template checks for arithmetic and application package identity, not incident workflow or alarm delivery tests.

## Current MVP limitations

- **Alert delivery:** Android uses activity-based polling, not push notifications, a foreground service, or a scheduled background worker. No Firebase integration, SMS/email delivery, lock-screen delivery guarantee, or escalation scheduler is implemented. A help request records an event that clients can observe; the backend does not dispatch a notification.
- **Mobile scope:** there is no incident creation screen or full interactive incident-detail workspace. Existing incidents at login do not trigger an initial alarm. Tokens and seen-event state are not persisted across activity recreation or application restarts.
- **Accounts and sessions:** no registration, general user administration, password recovery, SSO, refresh-token flow, or server-side logout/revocation endpoint exists. Logging out clears client state; issued access tokens expire according to configuration.
- **Workflow scope:** no reassignment, reopening, incident editing/deletion, responder removal, or help-request reset endpoint exists. Acknowledgement, ownership, and responder membership remain distinct records.
- **Client/API differences:** the current web UI offers acknowledgement/unavailability only for unowned `NEW` incidents, while the API permits responses until resolution. Those web response buttons are not consistently hidden for `L2`; the backend rejects unauthorized actions. The API remains the authority for permissions.
- **Data access and refresh:** all authenticated users can list and view all incidents. There is no team/tenant scoping, API pagination, or server-side search/filtering. Web search is local, and there is no WebSocket/SSE update channel. Android polls details for each listed incident, which increases request volume as the list grows.
- **Configuration and deployment:** Python dependencies are not pinned in a manifest. Android's API URL is hardcoded. The repository has no container orchestration, CI pipeline, or production deployment configuration. Development HTTP settings require additional deployment work before production use.
- **Localization and quality coverage:** no English/Russian language selection is implemented. Backend tests rely on mocked sessions, frontend automated tests are absent, and Android tests do not cover application behavior.
