class JiraWorklogService:
    def __init__(self,jira): self.jira=jira
    def activity(self,issue_key,trace_id,agent,action,result,evidence=None):
        sources="\n".join(f"- {x}" for x in (evidence or [])) or "- none"
        self.jira.add_comment(issue_key,f"AI Agent Activity\nWorkflow: {trace_id}\nAgent: {agent}\nAction: {action}\nResult: {result}\nEvidence:\n{sources}")
