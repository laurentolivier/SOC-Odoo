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

import logging
_logger = logging.getLogger(__name__)

from openerp.osv import orm, fields, osv
from openerp import netsvc
from openerp.tools.translate import _

##Inherit and improve original sale invoice by SO line wizard

class jb__order_line_invoice_partially_line(orm.TransientModel):
    _name = "jb.order.line.invoice.partially.line"

    
    _columns = {
        'wizard_id': fields.many2one('sale.order.line.make.invoice',
                                     string='Wizard'),
        'sale_order_line_id': fields.many2one('sale.order.line',
                                              string='sale.order.line'),
        'name': fields.char('Desciption'),
        'amount_ordered': fields.float('Total commandé'),
        'amount_invoiced': fields.float('Total Facturé'),
        'percent2invoice': fields.float('% à facturer'),
        'amount_final': fields.float('Montant à facturer'),
        }


    def onchange_percent(self, cr, uid, ids, percent2invoice, amount_invoiced, so_line_id, context=None):
        so_line = self.pool.get('sale.order.line').browse(cr,uid, so_line_id,context)
        price_subtotal = so_line.price_subtotal
        if not percent2invoice:
            return {'value':{'amount_final':price_subtotal - amount_invoiced}}
        else:
            return {'value':{'amount_final':price_subtotal*percent2invoice/100}}


           
    
class sale_order_line_make_invoice(orm.TransientModel):
    _inherit = "sale.order.line.make.invoice"
    _description = "Sale OrderLine Make_invoice improved"


    _columns = {
        'name': fields.char('Name'),
        'line_ids': fields.one2many('jb.order.line.invoice.partially.line',
                                    'wizard_id', string="Lines"),
        }    
                        
    def default_get(self, cr, uid, fields, context=None):
        ''' populate the wizard with so line'''
        data = super( sale_order_line_make_invoice, self).default_get(cr, uid, fields, context=context)
        line_values = []
        sales_order_line_obj = self.pool.get('sale.order.line')
        for so_line in sales_order_line_obj.browse(cr, uid, context.get('active_ids', []), context=context):
            if so_line.state in ('confirmed', 'done') and not so_line.invoiced:
                val = {'sale_order_line_id': so_line.id,}
                val['name'] = so_line.name
                val['amount_ordered'] = so_line.price_subtotal
                val['amount_invoiced'] = so_line.amount_invoiced
                val['amount_final'] = so_line.price_subtotal - so_line.amount_invoiced
                line_values.append((0, 0, val))
        data['line_ids']=line_values
        return data    
        
    def make_invoices(self, cr, uid, ids, context=None):
        """
        To make invoices.

             @param self: The object pointer.
             @param cr: A database cursor
             @param uid: ID of the user currently logged in
             @param ids: the ID or list of IDs
             @param context: A standard dictionary

             @return: A dictionary which of fields with values.

        """
        if context is None:
            context = {}
        ctx = context.copy()
        ctx['_partial_invoice'] = {}
        #res = False
#        invoices = {}

        sales_order_line_obj = self.pool.get('sale.order.line')
        sales_order_obj = self.pool.get('sale.order')
        wf_service = netsvc.LocalService('workflow')
        partner_ids = []
        origin = []
        invoice_line_ids = []
        orders = []
        vals = {}
        order_lines = {}
    #    import ipdb; ipdb.set_trace()

        wiz=self.browse(cr,uid,ids,context)[0]

        for line_part  in wiz.line_ids:
            line = line_part.sale_order_line_id
            partner = line.order_id.partner_id           
            if not partner_ids:
                partner_ids.append(partner.id)
                vals['partner_id'] = line.order_id.partner_invoice_id.id
                vals['account_id'] = partner.property_account_receivable.id
                if partner.property_payment_term.id:
                    vals['pay_term'] = partner.property_payment_term.id
                else:
                    vals['pay_term'] = False
                vals['company_id'] = line.order_id.company_id and line.order_id.company_id.id or False
                vals['reference'] =  "P%dSO%d" % (line.order_id.partner_id.id, line.order_id.id)
                vals['currency_id'] = line.order_id.pricelist_id.currency_id.id
                vals['fiscal_position'] = line.order_id.fiscal_position.id or line.order_id.partner_id.property_account_position.id
                vals['user_id'] = line.order_id.user_id and line.order_id.user_id.id or False
            else:
                #TODO : to improve. Thise test should be in default_get
                if partner.id not in partner_ids:
                    raise osv.except_osv(_('Attention!'), _('Le client à facturer doit être le même dans toutes les lignes'))

            # if line_part.percent2invoice == 0 and line_part.amount2invoice == 0 :
            #     continue
            # if line_part.percent2invoice != 0 and line_part.amount2invoice != 0 :
            #     raise osv.except_osv(_('Attention!'), _('Vous avez renseigné un montant et un taux à facturer sur une même ligne. \n Ce n\'est pas possible'))
            
            sale_order = line_part.sale_order_line_id.order_id
            if sale_order.id not in order_lines:
                order_lines[sale_order.id] = []
            order_lines[sale_order.id].append(line_part.sale_order_line_id.id)
            ctx['_partial_invoice'][line_part.sale_order_line_id.id] = line_part.amount_final

            if (not line.invoiced) and (line.state not in ('draft', 'cancel')):
                if line.order_id not in orders:
                    orders.append(line.order_id)
                    origin.append(line.order_id.name)
                line_id = sales_order_line_obj.invoice_line_create(cr, uid, [line.id],context=ctx)
                for lid in line_id:
                    invoice_line_ids.append(lid)

        vals['origin'] = '-'.join(origin)
        vals['type'] = 'out_invoice'
        vals['invoice_line'] = [(6, 0, invoice_line_ids)]
        vals['date_invoice'] = fields.date.today()

        inv_id = self.pool.get('account.invoice').create(cr, uid, vals)
        _logger.info('created invoice %d', inv_id)
        for order in orders:
#            res = make_invoice(order, il)
            cr.execute('INSERT INTO sale_order_invoice_rel \
                    (order_id,invoice_id) values (%s,%s)', (order.id, inv_id))
            flag = True
            data_sale = sales_order_obj.browse(cr, uid, order.id, context=context)
            for line in data_sale.order_line:
                if not line.invoiced:
                    flag = False
                    break
            if flag:
                line.order_id.write({'state': 'progress'})
                wf_service.trg_validate(uid, 'sale.order', order.id, 'all_lines', cr)

        if not invoice_line_ids:
            raise osv.except_osv(_('Warning!'), _('Invoice cannot be created for this Sales Order Line due to one of the following reasons:\n1.The state of this sales order line is either "draft" or "cancel"!\n2.The Sales Order Line is Invoiced!'))
        if context.get('open_invoices', False):
            return self.open_invoices(cr, uid, ids, inv_id, context=context)
        return {'type': 'ir.actions.act_window_close'}
