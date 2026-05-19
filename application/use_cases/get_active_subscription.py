from domain.enums import SubscriptionStatus


class GetActiveSubscriptionsUseCase:
    def __init__(self, repository):
        self.repository = repository

    def execute(self):
        subscriptions = self.repository.get_all_subscriptions()

        return [
            sub for sub in subscriptions
            if sub.status == SubscriptionStatus.ACTIVE
        ]