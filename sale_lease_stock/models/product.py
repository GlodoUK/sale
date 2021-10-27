from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    lease_ok = fields.Boolean(
        string="Can be Leased", help="Allow leasing of this product."
    )
    lease_pricing_ids = fields.One2many(
        "sale_lease_stock.pricing",
        "product_template_id",
        string="Lease Pricings",
        auto_join=True,
        copy=True,
    )

    def _get_combination_info(
        self,
        combination=False,
        product_id=False,
        add_qty=1,
        pricelist=False,
        parent_combination=False,
        only_template=False,
    ):
        combination_info = super()._get_combination_info(
            combination=combination,
            product_id=product_id,
            add_qty=add_qty,
            pricelist=pricelist,
            parent_combination=parent_combination,
            only_template=only_template,
        )

        if combination_info.get("product_id"):
            product = self.env["product.product"].browse(
                combination_info.get("product_id")
            )
        else:
            product = self.env["product.product"].search(
                [("product_tmpl_id", "=", combination_info.get("product_template_id"))],
                limit=1,
            )

        if product:
            combination_info.update(
                {
                    "lease_ok": self.sudo().lease_ok,
                    "lease_pricing_rules": {
                        rule.id: rule.display_name
                        for rule in product._get_lease_price_rules(pricelist=pricelist)
                    },
                }
            )

        return combination_info


class ProductProduct(models.Model):
    _inherit = "product.product"

    def _get_lease_price_rules(self, **kwargs):
        self.ensure_one()

        # Alternatively we can use the following domain.
        # This filter works better for smaller lists.
        # [
        #     '&',
        #     '&',
        #     ('product_template_id', '=', product_template_id),
        #     '|',
        #     ('product_variant_ids', '=', False),
        #     ('product_variant_ids.id', '=', product_id),
        #     '|',
        #     ('pricelist_id', '=', False),
        #     ('pricelist_id', '=', parent.pricelist_id)
        # ]

        pricelist = kwargs.get("pricelist", self.env["product.pricelist"])

        available_pricings = self.sudo().lease_pricing_ids.filtered(
            lambda p: p.pricelist_id == pricelist
        )
        if not available_pricings:
            # If no pricing is defined for given pricelist:
            # fallback on generic pricings
            available_pricings = self.lease_pricing_ids.filtered(
                lambda p: not p.pricelist_id
            )

        return available_pricings.filtered(lambda r: r.applies_to(self))
