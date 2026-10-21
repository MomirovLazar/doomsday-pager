
"""Tests for the public API route contract."""

from main import app


EXPECTED_ROUTES = {
    ("GET", "/"),
    ("POST", "/login"),
    ("GET", "/me"),
    ("GET", "/admin-only"),
    ("GET", "/incidents"),
    ("POST", "/incidents"),
    ("GET", "/incidents/{incident_id}"),
    ("POST", "/incidents/{incident_id}/claim"),
    ("POST", "/incidents/{incident_id}/acknowledge"),
    ("POST", "/incidents/{incident_id}/unavailable"),
    ("POST", "/incidents/{incident_id}/join"),
    ("POST", "/incidents/{incident_id}/request-help"),
    ("POST", "/incidents/{incident_id}/comments"),
    ("POST", "/incidents/{incident_id}/resolve"),
}


def get_registered_routes() -> set[tuple[str, str]]:
    """Extract HTTP methods and paths from the OpenAPI schema."""
    schema = app.openapi()

    return {
        (method.upper(), path)
        for path, operations in schema["paths"].items()
        for method in operations
        if method.lower() in {
            "get",
            "post",
            "put",
            "patch",
            "delete",
            "head",
            "options",
            "trace",
        }
    }


def test_expected_routes_are_registered() -> None:
    """Verify that the existing API contract is preserved."""
    registered_routes = get_registered_routes()

    missing_routes = EXPECTED_ROUTES - registered_routes

    assert not missing_routes, (
        f"Missing API routes: {sorted(missing_routes)}"
    )


def test_incident_routes_are_not_duplicated() -> None:
    """Prevent accidental duplication of the incident prefix."""
    registered_routes = get_registered_routes()

    duplicated_paths = {
        path
        for _, path in registered_routes
        if path.startswith("/incidents/incidents")
    }

    assert not duplicated_paths, (
        f"Duplicated incident paths: {sorted(duplicated_paths)}"
    )
