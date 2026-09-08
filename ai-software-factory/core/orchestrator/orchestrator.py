"""Minimal orchestration contract for the AI Software Factory V2."""

class Orchestrator:
    def run(self, task):
        """Execute a task through discovery, planning, implementation and validation.

        Real implementation should persist state and invoke adapters/agents.
        """
        raise NotImplementedError
