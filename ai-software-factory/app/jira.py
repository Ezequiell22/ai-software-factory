import hashlib, io, json, mimetypes, httpx
from pathlib import Path
from pypdf import PdfReader
from docx import Document
from .settings import settings

def adf_text(value):
    if isinstance(value, str): return value
    if isinstance(value, list): return "\n".join(filter(None,(adf_text(x) for x in value)))
    if not isinstance(value, dict): return ""
    own=value.get("text","")
    children=adf_text(value.get("content",[]))
    if value.get("type") in {"paragraph","heading","listItem"} and children:
        children += "\n"
    return own + children

def adf_document(text):
    paragraphs=[]
    for line in text.splitlines():
        paragraphs.append({"type":"paragraph","content":[{"type":"text","text":line or " "}]})
    return {"type":"doc","version":1,"content":paragraphs or [{"type":"paragraph","content":[]}]}

class JiraClient:
    def __init__(self):
        self.base=settings.jira_base_url.rstrip("/"); self.auth=(settings.jira_email,settings.jira_api_token)
    @property
    def configured(self): return bool(self.base and settings.jira_email and settings.jira_api_token)
    def _request(self,method,path,**kwargs):
        if not self.configured: raise RuntimeError("Jira is not configured")
        with httpx.Client(base_url=self.base,auth=self.auth,timeout=30,follow_redirects=True) as c:
            r=c.request(method,path,**kwargs); r.raise_for_status()
            return r.json() if r.content else None
    def search_ideas(self):
        if not settings.jira_idea_jql: return []
        d=self._request("POST","/rest/api/3/search/jql",json={"jql":settings.jira_idea_jql,"maxResults":50,"fields":["summary","description","updated","status","issuetype","attachment"]})
        return d.get("issues",[])
    def add_comment(self,key,text):
        return self._request("POST",f"/rest/api/3/issue/{key}/comment",json={"body":adf_document(text)})
    def create_story(self,summary,description):
        data={"fields":{"project":{"key":settings.jira_project_key},"summary":summary,"description":adf_document(description),"issuetype":{"name":settings.jira_story_issue_type}}}
        return self._request("POST","/rest/api/3/issue",json=data)
    def create_ux_subtask(self,parent_key,summary,description):
        data={"fields":{"project":{"key":settings.jira_project_key},"parent":{"key":parent_key},"summary":summary,"description":adf_document(description),"issuetype":{"name":settings.jira_ux_issue_type}}}
        return self._request("POST","/rest/api/3/issue",json=data)
    def link_issues(self,source,destination,link_type=None):
        return self._request("POST","/rest/api/3/issueLink",json={"type":{"name":link_type or settings.jira_issue_link_type},"inwardIssue":{"key":source},"outwardIssue":{"key":destination}})
    def attach_file(self,issue_key,path):
        path=Path(path)
        if not path.exists(): raise FileNotFoundError(path)
        mime=mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        with path.open("rb") as f:
            return self._request("POST",f"/rest/api/3/issue/{issue_key}/attachments",headers={"X-Atlassian-Token":"no-check"},files={"file":(path.name,f,mime)})
    def attachment_text(self,attachment):
        size=int(attachment.get("size") or 0)
        if size and size > settings.max_attachment_mb*1024*1024:
            return "[ATTACHMENT_SKIPPED_TOO_LARGE]"
        url=attachment.get("content")
        if not url: return ""
        with httpx.Client(auth=self.auth,timeout=60,follow_redirects=True) as c:
            r=c.get(url); r.raise_for_status(); data=r.content
        mime=(attachment.get("mimeType") or "").lower()
        name=(attachment.get("filename") or "").lower()
        try:
            if mime.startswith("text/") or name.endswith((".md",".txt",".csv",".json",".log")):
                text=data.decode("utf-8",errors="replace")
            elif mime=="application/pdf" or name.endswith(".pdf"):
                reader=PdfReader(io.BytesIO(data)); text="\n".join((p.extract_text() or "") for p in reader.pages)
            elif name.endswith(".docx") or "wordprocessingml" in mime:
                doc=Document(io.BytesIO(data)); text="\n".join(p.text for p in doc.paragraphs)
            else:
                return "[ATTACHMENT_UNSUPPORTED_FOR_TEXT_EXTRACTION]"
            return text[:settings.max_attachment_chars]
        except Exception as exc:
            return f"[ATTACHMENT_EXTRACTION_FAILED: {type(exc).__name__}]"
    def source_context(self,issue):
        source=self.normalized_source(issue)
        enriched=[]
        for a in issue.get("fields",{}).get("attachment",[]):
            enriched.append({**{k:a.get(k) for k in ("id","filename","mimeType","size","content")},"text":self.attachment_text(a)})
        source["attachments"]=enriched
        return source
    @staticmethod
    def normalized_source(issue):
        f=issue.get("fields",{})
        return {"key":issue.get("key"),"summary":f.get("summary",""),"description":adf_text(f.get("description")).strip(),"updated":f.get("updated"),"attachments":[{"id":a.get("id"),"filename":a.get("filename"),"mimeType":a.get("mimeType"),"size":a.get("size"),"content":a.get("content")} for a in f.get("attachment",[])]}
    @staticmethod
    def revision(issue):
        source=JiraClient.normalized_source(issue)
        raw=json.dumps(source,sort_keys=True,default=str)
        return hashlib.sha256(raw.encode()).hexdigest()
