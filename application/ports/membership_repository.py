from abc import ABC, abstractmethod


class MembershipRepository(ABC):

    @abstractmethod
    def save_client(self, client):
        pass

    @abstractmethod
    def save_plan(self, plan):
        pass

    @abstractmethod
    def save_subscription(self, subscription):
        pass

    @abstractmethod
    def get_client(self, client_id):
        pass

    @abstractmethod
    def get_plan(self, plan_id):
        pass

    @abstractmethod
    def get_subscription(self, subscription_id):
        pass

    @abstractmethod
    def get_all_subscriptions(self):
        pass