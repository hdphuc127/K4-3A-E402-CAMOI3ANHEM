from typing import Literal

from pydantic import BaseModel


class HealthStatus(BaseModel):
    service: str
    environment: str
    status: Literal["ok"]
