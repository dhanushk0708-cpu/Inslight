import json
import httpx
from typing import Optional, List
from app.core.config import settings
from app.core.logging import logger

FALLBACK_MODELS: List[str] = [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "qwen/qwen3.8-27b",
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
]


class AIService:
    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        self.url = settings.GROQ_URL
        self.model = settings.GROQ_MODEL or "openai/gpt-oss-120b"

    async def chat(self, system: str, user: str, temp: float = 0.1, max_tokens: int = 4096) -> str:
        """Call Groq Cloud LLM asynchronously with automatic model fallback."""
        if not self.api_key:
            raise Exception("GROQ_API_KEY is not configured in backend environment.")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Build candidate list starting with configured model
        models_to_try = [self.model] + [m for m in FALLBACK_MODELS if m != self.model]

        last_error = None
        async with httpx.AsyncClient(timeout=35.0) as client:
            for model_candidate in models_to_try:
                payload = {
                    "model": model_candidate,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user}
                    ],
                    "temperature": temp,
                    "max_tokens": max_tokens
                }

                try:
                    response = await client.post(self.url, headers=headers, json=payload)
                    if response.status_code == 200:
                        data = response.json()
                        # If a fallback succeeded, remember the working model
                        if model_candidate != self.model:
                            logger.info(f"Switched active LLM model from '{self.model}' to '{model_candidate}'.")
                            self.model = model_candidate
                        return data["choices"][0]["message"]["content"].strip()

                    error_body = response.text
                    # Check if error is related to model availability (404 model_not_found or 400 decommissioned)
                    if response.status_code in (400, 404) and any(
                        err_key in error_body.lower() for err_key in ["model", "decommissioned", "not found", "access"]
                    ):
                        logger.warning(
                            f"Model '{model_candidate}' unavailable ({response.status_code}): {error_body[:150]}. Trying next candidate..."
                        )
                        last_error = f"Model {model_candidate} error ({response.status_code}): {error_body[:200]}"
                        continue
                    else:
                        logger.error(f"Groq API Error {response.status_code}: {error_body[:300]}")
                        raise Exception(f"AI Service error ({response.status_code}): {error_body[:200]}")

                except httpx.RequestError as e:
                    logger.error(f"HTTP request error for model {model_candidate}: {e}")
                    last_error = str(e)
                    continue

        raise Exception(f"All LLM candidate models failed. Last error: {last_error}")

    async def generate_text(self, prompt: str, system: str = "You are INSLIGHT AI Business Intelligence Assistant.") -> str:
        """Convenience method for text generation."""
        return await self.chat(system=system, user=prompt)


ai_service = AIService()
