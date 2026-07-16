from dataclasses import dataclass


class PlanEnum:
    free = "free"
    paid = "paid"


@dataclass
class User:
    id: str
    clerk_id: str
    plan: str = "free"

    @property
    def is_paid(self) -> bool:
        return self.plan == "paid"

    @property
    def email(self) -> str:
        return f"{self.clerk_id[:64]}@users.clerk.placeholder"
