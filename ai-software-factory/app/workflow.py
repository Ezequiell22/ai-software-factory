import uuid
from .agents import AgentRegistry
from .jira import JiraClient
from .repository import WorkflowRepository
from .schedule import inside_work_window
from .settings import settings
from .story_engine import StoryEngine
from .worklog import JiraWorklogService

KNOWLEDGE_AGENTS={"sap_b1","agrotis","accounting"}

class ProductWorkflow:
    def __init__(self):
        self.jira=JiraClient(); self.repo=WorkflowRepository(); self.registry=AgentRegistry(); self.registry.load()
        self.worklog=JiraWorklogService(self.jira); self.story_engine=StoryEngine(self.registry)

    def process_issue(self,issue):
        if not inside_work_window(): return "OUTSIDE_WORK_WINDOW"
        if not self.story_engine.llm.configured: return "LLM_NOT_CONFIGURED"
        key=issue["key"]; revision=self.jira.revision(issue); proposed=f"wf_{key}_{revision[:10]}_{uuid.uuid4().hex[:6]}"
        wf=self.repo.create_or_get(proposed,key,revision); trace=wf["trace_id"]
        if wf["status"] in {"PROCESSING","COMPLETED","WAITING_HUMAN"}: return wf["status"]
        self.repo.update_status(wf["id"],"PROCESSING")
        source=self.jira.normalized_source(issue)
        self.repo.record_execution(wf["id"],"intake","COMPLETED",key,"Started product refinement")
        self.worklog.activity(key,trace,"intake","Captured Jira input","Started product refinement.")

        try:
            result=self.story_engine.initial_draft(source)
            self.worklog.activity(key,trace,"po","Produced initial Story draft",f"{len(result.questions)} refinement question(s) found.")
            for cycle in range(1,settings.max_refinement_cycles+1):
                if self.story_engine.is_complete(result): break
                answers=[]
                blocking_external=False
                for q in result.questions:
                    qid=self.repo.add_question(wf["id"],key,"refinement",q.question,q.requested_agent,q.blocking)
                    self.worklog.activity(key,trace,"refinement",f"Question {qid}",f"{q.question} | routed_to={q.requested_agent or 'unspecified'}")
                    if q.requested_agent in KNOWLEDGE_AGENTS:
                        blocking_external = blocking_external or q.blocking
                        answers.append({"question":q.question,"agent":q.requested_agent,"answer":"KNOWLEDGE_UNAVAILABLE","evidence":[]})
                    elif q.requested_agent in self.registry._agents:
                        definition=self.registry._agents[q.requested_agent]
                        answer=self.story_engine.llm.run_json(definition.prompt+"\nReturn JSON only with keys answer, evidence, confidence.",str({"source":source,"story":result.story.model_dump(),"question":q.question}))
                        answers.append({"question":q.question,"agent":q.requested_agent,**answer})
                if blocking_external:
                    self.repo.update_status(wf["id"],"WAITING_HUMAN")
                    self.worklog.activity(key,trace,"orchestrator","Blocked unsafe inference","A blocking SAP/Agrotis/accounting question has no configured knowledge evidence. Human or knowledge-source input is required.")
                    return "WAITING_HUMAN"
                result=self.story_engine.refine(result,answers)
                self.worklog.activity(key,trace,"refinement",f"Completed refinement cycle {cycle}",f"Remaining questions: {len(result.questions)}")

            if not self.story_engine.is_complete(result):
                self.repo.update_status(wf["id"],"WAITING_HUMAN")
                self.worklog.activity(key,trace,"story_reviewer","Story quality gate failed","Maximum refinement cycles reached with unresolved gaps.")
                return "WAITING_HUMAN"

            story_text=self.story_engine.render_story(result.story)
            story=self.jira.create_story(result.story.title,story_text)
            story_key=story["key"]; self.repo.set_story(wf["id"],story_key)
            self.jira.link_issues(key,story_key)
            self.worklog.activity(key,trace,"orchestrator","Created refined Story",f"Generated {story_key} and linked it to {key}.")
            self.worklog.activity(story_key,trace,"story_reviewer","Story passed completeness gate","All required completeness flags are closed.")

            ux_description=f"Source Story: {story_key}\nWorkflow: {trace}\n\nCreate and attach exactly two prototype files: index.html and components.js. Any functional ambiguity must be routed back to the appropriate product/domain agent and propagated to the Story."
            ux=self.jira.create_ux_subtask(story_key,f"UX/UI prototype — {result.story.title}",ux_description)
            ux_key=ux["key"]; self.repo.set_ux(wf["id"],ux_key)
            self.worklog.activity(story_key,trace,"ux_ui","Created UX/UI subtask",ux_key)
            self.worklog.activity(ux_key,trace,"ux_ui","Received approved Story","Prototype generation is the next workflow stage.")
            self.repo.update_status(wf["id"],"UX_PENDING")
            return "UX_PENDING"
        except Exception as exc:
            self.repo.record_execution(wf["id"],"orchestrator","FAILED",key,error=str(exc))
            self.repo.update_status(wf["id"],"FAILED")
            try: self.worklog.activity(key,trace,"orchestrator","Workflow failed",str(exc))
            finally: raise
