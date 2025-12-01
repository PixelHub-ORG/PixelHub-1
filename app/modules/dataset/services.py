import difflib
import hashlib
import logging
import os
import shutil
import uuid
from typing import Optional

from flask import request

from app.modules.auth.services import AuthenticationService
from app.modules.dataset.models import DataSet, DSMetaData, DSViewRecord
from app.modules.dataset.repositories import (
    AuthorRepository,
    DataSetRepository,
    DOIMappingRepository,
    DSDownloadRecordRepository,
    DSMetaDataRepository,
    DSViewRecordRepository,
)
from app.modules.filemodel.repositories import FileModelRepository, FMMetaDataRepository
from app.modules.hubfile.repositories import (
    HubfileDownloadRecordRepository,
    HubfileRepository,
    HubfileViewRecordRepository,
)
from core.services.BaseService import BaseService

logger = logging.getLogger(__name__)


def calculate_checksum_and_size(file_path):
    file_size = os.path.getsize(file_path)
    with open(file_path, "rb") as file:
        content = file.read()
        hash_md5 = hashlib.md5(content).hexdigest()
        return hash_md5, file_size


class DataSetService(BaseService):
    def __init__(self):
        super().__init__(DataSetRepository())
        self.file_model_repository = FileModelRepository()
        self.author_repository = AuthorRepository()
        self.dsmetadata_repository = DSMetaDataRepository()
        self.fmmetadata_repository = FMMetaDataRepository()
        self.dsdownloadrecord_repository = DSDownloadRecordRepository()
        self.hubfiledownloadrecord_repository = HubfileDownloadRecordRepository()
        self.hubfilerepository = HubfileRepository()
        self.dsviewrecord_repostory = DSViewRecordRepository()
        self.hubfileviewrecord_repository = HubfileViewRecordRepository()

    def move_file_models(self, dataset: DataSet):
        current_user = AuthenticationService().get_authenticated_user()
        source_dir = current_user.temp_folder()

        working_dir = os.getenv("WORKING_DIR", "")
        dest_dir = os.path.join(working_dir, "uploads", f"user_{current_user.id}", f"dataset_{dataset.id}")

        os.makedirs(dest_dir, exist_ok=True)

        for file_model in dataset.file_models:
            filename = file_model.fm_meta_data.filename
            shutil.move(os.path.join(source_dir, filename), dest_dir)

    def get_synchronized(self, current_user_id: int) -> DataSet:
        return self.repository.get_synchronized(current_user_id)

    # ordenamos por descargas y si hay empate por reciente
    def get_dataset_recommendations(self, dataset, limit=5) -> DataSet:
        other_datasets = DataSet.query.filter(DataSet.id != dataset.id).all()
        scored_datasets = []
        for ds in other_datasets:
            score = dataset.calculate_similarity_score(ds)
            scored_datasets.append((ds, score))
        scored_datasets_sorted = sorted(
            scored_datasets,
            key=lambda x: (x[1], x[0].get_download_count(), x[0].created_at),
            reverse=True
        )
        datasets_with_doi = [d for d, _ in scored_datasets_sorted if d.ds_meta_data and d.ds_meta_data.dataset_doi]
        return [ds for ds in datasets_with_doi[:limit]]

    def get_unsynchronized(self, current_user_id: int) -> DataSet:
        return self.repository.get_unsynchronized(current_user_id)

    def get_unsynchronized_dataset(self, current_user_id: int, dataset_id: int) -> DataSet:
        return self.repository.get_unsynchronized_dataset(current_user_id, dataset_id)

    def latest_synchronized(self):
        return self.repository.latest_synchronized()

    def count_synchronized_datasets(self):
        return self.repository.count_synchronized_datasets()

    def count_file_models(self):
        return self.file_model_repository.count_file_models()

    def count_authors(self) -> int:
        return self.author_repository.count()

    def count_dsmetadata(self) -> int:
        return self.dsmetadata_repository.count()

    def total_dataset_downloads(self) -> int:
        return self.dsdownloadrecord_repository.total_dataset_downloads()

    def total_dataset_views(self) -> int:
        return self.dsviewrecord_repostory.total_dataset_views()

    def get_dataset_leaderboard(self, period="week") -> DataSet:
        period = "".join(e for e in period if e.isalnum())
        if period not in ["week", "month"]:
            raise ValueError("Periodo no soportado: usa 'week' o 'month'")
        datasets = self.dsdownloadrecord_repository.top_3_dowloaded_datasets_per_week(period=period)
        if not datasets:  # Manejar None o lista vacía
            return []
        datasets_with_doi = [d for d in datasets if d.ds_meta_data and d.ds_meta_data.dataset_doi]
        return datasets_with_doi

    def create_from_form(self, form, current_user, parent_dataset=None) -> DataSet:
        main_author = {
            "name": f"{current_user.profile.surname}, {current_user.profile.name}",
            "affiliation": current_user.profile.affiliation,
            "orcid": current_user.profile.orcid,
        }
        try:

            logger.info(f"Creating dsmetadata...: {form.get_dsmetadata()}")
            dsmetadata = self.dsmetadata_repository.create(**form.get_dsmetadata())

            for author_data in [main_author] + form.get_authors():
                author = self.author_repository.create(commit=False, ds_meta_data_id=dsmetadata.id, **author_data)
                dsmetadata.authors.append(author)

            target_version = 1
            target_prev_id = None

            if parent_dataset:
                target_version = parent_dataset.version + 1
                target_prev_id = parent_dataset.id

            dataset = self.create(
                commit=False,
                user_id=current_user.id,
                ds_meta_data_id=dsmetadata.id,
                version=target_version,
                previous_version_id=target_prev_id,
            )

            dataset.version = target_version
            dataset.previous_version_id = target_prev_id

            for file_model in form.file_models:
                filename = file_model.filename.data
                fmmetadata = self.fmmetadata_repository.create(commit=False, **file_model.get_fmmetadata())
                for author_data in file_model.get_authors():
                    author = self.author_repository.create(commit=False, fm_meta_data_id=fmmetadata.id, **author_data)
                    fmmetadata.authors.append(author)

                fm = self.file_model_repository.create(
                    commit=False, data_set_id=dataset.id, fm_meta_data_id=fmmetadata.id
                )

                file_path = os.path.join(current_user.temp_folder(), filename)
                checksum, size = calculate_checksum_and_size(file_path)

                file = self.hubfilerepository.create(
                    commit=False,
                    name=filename,
                    checksum=checksum,
                    size=size,
                    file_model_id=fm.id,
                )
                fm.files.append(file)

            self.repository.session.commit()

        except Exception as exc:
            logger.exception(f"Exception creating dataset from form...: {exc}")
            self.repository.session.rollback()
            raise exc

        return dataset

    def update_dsmetadata(self, id, **kwargs):
        return self.dsmetadata_repository.update(id, **kwargs)

    def get_pixelhub_doi(self, dataset: DataSet) -> str:
        env = os.getenv("FLASK_ENV", "production")
        domain = os.getenv("DOMAIN", "localhost")

        if env == "development":
            protocol = "http"
        else:
            protocol = "https"

        # 4. Construye la URL
        return f"{protocol}://{domain}/doi/{dataset.ds_meta_data.dataset_doi}"

    def get_dataset_history(self, dataset_id: int) -> list:
        """
        Recupera toda la línea temporal de versiones de un dataset.
        1. Encuentra el dataset raíz (Versión 1).
        2. Recorre descendientemente para encontrar todas las versiones posteriores.
        """
        current = self.repository.get_by_id(dataset_id)
        if not current:
            return []

        root = current
        while root.previous_version_id is not None:
            parent = self.repository.get_by_id(root.previous_version_id)
            if not parent:
                break
            root = parent

        history = [root]

        queue = [root]

        while queue:
            node = queue.pop(0)
            children = sorted(node.next_versions, key=lambda x: x.version)

            for child in children:
                history.append(child)
                queue.append(child)

        return sorted(history, key=lambda x: x.version)


