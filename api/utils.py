"""
Utility functions: loading era embeddings, similarity search, drift/shift computation.
Enhanced with better error handling and validation.
"""
from pathlib import Path
import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from functools import lru_cache
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

BASE_EMBED_DIR = Path("embeddings")

class EmbeddingValidationError(Exception):
    """Raised when embedding data is malformed or missing required fields."""
    pass

def validate_item(item: Dict[str, Any], index: int) -> None:
    """Validate that an item has required fields with correct types."""
    required_fields = ["id", "text", "embedding"]
    
    for field in required_fields:
        if field not in item:
            raise EmbeddingValidationError(
                f"Item at index {index} missing required field: {field}"
            )
    
    if not isinstance(item["embedding"], (list, np.ndarray)):
        raise EmbeddingValidationError(
            f"Item {item.get('id', index)} has invalid embedding type: {type(item['embedding'])}"
        )
    
    if isinstance(item["embedding"], list) and len(item["embedding"]) == 0:
        raise EmbeddingValidationError(
            f"Item {item['id']} has empty embedding"
        )

def load_era_items(concept: str, era_file: str) -> List[Dict[str, Any]]:
    """
    Load items from embeddings/<concept>/<era_file>.json
    era_file should include .json suffix (e.g., '1900s.json')
    
    Raises:
        FileNotFoundError: If the file doesn't exist
        EmbeddingValidationError: If data format is invalid
    """
    p = BASE_EMBED_DIR / concept / era_file
    if not p.exists():
        raise FileNotFoundError(f"Embedding file not found: {p}")
    
    try:
        with p.open("r", encoding="utf8") as f:
            js = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from {p}: {e}")
        raise EmbeddingValidationError(f"Invalid JSON in {p}: {e}")
    
    items = js.get("items", [])
    
    # Validate each item
    for i, item in enumerate(items):
        try:
            validate_item(item, i)
        except EmbeddingValidationError as e:
            logger.warning(f"Skipping invalid item in {p}: {e}")
            continue
    
    # Filter out any items that failed validation
    valid_items = [item for i, item in enumerate(items) 
                   if all(field in item for field in ["id", "text", "embedding"])]
    
    if not valid_items:
        logger.warning(f"No valid items found in {p}")
    
    return valid_items

@lru_cache(maxsize=128)
def load_all_eras(concept: str) -> List[Dict[str, Any]]:
    """
    Returns list of dicts: { era: '1900s', items: [...] }
    
    Raises:
        FileNotFoundError: If concept directory doesn't exist
    """
    base = BASE_EMBED_DIR / concept
    if not base.exists():
        raise FileNotFoundError(f"Concept directory not found: {base}")
    
    files = sorted([x.name for x in base.iterdir() if x.suffix == ".json"])
    
    if not files:
        logger.warning(f"No JSON files found in {base}")
        return []
    
    result = []
    for fn in files:
        try:
            items = load_era_items(concept, fn)
            if items:  # Only add eras with valid items
                era_name = fn.replace(".json", "")
                result.append({"era": era_name, "items": items})
        except (FileNotFoundError, EmbeddingValidationError) as e:
            logger.error(f"Failed to load era {fn}: {e}")
            continue
    
    return result

def _to_numpy_embeddings(items: List[Dict[str, Any]]) -> np.ndarray:
    """Convert list of items with embeddings to numpy array."""
    if not items:
        return np.array([])
    
    try:
        embs = [np.array(it["embedding"], dtype=float) for it in items]
        return np.array(embs)
    except (KeyError, ValueError, TypeError) as e:
        raise EmbeddingValidationError(f"Failed to convert embeddings to numpy: {e}")

def top_similar_in_era(
    query_emb: List[float], 
    items: List[Dict[str, Any]], 
    top_n: int = 6
) -> List[Dict[str, Any]]:
    """
    Return top_n items most similar to query_emb from items.
    Each returned item: {id, text, score}
    """
    if not items:
        logger.warning("No items provided for similarity search")
        return []
    
    if not query_emb:
        logger.error("Empty query embedding provided")
        return []
    
    try:
        X = _to_numpy_embeddings(items)
        if X.size == 0:
            return []
        
        sims = cosine_similarity([query_emb], X)[0]
        
        # Handle case where top_n > number of items
        actual_top_n = min(top_n, len(items))
        idx = np.argsort(sims)[::-1][:actual_top_n]
        
        out = []
        for i in idx:
            out.append({
                "id": items[i]["id"],
                "text": items[i]["text"],
                "score": float(sims[i])
            })
        return out
    except EmbeddingValidationError as e:
        logger.error(f"Error in similarity computation: {e}")
        return []

def compute_centroid(items: List[Dict[str, Any]]) -> Optional[np.ndarray]:
    """Compute the centroid (mean) of all item embeddings."""
    if not items:
        return None
    
    try:
        X = _to_numpy_embeddings(items)
        if X.size == 0:
            return None
        return np.mean(X, axis=0)
    except EmbeddingValidationError as e:
        logger.error(f"Failed to compute centroid: {e}")
        return None

def centroid_shift_score(centroid_a: Optional[np.ndarray], 
                         centroid_b: Optional[np.ndarray]) -> float:
    """
    Return 1 - cosine_similarity(centroid_a, centroid_b) to indicate shift magnitude.
    Larger value => more shift.
    Returns 0.0 if either centroid is None.
    """
    if centroid_a is None or centroid_b is None:
        return 0.0
    
    try:
        a = centroid_a.reshape(1, -1)
        b = centroid_b.reshape(1, -1)
        sim = cosine_similarity(a, b)[0][0]
        return float(1.0 - sim)
    except Exception as e:
        logger.error(f"Error computing centroid shift: {e}")
        return 0.0

def build_timeline_for_query(
    concept: str, 
    query_emb: List[float], 
    top_n: int = 6
) -> Dict[str, Any]:
    """
    Returns:
      { concept, timeline: [ { era, top: [{id,text,score}], centroid_shift_from_prev }, ... ] }
    """
    try:
        eras = load_all_eras(concept)
    except FileNotFoundError as e:
        logger.error(f"Failed to load eras for concept '{concept}': {e}")
        return {"concept": concept, "timeline": [], "error": str(e)}
    
    if not eras:
        logger.warning(f"No eras found for concept '{concept}'")
        return {"concept": concept, "timeline": []}
    
    result = []
    prev_centroid = None
    
    for era in eras:
        items = era["items"]
        top = top_similar_in_era(query_emb, items, top_n=top_n)
        centroid = compute_centroid(items)
        shift = centroid_shift_score(prev_centroid, centroid) if prev_centroid is not None else 0.0
        
        result.append({
            "era": era["era"], 
            "top": top, 
            "centroid_shift_from_prev": shift
        })
        prev_centroid = centroid
    
    return {"concept": concept, "timeline": result}