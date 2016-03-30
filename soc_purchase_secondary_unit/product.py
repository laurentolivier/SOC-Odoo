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

from openerp.osv import fields, osv, expression
from openerp import tools
from openerp.tools.translate import _


class product_template(osv.osv):

    _name = 'product.template'
    _inherit = 'product.template'

    _columns = {
        'uom_po_id2': fields.many2one('product.uom', u'Unité d\'achat'), 
        }

    _defaults = {
        'uom_po_id2': 1,#TODO : use default _get_uom_id
    }
