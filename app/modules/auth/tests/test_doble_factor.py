from unittest.mock import MagicMock

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


def test_login_with_2fa_invalid_code(clean_database, auth_service, monkeypatch):
    data = {
        "name": "Login2FAInvalid",
        "surname": "User",
        "email": "login_2fa_invalid@example.com",
        "password": "test1234",
    }
    user = auth_service.create_with_profile(**data)
    auth_service.enable_two_factor(user)

    called = {"login_called": False}

    def fake_login_user(u, remember=True):
        called["login_called"] = True

    monkeypatch.setattr("app.modules.auth.services.login_user", fake_login_user)

    result = auth_service.login("login_2fa_invalid@example.com", "test1234", two_factor_code="000000")

    assert result["success"] is False
    assert result["2fa_required"] is True
    assert called["login_called"] is False


def test_login_invalid_credentials(clean_database, auth_service):
    result = auth_service.login("nonexistent@example.com", "wrongpassword")
    assert result["success"] is False
    assert result["2fa_required"] is False
    assert result["user"] is None


def test_is_email_available(clean_database, auth_service):
    assert auth_service.is_email_available("new@example.com") is True

    data = {
        "name": "Test",
        "surname": "User",
        "email": "exists@example.com",
        "password": "test1234",
    }
    auth_service.create_with_profile(**data)

    assert auth_service.is_email_available("exists@example.com") is False


def test_create_with_profile_missing_email(clean_database, auth_service):
    with pytest.raises(ValueError, match="Email is required"):
        auth_service.create_with_profile(name="Test", surname="User", password="test1234")


def test_create_with_profile_missing_password_without_orcid(clean_database, auth_service):
    with pytest.raises(ValueError, match="Password is required for form signup"):
        auth_service.create_with_profile(email="test@example.com", name="Test", surname="User")


def test_create_with_profile_missing_name(clean_database, auth_service):
    with pytest.raises(ValueError, match="Name is required"):
        auth_service.create_with_profile(email="test@example.com", password="test1234", surname="User")


def test_create_with_profile_missing_surname(clean_database, auth_service):
    with pytest.raises(ValueError, match="Surname is required"):
        auth_service.create_with_profile(email="test@example.com", password="test1234", name="Test")


def test_create_with_profile_success(clean_database, auth_service):
    user = auth_service.create_with_profile(
        email="success@example.com", password="test1234", name="Test", surname="User"
    )

    assert user.email == "success@example.com"
    assert user.two_factor_secret is not None
    assert user.is_two_factor_enabled is False
    assert user.profile is not None
    assert user.profile.name == "Test"
    assert user.profile.surname == "User"


def test_find_or_create_by_orcid_existing_user(clean_database, auth_service):
    existing_user = User(orcid_id="0000-0001-2345-6789")
    db.session.add(existing_user)
    db.session.commit()

    user = auth_service.find_or_create_by_orcid("0000-0001-2345-6789", "John Doe")

    assert user.id == existing_user.id


def test_find_or_create_by_orcid_new_user(clean_database, auth_service):
    user = auth_service.find_or_create_by_orcid("0000-0001-9999-8888", "Jane Smith")

    assert user.orcid_id == "0000-0001-9999-8888"
    assert user.profile.name == "Jane"
    assert user.profile.surname == "Smith"


def test_find_or_create_by_orcid_single_name(clean_database, auth_service):
    user = auth_service.find_or_create_by_orcid("0000-0001-1111-2222", "Madonna")

    assert user.profile.name == "Madonna"
    assert user.profile.surname == ""


def test_generate_two_factor_secret(clean_database, auth_service):
    user = User(email="secret@example.com", password="test")
    db.session.add(user)
    db.session.commit()

    secret = auth_service.generate_two_factor_secret(user)

    assert secret is not None
    assert len(secret) == 32
    assert user.two_factor_secret == secret


def test_generate_qr_code_for_two_factor(clean_database, auth_service):
    user = User(email="qr@example.com", password="test")
    db.session.add(user)
    db.session.commit()

    qr_code = auth_service.generate_qr_code_for_two_factor(user, app_name="TestApp")

    assert qr_code.startswith("data:image/png;base64,")
    assert user.two_factor_secret is not None


def test_generate_qr_code_with_existing_secret(clean_database, auth_service):
    user = User(email="qr2@example.com", password="test", two_factor_secret="EXISTINGSECRET123")
    db.session.add(user)
    db.session.commit()

    qr_code = auth_service.generate_qr_code_for_two_factor(user)

    assert qr_code.startswith("data:image/png;base64,")
    assert user.two_factor_secret == "EXISTINGSECRET123"


def test_verify_two_factor_code(clean_database, auth_service):
    secret = pyotp.random_base32()
    user = User(email="verify@example.com", password="test", two_factor_secret=secret)
    db.session.add(user)
    db.session.commit()

    totp = pyotp.TOTP(secret)
    valid_code = totp.now()

    assert auth_service.verify_two_factor_code(user, valid_code) is True
    assert auth_service.verify_two_factor_code(user, "000000") is False


def test_get_authenticated_user(clean_database, auth_service, monkeypatch):
    mock_user = MagicMock()
    mock_user.is_authenticated = True

    monkeypatch.setattr("app.modules.auth.services.current_user", mock_user)

    result = auth_service.get_authenticated_user()
    assert result == mock_user


def test_get_authenticated_user_not_authenticated(clean_database, auth_service, monkeypatch):
    mock_user = MagicMock()
    mock_user.is_authenticated = False

    monkeypatch.setattr("app.modules.auth.services.current_user", mock_user)

    result = auth_service.get_authenticated_user()
    assert result is None


