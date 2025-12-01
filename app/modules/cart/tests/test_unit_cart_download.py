import pytest

from app import db
from app.modules.auth.models import User
from app.modules.cart.models import Cart
from app.modules.conftest import login, logout
from app.modules.dataset.models import DataSet, DSMetaData, PublicationType
from app.modules.filemodel.models import FileModel, FMMetaData
from app.modules.profile.models import UserProfile


@pytest.fixture(scope="module")
def download_env(test_client):
    """
    Fixture dedicado para el test de descargas.
    Crea un entorno limpio (User, Cart, Dataset, FM) y lo destruye al final.
    """
    # Datos para el test
    email = "download_tester@example.com"
    password = "password123"

    user_id = None
    fm_id = None
    dataset_id = None

    # --- SETUP (Creación de datos) ---
    with test_client.application.app_context():
        # 1. Crear Usuario
        user = User(email=email, password=password)
        db.session.add(user)
        db.session.commit()
        user_id = user.id

        # 2. Crear Carrito (Vital para que funcione)
        cart = Cart(user_id=user_id)
        db.session.add(cart)

        # 3. Crear Perfil
        profile = UserProfile(user_id=user_id, name="Downloader", surname="Test", orcid="0000-1111-2222-3333")
        db.session.add(profile)

        # 4. Crear Dataset
        ds_meta = DSMetaData(
            title="Download Dataset", description="Dataset for download test", publication_type=PublicationType.OTHER
        )
        db.session.add(ds_meta)
        db.session.commit()

        dataset = DataSet(user_id=user_id, ds_meta_data_id=ds_meta.id)
        db.session.add(dataset)
        db.session.commit()
        dataset_id = dataset.id

        # 5. Crear File Model
        fm_meta = FMMetaData(
            filename="download_model.uvl",
            title="Download Model",
            description="Model for download test",
            publication_type=PublicationType.JOURNAL_ARTICLE,
            uvl_version="1.0",
        )
        db.session.add(fm_meta)
        db.session.commit()

        fm = FileModel(data_set_id=dataset_id, fm_meta_data_id=fm_meta.id)
        db.session.add(fm)
        db.session.commit()
        fm_id = fm.id

    # Entregamos los datos a los tests
    yield test_client, email, password, fm_id

    # --- TEARDOWN (Limpieza en orden correcto) ---
    with test_client.application.app_context():
        # 1. Borrar Carrito (Elimina los items en cascada)
        if user_id:
            Cart.query.filter_by(user_id=user_id).delete()
            db.session.commit()

        # 2. Borrar File Model (Ahora libre de items)
        if fm_id:
            FileModel.query.filter_by(id=fm_id).delete()
            db.session.commit()

        # 3. Borrar Dataset (Eliminar cualquier dataset asociado al usuario)
        # First remove FileModel rows referencing those datasets, then delete
        # DataSet objects by loading them and calling session.delete() to
        # avoid SQLAlchemy emitting a DELETE with a cartesian product and
        # raising an SAWarning.
        if user_id:
            # collect dataset ids for this user
            ds_list = DataSet.query.filter_by(user_id=user_id).all()
            ds_ids = [d.id for d in ds_list]

            if ds_ids:
                # delete FileModel rows referencing these datasets
                FileModel.query.filter(FileModel.data_set_id.in_(ds_ids)).delete(synchronize_session=False)
                db.session.commit()

                # delete each DataSet instance via session.delete() to avoid
                # generating a multi-from DELETE SQL that can produce an SAWarning
                for ds in ds_list:
                    db.session.delete(ds)
                db.session.commit()

        # 4. Borrar Perfil y Usuario
        if user_id:
            UserProfile.query.filter_by(user_id=user_id).delete()
            User.query.filter_by(id=user_id).delete()
            db.session.commit()


def test_download_cart_empty_returns_400(download_env):
    """
    Prueba que intentar descargar un carrito vacío devuelve error 400.
    """
    test_client, email, password, _ = download_env

    login(test_client, email, password)

    # Aseguramos que el carro esté vacío
    test_client.post("/user/cart/delete", json={})

    response = test_client.get("/user/cart/download")

    assert response.status_code == 400
    assert "Cart is empty" in response.get_json()["message"]

    logout(test_client)


def test_download_cart_with_items_returns_zip(download_env):
    """
    Prueba el flujo correcto: Añadir item -> Descargar ZIP.
    """
    test_client, email, password, fm_id = download_env

    login(test_client, email, password)

    # 1. Añadir item al carro
    add_resp = test_client.post("/filemodel/cart/add", json={"item_id": fm_id})
    assert add_resp.status_code == 200, f"Fallo al añadir: {add_resp.data}"

    # 2. Descargar
    response = test_client.get("/user/cart/download")

    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/zip"
    assert "attachment; filename=" in response.headers["Content-Disposition"]

    # 3. Limpieza del test (Vaciar carro)
    # Es vital vaciar el carro aquí para que el Teardown del fixture
    # pueda borrar el FileModel sin errores de Foreign Key.
    test_client.post("/user/cart/delete", json={"item_id": fm_id})

    logout(test_client)
