{
    'name': 'Gestion de visitas',
    'version': '1.0',
    'author': 'Abel Murgas',
    'category': 'Ventas/Gestión de Clientes',
    'website': 'https://github.com/AbelMurgas',
    'summary': """Mejora la eficiencia de tus ruteros con la Gestión de Visitas para Ruteros. 
    Un módulo diseñado para ayudar a vendedores en calle a llevar un control detallado de sus visitas, clientes y actividades comerciales.
    Facilita la toma de decisiones estratégicas al proporcionar insights valiosos sobre la efectividad de las visitas y las oportunidades de venta.""",
    'license': 'LGPL-3',
    'description': """Optimiza la gestión y control de las visitas realizadas por los ruteros o vendedores en calle. 
    Este módulo facilita el seguimiento de clientes, eficacia en las visitas y registro detallado
    de la actividad comercial en terreno.""",
    'depends': ['mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/gestion_visitas_visita_views.xml',
        'views/gestion_visitas_cliente_views.xml',
'views/gestion_visitas_cliente_wizard.xml',
        'views/gestion_visitas_menu_views.xml',

    ],
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': True,
    'auto_install': True,
}
