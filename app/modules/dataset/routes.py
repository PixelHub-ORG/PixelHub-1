import json
import logging
import os
import shutil
import tempfile
import uuid
from datetime import datetime, timezone
from urllib.parse import urlparse
from zipfile import ZipFile

import requests
from flask import (
    abort,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from flask_login import current_user, login_required

from app.modules.dataset import dataset_bp
from app.modules.dataset.forms import DataSetForm
from app.modules.dataset.services import (
    AuthorService,
    DataSetComparisonService,
    DataSetService,
    DOIMappingService,
    DSDownloadRecordService,
    DSMetaDataService,
    DSViewRecordService,
)
from app.modules.zenodo.services import ZenodoService

logger = logging.getLogger(__name__)


dataset_service = DataSetService()
author_service = AuthorService()
dsmetadata_service = DSMetaDataService()
zenodo_service = ZenodoService()
doi_mapping_service = DOIMappingService()
ds_view_record_service = DSViewRecordService()


@dataset_bp.route("/dataset/upload", methods=["GET", "POST"])
@login_required
def create_dataset():
    form = DataSetForm()
    if request.method == "POST":
        dataset = None

        if not form.validate_on_submit():
            return jsonify({"message": form.errors}), 400

        try:
            logger.info("Creating dataset...")
            dataset = dataset_service.create_from_form(form=form, current_user=current_user)
            logger.info(f"Created dataset: {dataset}")
            dataset_service.move_file_models(dataset)
        except Exception as exc:
            logger.exception(f"Exception while create dataset data in local {exc}")
            return jsonify({"Exception while create dataset data in local: ": str(exc)}), 400

        # send dataset as deposition to Zenodo
        data = {}
        try:
            zenodo_response_json = zenodo_service.create_new_deposition(dataset)
            response_data = json.dumps(zenodo_response_json)
            data = json.loads(response_data)
        except Exception as exc:
            data = {}
            zenodo_response_json = {}
            logger.exception(f"Exception while create dataset data in Zenodo {exc}")

        if data.get("id"):
            deposition_id = data.get("id")

            # update dataset with deposition id in Zenodo
            dataset_service.update_dsmetadata(dataset.ds_meta_data_id, deposition_id=deposition_id)

            try:
                # iterate for each file model (one file model = one request to
                # Zenodo)
                for file_model in dataset.file_models:
                    zenodo_service.upload_file(dataset, deposition_id, file_model)

                # publish deposition
                zenodo_service.publish_deposition(deposition_id)

                # update DOI
                deposition_doi = zenodo_service.get_doi(deposition_id)
                dataset_service.update_dsmetadata(dataset.ds_meta_data_id, dataset_doi=deposition_doi)
            except Exception as e:
                msg = f"it has not been possible upload file models in Zenodo and update the DOI: {e}"
                return jsonify({"message": msg}), 200

        # Delete temp folder
        file_path = current_user.temp_folder()
        if os.path.exists(file_path) and os.path.isdir(file_path):
            shutil.rmtree(file_path)

        msg = "Everything works!"
        return jsonify({"message": msg}), 200

    return render_template("dataset/upload_dataset.html", form=form)


@dataset_bp.route("/dataset/list", methods=["GET", "POST"])
@login_required
def list_dataset():
    return render_template(
        "dataset/list_datasets.html",
        datasets=dataset_service.get_synchronized(current_user.id),
        local_datasets=dataset_service.get_unsynchronized(current_user.id),
    )


@dataset_bp.route("/home/leaderboard", methods=["GET"])
def home_leaderboard():
    period = request.args.get("period", "week")  # Por defecto semana
    leaderboard_data = dataset_service.get_dataset_leaderboard(period=period)
    return render_template("dataset/leaderboard.html", leaderboard=leaderboard_data)


@dataset_bp.route("/dataset/file/upload", methods=["POST"])
@login_required
def upload():
    file = request.files.get("file")
    temp_folder = current_user.temp_folder()

    if not file or not file.filename:
        return jsonify({"message": "No file provided"}), 400

    _, extension = os.path.splitext(file.filename.lower())

    if extension not in {".pix", ".zip"}:
        return jsonify({"message": "Only .pix or .zip files are allowed"}), 400

    if not os.path.exists(temp_folder):
        os.makedirs(temp_folder)

    def _generate_unique_filename(original_name: str) -> str:
        base_name, ext = os.path.splitext(original_name)
        candidate = original_name
        i = 1
        while os.path.exists(os.path.join(temp_folder, candidate)):
            candidate = f"{base_name} ({i}){ext}"
            i += 1
        return candidate

    saved_filenames = []

    try:
        if extension == ".pix":
            new_filename = _generate_unique_filename(file.filename)
            file_path = os.path.join(temp_folder, new_filename)
            file.save(file_path)
            saved_filenames.append(new_filename)
        else:  # .zip
            with tempfile.NamedTemporaryFile(delete=False) as tmp_zip:
                file.save(tmp_zip)
                temp_zip_path = tmp_zip.name

            try:
                with ZipFile(temp_zip_path) as zip_file:
                    pix_members = [
                        info
                        for info in zip_file.infolist()
                        if not info.is_dir() and info.filename.lower().endswith(".pix")
                    ]

                    if not pix_members:
                        return jsonify({"message": "Zip file does not contain any .pix files"}), 400

                    for member in pix_members:
                        file_data = zip_file.read(member)
                        base_name = os.path.basename(member.filename)
                        if not base_name:
                            continue
                        new_filename = _generate_unique_filename(base_name)
                        file_path = os.path.join(temp_folder, new_filename)
                        with open(file_path, "wb") as output_file:
                            output_file.write(file_data)
                        saved_filenames.append(new_filename)
            finally:
                if os.path.exists(temp_zip_path):
                    os.remove(temp_zip_path)
    except Exception as e:
        return jsonify({"message": str(e)}), 500

    return (
        jsonify(
            {
                "message": "Files uploaded successfully",
                "filename": saved_filenames[0] if saved_filenames else None,
                "filenames": saved_filenames,
            }
        ),
        200,
    )


@dataset_bp.route("/dataset/file/upload_github", methods=["POST"])
@login_required
def upload_github():
    """Import .pix files from a public GitHub repository folder.

    Expects JSON body with `repo_url` and `path` (path within the repo).
    Returns the same response format as `upload()` for compatibility.
    """
    data = request.get_json() or {}
    repo_url = data.get("repo_url")
    folder_path = data.get("path") or ""

    if not repo_url:
        return jsonify({"message": "repo_url is required"}), 400

    # parse owner/repo from common GitHub URL formats
    def _parse_owner_repo(url: str):
        # https://github.com/owner/repo or https://github.com/owner/repo/
        parsed = urlparse(url)
        if parsed.netloc and parsed.netloc.lower().endswith("github.com"):
            parts = parsed.path.strip("/").split("/")
            if len(parts) >= 2:
                owner = parts[0]
                repo = parts[1].replace(".git", "")
                return owner, repo
        # git@github.com:owner/repo.git
        if url.startswith("git@github.com:"):
            tail = url.split(":", 1)[1]
            parts = tail.split("/")
            if len(parts) >= 2:
                owner, repo = parts[0], parts[1].replace(".git", "")
                return owner, repo
        return None, None

    owner, repo = _parse_owner_repo(repo_url)
    if not owner or not repo:
        return jsonify({"message": "Could not parse GitHub repo URL"}), 400

    temp_folder = current_user.temp_folder()
    if not os.path.exists(temp_folder):
        os.makedirs(temp_folder)

    def _generate_unique_filename(original_name: str) -> str:
        base_name, ext = os.path.splitext(original_name)
        candidate = original_name
        i = 1
        while os.path.exists(os.path.join(temp_folder, candidate)):
            candidate = f"{base_name} ({i}){ext}"
            i += 1
        return candidate

    saved_filenames = []

    # Use GitHub API to list contents; traverse directories recursively
    session = requests.Session()
    # Add GitHub token if available to increase rate limit
    github_token = os.getenv("GITHUB_TOKEN")
    if github_token:
        session.headers.update({"Authorization": f"token {github_token}"})

    api_base = f"https://api.github.com/repos/{owner}/{repo}/contents"

    def _fetch_contents(api_url):
        try:
            resp = session.get(api_url, timeout=10)
            if resp.status_code != 200:
                return None, f"GitHub API error: {resp.status_code}"
            return resp.json(), None
        except Exception as e:
            return None, str(e)

    def _process_dir(rel_path):
        url = api_base
        if rel_path:
            url = f"{api_base}/{rel_path.strip('/')}"
        items, err = _fetch_contents(url)
        if err:
            return err
        if not isinstance(items, list):
            return f"Unexpected response for path: {rel_path}"

        for item in items:
            t = item.get("type")
            if t == "file":
                name = item.get("name")
                if name and name.lower().endswith(".pix"):
                    download_url = item.get("download_url")
                    if not download_url:
                        continue
                    r = session.get(download_url, timeout=10)
                    if r.status_code != 200:
                        continue
                    new_filename = _generate_unique_filename(name)
                    file_path = os.path.join(temp_folder, new_filename)
                    with open(file_path, "wb") as fh:
                        fh.write(r.content)
                    saved_filenames.append(new_filename)
            elif t == "dir":
                subpath = item.get("path")
                err = _process_dir(subpath)
                if err:
                    return err
        return None

    # start processing
    err = _process_dir(folder_path)
    if err:
        return jsonify({"message": err}), 400

    if not saved_filenames:
        return jsonify({"message": "No .pix files found in the given GitHub path"}), 400

    return (
        jsonify(
            {
                "message": "Files uploaded successfully",
                "filename": saved_filenames[0] if saved_filenames else None,
                "filenames": saved_filenames,
            }
        ),
        200,
    )


@dataset_bp.route("/dataset/file/delete", methods=["POST"])
def delete():
    data = request.get_json()
    filename = data.get("file")
    temp_folder = current_user.temp_folder()
    filepath = os.path.join(temp_folder, filename)

    if os.path.exists(filepath):
        os.remove(filepath)
        return jsonify({"message": "File deleted successfully"})

    return jsonify({"error": "Error: File not found"})


@dataset_bp.route("/dataset/download/<int:dataset_id>", methods=["GET"])
def download_dataset(dataset_id):
    dataset = dataset_service.get_or_404(dataset_id)

    file_path = f"uploads/user_{dataset.user_id}/dataset_{dataset.id}/"

    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, f"dataset_{dataset_id}.zip")

    with ZipFile(zip_path, "w") as zipf:
        for subdir, dirs, files in os.walk(file_path):
            for file in files:
                full_path = os.path.join(subdir, file)

                relative_path = os.path.relpath(full_path, file_path)

                zipf.write(
                    full_path,
                    arcname=os.path.join(os.path.basename(zip_path[:-4]), relative_path),
                )

    user_cookie = request.cookies.get("download_cookie")
    if not user_cookie:
        # Generate a new unique identifier if it does not exist
        user_cookie = str(uuid.uuid4())
        # Save the cookie to the user's browser
        resp = make_response(
            send_from_directory(
                temp_dir,
                f"dataset_{dataset_id}.zip",
                as_attachment=True,
                mimetype="application/zip",
            )
        )
        resp.set_cookie("download_cookie", user_cookie)
    else:
        resp = send_from_directory(
            temp_dir,
            f"dataset_{dataset_id}.zip",
            as_attachment=True,
            mimetype="application/zip",
        )

    # Record the download in your database
    DSDownloadRecordService().create(
        user_id=current_user.id if current_user.is_authenticated else None,
        dataset_id=dataset_id,
        download_date=datetime.now(timezone.utc),
        download_cookie=user_cookie,
    )

    return resp


