from odoo.tests import TransactionCase


class OdooHealthTestCommon(TransactionCase):
    """Shared setup for odoo_health_check tests.

    The module isolates its history writes in an independent cursor
    (`self.pool.cursor()`) so a cron's own rollback never erases the audit
    trail. Under `--test-enable` the model rides the test cursor instead
    (`config['test_enable']`), so seeded history rows are visible to the test and
    rolled back with it. No cursor monkeypatch is needed here: patching
    `registry.cursor` globally also intercepts Odoo's own `_callback` cursor use
    and corrupts the test savepoint stack.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.History = cls.env["ir.cron.history"]
        cls.Cron = cls.env["ir.cron"]
        cls.Params = cls.env["ir.config_parameter"].sudo()

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
