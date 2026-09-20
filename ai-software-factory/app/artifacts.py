from __future__ import annotations
import hashlib
from pathlib import Path

class ArtifactManager:
    def __init__(self, root: Path | str = "artifacts"):
        self.root = Path(root)

    def write_prototype(self, trace_id: str, ux_issue_key: str, html: str, components_js: str) -> list[Path]:
        folder = self.root / trace_id / ux_issue_key
        folder.mkdir(parents=True, exist_ok=True)
        html_path = folder / "index.html"
        js_path = folder / "components.js"
        html_path.write_text(html, encoding="utf-8")
        js_path.write_text(components_js, encoding="utf-8")
        return [html_path, js_path]

    @staticmethod
    def checksum(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()
