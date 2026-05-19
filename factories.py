"""
factories.py – Capa de Creación y Decoración
Principio aplicado: OCP (Open/Closed Principle)
  MembershipFactory y los decoradores permiten extender comportamiento
  sin modificar las clases de dominio existentes.
"""

from __future__ import annotations
from typing import Dict, List
from domain import (
    MembershipPlan, MonthlyPlan, QuarterlyPlan, AnnualPlan, PremiumPlan,
    Benefit, PlanType
)


# ── Factory Method ─────────────────────────────────────────────

class MembershipFactory:
    """
    OCP: centraliza la creación de planes.
    DRY: la inicialización de beneficios ocurre en un solo lugar.
    Nuevos planes se registran con register_plan() sin tocar el código existente.
    """

    _registry: Dict[PlanType, type] = {
        PlanType.MONTHLY:   MonthlyPlan,
        PlanType.QUARTERLY: QuarterlyPlan,
        PlanType.ANNUAL:    AnnualPlan,
        PlanType.PREMIUM:   PremiumPlan,
    }

    @classmethod
    def create(cls, plan_type: PlanType, name: str, price: float) -> MembershipPlan:
        plan_class = cls._registry.get(plan_type)
        if not plan_class:
            raise ValueError(f"Tipo de plan desconocido: {plan_type}")
        plan = plan_class(name, price, plan_type)
        plan.benefits = plan.get_base_benefits()
        return plan

    @classmethod
    def register_plan(cls, plan_type: PlanType, plan_class: type) -> None:
        """Extensión sin modificación (OCP)."""
        cls._registry[plan_type] = plan_class


# ── Decorator Base ─────────────────────────────────────────────

class MembershipDecorator(MembershipPlan):
    """
    Decorator base – envuelve un plan existente transparentemente.
    OCP: extiende comportamiento sin modificar MembershipPlan.
    """

    def __init__(self, wrapped: MembershipPlan):
        self._wrapped = wrapped

    @property
    def id(self):        return self._wrapped.id
    @property
    def name(self):      return self._wrapped.name
    @property
    def price(self):     return self._wrapped.price
    @property
    def plan_type(self): return self._wrapped.plan_type
    @property
    def active(self):    return self._wrapped.active
    @property
    def benefits(self):  return self._wrapped.benefits

    def duration_days(self)            -> int:          return self._wrapped.duration_days()
    def get_base_benefits(self)        -> List[Benefit]: return self._wrapped.get_base_benefits()
    def __str__(self):                                  return str(self._wrapped)


# ── Decoradores Concretos ──────────────────────────────────────

class LoyaltyDecorator(MembershipDecorator):
    """RF11 – Descuento y beneficios extra por años de fidelidad."""

    def __init__(self, wrapped: MembershipPlan, loyalty_years: int):
        super().__init__(wrapped)
        self.loyalty_years = loyalty_years

    @property
    def price(self) -> float:
        discount = min(self.loyalty_years * 0.05, 0.20)
        return round(self._wrapped.price * (1 - discount), 2)

    def get_base_benefits(self) -> List[Benefit]:
        pct = min(self.loyalty_years * 5, 20)
        return self._wrapped.get_base_benefits() + [
            Benefit("Descuento fidelidad",
                    f"{pct}% por {self.loyalty_years} año(s) de continuidad")
        ]

    def __str__(self):
        return f"{self._wrapped} ★ Fidelidad ({self.loyalty_years} año(s))"


class GuestPassDecorator(MembershipDecorator):
    """RF07 – Pases de invitado adicionales al plan base."""

    def __init__(self, wrapped: MembershipPlan, passes: int = 2):
        super().__init__(wrapped)
        self.passes = passes

    def get_base_benefits(self) -> List[Benefit]:
        return self._wrapped.get_base_benefits() + [
            Benefit("Pases de invitado", f"{self.passes} pases por mes incluidos")
        ]
