# models.py
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class Certificate(BaseModel):
    certificate_id: str
    issued_at: datetime
    valid_until: datetime
    subject_type: str  # "firmware", "drone", "operator"
    subject_id: str
    security_goals: List[str]   # цели безопасности
    digital_signature: str      # подпись регулятора

    def is_valid(self) -> bool:
        return datetime.utcnow() < self.valid_until