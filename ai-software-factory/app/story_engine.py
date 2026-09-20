from __future__ import annotations
import json
from .agents import AgentRegistry
from .llm import LLMClient
from .models import RefinementResult, Story

REQUIRED_FLAGS = {
    "actor_defined",
    "permissions_defined",
    "happy_path_defined",
    "error_paths_defined",
    "business_rules_closed",
    "dependencies_known",
    "integrations_known",
    "fiscal_questions_closed",
    "sap_questions_closed",
    "agrotis_questions_closed",
    "ux_impact_defined",
}

def _story_contract() -> str:
    return """Return JSON with this exact top-level shape:
{
  "story": {
    "title": "...",
    "context": "...",
    "business_rules": [],
    "functionalities": [],
    "use_cases": [],
    "acceptance_criteria": [],
    "dependencies": [],
    "constraints": [],
    "assumptions": [],
    "decisions": []
  },
  "questions": [
    {"question":"...", "requested_agent":"pm|po|pmo|ux_ui|sap_b1|agrotis|accounting|null", "blocking":true}
  ],
  "completeness_flags": {
    "actor_defined": false,
    "permissions_defined": false,
    "happy_path_defined": false,
    "error_paths_defined": false,
    "business_rules_closed": false,
    "dependencies_known": false,
    "integrations_known": false,
    "fiscal_questions_closed": false,
    "sap_questions_closed": false,
    "agrotis_questions_closed": false,
    "ux_impact_defined": false
  }
}"""

class StoryEngine:
    def __init__(self, registry: AgentRegistry):
        self.registry = registry
        self.llm = LLMClient()

    def _run(self, agent: str, payload: dict) -> dict:
        definition = self.registry._agents[agent]
        return self.llm.run_json(definition.prompt + "\n" + _story_contract(), json.dumps(payload, ensure_ascii=False))

    def initial_draft(self, source: dict) -> RefinementResult:
        intake = self._run("intake", {"source": source, "task": "Normalize this source without inventing facts."})
        pm = self._run("pm", {"source": source, "intake": intake, "task": "Define product intent and preserve uncertainties."})
        po = self._run("po", {"source": source, "intake": intake, "pm": pm, "task": "Produce the first complete functional Story draft."})
        return RefinementResult.model_validate(po)

    def refine(self, current: RefinementResult, specialist_answers: list[dict]) -> RefinementResult:
        data = self._run("refinement", {
            "current": current.model_dump(),
            "specialist_answers": specialist_answers,
            "task": "Challenge the story. Close only gaps supported by the provided evidence/answers."
        })
        return RefinementResult.model_validate(data)

    @staticmethod
    def is_complete(result: RefinementResult) -> bool:
        return not result.questions and all(result.completeness_flags.get(flag, False) for flag in REQUIRED_FLAGS)

    @staticmethod
    def render_story(story: Story) -> str:
        def section(title, items):
            values = items or ["Nenhum identificado."]
            return f"## {title}\n" + "\n".join(f"- {x}" for x in values)
        return "\n\n".join([
            f"# {story.title}",
            f"## Contexto / Objetivo\n{story.context}",
            section("Regras de negócio", story.business_rules),
            section("Funcionalidades", story.functionalities),
            section("Casos de uso", story.use_cases),
            section("Critérios de aceite", story.acceptance_criteria),
            section("Dependências", story.dependencies),
            section("Restrições", story.constraints),
            section("Premissas", story.assumptions),
            section("Decisões", story.decisions),
        ])
