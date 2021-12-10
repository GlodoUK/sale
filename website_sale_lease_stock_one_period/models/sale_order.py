from odoo import _, api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    warning_lease = fields.Char("Lease Warning", compute="_compute_warning_lease")

    @api.depends("order_line", "order_line.is_lease", "order_line.lease_pricing_id")
    def _compute_warning_lease(self):
        for record in self:
            is_leased_count = len(set(record.order_line.mapped("is_lease")))
            is_leased_by_duration_count = len(
                set(
                    record.order_line.mapped(
                        lambda r: (r.lease_pricing_id.duration, r.lease_pricing_id.unit)
                    )
                )
            )

            clear_warning = True

            if is_leased_count > 1:
                record.warning_lease = _(
                    "You cannot mix and match lease and non-lease products in the same order."
                )
                clear_warning = False

            if is_leased_by_duration_count > 1:
                record.warning_lease = _(
                    "You cannot mix and match lease products with different"
                    " periods in the same order."
                )
                clear_warning = False

            if clear_warning:
                record.warning_lease = False

    @api.depends("order_line", "warning_lease")
    def _cart_can_checkout(self):
        res = super()._cart_can_checkout()

        if self.warning_lease:
            res = False

        return res
