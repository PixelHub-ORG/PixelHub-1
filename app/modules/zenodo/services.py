import logging
import os

import requests
from dotenv import load_dotenv
from flask import Response, jsonify
from flask_login import current_user

from app.modules.dataset.models import DataSet
from app.modules.filemodel.models import FileModel
from app.modules.zenodo.forms import ZenodoForm
from app.modules.zenodo.repositories import ZenodoRepository
from core.configuration.configuration import uploads_folder_name
from core.services.BaseService import BaseService

logger = logging.getLogger(__name__)

load_dotenv()


class ZenodoService(BaseService):

    def get_zenodo_url(self):

        FLASK_ENV = os.getenv("FLASK_ENV", "development")
        ZENODO_API_URL = ""

        if FLASK_ENV == "development":
            ZENODO_API_URL = os.getenv("FAKENODO_BACKEND_URL", "http://localhost:5001/api")
        elif FLASK_ENV == "production":
            ZENODO_API_URL = os.getenv("FAKENODO_URL", "https://pixelhub-2-51iz.onrender.com/api/")
        else:
            ZENODO_API_URL = os.getenv("FAKENODO_BACKEND_URL", "http://localhost:5001/api")

        return ZENODO_API_URL

    def __init__(self):
        super().__init__(ZenodoRepository())
        self.ZENODO_API_URL = self.get_zenodo_url()
        # Ensure we target the depositions collection
        if not self.ZENODO_API_URL.rstrip("/").endswith("/depositions"):
            self.ZENODO_API_URL = f"{self.ZENODO_API_URL.rstrip('/')}/depositions"
        self.headers = {"Content-Type": "application/json"}
        # Ensure params is always defined (e.g., access_token or empty)
        token = (
            getattr(self, "ZENODO_ACCESS_TOKEN", None)
            or os.getenv("FAKENODO_TOKEN")
            or os.getenv("ZENODO_ACCESS_TOKEN")
        )
        self.params = {"access_token": token} if token else {}

    def test_connection(self) -> bool:
        """
        Test the connection with Zenodo.

        Returns:
            bool: True if the connection is successful, False otherwise.
        """
        response = requests.get(self.ZENODO_API_URL, params=self.params, headers=self.headers)
        return response.status_code == 200

    def test_full_connection(self) -> Response:
        """
        Test the connection with Zenodo by creating a deposition, uploading an empty test file, and deleting the
        deposition.

        Returns:
            bool: True if the connection, upload, and deletion are successful, False otherwise.
        """

        success = True

        # Create a test file
        working_dir = os.getenv("WORKING_DIR", "")
        file_path = os.path.join(working_dir, "test_file.txt")
        with open(file_path, "w") as f:
            f.write("This is a test file with some content.")

        messages = []  # List to store messages

        # Step 1: Create a deposition on Zenodo
        data = {
            "metadata": {
                "title": "Test Deposition",
                "upload_type": "dataset",
                "description": "This is a test deposition created via Zenodo API",
                "creators": [{"name": "John Doe"}],
            }
        }

        response = requests.post(self.ZENODO_API_URL, json=data, params=self.params, headers=self.headers)

        if response.status_code != 201:
            return jsonify(
                {
                    "success": False,
                    "messages": "Failed to create test deposition on Zenodo.\n"
                    "Response code: {}. Body: {}".format(response.status_code, response.text),
                }
            )

        deposition_id = response.json()["id"]

        # Step 2: Upload an empty file to the deposition
        data = {"name": "test_file.txt"}
        files = {"file": open(file_path, "rb")}
        publish_url = f"{self.ZENODO_API_URL}/{deposition_id}/files"
        response = requests.post(publish_url, params=self.params, data=data, files=files)
        files["file"].close()  # Close the file after uploading

        logger.info(f"Publish URL: {publish_url}")
        logger.info(f"Params: {self.params}")
        logger.info(f"Data: {data}")
        logger.info(f"Files: {files}")
        logger.info(f"Response Status Code: {response.status_code}")
        logger.info(f"Response Content: {response.content}")

        if response.status_code != 201:
            messages.append(f"Failed to upload test file to Zenodo. Response code: {response.status_code}")
            success = False

        # Step 3: Delete the deposition
        response = requests.delete(f"{self.ZENODO_API_URL}/{deposition_id}", params=self.params)

        if os.path.exists(file_path):
            os.remove(file_path)

        return jsonify({"success": success, "messages": messages})

    def get_all_depositions(self) -> dict:
        """
        Get all depositions from Zenodo.

        Returns:
            dict: The response in JSON format with the depositions.
        """
        response = requests.get(self.ZENODO_API_URL, params=self.params, headers=self.headers)
        if response.status_code != 200:
            raise Exception(f"Failed to get depositions. Status: {response.status_code}. Body: {response.text}")
        return response.json()

    def create_new_deposition(self, dataset: DataSet) -> dict:
        """
        Create a new deposition in Zenodo.

        Args:
            dataset (DataSet): The DataSet object containing the metadata of the deposition.

        Returns:
            dict: The response in JSON format with the details of the created deposition.
        """

        logger.info("Dataset sending to Zenodo...")
        logger.info(f"Publication type...{dataset.ds_meta_data.publication_type.value}")

        metadata = {
            "title": dataset.ds_meta_data.title,
            "upload_type": "dataset" if dataset.ds_meta_data.publication_type.value == "none" else "publication",
            "publication_type": (
                dataset.ds_meta_data.publication_type.value
                if dataset.ds_meta_data.publication_type.value != "none"
                else None
            ),
            "description": dataset.ds_meta_data.description,
            "creators": [
                {
                    "name": author.name,
                    **({"affiliation": author.affiliation} if author.affiliation else {}),
                    **({"orcid": author.orcid} if author.orcid else {}),
                }
                for author in dataset.ds_meta_data.authors
            ],
            "keywords": (
                ["pixelhub"] if not dataset.ds_meta_data.tags else dataset.ds_meta_data.tags.split(", ") + ["pixelhub"]
            ),
            "access_right": "open",
            "license": "CC-BY-4.0",
        }

        data = {"metadata": metadata}

        logger.info(f"Zenodo deposition metadata...{dataset.ds_meta_data.publication_type.value}")
        response = requests.post(self.ZENODO_API_URL, params=self.params, json=data, headers=self.headers)
        if response.status_code != 201:
            try:
                err = response.json()
            except ValueError:
                err = response.text
            error_message = f"Failed to create deposition. Status: {response.status_code}. Error details: {err}"
            raise Exception(error_message)
        return response.json()

    def upload_file(self, dataset: DataSet, deposition_id: int, file_model: FileModel, user=None) -> dict:
        """
        Upload a file to a deposition in Zenodo.

        Args:
            deposition_id (int): The ID of the deposition in Zenodo.
            file_model (FileModel): The FileModel object representing the file model.
            user (FileModel): The User object representing the file owner.

        Returns:
            dict: The response in JSON format with the details of the uploaded file.
        """
        filename = file_model.fm_meta_data.filename
        data = {"name": filename}
        user_id = current_user.id if user is None else user.id
        file_path = os.path.join(uploads_folder_name(), f"user_{str(user_id)}", f"dataset_{dataset.id}/", filename)
        files = {"file": open(file_path, "rb")}

        publish_url = f"{self.ZENODO_API_URL}/{deposition_id}/files"
        response = requests.post(publish_url, params=self.params, data=data, files=files)

        if response.status_code != 201:
            error_message = f"Failed to upload files. Error details: {response.json()}"
            raise Exception(error_message)
        return response.json()

    def _compute_next_doi(self) -> str:
        """Compute the next Zenodo-like DOI based on persisted PixelHub data.
        Pattern: 10.5281/zenodo.<numeric>
        """
        try:
            # Import here to avoid circulars
            import re

            from app.modules.dataset.models import DSMetaData

            # Fetch all existing DOIs (could be optimized with a SQL MAX on numeric substring if available)
            existing = []
            for md in DSMetaData.query.with_entities(DSMetaData.dataset_doi).all():
                doi = md[0]
                if not doi:
                    continue
                m = re.search(r"^10\.5281/zenodo\.(\d+)$", doi)
                if m:
                    existing.append(int(m.group(1)))
            next_suffix = (max(existing) + 1) if existing else 1000001
            return f"10.5281/zenodo.{next_suffix}"
        except Exception as e:
            # Safe fallback to a deterministic, readable format if the query fails
            logger.warning("Falling back DOI computation due to error: %s", e)

            return "10.5281/zenodo.1000001"

    def publish_deposition(self, deposition_id: int) -> dict:
        """
        Publish a deposition in Zenodo.

        Args:
            deposition_id (int): The ID of the deposition in Zenodo.

        Returns:
            dict: The response in JSON format with the details of the published deposition.
        """
        publish_url = f"{self.ZENODO_API_URL}/{deposition_id}/publish"

        # Always compute and provide the DOI so fakenodo stays consistent across restarts
        next_doi = self._compute_next_doi()
        payload = {"doi": next_doi}

        response = requests.post(publish_url, params=self.params, headers=self.headers, json=payload)
        if response.status_code not in (200, 202):
            raise Exception(f"Failed to publish deposition. Status: {response.status_code}. Body: {response.text}")
        return response.json()

    def get_deposition(self, deposition_id: int) -> dict:
        """
        Get a deposition from Zenodo.

        Args:
            deposition_id (int): The ID of the deposition in Zenodo.

        Returns:
            dict: The response in JSON format with the details of the deposition.
        """
        deposition_url = f"{self.ZENODO_API_URL}/{deposition_id}"
        response = requests.get(deposition_url, params=self.params, headers=self.headers)
        if response.status_code != 200:
            raise Exception(f"Failed to get deposition. Status: {response.status_code}. Body: {response.text}")
        return response.json()

    def get_doi(self, deposition_id: int) -> str:
        """
        Get the DOI of a deposition from Zenodo.

        Args:
            deposition_id (int): The ID of the deposition in Zenodo.

        Returns:
            str: The DOI of the deposition.
        """
        return self.get_deposition(deposition_id).get("doi")


def test_zenodo_form_creation(test_client):
    """
    Prueba la creación de ZenodoForm para cubrir forms.py.
    """
    # El test se ejecuta dentro del contexto de la app para cargar extensiones (como CSRF)
    with test_client.application.app_context():
        form = ZenodoForm()
        # Verificamos que el formulario se haya creado y tenga el campo submit
        assert form is not None
        assert form.submit is not None
