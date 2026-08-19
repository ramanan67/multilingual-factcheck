import chromadb
from chromadb import Documents, EmbeddingFunction, Embeddings
from sentence_transformers import SentenceTransformer
from app.core.config import settings

_client = None
_collection = None
_model = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(settings.EMBEDDING_MODEL)
    return _model


class E5PassageEmbeddingFunction(EmbeddingFunction):
    """
    intfloat/e5 models use an ASYMMETRIC prefix scheme: passages must be
    embedded with "passage: " and queries with "query: ". Skipping this
    is a common e5 mistake and it doesn't fail loudly -- it just silently
    compresses all similarity scores into a narrow, uninformative band
    (observed: ~0.79-0.85 for both genuinely matching AND completely
    unrelated headlines), which is exactly the false-positive pattern
    that showed up in testing (a Bigg Boss story scoring ~0.79 against a
    Tamil Thai Vazhthu claim).

    This embedding function is registered on the Chroma collection and is
    only invoked automatically for documents (add/upsert). Queries are
    embedded separately via embed_query() below with the "query: " prefix
    and passed in manually as query_embeddings, since Chroma calls the
    same embedding function for both sides and can't apply the prefix
    conditionally on its own.
    """

    def __call__(self, input: Documents) -> Embeddings:
        model = get_model()
        prefixed = [f"passage: {t}" for t in input]
        return model.encode(prefixed, normalize_embeddings=True).tolist()


def embed_query(text: str) -> list:
    model = get_model()
    return model.encode(f"query: {text}", normalize_embeddings=True).tolist()


def get_collection():
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR,
            settings=chromadb.Settings(anonymized_telemetry=False),
        )
        _collection = _client.get_or_create_collection(
            name="whitelisted_news",
            embedding_function=E5PassageEmbeddingFunction(),
            metadata={"hnsw:space": "cosine"},
        )
    return _collection
