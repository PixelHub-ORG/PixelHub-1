import pytest
from unittest.mock import patch # <--- Import necesario

from app import db
from app.modules.auth.models import User
from app.modules.auth.services import AuthenticationService # <--- Import necesario
from app.modules.cart.models import Cart
from app.modules.conftest import logout # Quitamos login, usaremos uno personalizado
from app.modules.dataset.models import DataSet, DSMetaData, PublicationType
from app.modules.filemodel.models import FileModel, FMMetaData
from app.modules.profile.models import UserProfile


# --- HELPER PARA LOGIN CON 2FA ---
def login_with_2fa(client, email, password):
    """
    Simula el flujo de login en dos pasos usando el test_client.
    1. Post de credenciales.
    2. Post del código 2FA (mockeado).
    """
    # 1. Primer paso: Credenciales
    response = client.post("/login", data=dict(email=email, password=password), follow_redirects=True)
    
    # Verificamos que no haya fallado el primer paso (normalmente redirige a la página de 2FA)
    assert response.status_code == 200
    
    # 2. Segundo paso: Enviar el código
    # NOTA: Ajusta la ruta "/auth/verify_2fa" si tu ruta real es diferente (ej: /login/verify)
    # Basado en tu Selenium, aquí simulamos enviar el código.
    response_2fa = client.post("/auth/verify_2fa", data=dict(code="000000"), follow_redirects=True)
    
    assert response_2fa.status_code == 200
    return response_2fa


@pytest.fixture(scope="module")
def download_env(test_client):
    """
    Fixture dedicado para el test de descargas CON 2FA ACTIVO.
    """
    email = "download_tester@example.com"
    password = "password123"

    user_id = None
    fm_id = None
    
    # --- MOCK 2FA ---
    # Iniciamos el patch antes de crear nada para asegurar que el entorno es consistente
    patcher = patch.object(AuthenticationService, "verify_two_factor_code", return_value=True)
    mock_verify = patcher.start()

    with test_client.application.app_context():
        # 1. Crear Usuario CON 2FA HABILITADO
        user = User(
            email=email, 
            password=password,
            is_two_factor_enabled=True,    # <--- Activamos 2FA
            two_factor_secret="MOCKSECRET" # <--- Secreto dummy
        )
        db.session.add(user)
        db.session.commit()
        user_id = user.id

        # 2. Crear Carrito
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

    # --- TEARDOWN ---
    patcher.stop() # Detenemos el mock

    with test_client.application.app_context():
        if user_id:
            Cart.query.filter_by(user_id=user_id).delete()
            db.session.commit()

        if fm_id:
            FileModel.query.filter_by(id=fm_id).delete()
            db.session.commit()

        if user_id:
            ds_list = DataSet.query.filter_by(user_id=user_id).all()
            ds_ids = [d.id for d in ds_list]

            if ds_ids:
                FileModel.query.filter(FileModel.data_set_id.in_(ds_ids)).delete(synchronize_session=False)
                db.session.commit()
                for ds in ds_list:
                    db.session.delete(ds)
                db.session.commit()

        if user_id:
            UserProfile.query.filter_by(user_id=user_id).delete()
            User.query.filter_by(id=user_id).delete()
            db.session.commit()


def test_download_cart_empty_returns_400(download_env):
    """
    Prueba que intentar descargar un carrito vacío devuelve error 400.
    """
    test_client, email, password, _ = download_env

    # USAMOS EL NUEVO LOGIN CON 2FA
    login_with_2fa(test_client, email, password)

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

    # USAMOS EL NUEVO LOGIN CON 2FA
    login_with_2fa(test_client, email, password)

    # 1. Añadir item al carro
    add_resp = test_client.post("/filemodel/cart/add", json={"item_id": fm_id})
    assert add_resp.status_code == 200, f"Fallo al añadir: {add_resp.data}"

    # 2. Descargar
    response = test_client.get("/user/cart/download")

    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/zip"
    assert "attachment; filename=" in response.headers["Content-Disposition"]

    # 3. Limpieza del test
    test_client.post("/user/cart/delete", json={"item_id": fm_id})

    logout(test_client)