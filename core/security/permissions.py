from enum import StrEnum

from pydantic import BaseModel


class RiskLevel(StrEnum):
    SAFE = "safe"
    CONFIRM = "confirm"
    CRITICAL = "critical"


class StructuredIntent(BaseModel):
    action: str
    target: str
    risk: RiskLevel


class PermissionGuard:
    def validate(self, intent: StructuredIntent) -> bool:
        return intent.risk == RiskLevel.SAFE
