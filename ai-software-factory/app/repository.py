from sqlalchemy import text
from .db import SessionLocal
class WorkflowRepository:
    def create_or_get(self,trace_id,issue_key,revision):
        with SessionLocal.begin() as db:
            row=db.execute(text("""INSERT INTO workflows(trace_id,source_issue_key,source_revision) VALUES (:trace_id,:issue_key,:revision)
            ON CONFLICT (source_issue_key,source_revision) DO UPDATE SET updated_at=now()
            RETURNING id,trace_id,status"""),locals()).mappings().one()
            return dict(row)
    def record_execution(self,workflow_id,agent_id,status,input_summary="",output_summary="",error=None):
        with SessionLocal.begin() as db:
            db.execute(text("""INSERT INTO executions(workflow_id,agent_id,status,input_summary,output_summary,error,finished_at)
            VALUES (:workflow_id,:agent_id,:status,:input_summary,:output_summary,:error,
            CASE WHEN :status IN ('COMPLETED','FAILED') THEN now() ELSE NULL END)"""),locals())
    def update_status(self,workflow_id,status):
        with SessionLocal.begin() as db:
            db.execute(text("UPDATE workflows SET status=:status,updated_at=now() WHERE id=:workflow_id"),locals())
