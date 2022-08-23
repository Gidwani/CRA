from odoo import api, fields, models


class FollowUpReport(models.Model):
    _inherit = "res.partner"

    def excel_report(self):
        data = {}
        return self.env.ref('follow_excel_report.invoice_report_excel').report_action(self, data=data)