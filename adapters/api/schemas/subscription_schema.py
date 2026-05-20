from pydantic import BaseModel


class AssignMembershipRequest(BaseModel):
    client_id: str
    plan_id: str