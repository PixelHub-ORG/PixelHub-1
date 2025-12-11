import pytest

from app import db
from app.modules.auth.models import User
from app.modules.cart.services import CartService
from app.modules.conftest import login, logout
from app.modules.dataset.models import DataSet, DSMetaData, PublicationType
from app.modules.filemodel.models import FileModel, FMMetaData
from app.modules.profile.models import UserProfile


@pytest.fixture(scope="module")
def test_data(test_client):
    """
    Crea un usuario, un dataset y un filemodel.
    """
    with test_client.application.app_context():
        user = User(email="cart_test@example.com", password="password123")
        db.session.add(user)
        db.session.commit()

        ds_meta = DSMetaData(title="Test DS", description="D", publication_type=PublicationType.NONE)
        dataset = DataSet(user_id=user.id, ds_meta_data=ds_meta)
        db.session.add(dataset)
        db.session.commit()

        fm_meta = FMMetaData(filename="test.uvl", title="Test FM", description="D",
                             publication_type=PublicationType.NONE, uvl_version="1.0")
        file_model = FileModel(data_set_id=dataset.id, fm_meta_data=fm_meta)
        db.session.add(file_model)
        db.session.commit()

        yield user, file_model

        db.session.delete(file_model)
        db.session.delete(dataset)
        db.session.delete(user)
        db.session.commit()


def test_cart_service_add_and_remove(test_client, test_data):
    """
    Prueba la lógica de CartService.
    """
    user, file_model = test_data
    service = CartService()

    with test_client.application.app_context():
        response, code = service.add_to_cart(user.id, file_model.id)
        assert code == 200
        assert "added to cart" in response["message"]

        cart = service.cart_repository.get_cart_by_user_id(user.id)
        assert len(cart.items) == 1
        assert cart.items[0].file_model_id == file_model.id

        response, code = service.add_to_cart(user.id, file_model.id)
        assert code == 400
        assert "already in cart" in response["message"]

        response, code = service.delete_from_cart(user.id, file_model.id)
        assert code == 200
        assert len(cart.items) == 0


def test_route_add_to_cart(test_client, test_data):
    """
    Prueba el POST /filemodel/cart/add
    """
    user, file_model = test_data

    test_client.post("/login", data={"email": "cart_test@example.com", "password": "password123"})

    response = test_client.post("/filemodel/cart/add", json={"item_id": file_model.id})
    assert response.status_code == 200
    assert response.is_json
    assert "added to cart" in response.get_json()["message"]


def test_route_view_cart_page(test_client, test_data):
    """
    Prueba que la página del carrito carga correctamente (GET).
    """
    test_client.post("/login", data={"email": "cart_test@example.com", "password": "password123"})

    response = test_client.get("/user/cart/view_page")
    assert response.status_code == 200
    assert b"Test FM" in response.data


@pytest.fixture(scope="module")
def test_client_with_user(test_client):
    """
    Extend the test_client to create a test user with an associated profile.
    """
    with test_client.application.app_context():
        User.query.filter_by(email="user_cart@example.com").delete()
        db.session.commit()

        user_test = User(email="user_cart@example.com", password="test1234")
        db.session.add(user_test)
        db.session.commit()

        profile = UserProfile(
            user_id=user_test.id,
            name="Name",
            surname="Surname",
            affiliation="Test University",
            orcid="0000-0000-0000-0000",
        )
        db.session.add(profile)
        db.session.commit()

    yield test_client


@pytest.fixture(scope="module")
def setup_user_and_model(test_client_with_user):
    """
    Creates a user and a test FileModel.
    Returns (test_client, fm_id, user_email, dummy_ds_id).
    """
    test_client = test_client_with_user
    user_email = "user_cart@example.com"
    fm_id = None

    with test_client.application.app_context():
        user = User.query.filter_by(email=user_email).first()

        dummy_ds_metadata = DSMetaData(
            title="Dummy Dataset Meta", description="Dummy description", publication_type=PublicationType.OTHER
        )
        db.session.add(dummy_ds_metadata)
        db.session.commit()

        dummy_dataset = DataSet(user_id=user.id, ds_meta_data_id=dummy_ds_metadata.id)
        db.session.add(dummy_dataset)
        db.session.commit()
        dummy_ds_id = dummy_dataset.id

        fm_meta_data = FMMetaData(
            filename="test_fm.uvl",
            title="Test File Model for Cart",
            description="A file model for cart testing.",
            publication_type=PublicationType.JOURNAL_ARTICLE,
        )
        db.session.add(fm_meta_data)
        db.session.commit()

        test_file_model = FileModel(
            data_set_id=dummy_dataset.id,
            fm_meta_data_id=fm_meta_data.id,
        )
        db.session.add(test_file_model)
        db.session.commit()
        fm_id = test_file_model.id

    yield test_client, fm_id, user_email, dummy_ds_id

    with test_client.application.app_context():
        if fm_id:
            FileModel.query.filter_by(id=fm_id).delete()
        if dummy_ds_id:
            DataSet.query.filter_by(id=dummy_ds_id).delete()
        db.session.commit()


