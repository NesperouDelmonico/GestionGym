from uuid import uuid4


class Client:
    def __init__(self, name: str, email: str):
        self.id = str(uuid4())
        self.name = name
        self.email = email

    def update_email(self, new_email: str):
        self.email = new_email