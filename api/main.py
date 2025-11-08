"""
Streamlined FastAPI application for Echoes backend.
Optimized for OpenRouter API usage.
"""
from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from sentence_transformers import SentenceTransformer
from typing import List
import logging
import json

from api import settings
from api import utils
from api.models import TimelineResponse
from api.etymology_service import etymology_service, OpenRouterError

# Setup logging
logging.basicConfig(
    level=settings.log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(settings.log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Echoes Backend",
    version="1.1.0",
    description="Track semantic evolution of concepts across time using OpenRouter LLMs"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lazy model loading
_model = None

def get_model() -> SentenceTransformer:
    """Load sentence transformer model on first use."""
    global _model
    if _model is None:
        logger.info(f"Loading sentence transformer: {settings.sentence_transformer_model}")
        _model = SentenceTransformer(settings.sentence_transformer_model)
        logger.info("Model loaded successfully")
    return _model


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("="*60)
    logger.info("Starting Echoes Backend v1.1.0")
    logger.info("="*60)
    logger.info(f"OpenRouter Model: {settings.openrouter_model}")
    logger.info(f"LLM Etymology: {settings.use_llm_etymology}")
    logger.info(f"Response Caching: {settings.cache_llm_responses}")
    logger.info(f"CORS Origins: {settings.cors_origins}")
    logger.info("="*60)


@app.get("/")
def root():
    """Root endpoint with API info."""
    return {
        "name": "Echoes Backend",
        "version": "1.1.0",
        "description": "Semantic evolution tracking across time periods",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
def health():
    """Health check endpoint."""
    return {
        "status": "ok",
        "version": "1.1.0",
        "model": settings.openrouter_model,
        "llm_enabled": settings.use_llm_etymology,
        "cache_enabled": settings.cache_llm_responses
    }


@app.post("/embed")
def embed_text(text: str = Body(..., embed=True)):
    """
    Generate embedding for arbitrary text.
    
    Args:
        text: Input text to embed
    
    Returns:
        Dictionary with embedding vector and original text
    """
    if not text or not text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    try:
        model = get_model()
        emb = model.encode(text)
        return {
            "embedding": emb.tolist(),
            "text": text,
            "dimensions": len(emb)
        }
    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate embedding: {str(e)}"
        )


@app.get("/timeline", response_model=TimelineResponse)
def timeline(
    concept: str = Query(..., description="Concept name (e.g., 'freedom')"),
    top_n: int = Query(
        settings.DEFAULT_TOP_N,
        ge=1,
        le=settings.MAX_TOP_N,
        description="Number of top items per era"
    )
):
    """
    Get timeline showing concept evolution across eras.
    
    Args:
        concept: Name of the concept (must have embeddings generated)
        top_n: Number of top similar items per era
    
    Returns:
        Timeline data with top items and centroid shifts
    """
    concept_dir = settings.embeddings_path / concept
    
    if not concept_dir.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Concept '{concept}' not found. Generate embeddings first using /build-embeddings"
        )
    
    try:
        model = get_model()
        query_emb = model.encode(concept)
        timeline_data = utils.build_timeline_for_query(
            concept,
            query_emb.tolist(),
            top_n=top_n
        )
        return timeline_data
    
    except Exception as e:
        logger.error(f"Error building timeline for '{concept}': {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to build timeline: {str(e)}"
        )


@app.get("/era")
def era(
    concept: str = Query(..., description="Concept name"),
    era: str = Query(..., description="Era name (e.g., '1900s')"),
    top_n: int = Query(10, ge=1, le=100, description="Number of top items")
):
    """
    Get top items for a specific era.
    
    Args:
        concept: Concept name
        era: Era name (e.g., '1900s', '2020s')
        top_n: Number of top items to return
    
    Returns:
        Top similar items for the specified era
    """
    era_file = f"{era}.json" if not era.endswith(".json") else era
    
    try:
        items = utils.load_era_items(concept, era_file)
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Era '{era}' not found for concept '{concept}'"
        )
    except Exception as e:
        logger.error(f"Error loading era {era} for {concept}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load era data: {str(e)}"
        )
    
    try:
        model = get_model()
        query_emb = model.encode(concept)
        top = utils.top_similar_in_era(query_emb.tolist(), items, top_n=top_n)
        
        return {
            "concept": concept,
            "era": era,
            "top": top,
            "total_items": len(items)
        }
    except Exception as e:
        logger.error(f"Error computing similarities: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to compute similarities: {str(e)}"
        )


