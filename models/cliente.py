from odoo import models, fields, api
from odoo.exceptions import ValidationError

class Cliente(models.Model):
    _name = 'gestion_visitas.cliente'
    _inherit = 'mail.thread'
    _description = 'Cliente para Gestion de Visitas'
    _rec_name = "display_name"  # Apunta a el siguiente atributo
    display_name = fields.Char(string="Display Name", compute="get_display_name", store=True)

    rutero_id = fields.Many2one('res.users', string='Rutero Asignado')
    cliente_id = fields.Many2one('res.partner', string='Cliente', required=True, ondelete='restrict')
    name = fields.Char(string="Nombre", related='cliente_id.name')
    avatar_image = fields.Binary(string="Avatar Image", related='cliente_id.avatar_128')
    linea = fields.Many2many('gestion_visitas.linea_cliente', string='Líneas del cliente', tracking=True)

    status = fields.Selection([
        ('0', 'Inactivo'),
        ('1', 'Activo')
    ], string='Status', default='1', help='Estado del cliente')

    @api.model_create_single
    def create(self, vals):
        if 'rutero_id' in vals and 'cliente_id' in vals and 'linea' in vals:
            domain = [
                ('rutero_id', '=', vals['rutero_id']),
                ('cliente_id', '=', vals['cliente_id']),
            ]
            existing_clientes = self.search_count(domain)
            if existing_clientes > 0:
                raise ValidationError(
                    f"El cliente ya está asignado a este rutero."
                )
        return super(Cliente, self).create(vals)

    @api.constrains('rutero_id', 'cliente_id', 'linea')
    def _check_unique_rutero_cliente(self):
        for cliente in self:
            print(cliente.rutero_id, cliente.cliente_id, cliente.linea)
            if cliente.rutero_id and cliente.cliente_id and cliente.linea:
                domain = [
                    ('rutero_id', '=', cliente.rutero_id.id),
                    ('cliente_id', '=', cliente.cliente_id.id),
                    ('id', '=', cliente.id)
                ]
                existing_clientes = self.search_count(domain)
                print(existing_clientes)
                if existing_clientes > 1:
                    raise ValidationError(
                        f"El cliente {cliente.cliente_id.name} ya está asignado a este rutero."
                    )

                # Revision de lineas de el cliente para evitar repetido de cliente - linea
                lineas_repetidas = []
                for linea in cliente.linea:
                    # Buscar otros clientes que tengan el mismo rutero y la misma línea
                    domain = [
                        ('cliente_id', '=', cliente.cliente_id.id),
                        ('rutero_id', '!=', cliente.rutero_id.id),
                        ('linea', 'in', linea.ids),

                    ]
                    existing_clientes = self.search(domain)
                    if existing_clientes:
                        lineas_repetidas.append(linea.name)

                if  len(lineas_repetidas) > 0:
                    lineas_repetidas_str = '-'.join(lineas_repetidas)
                    raise ValidationError(
                        f"El cliente {cliente.cliente_id.name} ya está asignado a un rutero con las siguientes lienas: {lineas_repetidas_str}."
                    )

    @api.model
    def cambiar_rutero_action(self, selected_clientes):

        # Abre la vista del formulario del asistente como pop-up
        return {
            'type': 'ir.actions.act_window',
            'name': 'Cambiar Rutero - Clientes seleccionados',
            'res_model': 'gestion_visitas.cliente.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('gestion_visitas.view_form_cambiar_rutero_wizard').id,
            'view_type': 'form',
            'target': 'new',
            'context': {
                'default_cliente_ids': [(6, 0, selected_clientes)],
            },
        }

    @api.depends('cliente_id', 'linea')
    def get_display_name(self):
        for cliente in self:
            lineas = ', '.join(cliente.linea.mapped('name')) if cliente.linea else 'Líneas no identificadas'
            display_name = f"{cliente.cliente_id.name if cliente.cliente_id.name else 'Nuevo Cliente'} - {lineas}"
            cliente.display_name = display_name

    @api.model
    def inactivar_cliente(self):
        print("Y ahora que?")
        for rec in self.browse(self.env.context['active_ids']):
            rec.write({'status': '0'})