class AuthorService(BaseService):
    def __init__(self):
        super().__init__(AuthorRepository())


class DSDownloadRecordService(BaseService):
    def __init__(self):
        super().__init__(DSDownloadRecordRepository())


class DSMetaDataService(BaseService):
    def __init__(self):
        super().__init__(DSMetaDataRepository())

    def update(self, id, **kwargs):
        return self.repository.update(id, **kwargs)

    def filter_by_doi(self, doi: str) -> Optional[DSMetaData]:
        return self.repository.filter_by_doi(doi)


class DSViewRecordService(BaseService):
    def __init__(self):
        super().__init__(DSViewRecordRepository())

    def the_record_exists(self, dataset: DataSet, user_cookie: str):
        return self.repository.the_record_exists(dataset, user_cookie)

    def create_new_record(self, dataset: DataSet, user_cookie: str) -> DSViewRecord:
        return self.repository.create_new_record(dataset, user_cookie)

    def create_cookie(self, dataset: DataSet) -> str:
        user_cookie = request.cookies.get("view_cookie")
        if not user_cookie:
            user_cookie = str(uuid.uuid4())

        existing_record = self.the_record_exists(dataset=dataset, user_cookie=user_cookie)

        if not existing_record:
            self.create_new_record(dataset=dataset, user_cookie=user_cookie)

        return user_cookie


