import json
import os
from typing import Any, Dict

from openai import OpenAI


class AIProvider:
    """Central OpenAI API adapter for AI App Builder."""

    def __init__(self) -> None:
        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not configured."
            )

        self.model = os.getenv(
            "OPENAI_MODEL",
            "gpt-5-mini"
        )

        self.client = OpenAI(
            api_key=api_key
        )

    def generate_json(
        self,
        system_prompt: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:

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

        try:
            return json.loads(text)

        except json.JSONDecodeError as exc:
            raise ValueError(
                "OpenAI returned invalid JSON."
            ) from exc
