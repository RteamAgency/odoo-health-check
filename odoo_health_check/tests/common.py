from unittest.mock import patch

from odoo.addons.base.models.ir_cron import IrCron as BaseIrCron
from odoo.tests import TransactionCase
from odoo.tools import mute_logger


def _callback_without_commit(self, cron_name, server_action_id):
    """Odoo's ir.cron._callback runs the server action, then commits, or
    rolls back and re-raises. A test transaction forbids both, and a rollback
    to the job's savepoint would also take the history rows the module wrote
    in its own (test) cursor. The tests run the action alone: the module's
    override around it is what they check."""
    self.ensure_one()
    self.env["ir.actions.server"].browse(server_action_id).run()


class OdooHealthTestCommon(TransactionCase):
    """Shared setup for odoo_health_check tests.

    The module writes history in its own cursor (`self.pool.cursor()`) so a
    cron's rollback never erases the audit trail. In registry test mode those
    cursors wrap the test's cursor, so the rows ride the test transaction and
    are rolled back with it.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.History = cls.env["ir.cron.history"]
        cls.Cron = cls.env["ir.cron"]
        cls.Params = cls.env["ir.config_parameter"].sudo()

    def setUp(self):
        super().setUp()
        self.enterContext(self.registry_test_mode())
        callback_patcher = patch.object(BaseIrCron, "_callback", _callback_without_commit)
        callback_patcher.start()
        self.addCleanup(callback_patcher.stop)

    def _run_failing_callback(self, cron):
        """Run a cron whose action raises; return the exception.

        Not self.assertRaises: Odoo's version rolls back a savepoint when the
        exception arrives, and would take the history row and the alert mail
        with it. The action raises a plain Python exception, so the
        transaction stays usable without one."""
        try:
            with mute_logger("odoo.addons.base.models.ir_cron"):
                cron._callback(cron.name, cron.ir_actions_server_id.id)
        except Exception as exc:  # noqa: BLE001
            return exc
        self.fail("the cron's server action did not raise")

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
