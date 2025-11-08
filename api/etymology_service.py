"""
Streamlined etymology service using OpenRouter API.
Includes retry logic, caching, and proper error handling.
"""
import logging
import json
from typing import List, Dict, Any
from functools import lru_cache
from openai import OpenAI
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

from api.config import settings

logger = logging.getLogger(__name__)


class OpenRouterError(Exception):
    """Custom exception for OpenRouter API errors."""
    pass


class EtymologyService:
    """Service for generating word evolution data using OpenRouter."""
    
    def __init__(self):
        """Initialize OpenRouter client."""
        self.client = OpenAI(
            api_key=settings.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1"
        )
        self.model = settings.openrouter_model
        
        # Headers for OpenRouter
        self.extra_headers = {
            "HTTP-Referer": settings.openrouter_site_url,
            "X-Title": settings.openrouter_app_name,
        }
        
        logger.info(f"Initialized OpenRouter with model: {self.model}")
    
    def _build_prompt(self, word: str, eras: List[str], num_examples: int) -> str:
        """Build the LLM prompt for word evolution analysis."""
        return f"""Analyze how the word "{word}" evolved across different time periods.

For each era below, provide {num_examples} contextual examples that show how people understood and used this word during that period. Focus on:
- Semantic changes and shifts in meaning
- Cultural context and connotations
- Historical usage patterns
- Notable differences from other eras

Eras: {", ".join(eras)}

Requirements:
- Each example should be a complete phrase or short sentence (10-30 words)
- Show authentic period-appropriate usage
- Capture the essence of how meaning changed
- Be historically accurate and specific

Format as valid JSON only (no markdown, no preamble):
{{
  "1900s": [
    "example 1 showing meaning/context",
    "example 2 showing meaning/context",
    ...
  ],
  "2020s": [
    "example 1 showing meaning/context",
    ...
  ]
}}"""
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((OpenRouterError, TimeoutError)),
        reraise=True
    )
    def _call_openrouter(self, prompt: str) -> str:
        """
        Call OpenRouter API with retry logic.
        
        Raises:
            OpenRouterError: If API call fails after retries
            TimeoutError: If request times out
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a historical linguist and etymologist specializing in semantic evolution. Respond ONLY with valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=settings.llm_temperature,
                max_tokens=settings.llm_max_tokens,
                timeout=settings.llm_timeout,
                extra_headers=self.extra_headers
            )
            
            content = response.choices[0].message.content
            
            if not content:
                raise OpenRouterError("Empty response from OpenRouter")
            
            return content
        
        except TimeoutError as e:
            logger.error(f"OpenRouter request timed out: {e}")
            raise
        
        except Exception as e:
            logger.error(f"OpenRouter API error: {e}")
            raise OpenRouterError(f"API call failed: {str(e)}")
    
    def _parse_response(self, content: str) -> Dict[str, List[str]]:
        """
        Parse LLM response, handling markdown code blocks.
        
        Returns:
            Dict mapping era to list of examples
        
        Raises:
            ValueError: If response is not valid JSON
        """
        # Remove markdown code blocks if present
        content = content.strip()
        
        if content.startswith("```"):
            lines = content.split("\n")
            # Remove first and last lines (``` markers)
            content = "\n".join(lines[1:-1])
            # Remove 'json' language marker if present
            if content.startswith("json"):
                content = content[4:].strip()
        
        try:
            data = json.loads(content)
            
            # Validate structure
            if not isinstance(data, dict):
                raise ValueError("Response is not a JSON object")
            
            # Ensure all values are lists of strings
            for era, examples in data.items():
                if not isinstance(examples, list):
                    raise ValueError(f"Era '{era}' does not contain a list")
                if not all(isinstance(ex, str) for ex in examples):
                    raise ValueError(f"Era '{era}' contains non-string examples")
            
            return data
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.debug(f"Raw content: {content[:500]}")
            raise ValueError(f"Invalid JSON response: {str(e)}")
    
    @lru_cache(maxsize=100)
    def _cached_generation(self, word: str, eras_tuple: tuple, num_examples: int) -> str:
        """Cached API call (eras as tuple for hashability)."""
        eras = list(eras_tuple)
        prompt = self._build_prompt(word, eras, num_examples)
        return self._call_openrouter(prompt)
    
    def generate_word_evolution(
        self,
        word: str,
        eras: List[str],
        num_examples: int = 5
    ) -> Dict[str, List[str]]:
        """
        Generate word evolution data across eras.
        
        Args:
            word: The word to analyze
            eras: List of time periods (e.g., ["1900s", "2020s"])
            num_examples: Number of examples per era (1-20)
        
        Returns:
            Dictionary mapping era to list of contextual examples
        
        Raises:
            ValueError: If input validation fails or response is invalid
            OpenRouterError: If API call fails after retries
        """
        # Input validation
        if not word or not word.strip():
            raise ValueError("Word cannot be empty")
        
        word = word.strip().lower()
        
        if not eras:
            raise ValueError("Must provide at least one era")
        
        if num_examples < 1 or num_examples > settings.MAX_EXAMPLES_PER_ERA:
            raise ValueError(
                f"num_examples must be between 1 and {settings.MAX_EXAMPLES_PER_ERA}"
            )
        
        # Validate era format (basic check)
        for era in eras:
            if not era.strip():
                raise ValueError(f"Invalid era: '{era}'")
        
        logger.info(
            f"Generating evolution for '{word}' across {len(eras)} eras "
            f"({num_examples} examples each)"
        )
        
        try:
            # Use cache if enabled
            if settings.cache_llm_responses:
                content = self._cached_generation(
                    word,
                    tuple(eras),  # Convert to tuple for caching
                    num_examples
                )
            else:
                prompt = self._build_prompt(word, eras, num_examples)
                content = self._call_openrouter(prompt)
            
            # Parse response
            result = self._parse_response(content)
            
            # Validate we got data for all requested eras
            missing_eras = set(eras) - set(result.keys())
            if missing_eras:
                logger.warning(f"Missing data for eras: {missing_eras}")
            
            logger.info(
                f"Successfully generated {sum(len(v) for v in result.values())} "
                f"examples for '{word}'"
            )
            
            return result
        
        except (OpenRouterError, TimeoutError, ValueError) as e:
            logger.error(f"Failed to generate evolution for '{word}': {e}")
            raise


# Global service instance
etymology_service = EtymologyService()