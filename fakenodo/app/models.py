from dataclasses import asdict, dataclass
from typing import Optional

"Modelo Deposition: Se usa para poder crear y hacer fetch de Records"


@dataclass
class Deposition:
    id: int
    title: str
    description: str
    state: str
    doi: Optional[str] = None
    metadata: Optional[dict] = None

    def to_dict(self):
        "Convertir el modelo en un json"
        return asdict(self)

    @staticmethod
    def from_dict(data: dict):
        "Crear una Deposition desde un diccionario"
        return Deposition(**data)


"Modelo File: Los archivos asociados a una deposición"


@dataclass
class File:
    id: int
    deposition_id: int
    name: str
    size: int
    checksum: str

    def to_dict(self):
        "Convertir el modelo en un json"
        return asdict(self)

    @staticmethod
    def from_dict(data: dict):
        "Crear un File desde un diccionario"
        return File(**data)


"Modelo Creator: Representa el creado de una deposición"


@dataclass
class Creator:
    id: int
    name: str
    deposition_id: int

    def to_dict(self):
        "Convertir el modelo en un json"
        return asdict(self)

    def from_dict(data: dict):
        "Crear un Creator desde un diccionario"
        return Creator(**data)
