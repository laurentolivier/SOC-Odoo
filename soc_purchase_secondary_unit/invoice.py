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

class acccount_invoice_line(osv.osv):
    _name = 'account.invoice.line'
    _inherit = 'account.invoice.line'

       
    _columns = {
        'qty_uos2':fields.float(
            string='Quantité (UdS)',
            digits_compute=dp.get_precision('Product UoM'),
            states={'draft': [('readonly', False)]}
        ),
        'uos_id2': fields.many2one('product.uom', u'Unité de stock'),
    }
