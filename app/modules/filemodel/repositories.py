from sqlalchemy import func

from app.modules.filemodel.models import FileModel, FMMetaData
from core.repositories.BaseRepository import BaseRepository


class FileModelRepository(BaseRepository):
    def __init__(self):
        super().__init__(FileModel)

    def count_file_models(self) -> int:
        max_id = self.model.query.with_entities(func.max(self.model.id)).scalar()
        return max_id if max_id is not None else 0


class FMMetaDataRepository(BaseRepository):
    def __init__(self):
        super().__init__(FMMetaData)
