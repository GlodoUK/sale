from odoo import http

from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSale(WebsiteSale):
    @http.route()
    def cart_update_json(
        self, product_id, line_id=None, add_qty=None, set_qty=None, display=True
    ):
        res = super().cart_update_json(product_id, line_id, add_qty, set_qty, display)

        order = http.request.website.sale_get_order(force_create=1)
        if order.warning_lease:
            # XXX: We're overriding the warning message here because there's no
            # convenient way to override the warning message in the javascript.
            res["warning"] = order.warning_lease

        return res

    def checkout_redirection(self, order):
        res = super().checkout_redirection(order)
        if res:
            return res

        if order and order.warning_lease:
            return http.request.redirect("/shop/cart")
