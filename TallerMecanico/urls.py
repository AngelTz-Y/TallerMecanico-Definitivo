from django.urls import path
from App_TallerMecanico.views import *

urlpatterns = [
    # Página principal
    path('', inicio_view, name='inicio'),

    # Registro y autenticación
    path('registro/', registro_view, name='registro'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),

    # Perfil y paneles
    path('perfil/', perfil_view, name='perfil'),
    path('cliente_panel/', cliente_panel, name='cliente_panel'),
    path('mecanico_panel/', dashboard_mecanico, name='dashboard_mecanico'),

    # Clientes (Mecánico)
    path('mecanico_panel/ingresar_cliente/', ingresar_cliente, name='ingresar_cliente'),
    path('mecanico_panel/listar_clientes/', listar_clientes, name='listar_cliente'),

    # Panel de administrador
    path('admin_panel/', admin_panel, name='admin_panel'),
    path('admin_panel/agregar_mecanico/', agregar_mecanico, name='agregar_mecanico'),
    path('admin_panel/listar_mecanicos/', listar_mecanicos, name='listar_mecanicos'),
    path('admin_panel/modificar_mecanico/<str:mecanico_id>/', modificar_mecanico, name='modificar_mecanico'),
    path('admin_panel/eliminar_mecanico/<str:mecanico_id>/', eliminar_mecanico, name='eliminar_mecanico'),

    # Trabajos e informes (Administrador)
    path('admin_panel/registrar_informe/<int:trabajo_id>/', registrar_informe, name='registrar_informe'),
    path('admin_panel/consultar_historico_reparaciones/<str:patente>/', consultar_historico_reparaciones, name='consultar_historico_reparaciones'),

    # Vehículos (Mecánico o Administrador)
    path('vehiculos/agregar/', agregar_vehiculo, name='ingresar_vehiculo'),
    path('vehiculos/modificar/<str:patente>/', modificar_vehiculo, name='modificar_vehiculo'),
    path('vehiculos/eliminar/<str:patente>/', eliminar_vehiculo, name='eliminar_vehiculo'),
    path('vehiculos/listar/', listar_vehiculos, name='listar_vehiculos'),

    # Trabajos (Mecánico)
    path('trabajos/agregar/', ingresar_trabajo, name='ingresar_trabajo'),
    path('trabajos/consultar/', consultar_trabajos, name='consultar_trabajos'),
    path('trabajos/<int:trabajo_id>/reparaciones/', registrar_reparaciones, name='registrar_reparaciones'),
    
    # Detalles de reparaciones (Mecánico)
    path('trabajos/<int:trabajo_id>/detalles/', detalles_reparaciones, name='trabajos_detalles_reparaciones'),
    path('reset_password/<str:rut>/', reset_password, name='reset_password'),
    path('solicitar_cita/', solicitar_cita, name='solicitar_cita'),
    path('estado_vehiculos/', estado_vehiculo, name='estado_vehiculos')
]
