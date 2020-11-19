# Odoo-OpenErp
Here are some Odoo / OpenErp modules.
Some of them are original, some are inspired by other modules (see __openerp__.py for credits)
-
- soc_purchase secondary_unit : add a new unit in purchase order line. This can be usefull when you purchase with a unit different from your stock unit AND that thoses units are not from the same category (ex : purchasing in kg but stocking in units). The module alternates the units in the different object  during the worflow (SO=> Picking=> Invoice)


- soc_sale_order_partial_invoice : allow you to preprare invoice from sale order lines with some improvements :
-   you can group lignes from several SO in one invoice (be carefull, the module doesn't test much : only the customer must be the same. Payment terms, list price, ... are not tested).
-   before creating the invoice, a wizard let you  choose a amount or a rate to be invoiced for each line.
-   Finally, as the "invoiced" function is now based of comparison of price_subtotal ans the new field "amount_invoiced", a new field "force" is added to SO lines. When checked, the SO line become marked as "invoiced", even you did not  invoice all the amount of the line.

