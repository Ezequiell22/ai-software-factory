from __future__ import annotations
import json
from pydantic import BaseModel, Field
from .agents import AgentRegistry
from .llm import LLMClient
from .models import Story

class UXQuestion(BaseModel):
    question: str
    requested_agent: str | None = None
    blocking: bool = True

class UXResult(BaseModel):
    questions: list[UXQuestion] = Field(default_factory=list)
    index_html: str
    components_js: str

class UXEngine:
    def __init__(self, registry: AgentRegistry):
        self.registry = registry
        self.llm = LLMClient()

    def generate(self, story: Story, answers: list[dict] | None = None) -> UXResult:
        definition = self.registry._agents["ux_ui"]
        contract = """
Return JSON only:
{
  "questions":[{"question":"...","requested_agent":"pm|po|pmo|sap_b1|agrotis|accounting|null","blocking":true}],
  "index_html":"...",
  "components_js":"..."
}
The final prototype contract is strict: exactly index.html and components.js. index.html must import ./components.js and must not depend on a build step.
Use semantic HTML, accessible labels, keyboard focus, responsive layout, clear loading/empty/error/success states when relevant, and an Apple-inspired visual system with restrained typography, rounded surfaces, neutral colors and generous spacing.
Do not invent business rules. If a functional ambiguity changes behavior, return it as a blocking question.
"""
        payload={"story":story.model_dump(),"resolved_questions":answers or []}
        data=self.llm.run_json(definition.prompt+"\n"+contract,json.dumps(payload,ensure_ascii=False))
        return UXResult.model_validate(data)
