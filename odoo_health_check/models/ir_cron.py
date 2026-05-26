import logging
import traceback

from odoo import SUPERUSER_ID, api, fields, models, registry

_logger = logging.getLogger(__name__)


class IrCron(models.Model):
    _inherit = "ir.cron"

    def _callback(self, cron_name, server_action_id, job_id):
        cron_id = self.id or job_id
        history_id = self._odoo_health_log_start(cron_id)
        try:
            result = super()._callback(cron_name, server_action_id, job_id)
        except Exception:
            self._odoo_health_log_end(history_id, "failed", traceback.format_exc())
            raise
        self._odoo_health_log_end(history_id, "success", None)
        return result

    def method_direct_trigger(self):
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
        with registry(self.env.cr.dbname).cursor() as new_cr:
            new_env = api.Environment(new_cr, self.env.uid, {})
            history_id = new_env["ir.cron.history"].create({
                "cron_id": cron_id,
                "state": "running",
            }).id
            new_cr.commit()
            return history_id

    def _odoo_health_log_end(self, history_id, state, error_traceback):
        if not history_id:
            return

        db = self.env.cr.dbname
        if state == "failed":
            self._odoo_health_send_failure_email(history_id)

        with registry(db).cursor() as cr:
            cr.execute("""
                        UPDATE ir_cron_history
                           SET state = %s,
                               date_end = NOW(),
                               error_traceback = %s
                         WHERE id = %s
                    """, (state, error_traceback, history_id))
            cr.commit()

    def _odoo_health_send_failure_email(self, history_id):
        emails_param = (self.env["ir.config_parameter"].sudo()
                        .get_param("odoo_health_check.notify_emails") or "").strip()
        if not emails_param:
            return
        recipients = [e.strip() for e in emails_param.split(",") if e.strip()]
        if not recipients:
            return
        template = self.env.ref(
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
                history_id,
                force_send=True,
                email_values={"email_to": ",".join(recipients)},
                notif_layout='mail.mail_notification_light',
            )
        except Exception:
            _logger.exception(
                "odoo_health_check: failed to enqueue cron failure email for history_id=%s",
                history_id,
            )
