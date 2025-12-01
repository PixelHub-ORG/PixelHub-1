import json
from unittest.mock import MagicMock

import pytest

from app.modules.zenodo.services import ZenodoService


@pytest.fixture(scope="module")
def test_client(test_client):
    """
    Extiende el fixture test_client.
    No se necesita configuración de base de datos específica para el índice de Zenodo.
    """
    with test_client.application.app_context():
        # No se añaden nuevos elementos a la BD para estos tests
        pass

    yield test_client


def test_sample_assertion(test_client):
    """
    Test de ejemplo para verificar que el entorno de pruebas funciona.

    """
    greeting = "Hello, Zenodo!"
    assert greeting == "Hello, Zenodo!", "El saludo no coincide"


def test_zenodo_index_route(test_client):
    """
    Testea que la ruta principal del módulo Zenodo cargue correctamente.
    """
    # No se necesita login para esta ruta
    response = test_client.get("/zenodo")

    assert response.status_code == 200


def test_zenodo_test_route_success(test_client, mocker):
    """
    Prueba la ruta /zenodo/test simulando una conexión exitosa completa.
    """

    # 1. Mockear os.getenv
    def mock_getenv(key, default=None):
        if key == "FLASK_ENV":
            return "development"
        if key == "FAKENODO_URL":
            return "http://fakenodo/api"
        if key == "WORKING_DIR":
            return "/app"
        return default

    mocker.patch("app.modules.zenodo.services.os.getenv", side_effect=mock_getenv)

    # 2. Mockear 'requests.post' (Crear deposition y Subir archivo)
    mock_post_create = mocker.MagicMock()
    mock_post_create.status_code = 201
    mock_post_create.json.return_value = {"id": "12345"}

    mock_post_upload = mocker.MagicMock()
    mock_post_upload.status_code = 201

    mocker.patch("app.modules.zenodo.services.requests.post", side_effect=[mock_post_create, mock_post_upload])

    # 3. Mockear 'requests.delete'
    mock_delete = mocker.MagicMock()
    mock_delete.status_code = 204  # No Content
    mocker.patch("app.modules.zenodo.services.requests.delete", return_value=mock_delete)

    # 4. Mockear operaciones de fichero (open, os.path.exists, os.remove)
    mocker.patch("builtins.open", mocker.mock_open())
    mocker.patch("app.modules.zenodo.services.os.path.exists", return_value=True)
    mocker.patch("app.modules.zenodo.services.os.remove")

    response = test_client.get("/zenodo/test")
    data = json.loads(response.data)

    assert response.status_code == 200
    assert data["success"] is True
    assert data["messages"] == []


def test_zenodo_test_route_fail_create_deposition(test_client, mocker):
    """
    Prueba la ruta /zenodo/test cuando falla la creación del 'deposition'.
    """

    # 1. Mock de 'requests.post' para que falle en la primera llamada
    mock_post_fail = mocker.MagicMock()
    mock_post_fail.status_code = 500
    mock_post_fail.text = "Error Interno del Servidor"

    mocker.patch("app.modules.zenodo.services.os.getenv", return_value="development")
    mocker.patch("app.modules.zenodo.services.requests.post", return_value=mock_post_fail)
    mocker.patch("builtins.open", mocker.mock_open())
    mocker.patch("app.modules.zenodo.services.os.path.exists", return_value=True)
    mocker.patch("app.modules.zenodo.services.os.remove")

    response = test_client.get("/zenodo/test")
    data = json.loads(response.data)

    assert response.status_code == 200
    assert data["success"] is False
    assert "Failed to create test deposition" in data["messages"]


def test_zenodo_test_route_fail_upload(test_client, mocker):
    """
    Prueba la ruta /zenodo/test cuando falla la subida del archivo.
    """

    # 1. Mocks de 'requests.post'
    mock_post_create = mocker.MagicMock()
    mock_post_create.status_code = 201
    mock_post_create.json.return_value = {"id": "12345"}

    mock_post_upload_fail = mocker.MagicMock()
    mock_post_upload_fail.status_code = 400
    mock_post_upload_fail.content = b"Upload Error"

    mocker.patch("app.modules.zenodo.services.requests.post", side_effect=[mock_post_create, mock_post_upload_fail])

    # 2. Mock de 'requests.delete'
    mock_delete = mocker.MagicMock()
    mock_delete.status_code = 204
    mocker.patch("app.modules.zenodo.services.requests.delete", return_value=mock_delete)

    # 3. Mockear operaciones de fichero
    mocker.patch("builtins.open", mocker.mock_open())
    mocker.patch("app.modules.zenodo.services.os.path.exists", return_value=True)
    mocker.patch("app.modules.zenodo.services.os.remove")

    response = test_client.get("/zenodo/test")
    data = json.loads(response.data)

    assert response.status_code == 200
    assert data["success"] is False
    assert "Failed to upload test file" in data["messages"][0]


