from unittest.mock import patch

import pytest

from app import db
from app.modules.auth.models import User
from app.modules.auth.services import AuthenticationService
from app.modules.cart.models import Cart
from app.modules.conftest import logout
from app.modules.dataset.models import DataSet, DSMetaData, PublicationType
from app.modules.filemodel.models import FileModel, FMMetaData
from app.modules.profile.models import UserProfile


def login_with_2fa(client, email, password):
    r1 = client.post(
        "/login",
        data={
            "email": email,
            "password": password},
        follow_redirects=True)
    assert r1.status_code == 200
    r2 = client.post(
        "/2fa/verify",
        data={
            "code": "000000"},
        follow_redirects=True)
    assert r2.status_code == 200
    return r2


@pytest.fixture(scope="module")
def download_env(test_client):
    email = "download_tester@example.com"
    password = "password123"

    patcher = patch.object(
        AuthenticationService,
        "verify_two_factor_code",
        return_value=True)
    patcher.start()

    with test_client.application.app_context():
        user = User(
            email=email,
            password=password,
            is_two_factor_enabled=True,
            two_factor_secret="MOCKSECRET")
        db.session.add(user)
        db.session.commit()

        db.session.add(Cart(user_id=user.id))
        db.session.add(
            UserProfile(
                user_id=user.id,
                name="Downloader",
                surname="Test",
                orcid="0000-1111-2222-3333"))

        ds_meta = DSMetaData(
            title="Download Dataset",
            description="Dataset for download test",
            publication_type=PublicationType.OTHER,
        )
        db.session.add(ds_meta)
        db.session.commit()

        dataset = DataSet(user_id=user.id, ds_meta_data_id=ds_meta.id)
        db.session.add(dataset)
        db.session.commit()

        fm_meta = FMMetaData(
            filename="download_model.uvl",
            title="Download Model",
            description="Model for download test",
            publication_type=PublicationType.JOURNAL_ARTICLE,
            uvl_version="1.0",
        )
        db.session.add(fm_meta)
        db.session.commit()

        fm = FileModel(data_set_id=dataset.id, fm_meta_data_id=fm_meta.id)
        db.session.add(fm)
        db.session.commit()
        fm_id = fm.id
        user_id = user.id
        ds_meta_id = ds_meta.id
        fm_meta_id = fm_meta.id

    yield test_client, email, password, fm_id

    patcher.stop()

    with test_client.application.app_context():
        Cart.query.filter_by(user_id=user_id).delete()
        UserProfile.query.filter_by(user_id=user_id).delete()
        FileModel.query.filter_by(id=fm_id).delete()

        for ds in DataSet.query.filter_by(user_id=user_id).all():
            db.session.delete(ds)

        DSMetaData.query.filter_by(id=ds_meta_id).delete()
        FMMetaData.query.filter_by(id=fm_meta_id).delete()

        User.query.filter_by(id=user_id).delete()
        db.session.commit()


def test_download_cart_empty_returns_400(download_env):
    test_client, email, password, _ = download_env
    login_with_2fa(test_client, email, password)
    test_client.post("/user/cart/delete", json={})
    r = test_client.get("/user/cart/download")
    assert r.status_code == 400
    assert "Cart is empty" in r.get_json()["message"]
    logout(test_client)


def test_download_cart_with_items_returns_zip(download_env):
    test_client, email, password, fm_id = download_env
    login_with_2fa(test_client, email, password)
    add_resp = test_client.post("/filemodel/cart/add", json={"item_id": fm_id})
    assert add_resp.status_code == 200
    r = test_client.get("/user/cart/download")
    assert r.status_code == 200
    assert r.headers["Content-Type"] == "application/zip"
    assert "attachment; filename=" in r.headers["Content-Disposition"]
    test_client.post("/user/cart/delete", json={"item_id": fm_id})
    logout(test_client)
