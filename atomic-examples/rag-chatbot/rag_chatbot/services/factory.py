from .base import BaseVectorDBService
from .chroma_db import ChromaDBService
from .qdrant_db import QdrantDBService
from ..config import VECTOR_DB_TYPE, CHROMA_PERSIST_DIR, QDRANT_PERSIST_DIR


def create_vector_db_service(
    collection_name: str,
    recreate_collection: bool = False,
) -> BaseVectorDBService:
    """Create a vector database service based on configuration.

    Args:
        collection_name: Name of the collection to use
        recreate_collection: If True, deletes the collection if it exists before creating

    Returns:
        BaseVectorDBService: The appropriate vector database service instance
    """

    if VECTOR_DB_TYPE == VECTOR_DB_TYPE.CHROMA:
        return ChromaDBService(
            collection_name=collection_name,
            persist_directory=CHROMA_PERSIST_DIR,
            recreate_collection=recreate_collection,
        )
    elif VECTOR_DB_TYPE == VECTOR_DB_TYPE.QDRANT:
        return QdrantDBService(
            collection_name=collection_name,
            persist_directory=QDRANT_PERSIST_DIR,
            recreate_collection=recreate_collection,
        )
    else:
        raise ValueError(f"Unsupported database type: {VECTOR_DB_TYPE}")
