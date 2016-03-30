# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Alexandre Fayolle
#    Copyright 2013 Camptocamp SA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
"""
 * Adding qty_invoiced field on SO lines, computed based on invoice lines
   linked to it that has the same product. So this way, advance invoice will
   still work !

 * Adding qty_delivered field in SO Lines, computed from move lines linked to
   it. For services, the quantity delivered is a problem, the MRP will
   automatically run the procurement linked to this line and pass it to done. I
   suggest that in that case, delivered qty = invoiced_qty as the procurement
   is for the whole qty, it'll be a good alternative to follow what has been
   done and not.

 * Add in the "Order Line to invoice" view those fields

 * Change the behavior of the "invoiced" field of the SO line to be true when
   all is invoiced

 * Adapt the "_make_invoice" method in SO to deal with qty_invoiced

 * Adapt the sale_line_invoice.py wizard to deal with qty_invoiced, asking the
   user how much he want to invoice.

By having the delivered quantity, we can imagine in the future to provide an
invoicing "based on delivery" that will look at those values instead of looking
in picking.


"""
import logging
_logger = logging.getLogger(__name__)

from openerp.osv import orm, fields
from openerp import netsvc


class sale_order_line(orm.Model):
    _inherit = 'sale.order.line'

    def field_qty_invoiced(self, cr, uid, ids, fields, arg, context):
        res = dict.fromkeys(ids, 0)
        for line in self.browse(cr, uid, ids, context=context):
            for invoice_line in line.invoice_lines:
                if invoice_line.invoice_id.state != 'cancel':
                    res[line.id] += invoice_line.quantity # XXX uom !
        return res

    def field_amount_invoiced(self, cr, uid, ids, fields, arg, context):
        res = dict.fromkeys(ids, 0)
        for line in self.browse(cr, uid, ids, context=context):
            for invoice_line in line.invoice_lines:
                if invoice_line.invoice_id.state != 'cancel': #TODO use line in draft state or not  ?
                    res[line.id] += invoice_line.price_subtotal
        return res

    def field_rate_invoiced(self, cr, uid, ids, fields, arg, context):
        res = dict.fromkeys(ids, 0)
        for line in self.browse(cr, uid, ids, context=context):
            invoiced = 0.0
            for invoice_line in line.invoice_lines:
                if invoice_line.invoice_id.state != 'cancel': #TODO use line in draft state or not  ?
                    invoiced += invoice_line.price_subtotal
            if invoiced:
                res[line.id] = round((100.0*invoiced/line.price_subtotal),2)
            else:
                res[line.id] = 0.0
        return res
        
    def field_qty_delivered(self, cr, uid, ids, fields, arg, context):
        res = dict.fromkeys(ids, 0)
        for line in self.browse(cr, uid, ids, context=context):
            if not line.move_ids:
                # consumable or service: assume delivered == invoiced
                res[line.id] = line.qty_invoiced
            else:
                for move in line.move_ids:
                    if (move.state == 'done' and
                        move.picking_id and
                        move.picking_id.type == 'out'):
                        res[line.id] += move.product_qty
        return res

    def _prepare_order_line_invoice_line(self, cr, uid, line, account_id=False, context=None):
        res = super(sale_order_line,
                    self)._prepare_order_line_invoice_line(cr,
                                                           uid,
                                                           line,
                                                           account_id,
                                                           context)
        if '_partial_invoice' in context:
            # we are making a partial invoice for the line
            param = context['_partial_invoice'][line.id]
            # if param[0] == 'p': #the context send a percentage to invoice
            #     to_invoice_amount = line.price_subtotal*param[1]/100.0
            # elif param[0] == 'a': #the send an amount to invoice
            #     to_invoice_amount = param[1]
            to_invoice_amount = param
        else:
            # we are invoicing the yet uninvoiced part of the line
            to_invoice_amount = line.price_subtotal - line.amount_invoiced

        #with this hack, the invoice line subtotal is exactly what one want
        #but it doesn't manage  correctly quantities between sale_order_lines et invoice_lines
        res['price_unit'] = to_invoice_amount
        res['quantity'] = 1.0
        
        return res

    def _fnct_line_invoiced(self, cr, uid, ids, field_name, args, context=None):
        res = dict.fromkeys(ids, False)
        for this in self.browse(cr, uid, ids, context=context):
            if this.forced:
                res[this.id] = True
            else:
                res[this.id] = (abs(this.price_subtotal - this.amount_invoiced) < 0.01) #TODO : improve the test to mark SO line as invoiced
        print res
        return res

    def _order_lines_from_invoice2(self, cr, uid, ids, context=None):
        # overridden with different name because called by framework with
        # 'self' an instance of another class
        return self.pool['sale.order.line']._order_lines_from_invoice(cr, uid, ids, context)

    _columns = {
        'forced': fields.boolean(string='Solder la ligne',
                                        help="Cette ligne sera marquée comme entièrement facturée MEME s'il reste un solde non facturé"),
    #    'qty_invoiced': fields.function(field_qty_invoiced,
                                        # string='Invoiced Quantity',
                                        # type='float',
                                        # help="the quantity of product from this line "
                                        #      "already invoiced"),
        'amount_invoiced': fields.function(field_amount_invoiced,
                                        string='Montant facturé',
                                        type='float',
                                        help="the amount from this line "
                                             "already invoiced"),
        'rate_invoiced': fields.function(field_rate_invoiced,
                                        string='% Facturé',
                                        type='float',
                                        help="the amount rate from this line "
                                             "already invoiced"),        
        # 'qty_delivered': fields.function(field_qty_delivered,
        #                                  string='Invoiced Quantity',
        #                                  type='float',
        #                                  help="the quantity of product from this line "
        #                                       "already invoiced"),
        'invoiced': fields.function(_fnct_line_invoiced,
                                    string='Invoiced',
                                    type='boolean',
                                    store={
                                        'account.invoice': (_order_lines_from_invoice2,
                                                            ['state'], 10),
                                        'sale.order.line': (
                                            lambda self,cr,uid,ids,ctx=None: ids,
                                            ['invoice_lines','forced'], 10
                                            )
                                        }
                                    ),
        }

    _defaults = {
        'forced' : False,
        }

