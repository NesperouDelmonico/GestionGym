"""
frontend.py – Interfaz gráfica de usuario para gestionar el gimnasio.
Utiliza PyQt5 para mostrar planes, clientes, suscripciones y registros de evento.
"""

from __future__ import annotations
from datetime import date, timedelta
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication, QComboBox, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QMainWindow, QMessageBox, QPushButton, QPlainTextEdit,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, QInputDialog
)

from domain import Client, MembershipStatus
from events import AlertObserver, AuditObserver
from main import build_service, load_demo_data


class GymFrontend(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestión Gym - Frontend")
        self.service, self.audit, self.alert = build_service()
        self.data = load_demo_data(self.service)

        self._build_ui()
        self.refresh_all()

    def _build_ui(self):
        central = QWidget()
        main_layout = QVBoxLayout()

        main_layout.addLayout(self._build_stats_panel())
        main_layout.addLayout(self._build_action_panel())
        main_layout.addWidget(self._build_logs_panel())

        central.setLayout(main_layout)
        self.setCentralWidget(central)
        self.resize(1100, 700)

    def _build_stats_panel(self):
        layout = QHBoxLayout()
        self.stat_labels = {}
        for status in MembershipStatus:
            label = QLabel(f"{status.value}: 0")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("font-weight: bold; margin: 0 10px;")
            self.stat_labels[status] = label
            layout.addWidget(label)
        layout.addStretch()
        refresh_button = QPushButton("Actualizar")
        refresh_button.clicked.connect(self.refresh_all)
        layout.addWidget(refresh_button)
        return layout

    def _build_action_panel(self):
        layout = QHBoxLayout()
        layout.addLayout(self._build_subscriptions_panel(), 3)
        layout.addLayout(self._build_clients_plans_panel(), 2)
        return layout

    def _build_subscriptions_panel(self):
        box = QVBoxLayout()
        self.subs_table = QTableWidget(0, 7)
        self.subs_table.setHorizontalHeaderLabels([
            "ID", "Cliente", "Plan", "Estado", "Inicio", "Fin", "Renovaciones"
        ])
        self.subs_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.subs_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.subs_table.cellClicked.connect(self._on_subscription_selected)
        box.addWidget(QLabel("Suscripciones"))
        box.addWidget(self.subs_table)

        buttons = QHBoxLayout()
        renew_btn = QPushButton("Renovar")
        renew_btn.clicked.connect(self._renew_subscription)
        suspend_btn = QPushButton("Suspender")
        suspend_btn.clicked.connect(self._suspend_subscription)
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self._cancel_subscription)
        buttons.addWidget(renew_btn)
        buttons.addWidget(suspend_btn)
        buttons.addWidget(cancel_btn)
        box.addLayout(buttons)
        return box

    def _build_clients_plans_panel(self):
        layout = QVBoxLayout()
        layout.addWidget(self._build_clients_group())
        layout.addWidget(self._build_plans_group())
        layout.addWidget(self._build_assignment_group())
        return layout

    def _build_clients_group(self):
        group = QGroupBox("Clientes")
        vbox = QVBoxLayout()
        self.clients_table = QTableWidget(0, 5)
        self.clients_table.setHorizontalHeaderLabels([
            "Documento", "Nombre", "Teléfono", "Email", "Puntos"
        ])
        self.clients_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.clients_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        vbox.addWidget(self.clients_table)

        btn = QPushButton("Nuevo cliente")
        btn.clicked.connect(self._add_client)
        vbox.addWidget(btn)

        group.setLayout(vbox)
        return group

    def _build_plans_group(self):
        group = QGroupBox("Planes")
        vbox = QVBoxLayout()
        self.plans_table = QTableWidget(0, 5)
        self.plans_table.setHorizontalHeaderLabels([
            "ID", "Nombre", "Tipo", "Precio", "Activo"
        ])
        self.plans_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.plans_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        vbox.addWidget(self.plans_table)

        btn = QPushButton("Desactivar plan seleccionado")
        btn.clicked.connect(self._deactivate_plan)
        vbox.addWidget(btn)

        group.setLayout(vbox)
        return group

    def _build_assignment_group(self):
        group = QGroupBox("Asignar membresía")
        vbox = QVBoxLayout()

        self.client_combo = QComboBox()
        self.plan_combo = QComboBox()
        assign_btn = QPushButton("Asignar membresía")
        assign_btn.clicked.connect(self._assign_membership)

        vbox.addWidget(QLabel("Cliente"))
        vbox.addWidget(self.client_combo)
        vbox.addWidget(QLabel("Plan"))
        vbox.addWidget(self.plan_combo)
        vbox.addWidget(assign_btn)
        group.setLayout(vbox)
        return group

    def _build_logs_panel(self):
        container = QWidget()
        box = QVBoxLayout()
        box.addWidget(QLabel("Registro de auditoría y alertas"))
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        box.addWidget(self.log_view)
        container.setLayout(box)
        return container

    def refresh_all(self):
        self._refresh_stats()
        self._refresh_clients()
        self._refresh_plans()
        self._refresh_subscriptions()
        self._refresh_assignment_options()
        self._refresh_logs()

    def _refresh_stats(self):
        stats = self.service.get_statistics()
        for status, label in self.stat_labels.items():
            label.setText(f"{status.value}: {stats.get(status.value, 0)}")

    def _refresh_clients(self):
        clients = list(self.service._clients.values())
        self.clients_table.setRowCount(len(clients))
        for row, client in enumerate(clients):
            self.clients_table.setItem(row, 0, QTableWidgetItem(client.document))
            self.clients_table.setItem(row, 1, QTableWidgetItem(client.name))
            self.clients_table.setItem(row, 2, QTableWidgetItem(client.phone))
            self.clients_table.setItem(row, 3, QTableWidgetItem(client.email))
            self.clients_table.setItem(row, 4, QTableWidgetItem(str(client.loyalty_points)))
        self.clients_table.resizeColumnsToContents()

    def _refresh_plans(self):
        plans = self.service.list_plans(only_active=False)
        self.plans_table.setRowCount(len(plans))
        for row, plan in enumerate(plans):
            self.plans_table.setItem(row, 0, QTableWidgetItem(plan.id))
            self.plans_table.setItem(row, 1, QTableWidgetItem(plan.name))
            self.plans_table.setItem(row, 2, QTableWidgetItem(plan.plan_type.label))
            self.plans_table.setItem(row, 3, QTableWidgetItem(f"${plan.price:,.0f}"))
            self.plans_table.setItem(row, 4, QTableWidgetItem("Sí" if plan.active else "No"))
        self.plans_table.resizeColumnsToContents()

    def _refresh_subscriptions(self):
        subscriptions = self.service.list_all_subscriptions()
        self.subs_table.setRowCount(len(subscriptions))
        for row, sub in enumerate(subscriptions):
            self.subs_table.setItem(row, 0, QTableWidgetItem(sub.id))
            self.subs_table.setItem(row, 1, QTableWidgetItem(sub.client.name))
            self.subs_table.setItem(row, 2, QTableWidgetItem(sub.plan.name))
            self.subs_table.setItem(row, 3, QTableWidgetItem(sub.status.value))
            self.subs_table.setItem(row, 4, QTableWidgetItem(str(sub.start_date)))
            self.subs_table.setItem(row, 5, QTableWidgetItem(str(sub.end_date)))
            self.subs_table.setItem(row, 6, QTableWidgetItem(str(sub.renewals)))
        self.subs_table.resizeColumnsToContents()

    def _refresh_assignment_options(self):
        self.client_combo.clear()
        self.plan_combo.clear()
        for client in self.service._clients.values():
            self.client_combo.addItem(f"{client.name} ({client.document})", client.document)
        for plan in self.service.list_plans(only_active=True):
            self.plan_combo.addItem(f"{plan.name} - {plan.plan_type.label}", plan.id)

    def _refresh_logs(self):
        lines = [f"AUDIT: {entry}" for entry in self.audit.get_log()]
        lines += [f"ALERTA: {msg}" for msg in self.alert.messages]
        self.log_view.setPlainText("\n".join(lines))

    def _selected_subscription_id(self) -> str | None:
        selected = self.subs_table.selectedItems()
        if not selected:
            return None
        return selected[0].text()

    def _selected_plan_id(self) -> str | None:
        selected = self.plans_table.selectedItems()
        if not selected:
            return None
        return selected[0].text()

    def _selected_client_document(self) -> str | None:
        selected = self.clients_table.selectedItems()
        if not selected:
            return None
        return selected[0].text()

    def _on_subscription_selected(self):
        pass

    def _show_error(self, message: str):
        QMessageBox.critical(self, "Error", message)

    def _show_info(self, message: str):
        QMessageBox.information(self, "Información", message)

    def _assign_membership(self):
        client_data = self.client_combo.currentData()
        plan_id = self.plan_combo.currentData()
        if not client_data or not plan_id:
            self._show_error("Seleccione un cliente y un plan.")
            return

        client = self.service.find_client(client_data)
        plan = self.service._plans.get(plan_id)
        if not client or not plan:
            self._show_error("Cliente o plan no válido.")
            return

        self.service.assign_membership(client, plan, start_date=date.today())
        self._show_info("Membresía asignada correctamente.")
        self.refresh_all()

    def _renew_subscription(self):
        sub_id = self._selected_subscription_id()
        if not sub_id:
            self._show_error("Seleccione una suscripción para renovar.")
            return
        try:
            self.service.renew_subscription(sub_id)
            self._show_info("Suscripción renovada.")
        except Exception as exc:
            self._show_error(str(exc))
        self.refresh_all()

    def _suspend_subscription(self):
        sub_id = self._selected_subscription_id()
        if not sub_id:
            self._show_error("Seleccione una suscripción para suspender.")
            return

        reason, ok = QInputDialog.getText(self, "Suspender suscripción", "Motivo:")
        if not ok or not reason.strip():
            return

        days, ok = QInputDialog.getInt(self, "Suspender suscripción", "Días de suspensión:", 7, 1, 365)
        if not ok:
            return

        start = date.today()
        end = start + timedelta(days=days)
        try:
            self.service.suspend_subscription(sub_id, reason.strip(), start, end)
            self._show_info("Suscripción suspendida.")
        except Exception as exc:
            self._show_error(str(exc))
        self.refresh_all()

    def _cancel_subscription(self):
        sub_id = self._selected_subscription_id()
        if not sub_id:
            self._show_error("Seleccione una suscripción para cancelar.")
            return
        try:
            self.service.cancel_subscription(sub_id)
            self._show_info("Suscripción cancelada.")
        except Exception as exc:
            self._show_error(str(exc))
        self.refresh_all()

    def _add_client(self):
        document, ok = QInputDialog.getText(self, "Nuevo cliente", "Documento:")
        if not ok or not document.strip():
            return
        name, ok = QInputDialog.getText(self, "Nuevo cliente", "Nombre:")
        if not ok or not name.strip():
            return
        phone, ok = QInputDialog.getText(self, "Nuevo cliente", "Teléfono:")
        if not ok or not phone.strip():
            return
        email, ok = QInputDialog.getText(self, "Nuevo cliente", "Email:")
        if not ok or not email.strip():
            return

        if self.service.find_client(document.strip()):
            self._show_error("Ya existe un cliente con ese documento.")
            return

        client = Client(document.strip(), name.strip(), phone.strip(), email.strip())
        self.service.register_client(client)
        self._show_info("Cliente registrado correctamente.")
        self.refresh_all()

    def _deactivate_plan(self):
        plan_id = self._selected_plan_id()
        if not plan_id:
            self._show_error("Seleccione un plan para desactivar.")
            return
        self.service.deactivate_plan(plan_id)
        self._show_info("Plan desactivado.")
        self.refresh_all()


def main():
    app = QApplication(sys.argv)
    window = GymFrontend()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
