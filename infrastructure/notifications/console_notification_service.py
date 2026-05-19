from application.ports.notification_service import (
    NotificationService
)


class ConsoleNotificationService(NotificationService):
    def notify(self, message: str):
        print(f"[NOTIFICATION]: {message}")