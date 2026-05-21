from odoo.tests import TransactionCase


class OdooHealthTestCommon(TransactionCase):
    """Shared setup for odoo_health_check tests (Odoo 14 variant).

    Odoo 14 has no class-level ``cls.env`` in ``setUpClass`` (the environment is
    created per instance in ``setUp``), so the shared registry handles are bound
    on the instance here. The module rides the test cursor under ``--test-enable``
    (``config['test_enable']``); no ``registry.cursor`` monkeypatch is needed.
    """

    def setUp(self):
        super().setUp()
        self.History = self.env["ir.cron.history"]
        self.Cron = self.env["ir.cron"]
        self.Params = self.env["ir.config_parameter"].sudo()

    def _make_cron(self, name="oh_test", code="pass", active=False):
        server_action = self.env["ir.actions.server"].create({
            "name": name,
            "model_id": self.env.ref("base.model_ir_cron").id,
            "state": "code",
            "code": code,
        })
        return self.Cron.create({
            "name": name,
            "ir_actions_server_id": server_action.id,
            "interval_number": 1,
            "interval_type": "days",
            "active": active,
        })
