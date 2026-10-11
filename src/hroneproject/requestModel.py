from pydantic import BaseModel, Field
from typing import Literal
from datetime import datetime
class AttendanceRequest(BaseModel):
    employee_id: str = Field(
        min_length=1,
        description="Unique employee ID"
    )

class AttendanceCorrectionRequest(BaseModel):
    field: Literal["punch_in", "punch_out"]
    new_timestamp: datetime
    reason: str = Field(min_length=3, max_length=500)
    corrected_by: str = Field(min_length=1, max_length=100)