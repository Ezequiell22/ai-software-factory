from pydantic import BaseModel, Field

class Story(BaseModel):
    title: str
    context: str
    business_rules: list[str] = Field(default_factory=list)
    functionalities: list[str] = Field(default_factory=list)
    use_cases: list[str] = Field(default_factory=list)
    acceptance_criteria: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    decisions: list[str] = Field(default_factory=list)

class RefinementQuestion(BaseModel):
    question: str
    requested_agent: str | None = None
    blocking: bool = True

class RefinementResult(BaseModel):
    story: Story
    questions: list[RefinementQuestion] = Field(default_factory=list)
    completeness_flags: dict[str, bool] = Field(default_factory=dict)
