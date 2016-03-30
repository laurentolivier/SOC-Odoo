# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Laurent OLIVIER (<lolivier@soconseil.fr>)
#    All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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

from openerp.osv import fields, osv
from openerp.addons import decimal_precision as dp

class purchase_order_line(osv.osv):
    _name = 'purchase.order.line'
    _inherit = 'purchase.order.line'

       
    _columns = {
        'price_unit': fields.float('Unit Price', required=True, digits_compute= dp.get_precision('Purchase Price')),       
        'qty_uos2':fields.float(
            string='Quantité (UdS)',
            digits_compute=dp.get_precision('Product UoM'),
            states={'draft': [('readonly', False)]}
        ),
        'uos_id2': fields.many2one('product.uom', u'Unité de stock'),
        }

    def onchange_product_id(self, cr, uid, ids, pricelist_id, product_id, qty, uom_id,
            partner_id, date_order=False, fiscal_position_id=False, date_planned=False,
            name=False, price_unit=False, context=None):
        if context is None:
            context={}
        res = super(purchase_order_line,self).onchange_product_id(cr, uid, ids,pricelist_id, product_id, qty, uom_id, partner_id, date_order, fiscal_position_id, date_planned, name, price_unit, context)
        if product_id:
            prod = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
            res['value']['uos_id2']=prod.uom_id.id
        return res

    def onchange_product_uom(self, cr, uid, ids, pricelist_id, product_id, qty, uom_id,
            partner_id, date_order=False, fiscal_position_id=False, date_planned=False,
            name=False, price_unit=False, context=None):
        """ désactive l essentiel du onchange qui
        est fait avce onchange_product_id """
        if context is None:
            context = {}
        if not uom_id:
            return {'value': {'price_unit': price_unit or 0.0, 'name': name or '', 'product_uom' : uom_id or False}}
        else:
            return {'value':{}}



        
class purchase_order(osv.osv):
    _name = 'purchase.order'
    _inherit = 'purchase.order'

    def _prepare_order_line_move(self, cr, uid, order, order_line, picking_id, context=None):
        if context is None:
            context={}        
        res=super(purchase_order,self)._prepare_order_line_move(cr, uid, order, order_line, picking_id, context)
#        import ipdb; ipdb.set_trace()
    
        #intervertir les valeurs des qty et unit pour avant de créer le move
        res['qty_uos2'] = order_line.product_qty
        res['uos_id2'] = order_line.product_uom.id
        res['product_qty'] = order_line.qty_uos2
        res['product_uos_qty'] = order_line.qty_uos2
        res['product_uom'] = order_line.uos_id2.id
        res['product_uos'] = order_line.uos_id2.id

        return res



class purchase_purchase_requisition(osv.osv):
    _name = 'purchase.requisition'
    _inherit = 'purchase.requisition'

    def make_purchase_order(self, cr, uid, ids, partner_id, context=None):
        """
        Create New RFQ for Supplier with qty in uds added in purchase line
        """
        if context is None:
            context = {}
        assert partner_id, 'Supplier should be specified'
        purchase_order = self.pool.get('purchase.order')
        purchase_order_line = self.pool.get('purchase.order.line')
        res_partner = self.pool.get('res.partner')
        fiscal_position = self.pool.get('account.fiscal.position')
        supplier = res_partner.browse(cr, uid, partner_id, context=context)
        supplier_pricelist = supplier.property_product_pricelist_purchase or False
        res = {}
        for requisition in self.browse(cr, uid, ids, context=context):
            if supplier.id in filter(lambda x: x, [rfq.state <> 'cancel' and rfq.partner_id.id or None for rfq in requisition.purchase_ids]):
                 raise osv.except_osv(('Attention!'), ('Il y a déjà %s demande de prix pour ce fournisseur.Vous devez annuler cette demande en premier.') % rfq.state)
            location_id = requisition.warehouse_id.lot_input_id.id
            purchase_id = purchase_order.create(cr, uid, {
                        'origin': requisition.name,
                        'partner_id': supplier.id,
                        'pricelist_id': supplier_pricelist.id,
                        'location_id': location_id,
                        'company_id': requisition.company_id.id,
                        'fiscal_position': supplier.property_account_position and supplier.property_account_position.id or False,
                        'requisition_id':requisition.id,
                        'notes':requisition.description,
                        'warehouse_id':requisition.warehouse_id.id ,
            })
            res[requisition.id] = purchase_id
            for line in requisition.line_ids:
                product = line.product_id
                seller_price, qty, default_uom_po_id, date_planned = self._seller_details(cr, uid, line, supplier, context=context)
                qty_uos2 = line.product_qty #qty in stock unit
                uos_id2 = line.product_uom_id #stock unit
                taxes_ids = product.supplier_taxes_id
                taxes = fiscal_position.map_tax(cr, uid, supplier.property_account_position, taxes_ids)
                purchase_order_line.create(cr, uid, {
                    'order_id': purchase_id,
                    'name': product.partner_ref,
                    'product_qty': qty,
                    'qty_uos2' : qty_uos2,
                    'product_id': product.id,
                    'product_uom': default_uom_po_id,
                    'uos_id2': uos_id2.id,
                    'price_unit': seller_price,
                    'date_planned': date_planned,
                    'taxes_id': [(6, 0, taxes)],
                }, context=context)
                
        return res

