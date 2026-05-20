from fastapi import APIRouter

router = APIRouter()

from application.use_cases.assign_membership import (
    AssignMembershipUseCase
)

from infrastructure.persistence.in_memory_membership_repository import (
    InMemoryMembershipRepository
)

repository = InMemoryMembershipRepository()

assign_use_case = AssignMembershipUseCase(
    repository
)

from adapters.api.schemas.subscription_schema import (
    AssignMembershipRequest
)

@router.post("/subscriptions")
def assign_membership(
    request: AssignMembershipRequest
):
    subscription = assign_use_case.execute(
        request.client_id,
        request.plan_id
    )

    return {
        "subscription_id": subscription.id,
        "status": subscription.status.value
    }