def test_create_dataset_from_empty_cart_returns_400(setup_user_and_model):
    """
    If the cart is empty, the API must return 400.
    """
    test_client, _, user_email, _ = setup_user_and_model
    login_response = login(test_client, user_email, "test1234")
    assert login_response.status_code == 200, "Login failed."

    form_data = {
        "title": "My cart dataset",
        "desc": "Dataset created from an empty cart",
        "publication_type": PublicationType.JOURNAL_ARTICLE.value,
    }

    response = test_client.post("/user/cart/create", data=form_data)
    assert response.status_code == 400, "Expected 400 for empty cart."

    data = response.get_json()
    assert data is not None
    assert "message" in data
    assert "Cart is empty" in data["message"]

    logout(test_client)


def test_add_nonexistent_file_model_to_cart_returns_404(setup_user_and_model):
    """
    Attempt to add a FileModel ID that doesn't exist.
    """
    test_client, _, user_email, _ = setup_user_and_model
    login(test_client, user_email, "test1234")

    non_existent_id = 999999

    response = test_client.post("/filemodel/cart/add", json={"item_id": non_existent_id})

    assert response.status_code in [404, 400], "Expected 404/400 for nonexistent FM."

    logout(test_client)


def test_remove_file_model_from_cart_success(setup_user_and_model):
    """
    Add a FileModel and then remove it.
    """
    test_client, fm_id, user_email, _ = setup_user_and_model
    login(test_client, user_email, "test1234")

    test_client.post("/filemodel/cart/add", json={"item_id": fm_id})

    response = test_client.post("/user/cart/delete", json={"item_id": fm_id})
    assert response.status_code == 200, "Expected 200 upon removal from cart."

    logout(test_client)


def setup_cart_and_login(test_client, fm_id, user_email):
    """
    Helper function to ensure the cart is full and the user is logged in.
    """
    login(test_client, user_email, "test1234")
    test_client.post("/filemodel/cart/add", json={"item_id": fm_id})


def test_create_dataset_missing_required_fields_returns_400(setup_user_and_model):
    """
    Missing mandatory fields like 'title'
    """
    test_client, fm_id, user_email, _ = setup_user_and_model
    setup_cart_and_login(test_client, fm_id, user_email)

    form_data = {
        "desc": "Missing data",
        "publication_type": PublicationType.JOURNAL_ARTICLE.value,
    }

    response = test_client.post("/user/cart/create", data=form_data)
    assert response.status_code == 400, "Expected 400 due to missing 'title'."

    data = response.get_json()

    assert data is not None
    assert "title" in data.get("message", {}) or "title" in data.get(
        "errors", {}
    ), "The error must mention the 'title' field."
    logout(test_client)


def test_create_dataset_with_invalid_publication_type_returns_400(setup_user_and_model):
    """
    Invalid publication type.
    """
    test_client, fm_id, user_email, _ = setup_user_and_model
    setup_cart_and_login(test_client, fm_id, user_email)

    form_data = {
        "title": "Invalid Type",
        "desc": "Incorrect publication type",
        "publication_type": "INVALID_TYPE_ENUM",
    }

    response = test_client.post("/user/cart/create", data=form_data)
    assert response.status_code == 400, "Expected 400 for invalid publication type."

    logout(test_client)


def test_create_dataset_with_invalid_doi_format_returns_400(setup_user_and_model):
    """
    Invalid DOI format.
    """
    test_client, fm_id, user_email, _ = setup_user_and_model
    setup_cart_and_login(test_client, fm_id, user_email)

    form_data = {
        "title": "Invalid DOI",
        "desc": "Testing invalid DOI format",
        "publication_type": PublicationType.JOURNAL_ARTICLE.value,
        "publication_doi": "This is not a valid DOI",
    }

    response = test_client.post("/user/cart/create", data=form_data)
    assert response.status_code == 400, "Expected 400 for invalid DOI format."

    data = response.get_json()

    assert data is not None
    assert "publication_doi" in data.get("message", {}) or "publication_doi" in data.get(
        "errors", {}
    ), "The error must mention the 'publication_doi' field."
    logout(test_client)
