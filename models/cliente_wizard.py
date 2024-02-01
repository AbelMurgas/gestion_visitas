from odoo import api, fields, models

class GestionVisitasClienteWizard(models.TransientModel):
    _name = 'gestion_visitas.cliente.wizard'
    _description = 'Cambiar Rutero Wizard'

    nuevo_rutero_id = fields.Many2one('res.users', string='Rutero Asignado')

    def action_cambiar_rutero(self):
        # Lógica para cambiar el rutero de los clientes seleccionados
        clientes = self.env['gestion_visitas.cliente'].browse(self._context.get('active_ids'))
        clientes.write({'rutero_id': self.nuevo_rutero_id.id})
        return {'type': 'ir.actions.act_window_close'}