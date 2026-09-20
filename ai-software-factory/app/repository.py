from sqlalchemy import text
from .db import SessionLocal
class WorkflowRepository:
    def create_or_get(self,trace_id,issue_key,revision):
        with SessionLocal.begin() as db:
            row=db.execute(text("""INSERT INTO workflows(trace_id,source_issue_key,source_revision) VALUES (:trace_id,:issue_key,:revision)
            ON CONFLICT (source_issue_key,source_revision) WHERE source_revision IS NOT NULL
            DO UPDATE SET updated_at=now()
            RETURNING id,trace_id,status,story_issue_key,ux_issue_key"""),locals()).mappings().one()
            return dict(row)
    def record_execution(self,workflow_id,agent_id,status,input_summary="",output_summary="",error=None):
        with SessionLocal.begin() as db:
            db.execute(text("""INSERT INTO executions(workflow_id,agent_id,status,input_summary,output_summary,error,finished_at)
            VALUES (:workflow_id,:agent_id,:status,:input_summary,:output_summary,:error,
            CASE WHEN :status IN ('COMPLETED','FAILED') THEN now() ELSE NULL END)"""),locals())
    def add_question(self,workflow_id,issue_key,asked_by,question,requested_agent=None,blocking=True):
        with SessionLocal.begin() as db:
            return str(db.execute(text("""INSERT INTO questions(workflow_id,issue_key,asked_by,requested_agent,question,blocking)
            VALUES (:workflow_id,:issue_key,:asked_by,:requested_agent,:question,:blocking) RETURNING id"""),locals()).scalar_one())
    def add_artifact(self,workflow_id,issue_key,kind,path,checksum):
        with SessionLocal.begin() as db:
            db.execute(text("""INSERT INTO artifacts(workflow_id,issue_key,kind,path,checksum)
            VALUES (:workflow_id,:issue_key,:kind,:path,:checksum)"""),locals())
    def update_status(self,workflow_id,status):
        with SessionLocal.begin() as db:
            db.execute(text("UPDATE workflows SET status=:status,updated_at=now() WHERE id=:workflow_id"),locals())
    def set_story(self,workflow_id,story_key):
        with SessionLocal.begin() as db:
            db.execute(text("UPDATE workflows SET story_issue_key=:story_key,updated_at=now() WHERE id=:workflow_id"),locals())
    def set_ux(self,workflow_id,ux_key):
        with SessionLocal.begin() as db:
            db.execute(text("UPDATE workflows SET ux_issue_key=:ux_key,updated_at=now() WHERE id=:workflow_id"),locals())