def test_service_get_zenodo_url_uses_fakenodo_env_var(test_client, mocker):
    """
    Prueba que get_zenodo_url usa la variable de entorno FAKENODO_URL
    cuando está definida
    """

    # 1. Definimos una URL de prueba personalizada
    test_fakenodo_url = "https://mi-zenodo-personalizado.com/api"

    # 2. Creamos un mock inteligente para os.getenv
    def mock_getenv_side_effect(key, default=None):
        if key == "FLASK_ENV":
            return "development"  # Simula entorno de desarrollo
        if key == "FAKENODO_BACKEND_URL":
            return test_fakenodo_url  # Simula que la variable SÍ está definida
        return default

    # 3. Aplicamos el mock
    mocker.patch("app.modules.zenodo.services.os.getenv", side_effect=mock_getenv_side_effect)

    # 4. Ejecutamos y verificamos
    with test_client.application.app_context():
        service = ZenodoService()
        # El servicio ahora debe tomar la URL del mock
        assert service.get_zenodo_url() == test_fakenodo_url


def test_service_get_zenodo_url_uses_default_when_no_env_var(test_client, mocker):
    """
    Prueba que get_zenodo_url usa la URL por defecto cuando
    FAKENODO_URL NO está definida.
    """

    # 1. Creamos un mock que simula que FAKENODO_URL no está definida
    def mock_getenv_side_effect(key, default=None):
        if key == "FLASK_ENV":
            return "development"
        if key == "FAKENODO_URL":
            return default
        return default

    # 2. Aplicamos el mock
    mocker.patch("app.modules.zenodo.services.os.getenv", side_effect=mock_getenv_side_effect)

    # 3. Ejecutamos y verificamos
    with test_client.application.app_context():
        service = ZenodoService()
        assert service.get_zenodo_url() == "http://localhost:5001/api"


@pytest.fixture
def mock_service(mocker, test_client):
    """
    Fixture que crea una instancia de ZenodoService con todo mockeado
    para que no haga llamadas reales a la API de Zenodo.
    """

    # 1. Mockear os.getenv para que no dependa de variables de entorno
    def mock_getenv(key, default=None):
        if key == "FLASK_ENV":
            return "development"
        if key == "FAKENODO_URL":
            return "http://fake-zenodo.test/api"
        if key == "ZENODO_ACCESS_TOKEN":
            return "TEST_TOKEN"
        return default

    mocker.patch("app.modules.zenodo.services.os.getenv", side_effect=mock_getenv)

    # 2. Mockear todas las llamadas
    mocker.patch("app.modules.zenodo.services.requests.get")
    mocker.patch("app.modules.zenodo.services.requests.post")
    mocker.patch("app.modules.zenodo.services.requests.delete")

    # 3. Mockear operaciones de ficheros
    mocker.patch("builtins.open", mocker.mock_open())
    mocker.patch("app.modules.zenodo.services.os.path.exists", return_value=True)
    mocker.patch("app.modules.zenodo.services.os.remove")
    mocker.patch("app.modules.zenodo.services.os.path.join", return_value="/fake/path/file.txt")

    # 4. Mockear dependencias de otros módulos
    mocker.patch("app.modules.zenodo.services.uploads_folder_name", return_value="/fake/uploads")
    mocker.patch("app.modules.dataset.models.DSMetaData.query")

    # Devolvemos una instancia del servicio
    with test_client.application.app_context():
        service = ZenodoService()
        yield service, mocker


def test_service_init_with_token(mocker):
    """
    Prueba que el __init__ configura correctamente el token.
    """

    def mock_getenv(key, default=None):
        if key == "ZENODO_ACCESS_TOKEN":
            return "MI_TOKEN_SECRETO"
        return default

    mocker.patch("app.modules.zenodo.services.os.getenv", side_effect=mock_getenv)

    service = ZenodoService()
    assert service.params == {"access_token": "MI_TOKEN_SECRETO"}


