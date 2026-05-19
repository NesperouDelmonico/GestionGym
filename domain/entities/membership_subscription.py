from uuid import uuid4
from datetime import datetime, timedelta

from domain.enums import SubscriptionStatus


class MembershipSubscription:
    def __init__(self, client, membership_plan):
        self.id = str(uuid4())
        self.client = client
        self.membership_plan = membership_plan
        self.start_date = datetime.now()
        self.end_date = self.start_date + timedelta(
            days=membership_plan.duration_days
        )
        self.status = SubscriptionStatus.ACTIVE

    def suspend(self):
        if self.status == SubscriptionStatus.EXPIRED:
            raise ValueError("Cannot suspend expired subscription")

        self.status = SubscriptionStatus.SUSPENDED

    def renew(self):
        self.start_date = datetime.now()
        self.end_date = self.start_date + timedelta(
            days=self.membership_plan.duration_days
        )
        self.status = SubscriptionStatus.ACTIVE

    def expire(self):
        self.status = SubscriptionStatus.EXPIRED