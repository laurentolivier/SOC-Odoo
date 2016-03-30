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

class stock_picking(osv.osv):
    _name = 'stock.picking'
    _inherit = 'stock.picking'

    def _prepare_invoice_line(self, cr, uid, group, picking, move_line, invoice_id,
        invoice_vals, context=None):

        if context is None:
            context={}
        res = super(stock_picking,self)._prepare_invoice_line(cr, uid, group, picking, move_line, invoice_id, invoice_vals, context)
        #intervertir les valeurs des qty et unit pour avant de créer la invoice line
        res['qty_uos2'] = move_line.product_qty
        res['uos_id2'] = move_line.product_uom.id
        res['quantity'] = move_line.qty_uos2
 #       res['product_uos_qty'] = order_line.qty_uos2
#        res['product_uom'] = order_line.uos_id2.id
        res['uos_id'] = move_line.uos_id2.id
        return res
        

class stock_move(osv.osv):
    _name = 'stock.move'
    _inherit = 'stock.move'  
    
    _columns = {
        
        'qty_uos2':fields.float(
            string='Quantité (UdA)',
            digits_compute=dp.get_precision('Product UoM'),
            states={'draft': [('readonly', False)]}
        ),
        'uos_id2': fields.many2one('product.uom', u'Unité Achat'),
        }