class DOIMappingService(BaseService):
    def __init__(self):
        super().__init__(DOIMappingRepository())

    def get_new_doi(self, old_doi: str) -> str:
        doi_mapping = self.repository.get_new_doi(old_doi)
        if doi_mapping:
            return doi_mapping.dataset_doi_new
        else:
            return None


class SizeService:
    def __init__(self):
        pass

    def get_human_readable_size(self, size: int) -> str:
        if size < 1024:
            return f"{size} bytes"
        elif size < 1024**2:
            return f"{round(size / 1024, 2)} KB"
        elif size < 1024**3:
            return f"{round(size / (1024**2), 2)} MB"
        else:
            return f"{round(size / (1024**3), 2)} GB"


class DataSetComparisonService:
    def compare(self, old_ds, new_ds):
        """
        Compara dos datasets y devuelve un diccionario con las diferencias.
        """
        return {"metadata": self._compare_metadata(old_ds, new_ds), "files": self._compare_files(old_ds, new_ds)}

    def _compare_metadata(self, old_ds, new_ds):
        changes = []
        old_meta = old_ds.ds_meta_data
        new_meta = new_ds.ds_meta_data

        fields = [
            ("Title", "title"),
            ("Description", "description"),
            ("Publication Type", "publication_type"),
            ("Publication DOI", "publication_doi"),
            ("Tags", "tags"),
        ]

        for label, attr in fields:
            val_old = getattr(old_meta, attr)
            val_new = getattr(new_meta, attr)

            val_old_str = str(val_old.name) if hasattr(val_old, "name") else str(val_old)
            val_new_str = str(val_new.name) if hasattr(val_new, "name") else str(val_new)

            if val_old_str != val_new_str:
                changes.append({"field": label, "old": val_old_str, "new": val_new_str})

        old_authors = {a.name for a in old_meta.authors}
        new_authors = {a.name for a in new_meta.authors}

        if old_authors != new_authors:
            added = new_authors - old_authors
            removed = old_authors - new_authors
            if added or removed:
                changes.append(
                    {
                        "field": "Authors",
                        "old": ", ".join(removed) if removed else "-",
                        "new": ", ".join(added) if added else "-",
                    }
                )

        return changes

    def _compare_files(self, old_ds, new_ds):
        old_files = {f.name: f for f in old_ds.files()}
        new_files = {f.name: f for f in new_ds.files()}

        added = []
        deleted = []
        modified = []
        unchanged = []

        all_names = set(old_files.keys()) | set(new_files.keys())

        for name in all_names:
            if name in new_files and name not in old_files:
                added.append(new_files[name])
            elif name in old_files and name not in new_files:
                deleted.append(old_files[name])
            else:
                f_old = old_files[name]
                f_new = new_files[name]
                if f_old.checksum != f_new.checksum:
                    modified.append({"old": f_old, "new": f_new})
                else:
                    unchanged.append(f_new)

        return {"added": added, "deleted": deleted, "modified": modified, "unchanged": unchanged}

    def generate_diff_html(self, file_id_old, file_id_new):
        from app.modules.hubfile.models import Hubfile

        f_old = Hubfile.query.get(file_id_old)
        f_new = Hubfile.query.get(file_id_new)

        path_old = f_old.get_path()
        path_new = f_new.get_path()

        try:
            with open(path_old, "r", encoding="utf-8", errors="ignore") as f:
                lines_old = f.readlines()
            with open(path_new, "r", encoding="utf-8", errors="ignore") as f:
                lines_new = f.readlines()

            diff = difflib.HtmlDiff(wrapcolumn=90).make_table(
                lines_old,
                lines_new,
                fromdesc=f"Old: {f_old.name}",
                todesc=f"New: {f_new.name}",
                context=True,
                numlines=3,
            )
            return diff
        except Exception as e:
            return f"Error generating diff: {e}"
