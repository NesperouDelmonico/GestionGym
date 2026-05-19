"""
domain.py – Capa de Dominio
Principio aplicado: SoC (Separation of Concerns)
  Solo contiene enums, value objects y entidades puras de negocio.
  No conoce infraestructura, servicios ni UI.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum
from typing import List, Optional
import uuid


# ── Value Objects ──────────────────────────────────────────────

class MembershipStatus(Enum):
    ACTIVE    = "Activa"
    EXPIRING  = "Por vencer"
    EXPIRED   = "Vencida"
    SUSPENDED = "Suspendida"
    CANCELLED = "Cancelada"


class PlanType(Enum):
    MONTHLY   = ("Mensual",    30)
    QUARTERLY = ("Trimestral", 90)
    ANNUAL    = ("Anual",     365)
    PREMIUM   = ("Premium",   365)

    def __init__(self, label: str, days: int):
        self.label = label
        self.days  = days


@dataclass(frozen=True)
class Benefit:
    """Value Object inmutable – DRY: reutilizado por todos los planes."""
    name: str
    description: str


# ── Entidades de Dominio ───────────────────────────────────────

@dataclass
class Client:
    """Entidad Cliente – SRP: solo datos y representación del cliente."""
    document:       str
    name:           str
    phone:          str
    email:          str
    loyalty_points: int = 0

    def __str__(self):
        return f"{self.name} (Doc: {self.document}) – Puntos: {self.loyalty_points}"


@dataclass
class SuspensionRecord:
    """Value Object – registro de una suspensión."""
    reason:     str
    start_date: date
    end_date:   date


# ── Planes de Membresía (Factory Method) ──────────────────────

class MembershipPlan(ABC):
    """Producto abstracto del Factory Method – SRP: representa un plan."""

    def __init__(self, name: str, price: float, plan_type: PlanType):
        self.id        = str(uuid.uuid4())[:8]
        self.name      = name
        self.price     = price
        self.plan_type = plan_type
        self.active    = True
        self.benefits: List[Benefit] = []

    @abstractmethod
    def get_base_benefits(self) -> List[Benefit]: ...

    def duration_days(self) -> int:
        return self.plan_type.days

    def __str__(self):
        return f"[{self.plan_type.label}] {self.name} – ${self.price:,.0f}"


class MonthlyPlan(MembershipPlan):
    def get_base_benefits(self) -> List[Benefit]:
        return [
            Benefit("Acceso sala de pesas", "Lunes a viernes 6am–10pm"),
            Benefit("Vestuarios",           "Uso ilimitado"),
        ]


class QuarterlyPlan(MembershipPlan):
    def get_base_benefits(self) -> List[Benefit]:
        return [
            *MonthlyPlan("", 0, PlanType.QUARTERLY).get_base_benefits(),
            Benefit("Descuento tienda", "10% en productos del gimnasio"),
        ]


class AnnualPlan(MembershipPlan):
    def get_base_benefits(self) -> List[Benefit]:
        return [
            *QuarterlyPlan("", 0, PlanType.ANNUAL).get_base_benefits(),
            Benefit("Clases grupales",  "Acceso ilimitado a todas las clases"),
            Benefit("Evaluación física", "2 evaluaciones al año incluidas"),
        ]


class PremiumPlan(MembershipPlan):
    def get_base_benefits(self) -> List[Benefit]:
        return [
            *AnnualPlan("", 0, PlanType.PREMIUM).get_base_benefits(),
            Benefit("Entrenador personal", "4 sesiones mensuales incluidas"),
            Benefit("Zona VIP",            "Acceso a sauna y jacuzzi"),
        ]


# ── Suscripción ────────────────────────────────────────────────

class MembershipSubscription:
    """
    Ciclo de vida de una membresía asignada a un cliente.
    SRP: solo gestiona el ciclo de vida de UNA suscripción.
    No conoce observadores ni servicios externos.
    """

    def __init__(self, client: Client, plan: MembershipPlan, start_date: date):
        self.id           = str(uuid.uuid4())[:8]
        self.client       = client
        self.plan         = plan
        self.start_date   = start_date
        self.end_date     = start_date + timedelta(days=plan.duration_days())
        self.status       = MembershipStatus.ACTIVE
        self.suspensions: List[SuspensionRecord] = []
        self.renewals:    int = 0

    def refresh_status(self) -> MembershipStatus:
        """DRY: lógica de cálculo de estado centralizada aquí."""
        if self.status in (MembershipStatus.SUSPENDED, MembershipStatus.CANCELLED):
            return self.status
        days_left = (self.end_date - date.today()).days
        if days_left < 0:
            self.status = MembershipStatus.EXPIRED
        elif days_left <= 7:
            self.status = MembershipStatus.EXPIRING
        else:
            self.status = MembershipStatus.ACTIVE
        return self.status

    def days_remaining(self) -> int:
        return max((self.end_date - date.today()).days, 0)

    def __str__(self):
        return (f"Suscripción #{self.id} | {self.plan.name} | "
                f"{self.start_date} → {self.end_date} | {self.status.value}")
