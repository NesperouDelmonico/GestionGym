from datetime import datetime, timedelta

from domain.enums import SubscriptionStatus


class SubscriptionLifecycleService:
    @staticmethod
    def renew(subscription):
        subscription.start_date = datetime.now()
        subscription.end_date = (
            subscription.start_date +
            timedelta(days=subscription.membership_plan.duration_days)
        )
        subscription.status = SubscriptionStatus.ACTIVE

    @staticmethod
    def suspend(subscription):
        if subscription.status == SubscriptionStatus.EXPIRED:
            raise ValueError(
                "Cannot suspend an expired subscription"
            )

        subscription.status = SubscriptionStatus.SUSPENDED

    @staticmethod
    def expire_if_needed(subscription):
        if (
            datetime.now() > subscription.end_date and
            subscription.status != SubscriptionStatus.EXPIRED
        ):
            subscription.status = SubscriptionStatus.EXPIRED