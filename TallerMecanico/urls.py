from django.urls import path
from App_TallerMecanico.views import *

urlpatterns = [
    # Página principal
    path('', inicio_view, name='inicio'),

    # Registro y autenticación
    path('registro/', registro_view, name='registro'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('trabajos/<int:trabajo_id>/descargar_informe/', descargar_informe_pdf, name='descargar_informe_pdf'),

    # Perfil y paneles
    path('perfil/', perfil_view, name='perfil'),
    path('cliente_panel/', cliente_panel, name='cliente_panel'),
    path('mecanico_panel/', dashboard_mecanico, name='dashboard_mecanico'),

    # Clientes (Mecánico)
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
    path('trabajos/<int:trabajo_id>/detalles/', detalles_reparaciones, name='trabajos_detalles_reparaciones'),

    # Citas (Cliente y Mecánico)
    path('solicitar-cita/', solicitar_cita, name='solicitar_cita'),
    path('cita-exitosa/', cita_exitosa, name='cita_exitosa'),
    path('citas/', lista_citas, name='lista_citas'),
    path('citas/tomar/<int:cita_id>/', tomar_cita, name='tomar_cita'),
    path('mis-citas/', mis_citas, name='mis_citas'),

    # Otras funcionalidades
    path('reset_password/<str:rut>/', reset_password, name='reset_password'),
    path('estado_vehiculo/', estado_vehiculo, name='estado_vehiculo'),
    path('trabajo_tecnico_taller/', trabajo_tecnico_taller, name='trabajo_tecnico_taller'),
    path('solicitud_trabajo/', solicitud_trabajo, name='solicitud_trabajo'),
    path('progreso_vehiculo/', progreso_vehiculo, name='progreso_vehiculo'),
    path('ver_estado/', ver_estado, name='ver_estado'),
    path('metodo_pago/', metodo_pago, name='metodo_pago'),
    path('informacion_mecanico/', informacion_mecanico, name='informacion_mecanico'),
    path('asignar_cita/<int:cita_id>/', asignar_cita, name='asignar_cita'),
    path("citas-asignadas/", citas_asignadas_mecanico, name="citas_asignadas_mecanico"),
    path('detalle_trabajo/<int:trabajo_id>/', detalle_trabajo, name='detalle_trabajo'),
    path('trabajo/modificar/<int:trabajo_id>/', modificar_trabajo, name='modificar_trabajo'),
    path('informe/eliminar/<int:informe_id>/', eliminar_informe, name='eliminar_informe'),
    path('informe/modificar/<int:informe_id>/', modificar_informe, name='modificar_informe'),


]
