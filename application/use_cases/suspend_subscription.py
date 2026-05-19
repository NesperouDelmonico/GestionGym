from domain.services.subscription_lifecycle import (
    SubscriptionLifecycleService
)


class SuspendSubscriptionUseCase:
    def __init__(self, repository):
        self.repository = repository

    def execute(self, subscription_id):
        subscription = self.repository.get_subscription(
            subscription_id
        )

        SubscriptionLifecycleService.suspend(subscription)

        self.repository.save_subscription(subscription)

        return subscription