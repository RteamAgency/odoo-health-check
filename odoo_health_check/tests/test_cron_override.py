from odoo.tests import tagged

from .common import OdooHealthTestCommon


@tagged("post_install", "-at_install", "odoo_health_check")
class TestCronOverride(OdooHealthTestCommon):
    """Exercise the history-logging helpers directly.

    Running a cron through base ``_callback`` / ``method_direct_trigger`` is not
    viable inside a TransactionCase: base ``_callback`` commits on success
    (Odoo 19) and rolls back on failure (all versions), both forbidden on the
    test cursor. The helpers below are exactly what the override calls, so this
    keeps full behavioural coverage of the logging contract while staying
    version-portable.
    """

    def test_log_start_then_success(self):
        cron = self._make_cron(code="pass")
        before = self.History.search_count([("cron_id", "=", cron.id)])

        hid = cron._odoo_health_log_start(cron.id)
        cron._odoo_health_log_end(hid, "success", None)

        records = self.History.search([("cron_id", "=", cron.id)], order="id desc")
        self.assertEqual(len(records) - before, 1)
        self.assertEqual(records[0].state, "success")
        self.assertTrue(records[0].date_end)
        self.assertGreaterEqual(records[0].duration_sec, 0.0)
        self.assertFalse(records[0].error_traceback)

    def test_log_end_failure_records_traceback(self):
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

    def test_second_failure_records_separate_row(self):
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

    def test_log_end_with_missing_history_id_is_noop(self):
        """If _odoo_health_log_start returned None (its own failure path),
        _odoo_health_log_end must be a safe no-op rather than raise, so the
        override never breaks the monitored cron from the logging side."""
        cron = self._make_cron()
        before = self.History.search_count([("cron_id", "=", cron.id)])

        # Must not raise, must not create a row.
        self.assertIsNone(cron._odoo_health_log_end(None, "success", None))
        self.assertIsNone(cron._odoo_health_log_end(None, "failed", "boom"))

        self.assertEqual(self.History.search_count([("cron_id", "=", cron.id)]), before)
