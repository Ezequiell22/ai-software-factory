import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Header, HTTPException, Request
from apscheduler.schedulers.background import BackgroundScheduler
from .migrate import apply_migrations
from .schedule import inside_work_window
from .settings import settings
from .workflow import ProductWorkflow

workflow=ProductWorkflow(); scheduler=BackgroundScheduler(timezone=settings.app_timezone)

def reconcile():
    if not inside_work_window() or not workflow.jira.configured: return
    try:
        workflow.resume_waiting_human()
    except Exception:
        logging.exception("Failed resuming WAITING_HUMAN workflows")
    for issue in workflow.jira.search_ideas():
        try: workflow.process_issue(issue)
        except Exception: logging.exception("Failed processing Jira issue %s",issue.get("key"))

@asynccontextmanager
async def lifespan(app):
    apply_migrations()
    scheduler.add_job(reconcile,"interval",seconds=settings.reconciliation_seconds,id="jira-reconcile",replace_existing=True,max_instances=1)
    scheduler.start()
    try: yield
    finally: scheduler.shutdown(wait=False)

app=FastAPI(title="AI Product Factory",version="0.2.0",lifespan=lifespan)
@app.get("/health")
def health(): return {"status":"ok","work_window_open":inside_work_window(),"jira_configured":workflow.jira.configured}
@app.get("/agents")
def agents(): return [{"name":a.name,"description":a.description,"capabilities":a.capabilities} for a in workflow.registry._agents.values()]
@app.post("/jira/webhook")
async def jira_webhook(request:Request,x_webhook_secret:str|None=Header(default=None)):
    if settings.jira_webhook_secret and x_webhook_secret!=settings.jira_webhook_secret: raise HTTPException(status_code=401,detail="invalid webhook secret")
    payload=await request.json(); issue=payload.get("issue")
    if not issue: return {"accepted":False,"reason":"no issue"}
    if not inside_work_window(): return {"accepted":True,"queued":True,"reason":"outside work window"}
    workflow.resume_waiting_human()
    return {"accepted":True,"status":workflow.process_issue(issue)}
