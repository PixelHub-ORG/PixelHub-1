import pytest
import pyotp
from flask import url_for

from app import db, create_app
from app.modules.auth.repositories import UserRepository
from app.modules.auth.services import AuthenticationService
from app.modules.profile.repositories import UserProfileRepository
from app.modules.auth.models import User

#SERVICIO
@pytest.fixture(scope="session", autouse=True)
def configure_app(test_app):
    test_app.config['SERVER_NAME'] = 'localhost.localdomain'
    test_app.config['APPLICATION_ROOT'] = '/'

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


#RUTAS
@pytest.fixture(scope="module")

def test_client(test_client):
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