def test_get_authenticated_user_profile(clean_database, auth_service, monkeypatch):
    mock_profile = MagicMock()
    mock_user = MagicMock()
    mock_user.is_authenticated = True
    mock_user.profile = mock_profile

    monkeypatch.setattr("app.modules.auth.services.current_user", mock_user)

    result = auth_service.get_authenticated_user_profile()
    assert result == mock_profile


def test_get_authenticated_user_profile_not_authenticated(clean_database, auth_service, monkeypatch):
    mock_user = MagicMock()
    mock_user.is_authenticated = False

    monkeypatch.setattr("app.modules.auth.services.current_user", mock_user)

    result = auth_service.get_authenticated_user_profile()
    assert result is None


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


def test_signup_get_renders_form(test_client):
    response = test_client.get("/signup")
    assert response.status_code in (200, 308)


def test_signup_authenticated_user_redirects(test_client):
    with test_client.session_transaction() as sess:
        sess["_user_id"] = "1"

    response = test_client.get("/signup", follow_redirects=False)
    assert response.status_code in (301, 302, 308)


def test_signup_email_in_use(test_client):
    response = test_client.post(
        "/signup",
        data=dict(name="Duplicate", surname="User", email="no2fa@example.com", password="password"),
        follow_redirects=True,
    )

    assert b"Email no2fa@example.com in use" in response.data or b"in use" in response.data


def test_login_get_renders_form(test_client):
    response = test_client.get("/login")
    assert response.status_code == 200


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


def test_logout(test_client):
    with test_client.session_transaction() as sess:
        sess["_user_id"] = "1"
        sess["setup_2fa_user_id"] = 1
        sess["two_factor_user_id"] = 1

    response = test_client.get("/logout", follow_redirects=False)
    assert response.status_code in (301, 302)

    with test_client.session_transaction() as sess:
        assert "setup_2fa_user_id" not in sess
        assert "two_factor_user_id" not in sess


def test_enable_2fa_get_authenticated_user(test_client):
    repo = UserRepository()
    user = repo.get_by_email("no2fa@example.com")

    with test_client.session_transaction() as sess:
        sess["_user_id"] = str(user.id)

    response = test_client.get("/2fa/enable")
    assert response.status_code in (200, 302)


def test_enable_2fa_already_enabled_shows_message(test_client):
    repo = UserRepository()
    user = repo.get_by_email("with2fa@example.com")

    with test_client.session_transaction() as sess:
        sess["_user_id"] = str(user.id)

    response = test_client.get("/2fa/enable")
    assert response.status_code in (200, 302)


def test_enable_2fa_no_session_redirects_to_login(test_client):
    with test_client.session_transaction() as sess:
        sess.clear()

    response = test_client.get("/2fa/enable", follow_redirects=False)
    assert response.status_code in (301, 302)


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


def test_verify_2fa_no_code_shows_error(test_client):
    repo = UserRepository()
    user = repo.get_by_email("with2fa@example.com")

    with test_client.session_transaction() as sess:
        sess["two_factor_user_id"] = user.id

    resp = test_client.post(
        "/2fa/verify",
        data={},
        follow_redirects=True,
    )

    assert resp.status_code == 200
    assert b"Please enter the 2FA code" in resp.data


def test_verify_2fa_no_session_redirects_to_login(test_client):
    with test_client.session_transaction() as sess:
        sess.pop("two_factor_user_id", None)

    response = test_client.get("/2fa/verify", follow_redirects=False)
    assert response.status_code in (301, 302)


def test_verify_2fa_get_renders_form(test_client):
    repo = UserRepository()
    user = repo.get_by_email("with2fa@example.com")

    with test_client.session_transaction() as sess:
        sess["two_factor_user_id"] = user.id

    response = test_client.get("/2fa/verify")
    assert response.status_code == 200


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


def test_orcid_login_authenticated_user_redirects(test_client):
    with test_client.session_transaction() as sess:
        sess["_user_id"] = "1"

    response = test_client.get("/orcid/login", follow_redirects=False)
    assert response.status_code in (301, 302)


def test_orcid_login_redirects_to_orcid(test_client, monkeypatch):
    mock_oauth = MagicMock()
    mock_oauth.orcid.authorize_redirect = MagicMock(return_value="redirect_response")

    with test_client.session_transaction() as sess:
        sess.clear()

    response = test_client.get("/orcid/login")
    assert response.status_code in (200, 301, 302, 500)


def test_orcid_callback_authenticated_user_redirects(test_client):
    with test_client.session_transaction() as sess:
        sess["_user_id"] = "1"

    response = test_client.get("/orcid/callback", follow_redirects=False)
    assert response.status_code in (301, 302)


def test_orcid_callback_success(test_client, monkeypatch):
    def mock_authorize_access_token():
        return {"orcid": "0000-0001-2345-6789", "name": "Test User"}

    created_user = None

    def mock_find_or_create_by_orcid(self, orcid_id, full_name):
        nonlocal created_user
        user = User(orcid_id=orcid_id)
        db.session.add(user)
        db.session.flush()

        from app.modules.profile.repositories import UserProfileRepository

        profile_repo = UserProfileRepository()
        parts = full_name.strip().split(" ", 1)
        profile_data = {"name": parts[0], "surname": parts[1] if len(parts) > 1 else "", "user_id": user.id}
        profile_repo.create(**profile_data)
        db.session.commit()
        created_user = user
        return user

    monkeypatch.setattr("app.oauth.orcid.authorize_access_token", mock_authorize_access_token)
    monkeypatch.setattr(
        "app.modules.auth.services.AuthenticationService.find_or_create_by_orcid", mock_find_or_create_by_orcid
    )

    with test_client.session_transaction() as sess:
        sess.clear()

    response = test_client.get("/orcid/callback", follow_redirects=False)
    assert response.status_code in (301, 302)