@app.post("/generate-evolution")
async def generate_evolution(
    word: str = Body(..., description="Word to analyze", min_length=1, max_length=100),
    eras: List[str] = Body(..., description="List of eras", min_length=1),
    num_examples: int = Body(
        settings.DEFAULT_EXAMPLES_PER_ERA,
        ge=1,
        le=settings.MAX_EXAMPLES_PER_ERA,
        description="Examples per era"
    )
):
    """
    Generate word evolution data using OpenRouter LLM.
    
    This endpoint uses the configured LLM to generate contextual examples
    showing how a word's meaning evolved across different time periods.
    
    Args:
        word: Word to analyze
        eras: List of time periods (e.g., ["1900s", "1950s", "2020s"])
        num_examples: Number of examples per era (1-20)
    
    Returns:
        Evolution data with examples for each era
    
    Raises:
        400: Invalid input
        500: LLM API error or timeout
    """
    if not settings.use_llm_etymology:
        raise HTTPException(
            status_code=503,
            detail="LLM etymology is disabled in configuration"
        )
    
    try:
        logger.info(
            f"Generating evolution for '{word}' across {len(eras)} eras"
        )
        
        evolution_data = etymology_service.generate_word_evolution(
            word=word,
            eras=eras,
            num_examples=num_examples
        )
        
        total_examples = sum(len(examples) for examples in evolution_data.values())
        
        return {
            "word": word,
            "eras": eras,
            "evolution": evolution_data,
            "total_examples": total_examples,
            "model": settings.openrouter_model
        }
    
    except ValueError as e:
        logger.warning(f"Invalid input for '{word}': {e}")
        raise HTTPException(status_code=400, detail=str(e))
    
    except OpenRouterError as e:
        logger.error(f"OpenRouter API error for '{word}': {e}")
        raise HTTPException(
            status_code=500,
            detail=f"LLM API error: {str(e)}"
        )
    
    except TimeoutError:
        logger.error(f"OpenRouter request timed out for '{word}'")
        raise HTTPException(
            status_code=504,
            detail=f"Request timed out after {settings.llm_timeout}s"
        )
    
    except Exception as e:
        logger.error(f"Unexpected error generating evolution for '{word}': {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )


@app.post("/build-embeddings")
async def build_embeddings_endpoint(
    word: str = Body(..., min_length=1, max_length=100),
    eras: List[str] = Body(..., min_length=1),
    num_examples: int = Body(
        settings.DEFAULT_EXAMPLES_PER_ERA,
        ge=1,
        le=settings.MAX_EXAMPLES_PER_ERA
    )
):
    """
    Complete pipeline: Generate evolution data AND create embeddings.
    
    This combines /generate-evolution with embedding creation:
    1. Uses LLM to generate contextual examples
    2. Creates embeddings for each example
    3. Saves to JSON files in embeddings/<word>/<era>.json
    
    Args:
        word: Word to analyze
        eras: List of time periods
        num_examples: Examples per era
    
    Returns:
        Information about created embedding files
    """
    # First, generate the evolution data
    try:
        evolution_result = await generate_evolution(word, eras, num_examples)
        evolution_data = evolution_result["evolution"]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate evolution data: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Evolution generation failed: {str(e)}"
        )
    
    # Now create embeddings for each era
    try:
        model = get_model()
        concept_dir = settings.embeddings_path / word
        concept_dir.mkdir(parents=True, exist_ok=True)
        
        embeddings_created = []
        total_items = 0
        
        for era in eras:
            if era not in evolution_data:
                logger.warning(f"No data for era {era}, skipping")
                continue
            
            texts = evolution_data[era]
            if not texts:
                continue
            
            # Generate embeddings
            logger.info(f"Generating {len(texts)} embeddings for {word}/{era}")
            embs = model.encode(texts, show_progress_bar=False)
            
            # Create items
            items = []
            for i, (text, emb) in enumerate(zip(texts, embs)):
                items.append({
                    "id": f"{word}_{era}_{i}",
                    "text": text,
                    "era": era,
                    "embedding": emb.tolist()
                })
            
            # Save to JSON
            output_path = concept_dir / f"{era}.json"
            with output_path.open("w", encoding="utf8") as f:
                json.dump({
                    "items": items,
                    "meta": {
                        "concept": word,
                        "era": era,
                        "count": len(items),
                        "model": settings.openrouter_model,
                        "embedding_model": settings.sentence_transformer_model
                    }
                }, f, ensure_ascii=False, indent=2)
            
            embeddings_created.append(str(output_path))
            total_items += len(items)
            logger.info(f"Created embeddings file: {output_path}")
        
        return {
            "word": word,
            "eras": eras,
            "embeddings_files": embeddings_created,
            "total_items": total_items,
            "llm_model": settings.openrouter_model,
            "embedding_model": settings.sentence_transformer_model,
            "message": f"Successfully created embeddings for {len(embeddings_created)} eras ({total_items} items)"
        }
    
    except Exception as e:
        logger.error(f"Failed to create embeddings: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Embedding creation failed: {str(e)}"
        )