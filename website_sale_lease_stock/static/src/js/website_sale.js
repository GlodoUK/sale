odoo.define("website_sale_lease_stock.website_sale", function (require) {
    "use strict";

    var publicWidget = require("web.public.widget");
    // Needed to ensure we load after website_sale
    require("website_sale.website_sale");

    publicWidget.registry.WebsiteSale.include({
        _onProductReady: function () {
            // We need to inject our lease field, because Odoo doesn't just do a
            // normal field submission. Because why would it?
            this.rootProduct.lease = this.$form.find('select[name="lease"]').val();

            return this._super.apply(this, arguments);
        },

        _onChangeCombination: function (ev, $parent, combination) {
            this._super.apply(this, arguments);
            var leasing = $parent.find('select[name="lease"]');
            leasing.find("option[value!='']").remove();

            if (combination.lease_ok) {
                leasing.removeClass("disabled");
            } else {
                leasing.addClass("disabled");
            }

            if (combination.lease_pricing_rules !== undefined) {
                for (const [key, value] of Object.entries(
                    combination.lease_pricing_rules
                )) {
                    leasing.append(new Option(value, key));
                }
            }
        },
    });
});
