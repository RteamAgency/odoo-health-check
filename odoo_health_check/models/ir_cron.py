import logging
import traceback
from contextlib import contextmanager

from odoo import SUPERUSER_ID, api, fields, models
from odoo.tools import config

_logger = logging.getLogger(__name__)


class IrCron(models.Model):
    _inherit = "ir.cron"

    @contextmanager
    def _odoo_health_env(self):
        """Yield an Environment for writing the cron history + failure alert.

        Production: an INDEPENDENT cursor (`self.pool.cursor()`) so the history
        row and the alert survive the monitored cron's own rollback.
        Tests (`config['test_enable']`): ride the test cursor (an independent
        cursor cannot be committed/rolled back inside a TransactionCase).
        """
        if config["test_enable"]:
            yield self.env
        else:
            with self.pool.cursor() as new_cr:
                yield api.Environment(new_cr, SUPERUSER_ID, {})

    def _callback(self, cron_name, server_action_id, job_id):
        cron_id = self.id or job_id
        history_id = self._odoo_health_log_start(cron_id)
        # On Odoo 14-17 base `_callback` SWALLOWS a failing action: it calls
        # `_handle_callback_exception` and does NOT re-raise. So we cannot detect
        # failure by wrapping super() in try/except (the except never fires and we
        # would wrongly log "success"). Instead the failure is recorded in our
        # `_handle_callback_exception` override below; a shared mutable marker
        # passed through context tells us here whether that happened.
        marker = {"failed": False, "history_id": history_id}
        cron = self.with_context(_odoo_health_marker=marker)
        result = super(IrCron, cron)._callback(cron_name, server_action_id, job_id)
        if not marker["failed"]:
            self._odoo_health_log_end(history_id, "success", None)
        return result

    def _handle_callback_exception(self, cron_name, server_action_id, job_id, job_exception):
        # Called by base `_callback` when the scheduled action raised, BEFORE base
        # rolls back. Record the failure on an isolated cursor (prod) so it survives
        # that rollback, and flag the marker so `_callback` does not also log success.
        marker = self.env.context.get("_odoo_health_marker")
        if marker and marker.get("history_id"):
            marker["failed"] = True
            tb = "".join(traceback.format_exception(
                type(job_exception), job_exception, job_exception.__traceback__,
            ))
            self._odoo_health_log_end(marker["history_id"], "failed", tb)
        return super()._handle_callback_exception(
            cron_name, server_action_id, job_id, job_exception,
        )

    def method_direct_trigger(self):
        # Manual "Run" runs the action directly (not via _callback) and re-raises
        # on every version, so plain try/except is correct here.
        for cron in self:
            history_id = cron._odoo_health_log_start(cron.id)
            try:
                super(IrCron, cron).method_direct_trigger()
            except Exception:
                cron._odoo_health_log_end(history_id, "failed", traceback.format_exc())
                raise
            cron._odoo_health_log_end(history_id, "success", None)
        return True

    def _odoo_health_log_start(self, cron_id):
        with self._odoo_health_env() as env:
            return env["ir.cron.history"].create({
                "cron_id": cron_id,
                "state": "running",
            }).id

    def _odoo_health_log_end(self, history_id, state, error_traceback):
        if not history_id:
            return
        # History write in its own short-lived cursor (releases the row lock on
        # commit); the failure email is enqueued in a SEPARATE cursor afterwards
        # (no slow work inside the lock). Both isolated from the monitored cron in
        # prod; both ride the test cursor under --test-enable (see _odoo_health_env).
        with self._odoo_health_env() as env:
            env["ir.cron.history"].browse(history_id).write({
                "state": state,
                "date_end": fields.Datetime.now(),
                "error_traceback": error_traceback,
            })
        if state == "failed":
            with self._odoo_health_env() as env:
                history = env["ir.cron.history"].browse(history_id)
                self._odoo_health_send_failure_email(env, history)

    @staticmethod
    def _odoo_health_send_failure_email(env, history):
        emails_param = (env["ir.config_parameter"].sudo()
                        .get_param("odoo_health_check.notify_emails") or "").strip()
        if not emails_param:
            return
        recipients = [e.strip() for e in emails_param.split(",") if e.strip()]
        if not recipients:
            return
        template = env.ref(
            "odoo_health_check.mail_template_cron_failure",
            raise_if_not_found=False,
        )
        if not template:
            _logger.warning(
                "odoo_health_check: mail template not found, failure alert skipped"
            )
            return
        try:
            template.send_mail(
                history.id,
                force_send=False,
                email_values={"email_to": ",".join(recipients)},
            )
        except Exception:
            _logger.exception(
                "odoo_health_check: failed to enqueue cron failure email for history_id=%s",
                history.id,
            )
