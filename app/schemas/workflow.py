"""求职闭环中的岗位、行动任务和仪表盘数据契约。"""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


JobTargetStatus = Literal[
    "saved",
    "applied",
    "written_test",
    "interview",
    "offer",
    "rejected",
    "withdrawn",
]
JobPriority = Literal["A", "B", "C"]
ActionItemStatus = Literal["todo", "in_progress", "completed", "cancelled"]
ActionPriority = Literal["high", "medium", "low"]
EvidenceType = Literal["link", "note", "resume_version"]


class JobTargetCreate(BaseModel):
    """从一份市场报告中的已验证岗位创建投递目标。"""

    report_id: int = Field(gt=0)
    url: str = Field(min_length=8, max_length=2048)
    priority: JobPriority
    note: str = Field(default="", max_length=2000)


class JobTargetUpdate(BaseModel):
    """用户可维护投递状态、备注和人工确认的截止日期。"""

    status: JobTargetStatus | None = None
    note: str | None = Field(default=None, max_length=2000)
    deadline_at: date | None = None


class JobTargetResponse(BaseModel):
    id: int
    report_id: int
    job_post_id: int
    resume_version_id: int | None = None
    title: str
    company: str = ""
    url: str
    priority: JobPriority
    match_score: int | None = None
    source_status: str
    status: JobTargetStatus
    note: str = ""
    deadline_at: date | None = None
    applied_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class ApplicationEventCreate(BaseModel):
    """补充记录投递过程中的不可变事件，不会改变岗位状态。"""

    event_type: str = Field(min_length=2, max_length=64)
    occurred_at: datetime | None = None
    note: str = Field(default="", max_length=2000)


class ApplicationEventResponse(BaseModel):
    id: int
    job_target_id: int
    event_type: str
    occurred_at: datetime
    note: str = ""


class ActionItemsFromReportRequest(BaseModel):
    """仅把报告中的技能缺口转为可执行任务。"""

    skills: list[str] = Field(default_factory=list, max_length=10)
    resume_version_id: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def normalize_skills(self):
        self.skills = list(dict.fromkeys(skill.strip() for skill in self.skills if skill.strip()))
        return self


class ActionItemUpdate(BaseModel):
    status: ActionItemStatus | None = None
    priority: ActionPriority | None = None
    due_date: date | None = None
    title: str | None = Field(default=None, min_length=2, max_length=200)


class ActionItemResponse(BaseModel):
    id: int
    report_id: int
    resume_version_id: int | None = None
    action_type: str
    skill: str = ""
    title: str
    priority: ActionPriority
    status: ActionItemStatus
    expected_output: str
    due_date: date | None = None
    evidence_count: int = 0
    created_at: datetime
    updated_at: datetime


class ActionEvidenceCreate(BaseModel):
    evidence_type: EvidenceType
    content: str = Field(default="", max_length=3000)
    url: str | None = Field(default=None, max_length=2048)
    resume_version_id: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def require_evidence_content(self):
        if self.evidence_type == "link" and not self.url:
            raise ValueError("链接类型证据必须提供 url")
        if self.evidence_type == "note" and not self.content.strip():
            raise ValueError("说明类型证据必须提供内容")
        if self.evidence_type == "resume_version" and self.resume_version_id is None:
            raise ValueError("简历版本证据必须提供 resume_version_id")
        return self


class ActionEvidenceResponse(BaseModel):
    id: int
    action_item_id: int
    evidence_type: EvidenceType
    content: str = ""
    url: str | None = None
    resume_version_id: int | None = None
    created_at: datetime


class DashboardSummary(BaseModel):
    saved_job_count: int = 0
    applied_job_count: int = 0
    interview_job_count: int = 0
    offer_job_count: int = 0
    todo_action_count: int = 0
    in_progress_action_count: int = 0
    completed_action_count: int = 0
    evidence_count: int = 0
