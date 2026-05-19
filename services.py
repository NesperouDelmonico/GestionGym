"""
services.py – Capa de Servicios
Principio aplicado: SRP (Single Responsibility Principle)
  MembershipService solo orquesta operaciones; no contiene lógica de dominio.
  SubscriptionLifecycle gestiona exclusivamente el ciclo de vida de suscripciones
  y delega al EventBus, manteniendo el dominio desacoplado de los eventos.
"""

from __future__ import annotations
from datetime import date, timedelta
from typing import Dict, List, Optional

from domain import (
    Client, MembershipPlan, MembershipSubscription,
    MembershipStatus, SuspensionRecord
)
from events import EventBus, EventPayload, MembershipEvent


# ── Gestor de ciclo de vida de suscripciones ───────────────────

class SubscriptionLifecycle:
    """
    SRP: única responsabilidad – gestionar transiciones de estado de
    una suscripción y publicar los eventos correspondientes.
    Separa la lógica de ciclo de vida del servicio de coordinación.
    """

    def __init__(self, bus: EventBus):
        self._bus = bus

    def renew(self, sub: MembershipSubscription,
              new_plan: Optional[MembershipPlan] = None) -> date:
        if sub.status == MembershipStatus.CANCELLED:
            raise ValueError("No se puede renovar una membresía cancelada.")
        if new_plan:
            sub.plan = new_plan
        sub.end_date = (
            max(sub.end_date, date.today()) + timedelta(days=sub.plan.duration_days())
        )
        sub.status   = MembershipStatus.ACTIVE
        sub.renewals += 1
        self._bus.publish(EventPayload(
            MembershipEvent.RENEWED, sub.client, sub,
            {"renewals": sub.renewals}
        ))
        return sub.end_date

    def suspend(self, sub: MembershipSubscription,
                reason: str, start: date, end: date) -> None:
        if sub.status == MembershipStatus.CANCELLED:
            raise ValueError("No se puede suspender una membresía cancelada.")
        sub.suspensions.append(SuspensionRecord(reason, start, end))
        sub.status = MembershipStatus.SUSPENDED
        self._bus.publish(EventPayload(
            MembershipEvent.SUSPENDED, sub.client, sub,
            {"reason": reason, "until": str(end)}
        ))

    def cancel(self, sub: MembershipSubscription) -> None:
        sub.status = MembershipStatus.CANCELLED
        self._bus.publish(EventPayload(MembershipEvent.CANCELLED, sub.client, sub))

    def refresh(self, sub: MembershipSubscription) -> MembershipStatus:
        """
        DRY: delegado a la entidad; aquí solo publicamos el evento si expira.
        """
        prev = sub.status
        new  = sub.refresh_status()
        if prev != MembershipStatus.EXPIRED and new == MembershipStatus.EXPIRED:
            self._bus.publish(EventPayload(MembershipEvent.EXPIRED, sub.client, sub))
        return new


# ── Servicio Principal ─────────────────────────────────────────

class MembershipService:
    """
    SRP: orquesta operaciones de alto nivel sobre planes, clientes y suscripciones.
    No contiene lógica de dominio ni de ciclo de vida de suscripciones.
    """

    def __init__(self, event_bus: EventBus):
        self._bus            = event_bus
        self._lifecycle      = SubscriptionLifecycle(event_bus)
        self._plans:         Dict[str, MembershipPlan]         = {}
        self._clients:       Dict[str, Client]                 = {}
        self._subscriptions: Dict[str, MembershipSubscription] = {}

    # ── Planes ─────────────────────────────────────────────────

    def register_plan(self, plan: MembershipPlan) -> MembershipPlan:
        self._plans[plan.id] = plan
        return plan

    def list_plans(self, only_active: bool = True) -> List[MembershipPlan]:
        return [p for p in self._plans.values() if not only_active or p.active]

    def deactivate_plan(self, plan_id: str) -> None:
        plan = self._plans.get(plan_id)
        if plan:
            plan.active = False

    # ── Clientes ───────────────────────────────────────────────

    def register_client(self, client: Client) -> Client:
        self._clients[client.document] = client
        return client

    def find_client(self, document: str) -> Optional[Client]:
        return self._clients.get(document)

    # ── Suscripciones ──────────────────────────────────────────

    def assign_membership(self, client: Client, plan: MembershipPlan,
                          start_date: Optional[date] = None) -> MembershipSubscription:
        """RF08 – Asignar membresía a cliente."""
        sub = MembershipSubscription(client, plan, start_date or date.today())
        self._subscriptions[sub.id] = sub
        self._bus.publish(EventPayload(MembershipEvent.ASSIGNED, client, sub))
        return sub

    def renew_subscription(self, sub_id: str,
                           new_plan: Optional[MembershipPlan] = None) -> date:
        sub = self._subscriptions[sub_id]
        return self._lifecycle.renew(sub, new_plan)

    def suspend_subscription(self, sub_id: str,
                             reason: str, start: date, end: date) -> None:
        self._lifecycle.suspend(self._subscriptions[sub_id], reason, start, end)

    def cancel_subscription(self, sub_id: str) -> None:
        self._lifecycle.cancel(self._subscriptions[sub_id])

    def get_client_subscription(self, document: str) -> Optional[MembershipSubscription]:
        """RF07 – Suscripción activa de un cliente."""
        for sub in self._subscriptions.values():
            if sub.client.document == document and sub.status not in (
                    MembershipStatus.CANCELLED, MembershipStatus.EXPIRED):
                self._lifecycle.refresh(sub)
                return sub
        return None

    def list_active_subscriptions(self) -> List[MembershipSubscription]:
        result = []
        for sub in self._subscriptions.values():
            self._lifecycle.refresh(sub)
            if sub.status == MembershipStatus.ACTIVE:
                result.append(sub)
        return result

    def get_statistics(self) -> Dict[str, int]:
        stats: Dict[str, int] = {s.value: 0 for s in MembershipStatus}
        for sub in self._subscriptions.values():
            self._lifecycle.refresh(sub)
            stats[sub.status.value] += 1
        return stats

    def get_client_history(self, document: str) -> List[MembershipSubscription]:
        return [s for s in self._subscriptions.values()
                if s.client.document == document]

    def list_all_subscriptions(self) -> List[MembershipSubscription]:
        for sub in self._subscriptions.values():
            self._lifecycle.refresh(sub)
        return list(self._subscriptions.values())
