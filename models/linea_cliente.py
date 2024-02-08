from odoo import models, fields, api

class GestionLineaCliente(models.Model):
    _name = 'gestion_visitas.linea_cliente'
    _description = 'Línea de Cliente'
    _rec_name = 'display_name'
    display_name = fields.Char(string="Display Name", compute="get_display_name", store=True)

    name = fields.Char(string="Línea", required=True)

    @api.depends('name')
    def get_display_name(self):
        for linea in self:
            display_name = linea.name
            linea.display_name = display_name