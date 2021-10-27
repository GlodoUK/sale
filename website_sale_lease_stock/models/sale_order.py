from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _cart_find_product_line(self, product_id=None, line_id=None, **kwargs):
        self.ensure_one()
        lines = super()._cart_find_product_line(product_id, line_id, **kwargs)
        # if we've been asked for a specific line, we must use that
        if line_id:
            return lines

        # if we have a lease, find the line which is_lease = True and the
        # lease_pricing_id matches
        if kwargs.get("lease"):
            lease_id = int(kwargs.get("lease"))
            return lines.filtered(
                lambda l: l.lease_pricing_id.id == lease_id and l.is_lease
            )

        # otherwise just find any line which isn't a leasing line
        return lines.filtered(lambda l: not l.is_lease)

    def _cart_update(
        self, product_id=None, line_id=None, add_qty=0, set_qty=0, **kwargs
    ):
        res = super()._cart_update(
            product_id=product_id,
            line_id=line_id,
            add_qty=add_qty,
            set_qty=set_qty,
            **kwargs
        )

        if "lease" in kwargs:
            lease_id = self.env["sale_lease_stock.pricing"]
            lease = False
            if kwargs.get("lease"):
                lease = True
                lease_id = self.env["sale_lease_stock.pricing"].search(
                    [("id", "=", kwargs.get("lease"))], limit=1
                )

            line_id = self.env["sale.order.line"].browse(res["line_id"])

            to_change = {"is_lease": lease}
            if lease_id:
                to_change.update(
                    {
                        "lease_pricing_id": lease_id.id,
                    }
                )

            line_id.write(to_change)

        return res
