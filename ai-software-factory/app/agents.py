from dataclasses import dataclass
from pathlib import Path
import yaml
ROOT = Path(__file__).resolve().parent.parent
@dataclass(frozen=True)
class AgentDefinition:
    name: str
    description: str
    capabilities: tuple[str, ...]
    prompt: str
    can_delegate_to: tuple[str, ...]
class AgentRegistry:
    def __init__(self, directory=ROOT/"agents"):
        self.directory=directory; self._agents={}
    def load(self):
        agents={}
        for f in self.directory.glob("*/agent.yaml"):
            raw=yaml.safe_load(f.read_text()) or {}
            prompt=f.parent/raw.get("prompt_file","instructions.md")
            agents[raw["name"]]=AgentDefinition(raw["name"],raw.get("description",""),tuple(raw.get("capabilities",[])),prompt.read_text() if prompt.exists() else "",tuple(raw.get("can_delegate_to",[])))
        self._agents=agents
        return agents
