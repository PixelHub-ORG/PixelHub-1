import os
import shutil
from datetime import datetime, timezone

from dotenv import load_dotenv

from app.modules.auth.models import User
from app.modules.dataset.models import (
    Author,
    DataSet,
    DSMetaData,
    DSMetrics,
    PublicationType,
)
from app.modules.filemodel.models import FileModel, FMMetaData
from app.modules.hubfile.models import Hubfile
from core.seeders.BaseSeeder import BaseSeeder


class DataSetSeeder(BaseSeeder):

    priority = 2  # Lower priority

    def run(self):
        user1 = User.query.filter_by(email="user1@example.com").first()
        user2 = User.query.filter_by(email="user2@example.com").first()

        if not user1 or not user2:
            raise Exception("Users not found. Please seed users first.")

        # Create DSMetrics instance
        ds_metrics = DSMetrics(number_of_models="5", number_of_files="50")
        seeded_ds_metrics = self.seed([ds_metrics])[0]

        # Create DSMetaData instances
        ds_meta_data_list = [
            DSMetaData(
                deposition_id=1 + i,
                title=f"Sample dataset {i+1}",
                description=f"Description for dataset {i+1}",
                publication_type=PublicationType.DATA_MANAGEMENT_PLAN,
                publication_doi=f"10.1234/dataset{i+1}",
                dataset_doi=f"10.1234/dataset{i+1}",
                tags="tag1, tag2",
                ds_metrics_id=seeded_ds_metrics.id,
            )
            for i in range(4)
        ]
        seeded_ds_meta_data = self.seed(ds_meta_data_list)

        # Create Author instances and associate with DSMetaData
        authors = [
            Author(
                name=f"Author {i+1}",
                affiliation=f"Affiliation {i+1}",
                orcid=f"0000-0000-0000-000{i}",
                ds_meta_data_id=seeded_ds_meta_data[i % 4].id,
            )
            for i in range(4)
        ]
        self.seed(authors)

        # Create DataSet instances
        datasets = [
            DataSet(
                user_id=user1.id if i % 2 == 0 else user2.id,
                ds_meta_data_id=seeded_ds_meta_data[i].id,
                created_at=datetime.now(timezone.utc),
            )
            for i in range(4)
        ]
        seeded_datasets = self.seed(datasets)

        # Assume there are 11 files, create corresponding FMMetaData and FileModel
        fm_meta_data_list = [
            FMMetaData(
                filename=f"file{i+1}.pix",
                title=f"File Model {i+1}",
                description=f"Description for file model {i+1}",
                publication_type=PublicationType.SOFTWARE_DOCUMENTATION,
                publication_doi=f"10.1234/fm{i+1}",
                tags="tag1, tag2",
            )
            for i in range(11)
        ]
        seeded_fm_meta_data = self.seed(fm_meta_data_list)

        # Create Author instances and associate with FMMetaData
        fm_authors = [
            Author(
                name=f"Author {i+5}",
                affiliation=f"Affiliation {i+5}",
                orcid=f"0000-0000-0000-000{i+5}",
                fm_meta_data_id=seeded_fm_meta_data[i].id,
            )
            for i in range(11)
        ]
        self.seed(fm_authors)

        file_models = [
            FileModel(data_set_id=seeded_datasets[i // 3].id, fm_meta_data_id=seeded_fm_meta_data[i].id)
            for i in range(11)
        ]
        seeded_file_models = self.seed(file_models)

        # Create files, associate them with FileModels and copy files
        load_dotenv()
        working_dir = os.getenv("WORKING_DIR", "")
        src_folder = os.path.join(working_dir, "app", "modules", "dataset", "pix_examples")

        if not os.path.exists(src_folder):
            os.makedirs(src_folder)

        for i in range(11):
            dummy_path = os.path.join(src_folder, f"file{i+1}.pix")
            if not os.path.exists(dummy_path):
                with open(dummy_path, "w") as f:
                    f.write(f"Contenido dummy para file{i+1}")

        for i in range(11):
            file_name = f"file{i+1}.pix"
            file_model = seeded_file_models[i]
            dataset = next(ds for ds in seeded_datasets if ds.id == file_model.data_set_id)
            user_id = dataset.user_id

            dest_folder = os.path.join(working_dir, "uploads", f"user_{user_id}", f"dataset_{dataset.id}")
            os.makedirs(dest_folder, exist_ok=True)
            shutil.copy(os.path.join(src_folder, file_name), dest_folder)

            file_path = os.path.join(dest_folder, file_name)

            pix_file = Hubfile(
                name=file_name,
                checksum=f"checksum{i+1}",
                size=os.path.getsize(file_path),
                file_model_id=file_model.id,
            )
            self.seed([pix_file])

        ID_V1 = 9991
        ID_V2 = 9992

        ds_meta_v1 = DSMetaData(
            deposition_id=ID_V1,
            title="Locust Testing Dataset",
            description="Dataset Version 1",
            publication_type=PublicationType.SOFTWARE_DOCUMENTATION,
            publication_doi="10.1234/locust-v1",
            dataset_doi="10.1234/locust-v1",
            tags="locust,v1",
            ds_metrics_id=seeded_ds_metrics.id,
        )
        self.seed([ds_meta_v1])

        author_v1 = Author(
            name="Locust Tester",
            affiliation="Fakenodo University",
            orcid="0000-0000-0000-9991",
            ds_meta_data_id=ds_meta_v1.id,
        )
        self.seed([author_v1])

        dataset_v1 = DataSet(
            id=ID_V1,
            user_id=user1.id,
            ds_meta_data_id=ds_meta_v1.id,
            created_at=datetime.now(timezone.utc),
            type="pix",
            version=1,
        )
        self.seed([dataset_v1])

        fm_meta_v1 = FMMetaData(
            filename="file1.pix",
            title="File V1",
            description="Description for File V1",
            publication_type=PublicationType.SOFTWARE_DOCUMENTATION,
            tags="v1",
        )
        self.seed([fm_meta_v1])

        fm_v1 = FileModel(data_set_id=ID_V1, fm_meta_data_id=fm_meta_v1.id)
        seeded_fm_v1 = self.seed([fm_v1])[0]

        dest_v1 = os.path.join(working_dir, "uploads", f"user_{user1.id}", f"dataset_{ID_V1}")
        os.makedirs(dest_v1, exist_ok=True)
        shutil.copy(os.path.join(src_folder, "file1.pix"), dest_v1)

        hubfile_v1 = Hubfile(
            name="file1.pix",
            checksum="checksum1",
            size=os.path.getsize(os.path.join(dest_v1, "file1.pix")),
            file_model_id=seeded_fm_v1.id,
        )
        self.seed([hubfile_v1])

        ds_meta_v2 = DSMetaData(
            deposition_id=ID_V2,
            title="Locust Testing Dataset",
            description="Dataset Version 2 (Updated)",
            publication_type=PublicationType.SOFTWARE_DOCUMENTATION,
            publication_doi="10.1234/locust-v2",
            dataset_doi="10.1234/locust-v2",
            tags="locust,v2",
            ds_metrics_id=seeded_ds_metrics.id,
        )
        self.seed([ds_meta_v2])

        author_v2 = Author(
            name="Locust Tester",
            affiliation="Fakenodo University",
            orcid="0000-0000-0000-9991",
            ds_meta_data_id=ds_meta_v2.id,
        )
        self.seed([author_v2])

        dataset_v2 = DataSet(
            id=ID_V2,
            user_id=user1.id,
            ds_meta_data_id=ds_meta_v2.id,
            created_at=datetime.now(timezone.utc),
            type="pix",
            version=2,
            previous_version_id=ID_V1,
        )
        self.seed([dataset_v2])

        fm_meta_v2 = FMMetaData(
            filename="file2.pix",
            title="File V2",
            description="Description for File V2",
            publication_type=PublicationType.SOFTWARE_DOCUMENTATION,
            tags="v2",
        )
        self.seed([fm_meta_v2])

        fm_v2 = FileModel(data_set_id=ID_V2, fm_meta_data_id=fm_meta_v2.id)
        seeded_fm_v2 = self.seed([fm_v2])[0]

        dest_v2 = os.path.join(working_dir, "uploads", f"user_{user1.id}", f"dataset_{ID_V2}")
        os.makedirs(dest_v2, exist_ok=True)
        shutil.copy(os.path.join(src_folder, "file2.pix"), dest_v2)

        hubfile_v2 = Hubfile(
            name="file2.pix",
            checksum="checksum2",
            size=os.path.getsize(os.path.join(dest_v2, "file2.pix")),
            file_model_id=seeded_fm_v2.id,
        )
        self.seed([hubfile_v2])
