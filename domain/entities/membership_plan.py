from uuid import uuid4


class MembershipPlan:
    def __init__(
        self,
        name: str,
        price: float,
        duration_days: int,
        benefits=None
    ):
        self.id = str(uuid4())
        self.name = name
        self.price = price
        self.duration_days = duration_days
        self.benefits = benefits or []