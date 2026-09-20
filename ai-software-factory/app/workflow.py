import uuid
from .agents import AgentRegistry
from .jira import JiraClient
from .repository import WorkflowRepository
from .schedule import inside_work_window
from .worklog import JiraWorklogService
class ProductWorkflow:
    def __init__(self):
        self.jira=JiraClient(); self.repo=WorkflowRepository(); self.registry=AgentRegistry(); self.registry.load(); self.worklog=JiraWorklogService(self.jira)
    def process_issue(self,issue):
        if not inside_work_window(): return "OUTSIDE_WORK_WINDOW"
        key=issue["key"]; revision=self.jira.revision(issue); proposed=f"wf_{key}_{revision[:10]}_{uuid.uuid4().hex[:6]}"
        wf=self.repo.create_or_get(proposed,key,revision); trace=wf["trace_id"]
        if wf["status"] in {"PROCESSING","COMPLETED","WAITING_HUMAN","WAITING_REFINEMENT_ENGINE"}: return wf["status"]
        self.repo.update_status(wf["id"],"PROCESSING")
        self.repo.record_execution(wf["id"],"intake","COMPLETED",key,"Issue accepted for refinement")
        self.worklog.activity(key,trace,"intake","Captured Jira input","Queued for structured refinement.")
        self.repo.update_status(wf["id"],"WAITING_REFINEMENT_ENGINE")
        self.worklog.activity(key,trace,"orchestrator","Validated runtime and persistence","Refinement engine is not wired yet; no story was fabricated.")
        return "WAITING_REFINEMENT_ENGINE"
