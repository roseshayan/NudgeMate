from dataclasses import dataclass
from typing import Optional


@dataclass
class Task:
    id: Optional[int]
    user_id: int
    title: str
    remind_at: str  # ISO 8601 string
    status: str  # 'pending', 'completed', 'cancelled'
    category: str
    priority: str  # 'low', 'medium', 'high'
    nag_count: int
    last_nag_at: Optional[str]
    created_at: str
    completed_at: Optional[str] = None


@dataclass
class Note:
    id: Optional[int]
    user_id: int
    content: str
    tags: str
    created_at: str


@dataclass
class User:
    user_id: int
    first_name: str
    username: Optional[str]
    timezone: str
    daily_briefing_enabled: bool
    daily_briefing_time: str
    nag_interval_minutes: int
    max_nag_count: int
    created_at: str
