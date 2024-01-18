from odoo import models, fields, api

class Visita(models.Model):
    _name = 'gestion_visitas.visita'
    _inherit = 'mail.thread'
    _description = 'Registro de Visitas'
    _rec_name = "display_name"  # Apunta a el siguiente atributo
    display_name = fields.Char(string="Display Name", compute="get_display_name", store=True)

    # --- Estados ---
    estado = fields.Selection([
        ('finalizado', 'Finalizado'),
        ('planificado', 'Planificado'),
        ('en curso', 'En curso'),
        ('expirado', 'Expirado'),
        ('sin planificar', 'Sin Planificar')
    ], string='Estado', default='sin planificar', tracking=True)

    # --- Detalles Generales
    rutero_id = fields.Many2one('res.users', string='Rutero', readonly=True, required=True,
                                default=lambda self: self.env.user)

    contact_id = fields.Many2one('res.partner', string='Contacto', required=True,
                                 tracking=True, store=True)
    direccion_contacto = fields.Char(string='Dirección del Contacto', related='contact_id.street', readonly=True)
    motivo = fields.Selection([
        ('venta', 'Venta'),
        ('seguimiento', 'Seguimiento'),
        ('otro', 'Otro')
    ], string='Motivo de Visita', required=True, tracking=True)
    hora_programada = fields.Datetime(string='Fecha programada', tracking=True,
                                      store=True)

    # --- Detalles de la visita ---
    hora_inicio_visita = fields.Datetime(string='Hora de inicio Visita', tracking=True)
    hora_fin_visita = fields.Datetime(string='Hora de fin Visita', tracking=True)

    efectiva = fields.Boolean(string='Visita Efectiva', default=True, tracking=True)

    razon_no_venta = fields.Selection([
        ('precio', 'Precio'),
        ('competencia', 'Competencia'),
        ('no hay interès', 'No Hay Interés'),
        ('cliente no responde', 'Cliente No Responde'),
        ('re-agendar', 'Re-Agendar'),
        ('otro', 'Otro')
    ], string='Razón de no Efectiva', tracking=True)
    descripcion_no_venta = fields.Text(string='Descripción de No Venta', tracking=True)
    visit_images = fields.Many2many('ir.attachment', string='Carga de archivos', tracking=True)
    observaciones = fields.Text(string='Observaciones')
    # En caso de Re-Agendar
    descripcion_motivo_reagendado = fields.Text(string='Descripcion de Motivo de Re-Agenda', tracking=True)
    nueva_fecha_programada = fields.Datetime(string='Nueva Fecha Programada')

    @api.onchange('efectiva')
    def _onchange_efectiva(self):
        if not self.efectiva:
            self.razon_no_venta = False
            self.descripcion_no_venta = False

    @api.onchange('visit_images')
    def _onchange_visit_images(self):
        max_attachments = 5
        if len(self.visit_images) > max_attachments:
            warning_msg = {
                'title': 'Warning',
                'message': f'Solo puedes seleccionar {max_attachments} archivos.'
            }
            return {'warning': warning_msg}

    def action_iniciar_visita(self):
        for visita in self:
            visita.write({
                'estado': 'en curso',
                'hora_inicio_visita': fields.Datetime.now(),
            })
        return True

    def action_terminar_visita(self):
        for visita in self:
            visita.write({
                'estado': 'finalizado',
                'hora_fin_visita': fields.Datetime.now(),
            })
            if visita.razon_no_venta == 're-agendar':
                nueva_fecha_programada = visita.nueva_fecha_programada
                if nueva_fecha_programada:
                    # Crea una nueva visita programada para la fecha especificada
                    nueva_visita_vals = {
                        'estado': 'planificado',
                        'rutero_id': visita.rutero_id.id,
                        'contact_id': visita.contact_id.id,
                        'direccion_contacto': visita.direccion_contacto,
                        'hora_programada': nueva_fecha_programada,
                        'motivo': visita.motivo,
                    }
                    self.env['gestion_visitas.visita'].create(nueva_visita_vals)
        return True

    @api.model
    def create(self, vals):
        vals['estado'] = 'planificado'
        return super(Visita, self).create(vals)

    @api.depends('contact_id', 'estado')
    def get_display_name(self):
        for visita in self:
            display_name = f"{visita.contact_id.name if visita.contact_id.name else 'Nueva Visita'} - {visita.estado}"
            visita.display_name = display_name