def test_service_init_no_token(mocker):
    """
    Prueba que el __init__ se configura sin token si no hay variables.
    """

    def mock_getenv_side_effect(key, default=None):
        if key == "FLASK_ENV":
            return "development"  # Necesario para que get_zenodo_url devuelva un string
        if key == "FAKENODO_URL":
            return "http://fake-url.com/api"  # Necesario para que get_zenodo_url devuelva un string
        # Devuelve None para las claves de token
        if key in ("ZENODO_ACCESS_TOKEN", "FAKENODO_TOKEN"):
            return None
        return default  # o None

    mocker.patch("app.modules.zenodo.services.os.getenv", side_effect=mock_getenv_side_effect)

    service = ZenodoService()
    # Verificamos que los params estén vacíos
    assert service.params == {}


def test_service_init_url_stripping(mocker):
    """
    Prueba que el __init__ añade '/depositions' si falta.
    """
    mocker.patch("app.modules.zenodo.services.os.getenv", return_value="http://fakenodo/api/")
    service = ZenodoService()
    assert service.ZENODO_API_URL == "http://fakenodo/api/depositions"


def test_service_test_connection(mock_service):
    """
    Prueba el método test_connection (éxito y fallo).
    """
    service, mocker = mock_service

    # Caso 1: Éxito
    mock_response_ok = mocker.MagicMock()
    mock_response_ok.status_code = 200
    mocker.patch("app.modules.zenodo.services.requests.get", return_value=mock_response_ok)

    assert service.test_connection() is True

    # Caso 2: Fallo
    mock_response_fail = mocker.MagicMock()
    mock_response_fail.status_code = 404
    mocker.patch("app.modules.zenodo.services.requests.get", return_value=mock_response_fail)

    assert service.test_connection() is False


def test_service_get_all_depositions(mock_service):
    """
    Prueba get_all_depositions (éxito y fallo).
    """
    service, mocker = mock_service
    requests_get = mocker.patch("app.modules.zenodo.services.requests.get")

    # Caso 1: Éxito
    requests_get.return_value = MagicMock(status_code=200, json=lambda: {"id": 123})
    assert service.get_all_depositions() == {"id": 123}

    # Caso 2: Fallo
    requests_get.return_value = MagicMock(status_code=500, text="Server Error")
    with pytest.raises(Exception, match="Failed to get depositions"):
        service.get_all_depositions()


def test_service_create_new_deposition_full_branches(mock_service):
    """
    Prueba create_new_deposition cubriendo las ramas internas:
    1. publication_type == 'none'
    2. author.affiliation es None
    3. author.orcid es None
    4. dataset.ds_meta_data.tags es None
    """
    service, mocker = mock_service
    requests_post = mocker.patch("app.modules.zenodo.services.requests.post")
    requests_post.return_value = MagicMock(status_code=201, json=lambda: {"id": 1})

    # Creamos un mock de DataSet
    mock_author_no_details = MagicMock()
    mock_author_no_details.name = "John Doe"
    mock_author_no_details.affiliation = None
    mock_author_no_details.orcid = None

    mock_dataset = MagicMock()
    mock_dataset.ds_meta_data.title = "Test Title"
    mock_dataset.ds_meta_data.publication_type.value = "none"  # Rama 1
    mock_dataset.ds_meta_data.description = "Test Desc"
    mock_dataset.ds_meta_data.authors = [mock_author_no_details]  # Rama 2 y 3
    mock_dataset.ds_meta_data.tags = None  # Rama 4

    # Ejecutamos
    service.create_new_deposition(mock_dataset)

    # Verificamos que los 'if' se manejaron correctamente
    call_args = requests_post.call_args[1]["json"]["metadata"]
    assert call_args["upload_type"] == "dataset"
    assert call_args["publication_type"] is None
    assert call_args["creators"][0] == {"name": "John Doe"}
    assert call_args["keywords"] == ["pixelhub"]  # Fallback para tags=None


def test_service_create_new_deposition_handles_json_decode_error(mock_service):
    """
    Prueba la rama 'except ValueError' en create_new_deposition.
    """
    service, mocker = mock_service
    requests_post = mocker.patch("app.modules.zenodo.services.requests.post")

    # Simulamos un fallo 400 (Bad Request) que devuelve HTML
    mock_response = MagicMock(status_code=400, text="<HTML>Bad Request</HTML>")
    # Forzamos que .json() falle
    mock_response.json.side_effect = json.JSONDecodeError("msg", "doc", 0)
    requests_post.return_value = mock_response

    mock_dataset = MagicMock()
    mock_dataset.ds_meta_data.publication_type.value = "dataset"
    mock_dataset.ds_meta_data.tags = "tag"
    mock_dataset.ds_meta_data.authors = []

    # Verificamos que la excepción se captura y se usa .text en el mensaje
    with pytest.raises(Exception, match="Failed to create deposition"):
        service.create_new_deposition(mock_dataset)


