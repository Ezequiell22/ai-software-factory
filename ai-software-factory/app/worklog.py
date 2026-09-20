class JiraWorklogService:
    def __init__(self,jira): self.jira=jira
    def activity(self,issue_key,trace_id,agent,action,result,evidence=None):
        sources="\n".join(f"- {x}" for x in (evidence or [])) or "- none"
        self.jira.add_comment(issue_key,f"AI Agent Activity\nWorkflow: {trace_id}\nAgent: {agent}\nAction: {action}\nResult: {result}\nEvidence:\n{sources}")
    def ask_human(self,issue_key,trace_id,question_id,agent,question):
        self.jira.add_comment(issue_key,
            f"[AI QUESTION {question_id}]\n"
            f"Workflow: {trace_id}\n"
            f"Requested by: {agent}\n\n"
            f"{question}\n\n"
            f"Para continuar: responda esta pergunta em um novo comentário e mova este card para a raia/status de agentes."
        )
