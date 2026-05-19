"""
main.py – Punto de Entrada / Bootstrap
SoC: solo configura e inicializa el sistema. No contiene lógica de negocio.
Crea la infraestructura (bus, observadores, servicio) y carga datos de demo.
"""

from datetime import date, timedelta

from domain import Client, PlanType
from events import EventBus, AlertObserver, LoyaltyPointsObserver, AuditObserver
from factories import MembershipFactory, LoyaltyDecorator, GuestPassDecorator
from services import MembershipService


def build_service() -> tuple[MembershipService, AuditObserver, AlertObserver]:
    """Configura bus de eventos, observadores y servicio."""
    bus   = EventBus()
    alert = AlertObserver()
    audit = AuditObserver()
    bus.subscribe(alert)
    bus.subscribe(LoyaltyPointsObserver())
    bus.subscribe(audit)
    return MembershipService(bus), audit, alert


def load_demo_data(service: MembershipService) -> dict:
    """
    Carga datos de demostración.
    Retorna referencias para que la UI pueda operar sobre ellos.
    """
    # Planes
    plans = {
        "monthly":   service.register_plan(
            MembershipFactory.create(PlanType.MONTHLY,   "Plan Mensual",      120_000)),
        "quarterly": service.register_plan(
            MembershipFactory.create(PlanType.QUARTERLY, "Plan Trimestral",   320_000)),
        "annual":    service.register_plan(
            MembershipFactory.create(PlanType.ANNUAL,    "Plan Anual",        990_000)),
        "premium":   service.register_plan(
            MembershipFactory.create(PlanType.PREMIUM,   "Plan Premium",    1_500_000)),
    }

    # Decorator de ejemplo
    loyal_plan = LoyaltyDecorator(plans["annual"], loyalty_years=2)
    loyal_plan = GuestPassDecorator(loyal_plan, passes=3)

    # Clientes
    clients = {
        "c1": service.register_client(Client("1001", "Ana Torres",  "310-111", "ana@mail.com")),
        "c2": service.register_client(Client("1002", "Luis Gómez",  "310-222", "luis@mail.com")),
        "c3": service.register_client(Client("1003", "María Pérez", "310-333", "maria@mail.com")),
    }

    # Suscripciones
    sub1 = service.assign_membership(clients["c1"], plans["annual"])
    sub2 = service.assign_membership(clients["c2"], plans["monthly"])
    sub3 = service.assign_membership(clients["c3"], plans["premium"])

    # Suspender a María
    service.suspend_subscription(
        sub3.id,
        reason="Viaje al exterior",
        start=date.today(),
        end=date.today() + timedelta(days=30),
    )

    return {"plans": plans, "clients": clients,
            "subs": {"sub1": sub1, "sub2": sub2, "sub3": sub3},
            "loyal_plan": loyal_plan}


if __name__ == "__main__":
    service, audit, alert = build_service()
    data = load_demo_data(service)

    # Estadísticas rápidas
    stats = service.get_statistics()
    print("=== ESTADÍSTICAS ===")
    for estado, cantidad in stats.items():
        print(f"  {estado:<15} {'█' * cantidad} ({cantidad})")

    # Suscripciones activas
    print("\n=== ACTIVAS ===")
    for s in service.list_active_subscriptions():
        print(f"  {s}")

    # Log de auditoría
    print("\n=== AUDITORÍA ===")
    for entry in audit.get_log():
        print(f"  {entry}")