# lo modificamos para q ademas muestre los related datasets
@dataset_bp.route("/doi/<path:doi>/", methods=["GET"])
def subdomain_index(doi):
    new_doi = doi_mapping_service.get_new_doi(doi)
    if new_doi:
        return redirect(url_for("dataset.subdomain_index", doi=new_doi), code=302)

    ds_meta_data = dsmetadata_service.filter_by_doi(doi)

    if not ds_meta_data:
        abort(404)

    dataset = ds_meta_data.data_set

    user_cookie = ds_view_record_service.create_cookie(dataset=dataset)

    related_datasets = dataset_service.get_dataset_recommendations(dataset=dataset)

    history = dataset_service.get_dataset_history(dataset.id)

    resp = make_response(
        render_template(
            "dataset/view_dataset.html", dataset=dataset, related_datasets=related_datasets, history=history
        )
    )
    resp.set_cookie("view_cookie", user_cookie)

    return resp


@dataset_bp.route("/dataset/unsynchronized/<int:dataset_id>/", methods=["GET"])
@login_required
def get_unsynchronized_dataset(dataset_id):
    dataset = dataset_service.get_unsynchronized_dataset(current_user.id, dataset_id)
    if not dataset:
        abort(404)

    # --- NUEVO: Obtener historial ---
    history = dataset_service.get_dataset_history(dataset.id)
    # --------------------------------

    return render_template("dataset/view_dataset.html", dataset=dataset, history=history)  # <--- Pasamos la variable


