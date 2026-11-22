from unittest.mock import patch

from odoo.tests import tagged
from odoo.tools import mute_logger

from .common import OdooHealthTestCommon


@tagged("post_install", "-at_install", "odoo_health_check")
class TestCronOverride(OdooHealthTestCommon):

    def test_callback_records_success(self):
        cron = self._make_cron(code="pass")
        before = self.History.search_count([("cron_id", "=", cron.id)])

        cron._callback(cron.name, cron.ir_actions_server_id.id)

        records = self.History.search(
            [("cron_id", "=", cron.id)], order="id desc",
        )
        self.assertEqual(len(records) - before, 1)
        self.assertEqual(records[0].state, "success")
        self.assertTrue(records[0].date_end)
        self.assertGreaterEqual(records[0].duration_sec, 0.0)
        self.assertFalse(records[0].error_traceback)

    def test_callback_records_failure_with_traceback(self):
        cron = self._make_cron(code="raise Exception('test boom')")

        exc = self._run_failing_callback(cron)
        self.assertIn("test boom", str(exc))

        record = self.History.search(
            [("cron_id", "=", cron.id)], order="id desc", limit=1,
        )
        self.assertEqual(record.state, "failed")
        self.assertIn("test boom", record.error_traceback or "")
        self.assertTrue(record.date_end)

    def test_manual_trigger_records_success(self):
        cron = self._make_cron(code="pass", active=True)

        cron.method_direct_trigger()

        records = self.History.search([("cron_id", "=", cron.id)])
        self.assertEqual(len(records), 1, "one history row per manual run")
        self.assertEqual(records.state, "success")

    def test_manual_trigger_records_failure(self):
        """Since Odoo 19 a manual run goes through _process_job: the failure is
        logged and returned to the client, not raised."""
        cron = self._make_cron(code="raise Exception('manual boom')", active=True)

        with mute_logger("odoo.addons.base.models.ir_cron"):
            cron.method_direct_trigger()

        records = self.History.search([("cron_id", "=", cron.id)])
        self.assertEqual(len(records), 1, "one history row per manual run")
        self.assertEqual(records.state, "failed")
        self.assertIn("manual boom", records.error_traceback or "")

    def test_cron_survives_missing_history_id(self):
        """If _odoo_health_log_start returns None (its own exception path),
        _callback must still run the super() implementation without raising
        from the logging side."""
        cron = self._make_cron(code="pass")
        with patch.object(type(cron), "_odoo_health_log_start", return_value=None):
            cron._callback(cron.name, cron.ir_actions_server_id.id)
