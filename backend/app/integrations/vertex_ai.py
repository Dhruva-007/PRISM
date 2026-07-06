"""
Vertex AI and Gemini 2.5 integration for PRISM.

This module provides a clean interface to Google's Vertex AI platform,
specifically for Gemini 2.5 Flash model interactions.

All AI reasoning in PRISM flows through this module:
- Situation analysis
- Root cause identification
- Intervention generation
- Scenario simulation

The client is initialized once and reused across requests.
"""

from functools import lru_cache

import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig

from app.config import get_settings
from app.utils.logging import get_logger

logger = get_logger(__name__)


def _initialize_vertex_ai() -> None:
    """
    Initialize the Vertex AI SDK with project and location.

    Must be called before any model instantiation.
    Safe to call multiple times — SDK handles idempotency.
    """
    settings = get_settings()
    vertexai.init(
        project=settings.google_cloud_project_id,
        location=settings.google_cloud_location,
    )
    logger.info(
        "Vertex AI initialized: project=%s location=%s",
        settings.google_cloud_project_id,
        settings.google_cloud_location,
    )


@lru_cache()
def get_gemini_model() -> GenerativeModel:
    """
    Return a cached Gemini generative model instance.

    Initializes Vertex AI on first call.
    The model is configured for structured JSON output suitable
    for PRISM's decision intelligence pipeline.

    Returns:
        A configured GenerativeModel instance.
    """
    _initialize_vertex_ai()
    settings = get_settings()

    model = GenerativeModel(
        model_name=settings.vertex_ai_model_id,
        system_instruction=(
            "You are PRISM, an expert Decision Intelligence System. "
            "You analyze community health and environmental data to identify "
            "patterns, root causes, and generate evidence-based intervention strategies. "
            "You always respond with valid, structured JSON as specified in each prompt. "
            "You are precise, evidence-based, and transparent about uncertainty."
        ),
    )

    logger.info("Gemini model initialized: %s", settings.vertex_ai_model_id)
    return model


def get_generation_config(
    temperature: float = 0.2,
    max_output_tokens: int = 16384,
    response_mime_type: str = "application/json",
) -> GenerationConfig:
    """
    Return a GenerationConfig for structured Gemini outputs.

    Args:
        temperature: Creativity level (0.0=deterministic, 1.0=creative).
                     Lower values for analysis (more deterministic),
                     slightly higher for intervention generation (more creative).
        max_output_tokens: Maximum tokens in the response.
        response_mime_type: MIME type for structured output.

    Returns:
        A configured GenerationConfig instance.
    """
    return GenerationConfig(
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        response_mime_type=response_mime_type,
    )