@dataset_bp.route("/dataset/<int:dataset_id>/create_version", methods=["GET", "POST"])
@login_required
def create_dataset_version(dataset_id):
    parent_dataset = dataset_service.get_or_404(dataset_id)

    form = DataSetForm()

    if request.method == "POST":
        dataset = None

        if not form.validate_on_submit():
            return jsonify({"message": form.errors}), 400

        try:
            logger.info(f"Initiating version creation for dataset {dataset_id}")

            dataset = dataset_service.create_from_form(
                form=form, current_user=current_user, parent_dataset=parent_dataset
            )

            logger.info(f"Created dataset version: {dataset}")
            dataset_service.move_file_models(dataset)

        except Exception as exc:
            logger.exception(f"Exception while create dataset data in local {exc}")
            return jsonify({"Exception while create dataset data in local: ": str(exc)}), 400

        data = {}
        try:
            zenodo_response_json = zenodo_service.create_new_deposition(dataset)
            response_data = json.dumps(zenodo_response_json)
            data = json.loads(response_data)
        except Exception as exc:
            data = {}
            zenodo_response_json = {}
            logger.exception(f"Exception while create dataset data in Zenodo {exc}")

        if data.get("id"):
            deposition_id = data.get("id")
            dataset_service.update_dsmetadata(dataset.ds_meta_data_id, deposition_id=deposition_id)
            try:
                for file_model in dataset.file_models:
                    zenodo_service.upload_file(dataset, deposition_id, file_model)
                zenodo_service.publish_deposition(deposition_id)
                deposition_doi = zenodo_service.get_doi(deposition_id)
                dataset_service.update_dsmetadata(dataset.ds_meta_data_id, dataset_doi=deposition_doi)
            except Exception as e:
                msg = f"it has not been possible upload file models in Zenodo and update the DOI: {e}"
                return jsonify({"message": msg}), 200

        file_path = current_user.temp_folder()
        if os.path.exists(file_path) and os.path.isdir(file_path):
            shutil.rmtree(file_path)

        msg = "New version created successfully!"
        return jsonify({"message": msg}), 200

    if request.method == "GET":
        form.title.data = parent_dataset.ds_meta_data.title
        form.desc.data = parent_dataset.ds_meta_data.description
        form.publication_type.data = parent_dataset.ds_meta_data.publication_type.name
        form.tags.data = parent_dataset.ds_meta_data.tags

        return render_template(
            "dataset/upload_dataset.html",
            form=form,
            is_version_creation=True,
            parent_title=parent_dataset.ds_meta_data.title,
            version_number=parent_dataset.version + 1,
            parent_dataset=parent_dataset,
        )


@dataset_bp.route("/dataset/compare/<int:old_id>/<int:new_id>", methods=["GET"])
@login_required
def compare_datasets(old_id, new_id):
    old_ds = dataset_service.get_or_404(old_id)
    new_ds = dataset_service.get_or_404(new_id)

    comparison_service = DataSetComparisonService()
    diff_data = comparison_service.compare(old_ds, new_ds)

    return render_template(
        "dataset/compare.html",
        old_ds=old_ds,
        new_ds=new_ds,
        metadata_changes=diff_data["metadata"],
        file_changes=diff_data["files"],
    )


@dataset_bp.route("/file/diff/<int:old_file_id>/<int:new_file_id>", methods=["GET"])
def file_diff(old_file_id, new_file_id):
    comparison_service = DataSetComparisonService()
    diff_html = comparison_service.generate_diff_html(old_file_id, new_file_id)
    return jsonify({"diff_html": diff_html})
