import json
from openai import OpenAI
from .settings import settings

class LLMClient:
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

    @property
    def configured(self):
        return self.client is not None

    def run_json(self, instructions: str, input_text: str) -> dict:
        if not self.client:
            raise RuntimeError("LLM is not configured")
        response = self.client.responses.create(
            model=settings.openai_model,
            instructions=instructions + "\nReturn valid JSON only. Do not include markdown fences.",
            input=input_text,
        )
        raw = response.output_text.strip()
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Model returned invalid JSON: {raw[:500]}") from exc
