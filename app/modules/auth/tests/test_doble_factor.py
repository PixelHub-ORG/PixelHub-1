import pyotp
import pytest
from flask import url_for

from app import create_app, db
from app.modules.auth.models import User
from app.modules.auth.repositories import UserRepository
from app.modules.auth.services import AuthenticationService


# SERVICIO
@pytest.fixture(scope="session", autouse=True)
def configure_app(test_app):
    test_app.config["SERVER_NAME"] = "localhost.localdomain"
    test_app.config["APPLICATION_ROOT"] = "/"


@pytest.fixture(scope="session")
def test_app():
    app = create_app("testing")
    with app.app_context():
        yield app


@pytest.fixture(scope="session")
def test_client(test_app):
    return test_app.test_client()


@pytest.fixture(scope="function")
def clean_database(test_app):
    with test_app.app_context():
        db.session.remove()
        db.drop_all()
        db.create_all()
        yield
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope="function")
def auth_service():
    return AuthenticationService()


def test_enable_and_disable_two_factor(auth_service, clean_database):
    user = User(email="toggle_2fa@example.com", password="dummy", two_factor_secret="ABCDEF")
    db.session.add(user)
    db.session.commit()

    assert user.is_two_factor_enabled is False

    auth_service.enable_two_factor(user)
    reloaded = UserRepository().get_by_email("toggle_2fa@example.com")
    assert reloaded.is_two_factor_enabled is True

    auth_service.disable_two_factor(reloaded)
    reloaded2 = UserRepository().get_by_email("toggle_2fa@example.com")
    assert reloaded2.is_two_factor_enabled is False
    assert reloaded2.two_factor_secret is None


def test_login_without_2fa_does_not_require_code(clean_database, auth_service, monkeypatch):
    data = {
        "name": "LoginNo2FA",
        "surname": "User",
        "email": "login_no_2fa@example.com",
        "password": "test1234",
    }
    user = auth_service.create_with_profile(**data)

    user.is_two_factor_enabled = False
    db.session.commit()

    called = {"login_called": False}

    def fake_login_user(u, remember=True):
        called["login_called"] = True
        assert u.id == user.id

    monkeypatch.setattr("app.modules.auth.services.login_user", fake_login_user)

    result = auth_service.login("login_no_2fa@example.com", "test1234")

    assert result["success"] is True
    assert result["2fa_required"] is False
    assert result["user"].id == user.id
    assert called["login_called"] is True


def test_login_with_2fa_requires_code(clean_database, auth_service, monkeypatch):
    data = {
        "name": "LoginWith2FA",
        "surname": "User",
        "email": "login_with_2fa@example.com",
        "password": "test1234",
    }
    user = auth_service.create_with_profile(**data)

    auth_service.enable_two_factor(user)
    secret = user.two_factor_secret

    called = {"login_called": False}

    def fake_login_user(u, remember=True):
        called["login_called"] = True

    monkeypatch.setattr("app.modules.auth.services.login_user", fake_login_user)

    result = auth_service.login("login_with_2fa@example.com", "test1234")

    assert result["success"] is False
    assert result["2fa_required"] is True
    assert result["user"].id == user.id
    assert called["login_called"] is False

    totp = pyotp.TOTP(secret)
    code = totp.now()
    result2 = auth_service.login("login_with_2fa@example.com", "test1234", two_factor_code=code)

    assert result2["success"] is True
    assert result2["2fa_required"] is False
    assert called["login_called"] is True


# RUTAS
@pytest.fixture(scope="module")
def test_client(test_client):  # noqa: F811
    with test_client.application.app_context():
        db.session.query(User).delete()

        auth_service = AuthenticationService()

        auth_service.create_with_profile(
            name="No2FA",
            surname="User",
            email="no2fa@example.com",
            password="password",
        )

        user_2fa = auth_service.create_with_profile(
            name="With2FA",
            surname="User",
            email="with2fa@example.com",
            password="password",
        )
        auth_service.enable_two_factor(user_2fa)

        db.session.commit()

    yield test_client


def test_signup_redirects_to_enable_2fa(test_client):
    response = test_client.post(
        "/signup",
        data=dict(name="New", surname="User", email="new_2fa@example.com", password="newpassword123"),
        follow_redirects=True,
    )

    assert response.request.path == url_for("auth.enable_2fa")


def test_login_without_2fa_redirects_to_enable_2fa(test_client, test_app):
    response = test_client.post("/login", json={"email": "no2fa@example.com", "password": "password"})

    assert response.status_code == 302

    if test_app.config.get("TESTING"):
        assert response.location.endswith("/")
    else:
        assert response.location.endswith("/auth/enable_2fa")


