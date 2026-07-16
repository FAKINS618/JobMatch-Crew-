from pydantic import BaseModel, Field


class ResumeProject(BaseModel):
    name: str
    role: str = ""
    technologies: list[str] = Field(default_factory=list)
    description: str = ""
    achievements: list[str] = Field(default_factory=list)


class ResumeProfile(BaseModel):
    education: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    projects: list[ResumeProject] = Field(default_factory=list)
    internships: list[str] = Field(default_factory=list)
    awards: list[str] = Field(default_factory=list)
    target_roles: list[str] = Field(default_factory=list)
    available_from: str = ""
    parse_notes: list[str] = Field(default_factory=list)


class ResumeParseRequest(BaseModel):
    """调用简历解析接口时的原始输入。"""

    raw_text: str = Field(..., min_length=80, description="候选人简历文本")


class ResumeParseResponse(BaseModel):
    """模型解析并经过 Pydantic 校验后的简历档案。"""

    profile: ResumeProfile


class ResumeVersionCreate(BaseModel):
    resume_id: int | None = None
    version_name: str = Field(min_length=2, max_length=50)
    target_role: str = ""
    raw_text: str = Field(min_length=80)
    profile: ResumeProfile


class ResumeVersionResponse(BaseModel):
    id: int
    resume_id: int
    version_name: str
    target_role: str
    raw_text: str
    profile: ResumeProfile
    created_at: str | None = None
