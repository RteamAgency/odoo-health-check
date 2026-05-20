from datetime import timedelta

from odoo import fields
from odoo.tests import tagged

from .common import OdooHealthTestCommon


@tagged("post_install", "-at_install", "odoo_health_check")
class TestDashboardSuccessRate(OdooHealthTestCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Dashboard = cls.env["health.check.dashboard"]

    def setUp(self):
        super().setUp()
        self.cron = self._make_cron()

    def _seed(self, state, delta):
        return self.History.create({
            "cron_id": self.cron.id,
            "state": state,
            "date_start": fields.Datetime.now() - delta,
        })

    def test_empty_window_returns_zero_no_division_error(self):
        snap = self.Dashboard._compute_dashboard_snapshot()
        self.assertEqual(snap["success_rate_7d"], 0.0)

    def test_all_success_returns_hundred(self):
        for _ in range(4):
            self._seed("success", timedelta(hours=1))
        snap = self.Dashboard._compute_dashboard_snapshot()
        self.assertEqual(snap["success_rate_7d"], 100.0)

    def test_mixed_runs_returns_ratio(self):
        for _ in range(7):
            self._seed("success", timedelta(hours=1))
        for _ in range(3):
            self._seed("failed", timedelta(hours=1))
        snap = self.Dashboard._compute_dashboard_snapshot()
        self.assertEqual(snap["success_rate_7d"], 70.0)

    def test_running_rows_excluded_from_denominator(self):
        # 2 success + 0 failed completed -> 100%, the in-flight 'running'
        # row must not dilute the rate.
        self._seed("success", timedelta(hours=1))
        self._seed("success", timedelta(hours=2))
        self._seed("running", timedelta(minutes=5))
        snap = self.Dashboard._compute_dashboard_snapshot()
        self.assertEqual(snap["success_rate_7d"], 100.0)

    def test_runs_older_than_7d_excluded(self):
        # Inside the window: 1 success, 1 failed -> 50%.
        self._seed("success", timedelta(days=2))
        self._seed("failed", timedelta(days=3))
        # Outside the window: must affect neither numerator nor denominator.
        self._seed("success", timedelta(days=8))
        self._seed("failed", timedelta(days=10))
        snap = self.Dashboard._compute_dashboard_snapshot()
        self.assertEqual(snap["success_rate_7d"], 50.0)
