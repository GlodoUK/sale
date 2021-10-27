from odoo.tests import tagged

from odoo.addons.sale.tests.common import TestSaleCommon


@tagged("post_install", "-at_install")
class TestSaleOrder(TestSaleCommon):
    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)

        cls.product_lease = cls.env["product.template"].create(
            {
                "lease_ok": True,
                "sale_ok": True,
                "name": "LEASE PROD",
                "default_code": "PROD_LEASE",
                "lease_pricing_ids": [
                    (
                        0,
                        0,
                        {
                            "duration": 2,
                            "unit": "months",
                            "price": 12.0,
                        },
                    )
                ],
            }
        )

    def test_lease_sale(self):
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner_a.id,
                "partner_invoice_id": self.partner_a.id,
                "partner_shipping_id": self.partner_a.id,
                "pricelist_id": self.company_data["default_pricelist"].id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_lease.id,
                            "is_lease": True,
                            "lease_pricing_id": self.product_lease.lease_pricing_ids[
                                0
                            ].id,
                        },
                    )
                ],
            }
        )

        sale_order.action_confirm()

        self.assertEqual(sale_order.lease_schedule_count, 2)
        self.assertEqual(sale_order.order_line.qty_to_invoice, 0.0)
