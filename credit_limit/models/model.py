from odoo import fields, models
from odoo.exceptions import UserError


class StockQuantInh(models.Model):
    _inherit = 'stock.quant'

    yom = fields.Selection(selection=[(f'{i}', i) for i in range(1900, 3000)], string='YOM', related='lot_id.yom')


class StockProductionInh(models.Model):
    _inherit = 'stock.lot'

    yom = fields.Selection(selection=[(f'{i}', i) for i in range(1900, 3000)], string='YOM')


class ResPartner(models.Model):
    _inherit = 'res.partner'

    credit_limit = fields.Integer('Credit Limit', default=0)


class AccountMoveInh(models.Model):
    _inherit = 'account.move'

    def action_open(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Confirm',
            'view_id': self.env.ref('credit_limit.wizard_message_form', False).id,
            'context': {'default_text': '12', 'default_partner': self.partner_id.name},
            'target': 'new',
            'res_model': 'display.dialog.box',
            'view_mode': 'form',
        }

    def action_manager_approve(self):
        if 'default_move_type' in self._context and self.move_type == 'out_invoice':
            bal = self.get_balance()
            print(bal)
            if bal <= 0:
                print('1')
                if self.total_amount_net <= (self.partner_id.credit_limit + abs(bal)):
                    return super(AccountMoveInh, self).action_manager_approve()
                else:
                    return self.action_open()
            else:
                print("2")
                if self.total_amount_net <= (self.partner_id.credit_limit - abs(bal)):

                    return super(AccountMoveInh, self).action_manager_approve()
                else:
                    return self.action_open()
        else:
            return super(AccountMoveInh, self).action_manager_approve()

    def get_balance(self):
        partner_ledger = self.env['account.move.line'].search(
            [('partner_id', '=', self.partner_id.id),
             ('move_id.state', '=', 'posted'), ('balance', '!=', 0),
             ('account_id.reconcile', '=', True), ('full_reconcile_id', '=', False), '|',
             ('account_id.account_type', '=', 'liability_payable'), ('account_id.account_type', '=', 'asset_receivable')])
        # ('asset_receivable', 'liability_payable')
        bal = 0
        for par_rec in partner_ledger:
            bal = bal + (par_rec.debit - par_rec.credit)
        return bal

