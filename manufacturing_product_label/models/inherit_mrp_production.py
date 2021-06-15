from odoo import api, fields, models, _

class LabelGenerator(models.Model):
    _inherit = 'mrp.production'

    def mini_template_version(self, pname):
        rec = self.env['product.product'].search([('id','=',pname)])
        if "assist rail" in rec.display_name.lower():
            return True
        return False   