"""
events.py – Capa de Eventos (Observer Pattern)
Principio aplicado: SoC (Separation of Concerns)
  Los observadores viven aquí, completamente desacoplados del dominio.
  La suscripción y publicación de eventos no contamina la lógica de negocio.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from domain import Client, MembershipSubscription


# ── Eventos ────────────────────────────────────────────────────

class MembershipEvent(Enum):
    ASSIGNED  = "membresía_asignada"
    RENEWED   = "membresía_renovada"
    SUSPENDED = "membresía_suspendida"
    CANCELLED = "membresía_cancelada"
    EXPIRED   = "membresía_vencida"


@dataclass
class EventPayload:
    event:        MembershipEvent
    client:       "Client"
    subscription: "MembershipSubscription"
    extra:        dict = field(default_factory=dict)


# ── Interfaz Observer ──────────────────────────────────────────

class MembershipObserver(ABC):
    """SRP: cada observer tiene una única razón para cambiar."""

    @abstractmethod
    def update(self, payload: EventPayload) -> None: ...


# ── Observadores Concretos ─────────────────────────────────────

class AuditObserver(MembershipObserver):
    """RNF06 – Auditoría y trazabilidad."""

    def __init__(self):
        self.log: List[str] = []

    def update(self, payload: EventPayload) -> None:
        entry = (
            f"[{date.today()}] EVENTO={payload.event.value} "
            f"CLIENTE={payload.client.document} "
            f"PLAN={payload.subscription.plan.name} "
            f"EXTRA={payload.extra}"
        )
        self.log.append(entry)

    def get_log(self) -> List[str]:
        return list(self.log)


class LoyaltyPointsObserver(MembershipObserver):
    """RF07 – Puntos acumulados por fidelidad."""

    POINTS_MAP = {
        MembershipEvent.ASSIGNED: 50,
        MembershipEvent.RENEWED:  100,
    }

    def update(self, payload: EventPayload) -> None:
        points = self.POINTS_MAP.get(payload.event, 0)
        if points:
            payload.client.loyalty_points += points


class AlertObserver(MembershipObserver):
    """RNF01 – Notificaciones al cliente."""

    def __init__(self):
        self.messages: List[str] = []

    def update(self, payload: EventPayload) -> None:
        templates = {
            MembershipEvent.ASSIGNED:  f"Bienvenido/a {payload.client.name}! Tu membresía está activa.",
            MembershipEvent.RENEWED:   f"Membresía renovada hasta {payload.subscription.end_date}.",
            MembershipEvent.SUSPENDED: f"Membresía suspendida: {payload.extra.get('reason', '')}",
            MembershipEvent.CANCELLED: f"Membresía cancelada para {payload.client.name}.",
            MembershipEvent.EXPIRED:   f"La membresía de {payload.client.name} ha vencido.",
        }
        msg = templates.get(payload.event, "Evento sin mensaje")
        self.messages.append(msg)


# ── Bus de Eventos ─────────────────────────────────────────────

class EventBus:
    """
    Bus central de eventos – SoC: desacopla publicadores de suscriptores.
    OCP: se añaden nuevos observers sin modificar esta clase.
    """

    def __init__(self):
        self._observers: List[MembershipObserver] = []

    def subscribe(self, observer: MembershipObserver) -> None:
        self._observers.append(observer)

    def publish(self, payload: EventPayload) -> None:
        for obs in self._observers:
            obs.update(payload)