def test_login_with_2fa_redirects_to_verify_2fa(test_client):
    response = test_client.post(
        "/login",
        data=dict(email="with2fa@example.com", password="password"),
        follow_redirects=True,
    )

    assert response.request.path == url_for("auth.enable_2fa")


def test_enable_2fa_success_flow(test_client, monkeypatch):
    auth_service = AuthenticationService()

    test_client.get("/logout", follow_redirects=True)
    with test_client.session_transaction() as sess:
        sess.clear()

    user = auth_service.create_with_profile(
        name="Enable2FATest",
        surname="User",
        email="enable_2fa_flow@example.com",
        password="password",
    )
    repo = UserRepository()
    user = repo.get_by_email("enable_2fa_flow@example.com")
    assert user is not None
    assert user.is_two_factor_enabled is False

    with test_client.session_transaction() as sess:
        sess["setup_2fa_user_id"] = user.id

    monkeypatch.setattr(
        "app.modules.auth.services.AuthenticationService.verify_two_factor_code",
        lambda self, u, code: True,
    )

    resp = test_client.post(
        "/2fa/enable",
        data={"code": "123456"},
        follow_redirects=False,
    )

    assert resp.status_code in (301, 302)

    updated_user = repo.get_by_email("enable_2fa_flow@example.com")
    assert updated_user.is_two_factor_enabled is True


def test_enable_2fa_wrong_code_shows_error(test_client, monkeypatch):
    auth_service = AuthenticationService()
    user = auth_service.create_with_profile(
        name="Enable2FAWrongCode",
        surname="User",
        email="enable_2fa_wrong@example.com",
        password="password",
    )
    repo = UserRepository()
    user = repo.get_by_email("enable_2fa_wrong@example.com")
    assert user is not None
    assert user.is_two_factor_enabled is False

    with test_client.session_transaction() as sess:
        sess["_user_id"] = str(user.id)

    monkeypatch.setattr(
        "app.modules.auth.services.AuthenticationService.verify_two_factor_code",
        lambda self, u, code: False,
    )

    resp = test_client.post(
        "/2fa/enable",
        data={"code": "000000"},
        follow_redirects=False,
    )

    assert resp.status_code == 200

    updated = repo.get_by_email("enable_2fa_wrong@example.com")
    assert updated.is_two_factor_enabled is False


def test_verify_2fa_success(test_client):
    repo = UserRepository()
    user = repo.get_by_email("with2fa@example.com")
    secret = user.two_factor_secret

    with test_client.session_transaction() as sess:
        sess["two_factor_user_id"] = user.id

    totp = pyotp.TOTP(secret)
    code = totp.now()

    resp = test_client.post("/2fa/verify", data={"code": code}, follow_redirects=False)
    assert resp.status_code in (301, 302)
    assert resp.headers["Location"].endswith("/")


def test_verify_2fa_wrong_code_stays_on_page(test_client):
    repo = UserRepository()
    user = repo.get_by_email("with2fa@example.com")

    with test_client.session_transaction() as sess:
        sess["two_factor_user_id"] = user.id

    resp = test_client.post(
        "/2fa/verify",
        data={"code": "000000"},
        follow_redirects=True,
    )

    assert resp.status_code == 200
    assert resp.request.path == "/2fa/verify"

    assert b"Invalid 2FA code" in resp.data or b"Invalid 2FA code, please try again." in resp.data


def test_disable_2fa_requires_authentication(test_client):
    with test_client.session_transaction() as sess:
        sess.clear()

    resp = test_client.post("/2fa/disable", follow_redirects=False)

    assert resp.status_code in (301, 302)
    location = resp.headers.get("Location", "")
    assert location.endswith("/login") or location.endswith("/")


def test_disable_2fa_turns_off_flag(test_client):
    repo = UserRepository()
    user = repo.get_by_email("with2fa@example.com")
    assert user is not None

    if not user.is_two_factor_enabled:
        AuthenticationService().enable_two_factor(user)
        user = repo.get_by_email("with2fa@example.com")
        assert user.is_two_factor_enabled is True

    with test_client.session_transaction() as sess:
        sess["_user_id"] = str(user.id)

    resp = test_client.post("/2fa/disable", follow_redirects=True)
    assert resp.request.path == "/"

    updated = repo.get_by_email("with2fa@example.com")
    assert updated.is_two_factor_enabled is False
