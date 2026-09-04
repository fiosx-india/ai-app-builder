"""
MarketVerse Lab
ai_provider.py

Purpose:
Central AI provider adapter.

This module handles communication
with the configured OpenAI model.
"""

import json
import os
from typing import Any, Dict

from openai import OpenAI


class AIProvider:
    """
    Central OpenAI API adapter for AI App Builder.

    This layer is responsible only for
    communication with the OpenAI API.
    """

    def __init__(self) -> None:

        api_key = os.getenv(
            "OPENAI_API_KEY"
        )

        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not configured."
            )

        self.model = os.getenv(
            "OPENAI_MODEL",
            "gpt-5-mini",
        )

        self.client = OpenAI(
            api_key=api_key
        )

    def generate_json(
        self,
        system_prompt: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:

        if not system_prompt.strip():
            raise ValueError(
                "System prompt cannot be empty."
            )

        response = self.client.responses.create(
            model=self.model,
            input=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        payload,
                        ensure_ascii=False,
                    ),
                },
            ],
        )

        text = response.output_text.strip()

        if not text:
            raise ValueError(
                "OpenAI returned an empty response."
            )

        try:
            result = json.loads(text)

        except json.JSONDecodeError as exc:
            raise ValueError(
                "OpenAI returned invalid JSON."
            ) from exc

        if not isinstance(result, dict):
            raise ValueError(
                "OpenAI response must be a JSON object."
            )

        return result