def test_service_upload_file(mock_service):
    """
    Prueba upload_file (éxito y fallo) y se asegura de que file.close() es llamado.
    """
    service, mocker = mock_service
    requests_post = mocker.patch("app.modules.zenodo.services.requests.post")

    # Mockeamos current_user
    mocker.patch("app.modules.zenodo.services.current_user", MagicMock(id=1))

    # 1. Creamos un mock del manejador de fichero
    mock_file_handle = MagicMock()

    # 2. Configuramos mock_open para que devuelva nuestro manejador
    mock_open_instance = mocker.patch("builtins.open", mocker.mock_open())
    mock_open_instance.return_value = mock_file_handle

    # Creamos mocks para los modelos
    mock_dataset = MagicMock(id=1)
    mock_fm = MagicMock()
    mock_fm.fm_meta_data.filename = "test.uvl"
    mock_user = MagicMock(id=1)

    # Caso 1: Éxito (con user=None, usa current_user)
    requests_post.return_value = MagicMock(status_code=201, json=lambda: {"status": "ok"})
    result = service.upload_file(mock_dataset, 123, mock_fm, user=None)
    assert result == {"status": "ok"}

    # Reseteamos el mock para el siguiente caso
    mock_file_handle.close.reset_mock()

    # Caso 2: Éxito (con user proporcionado)
    result_user = service.upload_file(mock_dataset, 123, mock_fm, user=mock_user)
    assert result_user == {"status": "ok"}

    # Reseteamos el mock para el siguiente caso
    mock_file_handle.close.reset_mock()

    # Caso 3: Fallo (la API devuelve error)
    requests_post.return_value = MagicMock(status_code=400, json=lambda: {"error": "Bad file"})
    with pytest.raises(Exception, match="Error details: {'error': 'Bad file'}"):
        service.upload_file(mock_dataset, 123, mock_fm, user=mock_user)


def test_service_compute_next_doi(mock_service):
    """
    Prueba la lógica de _compute_next_doi (vacío, con datos, y con error).
    """
    service, mocker = mock_service
    mock_query = mocker.patch("app.modules.dataset.models.DSMetaData.query")

    # Caso 1: Base de datos vacía
    mock_query.with_entities.return_value.all.return_value = []
    assert service._compute_next_doi() == "10.5281/zenodo.1000001"

    # Caso 2: Base de datos con datos
    mock_query.with_entities.return_value.all.return_value = [
        ("10.5281/zenodo.1000005",),
        ("10.5281/zenodo.1000010",),  # Este es el máximo
        (None,),  # Ignora nulos
        ("doi-incorrecto",),  # Ignora formato incorrecto
    ]
    assert service._compute_next_doi() == "10.5281/zenodo.1000011"

    # Caso 3: Error en la consulta
    mock_query.with_entities.return_value.all.side_effect = Exception("DB Error")
    assert service._compute_next_doi() == "10.5281/zenodo.1000001"  # Devuelve el fallback


def test_service_publish_deposition(mock_service):
    """
    Prueba publish_deposition (éxito y fallo).
    """
    service, mocker = mock_service
    requests_post = mocker.patch("app.modules.zenodo.services.requests.post")
    mocker.patch.object(service, "_compute_next_doi", return_value="10.5281/zenodo.999")

    # Caso 1: Éxito
    requests_post.return_value = MagicMock(status_code=202, json=lambda: {"status": "published"})
    assert service.publish_deposition(123) == {"status": "published"}

    # Caso 2: Fallo
    requests_post.return_value = MagicMock(status_code=400, text="Already published")
    with pytest.raises(Exception, match="Failed to publish deposition"):
        service.publish_deposition(123)


def test_service_get_deposition(mock_service):
    """
    Prueba get_deposition (éxito y fallo).
    """
    service, mocker = mock_service
    requests_get = mocker.patch("app.modules.zenodo.services.requests.get")

    # Caso 1: Éxito
    requests_get.return_value = MagicMock(status_code=200, json=lambda: {"id": 123})
    assert service.get_deposition(123) == {"id": 123}

    # Caso 2: Fallo
    requests_get.return_value = MagicMock(status_code=404, text="Not Found")
    with pytest.raises(Exception, match="Failed to get deposition"):
        service.get_deposition(123)


def test_service_get_doi(mock_service):
    """
    Prueba get_doi (que depende de get_deposition).
    """
    service, mocker = mock_service

    mocker.patch.object(service, "get_deposition", return_value={"id": 123, "doi": "10.1234/zenodo.5678"})

    assert service.get_doi(123) == "10.1234/zenodo.5678"
