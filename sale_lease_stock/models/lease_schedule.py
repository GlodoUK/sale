from odoo import _, api, fields, models
from odoo.exceptions import UserError


class LeaseSchedule(models.Model):
    _name = "sale_lease_stock.lease.schedule"
    _description = "Lease Payment Schedule"

    # TODO: compute a name and then use it on the invoice. it should include
    # client_order_ref, SO, etc.
    # TODO: group invoices by partner_invoice_id?

    partner_id = fields.Many2one(related="order_id.partner_id", required=True)
    partner_invoice_id = fields.Many2one(
        related="order_id.partner_invoice_id",
        required=True,
    )
    line_id = fields.Many2one("sale.order.line", required=True, index=True)
    order_id = fields.Many2one(related="line_id.order_id", store=True)
    date = fields.Date(required=True)
    price = fields.Monetary(required=True)
    quantity_to_invoice = fields.Float()
    currency_id = fields.Many2one("res.currency", required=True)
    invoice_id = fields.Many2one("account.move")
    state = fields.Selection(
        [
            ("cancel", "Cancelled"),
            ("pending", "Pending"),
            ("done", "Done"),
        ],
        default="pending",
        compute="_compute_state",
        store=True,
    )
    company_id = fields.Many2one(related="order_id.company_id", store=True)
    cancelled_at = fields.Datetime()
    invoiced_at = fields.Date(
        related="invoice_id.invoice_date",
        store=True,
    )

    @api.depends("invoice_id.state", "cancelled_at")
    def _compute_state(self):
        for record in self:
            if record.cancelled_at:
                record.state = "cancel"
                continue

            if record.invoice_id and record.invoice_id.state != "cancel":
                record.state = "done"
                continue

            record.state = "pending"

    def action_cancel(self):
        for record in self:
            if record.state != "pending":
                raise UserError(_("Cannot cancel a schedule that is not pending"))
            record.cancelled_at = fields.Datetime.now()

    def _get_invoice_vals(self):
        self.ensure_one()

        journal = (
            self.env["account.move"]
            .with_context(default_move_type="out_invoice")
            ._get_default_journal()
        )
        if not journal:
            raise UserError(
                _("Please define an accounting sales journal for the company %s (%s).")
                % (self.order_id.company_id.name, self.order_id.company_id.id)
            )

        invoice_vals = {
            "ref": self.order_id.client_order_ref or "",
            "move_type": "out_invoice",
            "currency_id": self.currency_id.id,
            "campaign_id": self.order_id.campaign_id.id,
            "medium_id": self.order_id.medium_id.id,
            "source_id": self.order_id.source_id.id,
            "user_id": self.order_id.user_id.id,
            "invoice_user_id": self.order_id.user_id.id,
            "team_id": self.order_id.team_id.id,
            "partner_id": self.partner_invoice_id.id,
            "partner_shipping_id": self.order_id.partner_shipping_id.id,
            "fiscal_position_id": (
                self.order_id.fiscal_position_id
                or self.order_id.fiscal_position_id.get_fiscal_position(
                    self.partner_invoice_id.id
                )
            ).id,
            "partner_bank_id": self.order_id.company_id.partner_id.bank_ids[:1].id,
            "journal_id": journal.id,  # company comes from the journal
            "invoice_origin": self.order_id.name,
            "invoice_payment_term_id": self.order_id.payment_term_id.id,
            "payment_reference": self.order_id.reference,
            "invoice_line_ids": [(0, 0, self._get_invoice_line_vals())],
            "company_id": self.order_id.company_id.id,
        }
        return invoice_vals

    def _get_invoice_line_vals(self):
        self.ensure_one()

        res = {
            "name": self.line_id.name,
            "product_id": self.line_id.product_id.id,
            "product_uom_id": self.line_id.product_uom.id,
            "quantity": self.quantity_to_invoice,
            "discount": 0.0,
            "price_unit": self.price,
            "sale_line_ids": [(4, self.line_id.id)],
            "tax_ids": [(6, 0, self.line_id.tax_id.ids)],
            "analytic_tag_ids": [(6, 0, self.line_id.analytic_tag_ids.ids)],
        }
        return res

    def action_create_invoices(self):
        self.ensure_one()

        if self.invoice_id and self.invoice_id.state != "cancel":
            raise UserError(_("Cannot re-raise an invoice that is not cancelled"))

        move_id = self.env["account.move"].create(self._get_invoice_vals())

        self.invoice_id = move_id
        self.state = "done"

    @api.model
    def action_cron(self):
        pending = self.search(
            [
                ("date", "<=", fields.Date.today()),
                ("state", "=", "pending"),
            ]
        )

        for todo in pending:
            todo.action_create_invoices()
