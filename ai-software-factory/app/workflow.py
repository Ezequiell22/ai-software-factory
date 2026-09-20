import uuid
from .agents import AgentRegistry
from .artifacts import ArtifactManager
from .jira import JiraClient
from .repository import WorkflowRepository
from .schedule import inside_work_window
from .settings import settings
from .story_engine import StoryEngine
from .ux_engine import UXEngine
from .worklog import JiraWorklogService

KNOWLEDGE_AGENTS={"sap_b1","agrotis","accounting"}

class ProductWorkflow:
    def __init__(self):
        self.jira=JiraClient(); self.repo=WorkflowRepository(); self.registry=AgentRegistry(); self.registry.load()
        self.worklog=JiraWorklogService(self.jira); self.story_engine=StoryEngine(self.registry)
        self.ux_engine=UXEngine(self.registry); self.artifacts=ArtifactManager()

    def _answer_question(self, source, story, q):
        if q.requested_agent in KNOWLEDGE_AGENTS:
            return {"question":q.question,"agent":q.requested_agent,"answer":"KNOWLEDGE_UNAVAILABLE","evidence":[]}
        if q.requested_agent in self.registry._agents:
            definition=self.registry._agents[q.requested_agent]
            answer=self.story_engine.llm.run_json(
                definition.prompt+"\nReturn JSON only with keys answer, evidence, confidence.",
                str({"source":source,"story":story.model_dump(),"question":q.question})
            )
            return {"question":q.question,"agent":q.requested_agent,**answer}
        return {"question":q.question,"agent":"unassigned","answer":"UNRESOLVED","evidence":[]}

    def process_issue(self,issue):
        if not inside_work_window(): return "OUTSIDE_WORK_WINDOW"
        if not self.story_engine.llm.configured: return "LLM_NOT_CONFIGURED"
        key=issue["key"]; revision=self.jira.revision(issue); proposed=f"wf_{key}_{revision[:10]}_{uuid.uuid4().hex[:6]}"
        wf=self.repo.create_or_get(proposed,key,revision); trace=wf["trace_id"]
        if wf["status"] in {"PROCESSING","COMPLETED","WAITING_HUMAN"}: return wf["status"]
        self.repo.update_status(wf["id"],"PROCESSING")
        source=self.jira.source_context(issue)
        self.repo.record_execution(wf["id"],"intake","COMPLETED",key,"Started product refinement")
        self.worklog.activity(key,trace,"intake","Captured Jira input",f"Started product refinement with {len(source.get('attachments',[]))} attachment(s).")

        try:
            result=self.story_engine.initial_draft(source)
            self.worklog.activity(key,trace,"po","Produced initial Story draft",f"{len(result.questions)} refinement question(s) found.")
            for cycle in range(1,settings.max_refinement_cycles+1):
                if self.story_engine.is_complete(result): break
                answers=[]; blocked=False
                for q in result.questions:
                    qid=self.repo.add_question(wf["id"],key,"refinement",q.question,q.requested_agent,q.blocking)
                    self.worklog.activity(key,trace,"refinement",f"Question {qid}",f"{q.question} | routed_to={q.requested_agent or 'unspecified'}")
                    answer=self._answer_question(source,result.story,q)
                    answers.append(answer)
                    if q.blocking and answer.get("answer") in {"KNOWLEDGE_UNAVAILABLE","UNRESOLVED"}: blocked=True
                if blocked:
                    self.repo.update_status(wf["id"],"WAITING_HUMAN")
                    self.worklog.activity(key,trace,"orchestrator","Blocked unsafe inference","A blocking question could not be answered with available evidence. Human or knowledge-source input is required.")
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
            self.worklog.activity(ux_key,trace,"ux_ui","Received approved Story","Starting prototype refinement.")

            ux_answers=[]
            ux_result=self.ux_engine.generate(result.story)
            for cycle in range(1,settings.max_refinement_cycles+1):
                if not ux_result.questions: break
                blocked=False
                for q in ux_result.questions:
                    qid=self.repo.add_question(wf["id"],ux_key,"ux_ui",q.question,q.requested_agent,q.blocking)
                    self.worklog.activity(ux_key,trace,"ux_ui",f"Question {qid}",f"{q.question} | routed_to={q.requested_agent or 'unspecified'}")
                    answer=self._answer_question(source,result.story,q)
                    ux_answers.append(answer)
                    if q.blocking and answer.get("answer") in {"KNOWLEDGE_UNAVAILABLE","UNRESOLVED"}: blocked=True
                if blocked:
                    self.repo.update_status(wf["id"],"WAITING_HUMAN")
                    self.worklog.activity(ux_key,trace,"ux_ui","Prototype blocked","A functional UX question lacks reliable evidence.")
                    return "WAITING_HUMAN"
                ux_result=self.ux_engine.generate(result.story,ux_answers)

            if ux_result.questions:
                self.repo.update_status(wf["id"],"WAITING_HUMAN")
                self.worklog.activity(ux_key,trace,"ux_ui","Prototype quality gate failed","UX questions remain after maximum refinement cycles.")
                return "WAITING_HUMAN"

            paths=self.artifacts.write_prototype(trace,ux_key,ux_result.index_html,ux_result.components_js)
            for path in paths:
                checksum=self.artifacts.checksum(path)
                self.repo.add_artifact(wf["id"],ux_key,"prototype",str(path),checksum)
                self.jira.attach_file(ux_key,path)
            self.worklog.activity(ux_key,trace,"ux_ui","Prototype completed","Attached index.html and components.js to this card.")
            self.worklog.activity(story_key,trace,"orchestrator","UX/UI completed",f"Prototype available in {ux_key}.")
            self.repo.update_status(wf["id"],"COMPLETED")
            return "COMPLETED"
        except Exception as exc:
            self.repo.record_execution(wf["id"],"orchestrator","FAILED",key,error=str(exc))
            self.repo.update_status(wf["id"],"FAILED")
            try: self.worklog.activity(key,trace,"orchestrator","Workflow failed",str(exc))
            finally: raise
