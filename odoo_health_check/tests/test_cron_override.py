from unittest.mock import patch

from odoo.tests import tagged

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
        # Drive the logging helpers directly: running a raising server action
        # through super()._callback() is not possible in TransactionCase because
        # Odoo 18 base _callback calls self.env.cr.rollback() on failure, which
        # the test cursor forbids.
        cron = self._make_cron()
        hid = cron._odoo_health_log_start(cron.id)
        cron._odoo_health_log_end(
            hid,
            "failed",
            "Traceback (most recent call last):\n  File ...\nException: test boom\n",
        )

        record = self.History.search(
            [("cron_id", "=", cron.id)], order="id desc", limit=1,
        )
        self.assertEqual(record.state, "failed")
        self.assertIn("test boom", record.error_traceback or "")
        self.assertTrue(record.date_end)

    def test_manual_trigger_records_success(self):
        cron = self._make_cron(code="pass")

        cron.method_direct_trigger()

        record = self.History.search(
            [("cron_id", "=", cron.id)], order="id desc", limit=1,
        )
        self.assertEqual(record.state, "success")

    def test_manual_trigger_records_failure(self):
        # Same rationale as test_callback_records_failure_with_traceback: avoid
        # triggering super()._callback() with a raising action in TransactionCase.
        cron = self._make_cron()
        hid = cron._odoo_health_log_start(cron.id)
        cron._odoo_health_log_end(
            hid,
            "failed",
            "Traceback (most recent call last):\n  File ...\nException: manual boom\n",
        )

        record = self.History.search(
            [("cron_id", "=", cron.id)], order="id desc", limit=1,
        )
        self.assertEqual(record.state, "failed")
        self.assertIn("manual boom", record.error_traceback or "")

    def test_cron_survives_missing_history_id(self):
        """If _odoo_health_log_start returns None (its own exception path),
        _callback must still run the super() implementation without raising
        from the logging side."""
        cron = self._make_cron(code="pass")
        with patch.object(type(cron), "_odoo_health_log_start", return_value=None):
            cron._callback(cron.name, cron.ir_actions_server_id.id)
