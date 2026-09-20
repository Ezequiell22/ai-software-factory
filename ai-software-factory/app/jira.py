import hashlib, json, httpx
from .settings import settings
class JiraClient:
    def __init__(self):
        self.base=settings.jira_base_url.rstrip("/"); self.auth=(settings.jira_email,settings.jira_api_token)
    @property
    def configured(self): return bool(self.base and settings.jira_email and settings.jira_api_token)
    def _request(self,method,path,**kwargs):
        if not self.configured: raise RuntimeError("Jira is not configured")
        with httpx.Client(base_url=self.base,auth=self.auth,timeout=30) as c:
            r=c.request(method,path,**kwargs); r.raise_for_status()
            return r.json() if r.content else None
    def search_ideas(self):
        if not settings.jira_idea_jql: return []
        d=self._request("GET","/rest/api/3/search/jql",params={"jql":settings.jira_idea_jql,"maxResults":50,"fields":"summary,description,updated,status,issuetype"})
        return d.get("issues",[])
    def add_comment(self,key,text):
        body={"body":{"type":"doc","version":1,"content":[{"type":"paragraph","content":[{"type":"text","text":text}]}]}}
        return self._request("POST",f"/rest/api/3/issue/{key}/comment",json=body)
    def link_issues(self,source,destination,link_type="Relates"):
        return self._request("POST","/rest/api/3/issueLink",json={"type":{"name":link_type},"inwardIssue":{"key":source},"outwardIssue":{"key":destination}})
    @staticmethod
    def revision(issue):
        f=issue.get("fields",{})
        raw=json.dumps([issue.get("key"),f.get("updated"),f.get("summary"),f.get("description")],sort_keys=True,default=str)
        return hashlib.sha256(raw.encode()).hexdigest()
