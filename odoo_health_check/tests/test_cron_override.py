from unittest.mock import patch

from odoo.tests import tagged

from .common import OdooHealthTestCommon


@tagged("post_install", "-at_install", "odoo_health_check")
class TestCronOverride(OdooHealthTestCommon):
    """Exercise the history-logging helpers directly.

    Running a cron through base ``_callback`` is not viable inside a
    TransactionCase: base commits on success (Odoo 19) and rolls back on failure
    (all versions), both forbidden on the test cursor. The helpers below are
    exactly what the override calls, so this keeps behavioural coverage of the
    logging contract while staying version-portable.
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
        _odoo_health_log_end must be a safe no-op rather than raise."""
        cron = self._make_cron()
        before = self.History.search_count([("cron_id", "=", cron.id)])

        self.assertIsNone(cron._odoo_health_log_end(None, "success", None))
        self.assertIsNone(cron._odoo_health_log_end(None, "failed", "boom"))

        self.assertEqual(self.History.search_count([("cron_id", "=", cron.id)]), before)

    def test_handle_callback_exception_records_failure(self):
        """Odoo 14-17 only: base `_callback` swallows a failing scheduled action
        and calls `_handle_callback_exception`. Our override must record a
        'failed' history row there (so scheduled-cron failures are detected, not
        silently logged as success). Base's hook rolls back - illegal on the test
        cursor - so we patch it to a no-op and drive our override directly."""
        cron = self._make_cron()
        hid = cron._odoo_health_log_start(cron.id)
        marker = {"failed": False, "history_id": hid}
        cron_ctx = cron.with_context(_odoo_health_marker=marker)
        err = ValueError("scheduled boom")

        # Patch base's hook (it rolls back - illegal on the test cursor). Locate it
        # by stable module path rather than class name, which varies across majors.
        base_cls = next(
            c for c in type(cron).__mro__
            if c.__module__ == "odoo.addons.base.models.ir_cron"
        )
        with patch.object(base_cls, "_handle_callback_exception", return_value=None):
            cron_ctx._handle_callback_exception(
                cron.name, cron.ir_actions_server_id.id, cron.id, err,
            )

        self.assertTrue(marker["failed"])
        record = self.History.browse(hid)
        self.assertEqual(record.state, "failed")
        self.assertIn("scheduled boom", record.error_traceback or "")
