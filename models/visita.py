from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Visita(models.Model):
    _name = 'gestion_visitas.visita'
    _inherit = 'mail.thread'
    _description = 'Registro de Visitas'
    _rec_name = "display_name"
    display_name = fields.Char(string="Display Name", compute="get_display_name", store=True)

    # --- Estados ---

    estado = fields.Selection([
        ('sin planificar', 'Sin Planificar'),
        ('planificado', 'Planificado'),
        ('en curso', 'En Curso'),
        ('finalizado', 'Finalizado'),
        ('reagendado', 'Reagendado')
    ], string='Estado', default='sin planificar', tracking=True)

    # --- Detalles Generales ---
    rutero_id = fields.Many2one('res.users', string='Rutero', readonly=False, required=True,
                                default=lambda self: self.env.user)

    cliente_id = fields.Many2one('gestion_visitas.cliente', string='Cliente', required=True,
                                 domain="[('rutero_id','=',rutero_id)]")
    direccion_contacto = fields.Char(string='Dirección del Contacto', related='cliente_id.cliente_id.street',
                                     readonly=True)

    motivo = fields.Selection([
        ('venta', 'Venta'),
        ('seguimiento', 'Seguimiento'),
        ('otro', 'Otro')
    ], string='Motivo de Visita', required=True, tracking=True)
    hora_programada = fields.Datetime(string='Inicio Fecha programada', tracking=True, required=True,
                                      store=True)
    fecha_fin = fields.Datetime(string='Final Fecha progamada', tracking=True, required=True,
                                store=True)
    horas_programada = fields.Float(string='Horas de la visita', compute='_compute_horas_programada', store=True,
                                    readonly=True)
    # --- Smart Button ---
    oportunity_count = fields.Integer(compute='compute_count')

    def compute_count(self):
        for record in self:
            record.oportunity_count = self.env['crm.lead'].search_count(
                [('partner_id', '=', self.cliente_id.cliente_id.id)])

    # --- Detalles de la visita ---
    hora_inicio_visita = fields.Datetime(string='Hora de inicio Visita', tracking=True)
    hora_fin_visita = fields.Datetime(string='Hora de fin Visita', tracking=True)

    efectiva = fields.Boolean(string='Visita Efectiva', default=True, tracking=True)

    razon_no_venta = fields.Selection([
        ('precio', 'Precio'),
        ('competencia', 'Competencia'),
        ('no hay interès', 'No Hay Interés'),
        ('cliente no responde', 'Cliente No Responde'),
        ('otro', 'Otro')
    ], string='Razón de no Efectiva', tracking=True)
    descripcion_no_venta = fields.Text(string='Descripción de No Venta', tracking=True)
    visit_images = fields.Many2many('ir.attachment', string='Carga de archivos', tracking=True)
    observaciones = fields.Text(string='Observaciones')

    # --- En caso de Re-Agendar ---
    descripcion_motivo_reagendado = fields.Text(string='Descripcion de Motivo de Re-Agenda')
    nueva_fecha_programada = fields.Datetime(string='Nueva Fecha Programada')
    visita_id_reagendada = fields.Many2one('gestion_visitas.visita', string='Visita Reagendada', readonly=True)

    # --- Planificar nueva visita---
    fecha_nueva_planificada = fields.Datetime(string='Fecha Programada')
    visita_id_planificada = fields.Many2one('gestion_visitas.visita', string='Visita Reagendada', readonly=True)
    motivo_planificar = fields.Selection([
        ('venta', 'Venta'),
        ('seguimiento', 'Seguimiento'),
        ('otro', 'Otro')
    ], string='Motivo de Visita', default=lambda self: self.motivo, tracking=True)

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
                        'cliente_id': visita.cliente_id.cliente_id.id,
                        'direccion_contacto': visita.direccion_contacto,
                        'hora_programada': nueva_fecha_programada,
                        'motivo': visita.motivo,
                    }
                    self.env['gestion_visitas.visita'].create(nueva_visita_vals)

        return True

    def action_reagendar_visita(self):
        for visita in self:
            nueva_fecha_programada = visita.nueva_fecha_programada
            if nueva_fecha_programada:
                nueva_visita_vals = {
                    'estado': 'planificado',
                    'rutero_id': visita.rutero_id.id,
                    'cliente_id': visita.cliente_id.cliente_id.id,
                    'direccion_contacto': visita.direccion_contacto,
                    'hora_programada': nueva_fecha_programada,
                    'motivo': visita.motivo,
                }
                nueva_visita = self.env['gestion_visitas.visita'].create(nueva_visita_vals)

                visita.write({
                    'estado': 'reagendado',
                    'visita_id_reagendada': nueva_visita.id,
                })
            else:
                raise ValidationError('Se necesita la fecha programada para reagendar la visita.')
        return True

    def action_planificar_visita(self):
        for visita in self:
            fecha_nueva_planificada = visita.fecha_nueva_planificada
            if fecha_nueva_planificada:
                nueva_visita_vals = {
                    'estado': 'planificado',
                    'rutero_id': visita.rutero_id.id,
                    'cliente_id': visita.cliente_id.cliente_id.id,
                    'direccion_contacto': visita.direccion_contacto,
                    'hora_programada': fecha_nueva_planificada,
                    'motivo': visita.motivo_planificar,
                }
                nueva_visita = self.env['gestion_visitas.visita'].create(nueva_visita_vals)

                visita.write({
                    'visita_id_planificada': nueva_visita.id,

                })
            else:
                raise ValidationError('Se necesita la fecha programada para planificar la visita.')
        return True

    @api.model
    def create(self, vals):
        vals['estado'] = 'planificado'
        return super(Visita, self).create(vals)

    @api.depends('cliente_id', 'estado')
    def get_display_name(self):
        for visita in self:
            display_name = f"{visita.cliente_id.cliente_id.name if visita.cliente_id.cliente_id.name else 'Nueva Visita'} - {visita.estado}"
            visita.display_name = display_name

    def action_guardar_datos(self):
        for visita in self:
            visita.estado = 'planificado'
        return True

    def open_opportunities(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Oportunidades',
            'view_mode': 'tree,form',
            'res_model': 'crm.lead',
            'domain': [('partner_id', '=', self.cliente_id.cliente_id.id)],  # Ajusta el campo para el contacto adecuado
            'context': "{'create': False}"
        }

    @api.depends('hora_programada', 'fecha_fin')
    def _compute_horas_programada(self):
        for visita in self:
            if visita.hora_programada and visita.fecha_fin:
                hora_programada = fields.Datetime.from_string(visita.hora_programada)
                hora_fin = fields.Datetime.from_string(visita.fecha_fin)

                # Calcula la diferencia en horas y minutos
                diferencia = (hora_fin - hora_programada).total_seconds() / 3600.0

                visita.horas_programada = round(diferencia, 2)

    @api.constrains('fecha_fin')
    def _check_same_day(self):
        for visita in self:
            if visita.hora_programada and visita.fecha_fin:
                fecha_programada = fields.Datetime.from_string(visita.hora_programada).date()
                fecha_fin = fields.Datetime.from_string(visita.fecha_fin).date()

                if fecha_programada != fecha_fin:
                    raise ValidationError("La fecha de finalización debe ser la misma que la fecha programada.")

    @api.constrains('fecha_fin', 'hora_programada')
    def _check_end_time(self):
        for visita in self:
            if visita.hora_programada and visita.fecha_fin:
                hora_inicio = fields.Datetime.from_string(visita.hora_programada).time()
                hora_fin = fields.Datetime.from_string(visita.fecha_fin).time()

                if hora_fin <= hora_inicio:
                    raise ValidationError("La hora de finalización debe ser mayor que la hora de inicio.")
