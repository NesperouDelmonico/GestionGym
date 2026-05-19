from domain.entities.membership_subscription import (
    MembershipSubscription
)


class AssignMembershipUseCase:
    def __init__(self, repository):
        self.repository = repository

    def execute(self, client_id, plan_id):
        client = self.repository.get_client(client_id)
        plan = self.repository.get_plan(plan_id)

        subscription = MembershipSubscription(client, plan)

        self.repository.save_subscription(subscription)

        return subscription