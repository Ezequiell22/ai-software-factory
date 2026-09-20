from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "postgresql+psycopg://ai_factory:ai_factory@db:5432/ai_factory"
    app_timezone: str = "America/Sao_Paulo"
    work_start_hour: int = 7
    work_end_hour: int = 19
    reconciliation_seconds: int = 60
    max_refinement_cycles: int = 3
    jira_base_url: str = ""
    jira_email: str = ""
    jira_api_token: str = ""
    jira_project_key: str = ""
    jira_idea_jql: str = ""
    jira_story_issue_type: str = "Story"
    jira_ux_issue_type: str = "Sub-task"
    jira_issue_link_type: str = "Relates"
    jira_webhook_secret: str = ""
    openai_api_key: str = ""
    openai_model: str = "gpt-5.6"
settings = Settings()
