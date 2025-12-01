from typing import List, Optional

from app.models import Deposition


class DepositionService:
    """Servicio para gestionar depositions en memoria"""

    # Datos en memoria (se pierden al reiniciar)
    _depositions: dict = {}
    _files: dict = {}
    _next_deposition_id: int = 1
    _next_file_id: int = 1

    @classmethod
    def _initialize(cls):
        """Inicializa con datos de ejemplo"""
        if not cls._depositions:
            cls._depositions = {
                1: Deposition(
                    id=1,
                    title="Dataset inicial",
                    description="Un dataset de ejemplo",
                    state="draft",
                    doi=None,
                    metadata={"keywords": ["test"]},
                ),
                2: Deposition(
                    id=2,
                    title="Dataset publicado",
                    description="Ya está publicado",
                    state="published",
                    doi="10.5281/zenodo.1000002",
                    metadata={},
                ),
            }
            cls._next_deposition_id = 3

    @classmethod
    def crear_deposition(cls, title: str, description: str = "", metadata: dict = None) -> Deposition:
        """Crea un nuevo deposition"""
        cls._initialize()

        new_dep = Deposition(
            id=cls._next_deposition_id,
            title=title,
            description=description,
            state="draft",
            doi=None,
            metadata=metadata or {},
        )

        cls._depositions[cls._next_deposition_id] = new_dep
        cls._next_deposition_id += 1

        return new_dep

    @classmethod
    def obtener_deposition(cls, deposition_id: int) -> Optional[Deposition]:
        """Obtiene un deposition por ID"""
        cls._initialize()
        return cls._depositions.get(deposition_id)

    @classmethod
    def listar_depositions(cls) -> List[Deposition]:
        """Obtiene todos los depositions"""
        cls._initialize()
        return list(cls._depositions.values())

    @classmethod
    def publicar_deposition(cls, deposition_id: int, provided_doi: Optional[str] = None) -> Optional[Deposition]:
        """Publica un deposition y genera DOI.
        Si provided_doi está presente, se usa directamente. En caso contrario,
        se genera un DOI por defecto.
        """
        cls._initialize()

        dep = cls._depositions.get(deposition_id)
        if not dep:
            return None

        if not dep.doi:
            if provided_doi:
                dep.doi = provided_doi
            else:
                # Fallback: generate a numeric-looking DOI suffix to mimic Zenodo style.
                # We base it on the highest existing numeric suffix in memory.
                import re

                existing = []
                for d in cls._depositions.values():
                    if d.doi:
                        m = re.search(r"zenodo\.(\d+)$", d.doi)
                        if m:
                            existing.append(int(m.group(1)))
                next_suffix = (max(existing) + 1) if existing else 1000001
                dep.doi = f"10.5281/zenodo.{next_suffix}"

        dep.state = "published"
        return dep

    @classmethod
    def eliminar_deposition(cls, deposition_id: int) -> bool:
        """Elimina un deposition"""
        cls._initialize()

        if deposition_id in cls._depositions:
            del cls._depositions[deposition_id]
            return True
        return False
