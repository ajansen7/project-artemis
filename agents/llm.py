"""
Gemini LLM helper — centralized interface for Gemini API calls.

Provides both structured (JSON) and free-text generation via
Google's Generative AI SDK. Tracks token usage for cost control.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import google.generativeai as genai
import structlog

from agents.config import settings

logger = structlog.get_logger()

# Configure the SDK once at import time
genai.configure(api_key=settings.google_api_key)

# ─── Model instances ────────────────────────────────────────────

_model: genai.GenerativeModel | None = None

PROMPTS_DIR = Path(__file__).parent / "prompts"


def get_model(model_name: str = "gemini-2.5-flash") -> genai.GenerativeModel:
    """Get or create a Gemini GenerativeModel instance."""
    global _model
    if _model is None:
        _model = genai.GenerativeModel(model_name)
    return _model


def load_system_prompt(agent_name: str) -> str:
    """Load a system prompt from the prompts/ directory."""
    prompt_file = PROMPTS_DIR / f"{agent_name}.md"
    if prompt_file.exists():
        return prompt_file.read_text(encoding="utf-8")
    logger.warning("llm.prompt_not_found", agent=agent_name)
    return ""


async def generate_text(
    prompt: str,
    system_prompt: str | None = None,
    model_name: str = "gemini-2.5-flash",
) -> str:
    """Generate free-text completion from Gemini.

    Args:
        prompt: The user prompt / main instruction.
        system_prompt: Optional system instruction.
        model_name: Gemini model to use.

    Returns:
        The generated text response.
    """
    model = genai.GenerativeModel(
        model_name,
        system_instruction=system_prompt,
    )

    response = await model.generate_content_async(prompt)

    # Log token usage
    if hasattr(response, "usage_metadata") and response.usage_metadata:
        logger.info(
            "llm.usage",
            prompt_tokens=response.usage_metadata.prompt_token_count,
            completion_tokens=response.usage_metadata.candidates_token_count,
            total_tokens=response.usage_metadata.total_token_count,
        )

    return response.text


async def generate_json(
    prompt: str,
    system_prompt: str | None = None,
    model_name: str = "gemini-2.5-flash",
) -> dict[str, Any]:
    """Generate a JSON response from Gemini.

    Instructs the model to respond in JSON and parses the result.
    Falls back to extracting JSON from code fences if direct parsing fails.

    Args:
        prompt: The user prompt with JSON output instructions.
        system_prompt: Optional system instruction.
        model_name: Gemini model to use.

    Returns:
        Parsed JSON as a dict.
    """
    # Append JSON instruction to the system prompt
    json_system = (system_prompt or "") + (
        "\n\nIMPORTANT: You MUST respond with valid JSON only. "
        "Do not include any text outside of the JSON object. "
        "Do not wrap in markdown code fences."
    )

    model = genai.GenerativeModel(
        model_name,
        system_instruction=json_system,
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
        ),
    )

    response = await model.generate_content_async(prompt)

    # Log token usage
    if hasattr(response, "usage_metadata") and response.usage_metadata:
        logger.info(
            "llm.usage",
            prompt_tokens=response.usage_metadata.prompt_token_count,
            completion_tokens=response.usage_metadata.candidates_token_count,
            total_tokens=response.usage_metadata.total_token_count,
        )

    raw = response.text.strip()

    # Try direct JSON parse
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Try extracting from code fences
    if "```json" in raw:
        json_str = raw.split("```json")[1].split("```")[0].strip()
        return json.loads(json_str)
    if "```" in raw:
        json_str = raw.split("```")[1].split("```")[0].strip()
        return json.loads(json_str)

    # Last resort — find first { and last }
    start = raw.find("{")
    end = raw.rfind("}") + 1
    if start >= 0 and end > start:
        return json.loads(raw[start:end])

    raise ValueError(f"Failed to parse JSON from Gemini response: {raw[:200]}...")
