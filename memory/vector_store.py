# memory/vector_store.py
import os
import chromadb
from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer("all-MiniLM-L6-v2")

_base        = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_chroma_path = os.path.join(_base, "chroma_db")

client = chromadb.PersistentClient(path=_chroma_path)

# ── Collection 1: user behaviour embeddings (unchanged) ───────────────────────
collection = client.get_or_create_collection("user_profiles")

# ── Collection 2: product embeddings (NEW — RAG layer) ────────────────────────
product_collection = client.get_or_create_collection("products")


# ═══════════════════════════════════════════════════════════════════════════════
# USER PROFILE FUNCTIONS (unchanged)
# ═══════════════════════════════════════════════════════════════════════════════

def build_user_profile_v2(user_id: str, profile_text: str, metadata: dict) -> str:
    """Store a pre-built behaviour profile."""
    embedding = model.encode(profile_text).tolist()

    safe_meta = {
        k: (float(v) if isinstance(v, (int, float)) else str(v))
        for k, v in metadata.items()
    }

    collection.upsert(
        ids=[str(user_id)],
        embeddings=[embedding],
        documents=[profile_text],
        metadatas=[safe_meta]
    )
    return profile_text


def get_similar_users(user_id: str, n: int = 3) -> list:
    """Safe version - handles empty embeddings properly."""
    try:
        result = collection.get(ids=[str(user_id)], include=["embeddings"])

        embeddings = result.get("embeddings")
        if embeddings is None or len(embeddings) == 0 or (
            isinstance(embeddings, np.ndarray) and embeddings.size == 0
        ):
            return []

        similar = collection.query(
            query_embeddings=embeddings,
            n_results=n + 1
        )

        ids_list    = similar.get("ids", [[]])[0]
        similar_list = [str(uid) for uid in ids_list]
        return [uid for uid in similar_list if uid != str(user_id)]

    except Exception as e:
        print(f"Warning in get_similar_users: {e}")
        return []


def get_similar_users_safe(user_id: str, n: int = 3) -> list:
    """Extra safe wrapper."""
    return get_similar_users(user_id, n)


# ═══════════════════════════════════════════════════════════════════════════════
# PRODUCT RAG FUNCTIONS (NEW)
# ═══════════════════════════════════════════════════════════════════════════════

def is_products_indexed() -> bool:
    """Check whether products have already been indexed into ChromaDB."""
    try:
        return product_collection.count() > 0
    except Exception:
        return False


def index_products(products: list) -> int:
    """
    Embed and store each product in the products collection.
    Text indexed = name + description (richer than name alone).
    Safe to call multiple times — upserts, won't duplicate.
    Returns number of products indexed.
    """
    if not products:
        return 0

    ids, embeddings, documents, metadatas = [], [], [], []

    for p in products:
        item_id  = str(p.get("item_id", ""))
        name     = p.get("name", "")
        desc     = p.get("description", "")
        category = p.get("category", "")
        price    = float(p.get("price", 0.0))

        # Richer text = better semantic retrieval
        index_text = f"{name}. {desc}" if desc else name

        ids.append(item_id)
        embeddings.append(model.encode(index_text).tolist())
        documents.append(index_text)
        metadatas.append({
            "item_id":  item_id,
            "name":     name,
            "category": category,
            "price":    price,
            "cta":      str(p.get("call_to_action", "Shop Now")),
        })

    product_collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas,
    )
    print(f"✅ RAG: indexed {len(ids)} products into ChromaDB")
    return len(ids)


def retrieve_relevant_products(
    query_text: str,
    top_k: int = 8,
    category_hint: str = "",
) -> list:
    """
    Semantic search over the products collection.
    Returns up to top_k products as dicts, sorted by relevance.

    query_text   — user profile summary or predicted intent
    category_hint — optional: bias query toward a specific category
    """
    if product_collection.count() == 0:
        return []

    # Optionally enrich query with category context for better retrieval
    query = f"{query_text} {category_hint}".strip() if category_hint else query_text

    try:
        results = product_collection.query(
            query_embeddings=[model.encode(query).tolist()],
            n_results=min(top_k, product_collection.count()),
            include=["documents", "metadatas", "distances"],
        )

        retrieved = []
        ids_list       = results.get("ids",       [[]])[0]
        metadatas_list = results.get("metadatas", [[]])[0]
        distances_list = results.get("distances", [[]])[0]

        for item_id, meta, dist in zip(ids_list, metadatas_list, distances_list):
            # Convert cosine distance → similarity score (0–1)
            similarity = round(max(0.0, 1.0 - float(dist)), 4)
            retrieved.append({
                "item_id":      meta.get("item_id",  item_id),
                "name":         meta.get("name",     "Unknown"),
                "category":     meta.get("category", ""),
                "price":        float(meta.get("price", 0.0)),
                "call_to_action": meta.get("cta",   "Shop Now"),
                "rag_score":    similarity,   # internal — not shown in UI
            })

        return retrieved

    except Exception as e:
        print(f"Warning in retrieve_relevant_products: {e}")
        return []