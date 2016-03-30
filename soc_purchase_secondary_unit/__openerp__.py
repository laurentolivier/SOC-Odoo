# -*- encoding: utf-8 -*-
##############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see http://www.gnu.org/licenses/.
#
##############################################################################

{
    "name": "2nd Unit of Purchase",
    "version": "1.0",
    "summary": "SOC Purchase secondary unit",
    "depends": [
        "product",
        "purchase",
    ],
    "author": "SO Conseil",
             
    "category": "Purchase Management",
    "data": [
        "product_view.xml",
        "purchase_view.xml",
#        "invoice_view.xml",
    ],
    "installable": True,
}
