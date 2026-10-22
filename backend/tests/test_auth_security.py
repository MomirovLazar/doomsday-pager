"""Tests for authentication security"""

from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from dependencies import authentication_error, get_current_user

from types import SimpleNamespace

from constants import UserRole
from dependencies import require_roles

from fastapi.routing import APIRoute

from routers.incidents import router as incidents_router

def test_authentication_error_returns_401():
    error = authentication_error()

    assert error.status_code == 401
    assert error.headers["WWW-Authenticate"] == "Bearer"


def test_missing_token_returns_401():
    db = Mock()

    with pytest.raises(HTTPException) as exc:
        get_current_user(credentials=None, db=db)

    assert exc.value.status_code == 401
    db.scalar.assert_not_called()

@pytest.mark.parametrize(
    "role_name",
    ["L2", "SYSTEM_ADMIN", "ADMIN"],
)
def test_all_roles_can_access_common_actions(role_name):
    user = SimpleNamespace(
        role=SimpleNamespace(name=role_name)
    )

    checker = require_roles(
        "L2",
        "SYSTEM_ADMIN",
        "ADMIN",
    )

    result = checker(user)

    assert result is user


@pytest.mark.parametrize(
    "role_name",
    ["SYSTEM_ADMIN", "ADMIN"],
)
def test_privileged_roles_are_allowed(role_name):
    user = SimpleNamespace(
        role=SimpleNamespace(name=role_name)
    )

    checker = require_roles("SYSTEM_ADMIN", "ADMIN")

    result = checker(user)

    assert result is user


def test_l2_cannot_access_privileged_actions():
    user = SimpleNamespace(
        role=SimpleNamespace(name="L2")
    )

    checker = require_roles("SYSTEM_ADMIN", "ADMIN")

    with pytest.raises(HTTPException) as exc:
        checker(user)

    assert exc.value.status_code == 403


def test_only_admin_can_access_admin_routes():
    system_admin = SimpleNamespace(
        role=SimpleNamespace(name="SYSTEM_ADMIN")
    )

    checker = require_roles("ADMIN")

    with pytest.raises(HTTPException) as exc:
        checker(system_admin)

    assert exc.value.status_code == 403

def make_user(role_name):
    return SimpleNamespace(
        role=SimpleNamespace(name=role_name)
    )


@pytest.mark.parametrize(
    "role_name",
    [
        UserRole.L2,
        UserRole.SYSTEM_ADMIN,
        UserRole.ADMIN,
    ],
)
def test_all_roles_can_access_common_actions(role_name):
    user = make_user(role_name)

    checker = require_roles(
        UserRole.L2,
        UserRole.SYSTEM_ADMIN,
        UserRole.ADMIN,
    )

    assert checker(user) is user


@pytest.mark.parametrize(
    "role_name",
    [
        UserRole.SYSTEM_ADMIN,
        UserRole.ADMIN,
    ],
)
def test_privileged_roles_are_allowed(role_name):
    user = make_user(role_name)

    checker = require_roles(
        UserRole.SYSTEM_ADMIN,
        UserRole.ADMIN,
    )

    assert checker(user) is user


def test_l2_cannot_access_privileged_actions():
    user = make_user(UserRole.L2)

    checker = require_roles(
        UserRole.SYSTEM_ADMIN,
        UserRole.ADMIN,
    )

    with pytest.raises(HTTPException) as exc:
        checker(user)

    assert exc.value.status_code == 403


def test_only_admin_can_access_admin_routes():
    user = make_user(UserRole.SYSTEM_ADMIN)

    checker = require_roles(UserRole.ADMIN)

    with pytest.raises(HTTPException) as exc:
        checker(user)

    assert exc.value.status_code == 403

PROTECTED_ACTIONS = [
    "/incidents/{incident_id}/acknowledge",
    "/incidents/{incident_id}/unavailable",
    "/incidents/{incident_id}/claim",
    "/incidents/{incident_id}/join",
    "/incidents/{incident_id}/request-help",
    "/incidents/{incident_id}/resolve",
]


@pytest.mark.parametrize("path", PROTECTED_ACTIONS)
def test_incident_action_requires_role_check(path):
    route = None

    for candidate in incidents_router.routes:
        if isinstance(candidate, APIRoute) and candidate.path == path:
            route = candidate
            break

    assert route is not None, f"Route not found: {path}"

    role_check_found = False

    for dependency in route.dependant.dependencies:
        dependency_function = dependency.call

        if (
            callable(dependency_function)
            and dependency_function.__name__ == "role_checker"
        ):
            role_check_found = True
            break

    assert role_check_found, f"Role protection missing: {path}"

def test_comments_route_uses_authenticated_user():
    route = None

    for candidate in incidents_router.routes:
        if (
            isinstance(candidate, APIRoute)
            and candidate.path == "/incidents/{incident_id}/comments"
        ):
            route = candidate
            break

    assert route is not None

    dependency_functions = []

    for dependency in route.dependant.dependencies:
        dependency_functions.append(dependency.call)

    assert get_current_user in dependency_functions


def test_l2_is_allowed_for_incident_creation():
    user = make_user(UserRole.L2)

    checker = require_roles(
        UserRole.L2,
        UserRole.SYSTEM_ADMIN,
        UserRole.ADMIN,
    )

    assert checker(user) is user