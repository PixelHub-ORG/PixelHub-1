from app.modules.filemodel.repositories import FileModelRepository, FMMetaDataRepository
from app.modules.hubfile.services import HubfileService
from core.services.BaseService import BaseService


class FilemodelService(BaseService):
    def __init__(self):
        super().__init__(FileModelRepository())
        self.hubfile_service = HubfileService()

    def total_file_model_views(self) -> int:
        return self.hubfile_service.total_hubfile_views()

    def get_file_model_by_id(self, file_model_id: int):
        return self.repository.get_by_id(file_model_id)

    def total_file_model_downloads(self) -> int:
        return self.hubfile_service.total_hubfile_downloads()

    def count_file_models(self):
        return self.repository.count_file_models()

    class FMMetaDataService(BaseService):
        def __init__(self):
            super().__init__(FMMetaDataRepository())
