import uuid
from .agents import AgentRegistry
from .artifacts import ArtifactManager
from .jira import JiraClient
from .models import RefinementResult, Story
from .repository import WorkflowRepository
from .schedule import inside_work_window
from .settings import settings
from .story_engine import StoryEngine
from .ux_engine import UXEngine, UXResult
from .worklog import JiraWorklogService

KNOWLEDGE_AGENTS={"sap_b1","agrotis","accounting"}

class ProductWorkflow:
    def __init__(self):
        self.jira=JiraClient(); self.repo=WorkflowRepository(); self.registry=AgentRegistry(); self.registry.load()
        self.worklog=JiraWorklogService(self.jira); self.story_engine=StoryEngine(self.registry)
        self.ux_engine=UXEngine(self.registry); self.artifacts=ArtifactManager()

    def _answer_question(self, source, story, q):
        if q.requested_agent in KNOWLEDGE_AGENTS or not q.requested_agent:
            return None
        if q.requested_agent in self.registry._agents:
            definition=self.registry._agents[q.requested_agent]
            answer=self.story_engine.llm.run_json(definition.prompt+"\nReturn JSON only with keys answer, evidence, confidence.",
                str({"source":source,"story":story.model_dump(),"question":q.question}))
            return {"question":q.question,"agent":q.requested_agent,**answer}
        return None

    def _wait_human(self,wf,issue_key,trace,agent,q,state):
        qid=self.repo.add_question(wf["id"],issue_key,agent,q.question,q.requested_agent,q.blocking)
        state.update({"waiting_issue_key":issue_key,"question_id":qid})
        self.repo.set_state(wf["id"],state); self.repo.update_status(wf["id"],"WAITING_HUMAN")
        self.worklog.ask_human(issue_key,trace,qid,agent,q.question)
        self.jira.transition_to(issue_key,settings.jira_human_status)
        return "WAITING_HUMAN"

    def _continue_story(self,wf,key,trace,source,result,cycle=0):
        for current_cycle in range(cycle+1,settings.max_refinement_cycles+1):
            if self.story_engine.is_complete(result):
                return self._create_story_and_ux(wf,key,trace,source,result)
            answers=[]
            for q in result.questions:
                answer=self._answer_question(source,result.story,q)
                if answer is None and q.blocking:
                    return self._wait_human(wf,key,trace,"refinement",q,{
                        "phase":"story_refinement","source":source,"result":result.model_dump(),"cycle":current_cycle-1
                    })
                if answer: answers.append(answer)
            if not answers and result.questions:
                q=result.questions[0]
                return self._wait_human(wf,key,trace,"refinement",q,{
                    "phase":"story_refinement","source":source,"result":result.model_dump(),"cycle":current_cycle-1
                })
            result=self.story_engine.refine(result,answers)
            self.worklog.activity(key,trace,"refinement",f"Completed refinement cycle {current_cycle}",f"Remaining questions: {len(result.questions)}")
        if self.story_engine.is_complete(result):
            return self._create_story_and_ux(wf,key,trace,source,result)
        self.repo.update_status(wf["id"],"WAITING_HUMAN")
        self.worklog.activity(key,trace,"story_reviewer","Story quality gate failed","Maximum refinement cycles reached with unresolved gaps.")
        return "WAITING_HUMAN"

    def _create_story_and_ux(self,wf,key,trace,source,result):
        story_text=self.story_engine.render_story(result.story)
        story=self.jira.create_story(result.story.title,story_text); story_key=story["key"]
        self.repo.set_story(wf["id"],story_key); self.jira.link_issues(key,story_key)
        self.jira.transition_to(story_key,settings.jira_story_status)
        self.worklog.activity(key,trace,"orchestrator","Created refined Story",f"Generated {story_key} and linked it to {key}.")
        self.worklog.activity(story_key,trace,"story_reviewer","Story passed completeness gate","All required completeness flags are closed.")

        ux_description=f"Source Story: {story_key}\nWorkflow: {trace}\n\nCreate and attach exactly two prototype files: index.html and components.js."
        ux=self.jira.create_ux_subtask(story_key,f"UX/UI prototype — {result.story.title}",ux_description); ux_key=ux["key"]
        self.repo.set_ux(wf["id"],ux_key); self.jira.transition_to(ux_key,settings.jira_ux_status)
        self.worklog.activity(story_key,trace,"ux_ui","Created UX/UI subtask",ux_key)
        return self._continue_ux(wf,key,trace,source,result.story,story_key,ux_key,None,[],0)

    def _continue_ux(self,wf,key,trace,source,story,story_key,ux_key,ux_result,ux_answers,cycle):
        if ux_result is None:
            ux_result=self.ux_engine.generate(story,ux_answers)
        for current_cycle in range(cycle+1,settings.max_refinement_cycles+1):
            if not ux_result.questions: break
            for q in ux_result.questions:
                answer=self._answer_question(source,story,q)
                if answer is None and q.blocking:
                    return self._wait_human(wf,ux_key,trace,"ux_ui",q,{
                        "phase":"ux_refinement","source":source,"story":story.model_dump(),"story_key":story_key,
                        "ux_key":ux_key,"ux_result":ux_result.model_dump(),"ux_answers":ux_answers,"cycle":current_cycle-1
                    })
                if answer: ux_answers.append(answer)
            ux_result=self.ux_engine.generate(story,ux_answers)
        if ux_result.questions:
            q=ux_result.questions[0]
            return self._wait_human(wf,ux_key,trace,"ux_ui",q,{
                "phase":"ux_refinement","source":source,"story":story.model_dump(),"story_key":story_key,
                "ux_key":ux_key,"ux_result":ux_result.model_dump(),"ux_answers":ux_answers,"cycle":settings.max_refinement_cycles
            })
        paths=self.artifacts.write_prototype(trace,ux_key,ux_result.index_html,ux_result.components_js)
        for path in paths:
            checksum=self.artifacts.checksum(path); self.repo.add_artifact(wf["id"],ux_key,"prototype",str(path),checksum); self.jira.attach_file(ux_key,path)
        self.worklog.activity(ux_key,trace,"ux_ui","Prototype completed","Attached index.html and components.js to this card.")
        self.jira.transition_to(ux_key,settings.jira_done_status); self.jira.transition_to(story_key,settings.jira_ready_status)
        self.worklog.activity(story_key,trace,"orchestrator","UX/UI completed",f"Prototype available in {ux_key}. Story moved to {settings.jira_ready_status}.")
        self.repo.set_state(wf["id"],{}); self.repo.update_status(wf["id"],"COMPLETED")
        return "COMPLETED"

    def process_issue(self,issue):
        if not inside_work_window(): return "OUTSIDE_WORK_WINDOW"
        if not self.story_engine.llm.configured: return "LLM_NOT_CONFIGURED"
        key=issue["key"]; revision=self.jira.revision(issue); proposed=f"wf_{key}_{revision[:10]}_{uuid.uuid4().hex[:6]}"
        wf=self.repo.create_or_get(proposed,key,revision); trace=wf["trace_id"]
        if wf["status"] in {"PROCESSING","COMPLETED","WAITING_HUMAN"}: return wf["status"]
        self.repo.update_status(wf["id"],"PROCESSING"); self.jira.transition_to(key,settings.jira_agent_status)
        source=self.jira.source_context(issue)
        self.repo.record_execution(wf["id"],"intake","COMPLETED",key,"Started product refinement")
        self.worklog.activity(key,trace,"intake","Captured Jira input",f"Started product refinement with {len(source.get('attachments',[]))} attachment(s).")
        try:
            result=self.story_engine.initial_draft(source)
            self.worklog.activity(key,trace,"po","Produced initial Story draft",f"{len(result.questions)} refinement question(s) found.")
            return self._continue_story(wf,key,trace,source,result,0)
        except Exception as exc:
            self.repo.record_execution(wf["id"],"orchestrator","FAILED",key,error=str(exc)); self.repo.update_status(wf["id"],"FAILED")
            try: self.worklog.activity(key,trace,"orchestrator","Workflow failed",str(exc))
            finally: raise

    def resume_waiting_human(self):
        results=[]
        if not inside_work_window(): return results
        for wf in self.repo.waiting_workflows():
            state=wf.get("state") or {}; issue_key=state.get("waiting_issue_key")
            if not issue_key: continue
            if self.jira.current_status(issue_key).casefold()!=settings.jira_agent_status.casefold():
                continue
            question=self.repo.get_open_question(wf["id"])
            if not question: continue
            comment=self.jira.latest_human_comment_after(issue_key,question["created_at"])
            if not comment: continue
            self.repo.resolve_question(question["id"],comment["body"],comment["id"])
            self.worklog.activity(issue_key,wf["trace_id"],"human","Resolved blocking question",comment["body"],[f"Jira comment {comment['id']}"])
            self.repo.update_status(wf["id"],"PROCESSING")
            answer={"question":question["question"],"agent":"human","answer":comment["body"],"evidence":[f"Jira comment {comment['id']}"],"confidence":1.0}
            phase=state.get("phase")
            if phase=="story_refinement":
                result=RefinementResult.model_validate(state["result"])
                result=self.story_engine.refine(result,[answer])
                results.append((wf["trace_id"],self._continue_story(wf,wf["source_issue_key"],wf["trace_id"],state["source"],result,state.get("cycle",0))))
            elif phase=="ux_refinement":
                story=Story.model_validate(state["story"]); ux_answers=list(state.get("ux_answers",[])); ux_answers.append(answer)
                self.jira.transition_to(state["ux_key"],settings.jira_ux_status)
                ux_result=self.ux_engine.generate(story,ux_answers)
                results.append((wf["trace_id"],self._continue_ux(wf,wf["source_issue_key"],wf["trace_id"],state["source"],story,state["story_key"],state["ux_key"],ux_result,ux_answers,state.get("cycle",0))))
        return results
