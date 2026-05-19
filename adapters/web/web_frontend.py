"""
web_frontend.py – Interfaz web ligera para gestionar el gimnasio.
Utiliza Flask para exponer el servicio en una UI basada en navegador.
"""

from __future__ import annotations
from datetime import date, timedelta
from flask import Flask, redirect, render_template, request, url_for, flash

from main import build_service, load_demo_data
from domain import Client

app = Flask(__name__)
app.secret_key = "dev-secret-key"

service, audit, alert = build_service()
load_demo_data(service)


def _selected_subscription(sub_id: str):
    return service._subscriptions.get(sub_id)


def _selected_plan(plan_id: str):
    return service._plans.get(plan_id)


def _selected_client(document: str):
    return service._clients.get(document)


@app.route("/")
def index():
    stats = service.get_statistics()
    clients = list(service._clients.values())
    plans = list(service.list_plans(only_active=False))
    subscriptions = service.list_all_subscriptions()
    return render_template(
        "index.html",
        stats=stats,
        clients=clients,
        plans=plans,
        subscriptions=subscriptions,
        audit_log=audit.get_log(),
        alerts=alert.messages,
    )


@app.route("/assign", methods=["POST"])
def assign():
    document = request.form.get("client_document")
    plan_id = request.form.get("plan_id")
    client = _selected_client(document or "")
    plan = _selected_plan(plan_id or "")
    if not client or not plan:
        flash("Cliente o plan no válido.", "error")
        return redirect(url_for("index"))
    service.assign_membership(client, plan, start_date=date.today())
    flash("Membresía asignada correctamente.", "success")
    return redirect(url_for("index"))


@app.route("/renew", methods=["POST"])
def renew():
    sub_id = request.form.get("sub_id")
    if not sub_id:
        flash("Seleccione una suscripción para renovar.", "error")
        return redirect(url_for("index"))
    try:
        service.renew_subscription(sub_id)
        flash("Suscripción renovada.", "success")
    except Exception as exc:
        flash(str(exc), "error")
    return redirect(url_for("index"))


@app.route("/suspend", methods=["POST"])
def suspend():
    sub_id = request.form.get("sub_id")
    reason = request.form.get("reason", "")
    days_str = request.form.get("days", "0")
    if not sub_id or not reason.strip() or not days_str.isdigit():
        flash("Datos de suspensión incompletos.", "error")
        return redirect(url_for("index"))
    days = int(days_str)
    try:
        start = date.today()
        end = start + timedelta(days=days)
        service.suspend_subscription(sub_id, reason.strip(), start, end)
        flash("Suscripción suspendida.", "success")
    except Exception as exc:
        flash(str(exc), "error")
    return redirect(url_for("index"))


@app.route("/cancel", methods=["POST"])
def cancel():
    sub_id = request.form.get("sub_id")
    if not sub_id:
        flash("Seleccione una suscripción para cancelar.", "error")
        return redirect(url_for("index"))
    try:
        service.cancel_subscription(sub_id)
        flash("Suscripción cancelada.", "success")
    except Exception as exc:
        flash(str(exc), "error")
    return redirect(url_for("index"))


@app.route("/deactivate-plan", methods=["POST"])
def deactivate_plan():
    plan_id = request.form.get("plan_id")
    if not plan_id:
        flash("Seleccione un plan para desactivar.", "error")
        return redirect(url_for("index"))
    service.deactivate_plan(plan_id)
    flash("Plan desactivado.", "success")
    return redirect(url_for("index"))


@app.route("/add-client", methods=["POST"])
def add_client():
    document = request.form.get("document", "").strip()
    name = request.form.get("name", "").strip()
    phone = request.form.get("phone", "").strip()
    email = request.form.get("email", "").strip()
    if not document or not name or not phone or not email:
        flash("Todos los campos de cliente son obligatorios.", "error")
        return redirect(url_for("index"))
    if service.find_client(document):
        flash("Ya existe un cliente con ese documento.", "error")
        return redirect(url_for("index"))
    client = Client(document, name, phone, email)
    service.register_client(client)
    flash("Cliente registrado correctamente.", "success")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True, port=5000)
