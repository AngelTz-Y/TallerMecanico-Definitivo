from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib import messages
from django.core.paginator import Paginator
from django.forms import *
from django.db import transaction
from .models import *
from .forms import *
from django.urls import reverse
from django.utils.crypto import get_random_string
from .decoradores import role_required  # Importa el decorador personalizado
from django.contrib.messages import get_messages
from .login_requerit import *

# Vista para la página de inicio (sin restricciones)
def inicio_view(request):
    return render(request, "inicio.html")

# Vista de registro (sin restricciones)
# Vista de registro
def registro_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        confirm_password = request.POST.get("repassword")
        role = request.POST.get("role", "cliente")  # Si el rol es estático, se asigna "cliente"

        # Validar si el nombre de usuario ya está en uso
        if Registro.objects.filter(username=username).exists():
            messages.error(request, "El nombre de usuario ya está en uso.")
            return redirect("registro")

        # Validar que las contraseñas coincidan
        if password != confirm_password:
            messages.error(request, "Las contraseñas no coinciden.")
            return redirect("registro")

        # Validar longitud de la contraseña
        if len(password) < 6:
            messages.error(request, "La contraseña debe tener al menos 6 caracteres.")
            return redirect("registro")

        try:
            # Crear el nuevo usuario
            registro = Registro(username=username, password=password, role=role)
            registro.save()
            messages.success(request, "Registro exitoso. Puedes iniciar sesión.")
            return redirect("registro")
        except Exception as e:
            # Manejo de excepciones genéricas al guardar
            print("Error al guardar el registro:", e)
            messages.error(request, "Ocurrió un error al intentar registrarte. Inténtalo nuevamente.")
            return redirect("registro")

    # Limpiar mensajes irrelevantes
    storage = get_messages(request)
    for _ in storage:
        pass

    # Renderizar el formulario de registro
    return render(request, "registro.html")

# Vista de inicio de sesión
def login_view(request):
    if request.method == 'POST':
        step = request.POST.get('step')

        # Paso 1: Validar usuario y contraseña
        if step == 'step1':
            username = request.POST.get('username')
            password = request.POST.get('password')

            try:
                # Validar credenciales básicas en el modelo Registro
                user = Registro.objects.get(username=username, password=password)

                # Determinar el rol del usuario
                if user.role == 'admin':
                    return render(request, 'auth/login.html', {
                        'role': 'admin',
                        'username': username,
                        'password': password,
                    })
                elif user.role == 'mecanico':
                    return render(request, 'auth/login.html', {
                        'role': 'mecanico',
                        'username': username,
                        'password': password,
                    })
                elif user.role == 'cliente':
                    # Autenticación exitosa para clientes
                    request.session['user_id'] = user.id
                    request.session['role'] = user.role
                    return redirect('cliente_panel')  # Redirige al panel del cliente
                else:
                    # Si el rol no es reconocido
                    messages.error(request, "Rol no reconocido.")
                    return render(request, 'auth/login.html')

            except Registro.DoesNotExist:
                messages.error(request, "Usuario o contraseña incorrectos.")
                return render(request, 'auth/login.html')

        # Paso 2: Validar clave única o PIN según el rol
        elif step == 'step2':
            username = request.POST.get('username')
            password = request.POST.get('password')

            try:
                # Recuperar el usuario para continuar la validación
                user = Registro.objects.get(username=username, password=password)

                # Validar clave única para administradores
                if user.role == 'admin':
                    clave_unica = request.POST.get('clave_unica')
                    admin = Administrador.objects.get(registro=user)
                    if clave_unica != admin.clave_unica:
                        messages.error(request, "Clave Única incorrecta.")
                        return render(request, 'auth/login.html', {
                            'role': 'admin',
                            'username': username,
                            'password': password,
                        })

                    # Autenticación exitosa para administrador
                    request.session['user_id'] = user.id
                    request.session['role'] = user.role
                    return redirect('admin_panel')  # Cambia esto a tu vista del panel de administrador

                # Validar PIN para mecánicos
                elif user.role == 'mecanico':
                    pin = request.POST.get('pin')
                    mecanico = Mecanico.objects.get(registro=user)  # Supone relación OneToOne o ForeignKey
                    if pin != mecanico.pin:
                        messages.error(request, "PIN incorrecto.")
                        return render(request, 'auth/login.html', {
                            'role': 'mecanico',
                            'username': username,
                            'password': password,
                        })

                    # Autenticación exitosa para mecánico
                    request.session['user_id'] = user.id
                    request.session['role'] = user.role
                    return redirect('dashboard_mecanico')  # Cambia esto a tu vista del panel de mecánico

            except Registro.DoesNotExist:
                messages.error(request, "Credenciales inválidas.")
            except Administrador.DoesNotExist:
                messages.error(request, "Administrador no encontrado.")
            except Mecanico.DoesNotExist:
                messages.error(request, "Mecánico no encontrado.")
            except Exception as e:
                messages.error(request, f"Error inesperado: {str(e)}")

    # Renderizar el formulario inicial si no hay POST
    return render(request, 'auth/login.html')

# Vista para logout (sin restricciones)
def logout_view(request):
    # Limpia los datos de la sesión
    request.session.flush()
    return redirect('login')


# Vista de perfil (acceso solo para clientes)
@role_required("cliente")
def perfil_view(request):
    user_id = request.session.get('user_id')
    try:
        user = Registro.objects.get(id=user_id)
    except Registro.DoesNotExist:
        messages.error(request, "Usuario no encontrado.")
        return redirect("inicio")
    
    # Obtener cliente relacionado
    cliente = Cliente.objects.filter(registro=user).first()
    login_data = Login.objects.filter(user=user).first()

    # Contexto para la plantilla
    context = {
        "user": user,
        "login_data": login_data,
        "cliente": cliente,
    }
    return render(request, "perfil.html", context)

# Panel de administración (acceso solo para administradores)
@role_required("admin")
def admin_panel(request):
    user_id = request.session.get('user_id')
    user = Registro.objects.get(id=user_id)
    context = {"username": user.username}
    return render(request, "InterfazAdministrador/admin_panel.html", context)

# Agregar mecánico (acceso solo para administradores)
@role_required("admin")
def agregar_mecanico(request):
    try:
        user_id = request.session.get('user_id')
        # Verifica si el usuario logeado es un administrador
        registro_admin = Registro.objects.get(id=user_id, role='admin')
        username_admin = registro_admin.username
    except Registro.DoesNotExist:
        messages.error(request, "Administrador no encontrado o no autorizado.")
        return redirect("inicio")

    if request.method == "POST":
        username = request.POST.get("username").strip()
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")
        rut = request.POST.get("rut").strip()
        nombre = request.POST.get("nombre").strip()
        apellido = request.POST.get("apellido").strip()
        fecha_nacimiento = request.POST.get("fecha_nacimiento")
        genero = request.POST.get("genero")
        email = request.POST.get("email").strip()
        pin = request.POST.get("pin").strip()

        # Validaciones
        if not all([username, password, confirm_password, rut, nombre, apellido, fecha_nacimiento, genero, email, pin]):
            messages.error(request, "Todos los campos son obligatorios.")
            return render(request, "InterfazAdministrador/agregar_mecanico.html", {"username": username_admin})

        if password != confirm_password:
            messages.error(request, "Las contraseñas no coinciden.")
            return render(request, "InterfazAdministrador/agregar_mecanico.html", {"username": username_admin})

        if Registro.objects.filter(username=username).exists():
            messages.error(request, "El nombre de usuario ya está en uso.")
            return render(request, "InterfazAdministrador/agregar_mecanico.html", {"username": username_admin})

        if Mecanico.objects.filter(rut=rut).exists():
            messages.error(request, "Ya existe un mecánico con ese RUT.")
            return render(request, "InterfazAdministrador/agregar_mecanico.html", {"username": username_admin})

        if Mecanico.objects.filter(pin=pin).exists():
            messages.error(request, "Ya existe un mecánico con ese PIN.")
            return render(request, "InterfazAdministrador/agregar_mecanico.html", {"username": username_admin})

        try:
            # Operación atómica para garantizar que ambas tablas se actualicen juntas
            with transaction.atomic():
                # Crear el registro en la tabla `Registro`
                registro = Registro.objects.create(
                    username=username,
                    password=password,  # Nota: Considera encriptar las contraseñas para mayor seguridad
                    role="mecanico",
                    registro=timezone.now()
                )
                # Crear el registro en la tabla `Mecanico`
                Mecanico.objects.create(
                    rut=rut,
                    nombre=nombre,
                    apellido=apellido,
                    fecha_nacimiento=fecha_nacimiento,
                    genero=genero,
                    email=email,
                    pin=pin,
                    registro=registro  # Relación con la tabla `Registro`
                )
            messages.success(request, "Mecánico agregado exitosamente.")
            return redirect("listar_mecanicos")
        except Exception as e:
            messages.error(request, f"Error al agregar el mecánico: {e}")
            return render(request, "InterfazAdministrador/agregar_mecanico.html", {"username": username_admin})

    return render(request, "InterfazAdministrador/agregar_mecanico.html", {"username": username_admin})

# Listar mecánicos (acceso solo para administradores)
@role_required("admin")
def listar_mecanicos(request):
    mecanicos = Mecanico.objects.all()
    return render(request, "InterfazAdministrador/listar_mecanicos.html", {"mecanicos": mecanicos})

# Modificar mecánico (acceso solo para administradores)
@role_required("admin")
def modificar_mecanico(request, mecanico_id):
    mecanico = get_object_or_404(Mecanico, rut=mecanico_id)
    if request.method == "POST":
        mecanico.nombre = request.POST.get("nombre")
        mecanico.apellido = request.POST.get("apellido")
        mecanico.fecha_nacimiento = request.POST.get("fecha_nacimiento")
        mecanico.genero = request.POST.get("genero")
        mecanico.email = request.POST.get("email")
        mecanico.pin = request.POST.get("pin")
        mecanico.save()
        messages.success(request, "Mecánico modificado exitosamente.")
        return redirect("listar_mecanicos")
    return render(request, "InterfazAdministrador/modificar_mecanico.html", {"mecanico": mecanico})

# Eliminar mecánico (acceso solo para administradores)
@role_required("admin")
def eliminar_mecanico(request, mecanico_id):
    mecanico = get_object_or_404(Mecanico, rut=mecanico_id)
    if mecanico.registro:
        registro_id = mecanico.registro.id
        mecanico.delete()
        registro = Registro.objects.filter(id=registro_id).first()
        if registro:
            registro.delete()
            messages.success(request, "Mecánico y su cuenta asociados han sido eliminados exitosamente.")
        else:
            messages.info(request, "Mecánico eliminado exitosamente, pero no se encontró una cuenta asociada para eliminar.")
    else:
        mecanico.delete()
        messages.success(request, "Mecánico eliminado exitosamente, no había cuenta asociada.")
    return redirect("listar_mecanicos")

# Registrar informe (acceso solo para mecánicos)
@role_required("mecanico")
def registrar_informe(request, trabajo_id):
    try:
        # Obtener el mecánico autenticado
        user_id = request.session.get("user_id")
        registro = Registro.objects.get(id=user_id)
        mecanico = registro.mecanico

        # Obtener el trabajo y verificar que pertenece al mecánico
        trabajo = get_object_or_404(Trabajo.objects.select_related('vehiculo__cliente'), id=trabajo_id, mecanico=mecanico)
        cliente = trabajo.vehiculo.cliente  # Cliente del vehículo asociado

        if request.method == "POST":
            descripcion = request.POST.get("descripcion")
            costo = request.POST.get("costo")

            if not descripcion or not costo:
                messages.error(request, "Todos los campos son obligatorios.")
            else:
                try:
                    Informe.objects.create(
                        mecanico=mecanico,
                        trabajo=trabajo,
                        cliente=cliente,
                        descripcion=descripcion,
                        costo=costo,
                        fecha_informe=timezone.now()
                    )
                    messages.success(request, "Informe registrado exitosamente.")
                    return redirect("listar_trabajos")
                except Exception as e:
                    messages.error(request, f"Error al registrar el informe: {e}")

        return render(request, "InterfazMecanico/registrar_informe.html", {
            "trabajo": trabajo,
            "cliente": cliente,
        })

    except Registro.DoesNotExist:
        messages.error(request, "No se encontró el perfil del mecánico.")
        return redirect("login")
    except Exception as e:
        messages.error(request, f"Error inesperado: {str(e)}")
        return redirect("listar_trabajos")
    
    

from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
import os
from .models import Trabajo

def descargar_informe_pdf(request, trabajo_id):
    # Obtener el trabajo y los informes asociados
    trabajo = get_object_or_404(Trabajo, id=trabajo_id)
    informes = trabajo.informes.all()

    # Calcular costos
    costo_total_informes = sum(float(informe.costo) for informe in informes)
    costo_total_trabajo = float(trabajo.costo_total_reparaciones)
    costo_total_general = costo_total_trabajo + costo_total_informes

    # Configurar la respuesta como PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="informe_trabajo_{trabajo.vehiculo.patente}.pdf"'

    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter
    left_margin = 50
    top_margin = height - 50
    bottom_margin = 50

    # Encabezado con logo y título
    logo_path = os.path.join(os.getcwd(), "static/logo.png")  # Ajusta la ruta del logo
    if os.path.exists(logo_path):
        p.drawImage(logo_path, left_margin, top_margin - 60, width=80, height=80, mask='auto')

    p.setFont("Helvetica-Bold", 20)
    p.setFillColor(colors.darkblue)
    p.drawCentredString(width / 2, top_margin - 20, "Informe Completo de Reparaciones")
    p.setFont("Helvetica", 12)
    p.setFillColor(colors.grey)
    p.drawCentredString(width / 2, top_margin - 40, "Auto Mechanics - Taller de Confianza")

    # Separador
    p.line(left_margin, top_margin - 70, width - left_margin, top_margin - 70)

    # Sección del Cliente
    y = top_margin - 90
    p.setFont("Helvetica-Bold", 12)
    p.setFillColor(colors.black)
    p.drawString(left_margin, y, "Información del Cliente")
    y -= 15
    p.setFont("Helvetica", 10)
    p.drawString(left_margin, y, f"Nombre: {trabajo.vehiculo.cliente.nombre} {trabajo.vehiculo.cliente.apellido}")
    p.drawString(left_margin, y - 15, f"Teléfono: {trabajo.vehiculo.cliente.telefono}")

    # Sección del Vehículo
    y -= 60
    p.setFont("Helvetica-Bold", 12)
    p.drawString(left_margin, y, "Detalles del Vehículo")
    y -= 15
    p.setFont("Helvetica", 10)
    p.drawString(left_margin, y, f"Marca: {trabajo.vehiculo.marca}")
    p.drawString(left_margin, y - 15, f"Modelo: {trabajo.vehiculo.modelo}")
    p.drawString(left_margin, y - 30, f"Patente: {trabajo.vehiculo.patente}")

    # Información del Trabajo
    y -= 60
    p.setFont("Helvetica-Bold", 12)
    p.drawString(left_margin, y, "Detalles del Trabajo")
    y -= 15
    p.setFont("Helvetica", 10)
    p.drawString(left_margin, y, f"Fecha de Ingreso: {trabajo.fecha_ingreso.strftime('%Y-%m-%d')}")
    p.drawString(left_margin, y - 15, f"Fecha de Entrega: {trabajo.fecha_entrega.strftime('%Y-%m-%d') if trabajo.fecha_entrega else 'No entregada'}")
    p.drawString(left_margin, y - 30, f"Estado: {trabajo.estado}")
    p.drawString(left_margin, y - 45, f"Costo Total del Trabajo: ${costo_total_trabajo:.2f}")

    # Tabla de Reparaciones
    y -= 80
    p.setFont("Helvetica-Bold", 12)
    p.drawString(left_margin, y, "Detalles de Reparaciones")
    y -= 15

    if informes.exists():
        repair_data = [["Fecha", "Descripción", "Costo"]]
        for informe in informes:
            repair_data.append([
                informe.fecha_informe.strftime('%Y-%m-%d'),
                informe.descripcion,
                f"${float(informe.costo):.2f}"
            ])

        repair_table = Table(repair_data, colWidths=[100, 300, 100])
        repair_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
        ]))
        repair_table.wrapOn(p, width, height)
        repair_table.drawOn(p, left_margin, y - (20 * len(repair_data)))
    else:
        p.setFont("Helvetica", 10)
        p.drawString(left_margin, y, "No hay reparaciones registradas para este trabajo.")

    # Resumen de costos
    y -= 60 + (20 * len(informes) if informes.exists() else 0)
    p.setFont("Helvetica-Bold", 12)
    p.drawString(left_margin, y, f"Costo Total General: ${costo_total_general:.2f}")

    # Footer
    p.setFont("Helvetica-Oblique", 10)
    p.setFillColor(colors.grey)
    p.drawCentredString(width / 2, bottom_margin / 2, "Auto Mechanics | Su taller de confianza | Tel: 123-456-789 | www.automechanics.com")

    p.showPage()
    p.save()
    return response



def detalle_trabajo(request, trabajo_id):
    # Obtener el trabajo específico
    trabajo = get_object_or_404(Trabajo, id=trabajo_id)
    informes = trabajo.informes.all()  # Reparaciones asociadas al trabajo
    
    # Preparar datos
    contexto = {
        'trabajo': trabajo,
        'informes': informes
    }
    return render(request, 'detalle_trabajo.html', contexto)


def modificar_trabajo(request, trabajo_id):
    # Obtener el trabajo por ID
    trabajo = get_object_or_404(Trabajo, id=trabajo_id)
    mecanico_actual = request.user.mecanico if hasattr(request.user, 'mecanico') else None

    if request.method == 'POST':
        # Pasamos el mecánico actual al formulario
        form = TrabajoForm(request.POST, instance=trabajo, mecanico=mecanico_actual)
        if form.is_valid():
            form.save()
            return redirect('detalle_trabajo', trabajo_id=trabajo.id)  # Redirección a la vista de detalle
    else:
        form = TrabajoForm(instance=trabajo, mecanico=mecanico_actual)

    return render(request, 'modificar_trabajo.html', {'form': form, 'trabajo': trabajo})


def modificar_informe(request, informe_id):
    informe = get_object_or_404(Informe, id=informe_id)  # Obtiene el informe específico

    if request.method == "POST":
        form = InformeForm(request.POST, instance=informe)  # Actualiza los datos
        if form.is_valid():
            form.save()
            messages.success(request, "El informe ha sido modificado correctamente.")
            return redirect(reverse('detalle_trabajo', args=[informe.trabajo.id]))  # Redirige a detalles del trabajo
    else:
        form = InformeForm(instance=informe)  # Carga datos existentes en el formulario

    return render(request, 'modificar_informe.html', {'form': form, 'informe': informe})


def eliminar_informe(request, informe_id):
    # Obtener el informe específico
    informe = get_object_or_404(Informe, id=informe_id)
    trabajo_id = informe.trabajo.id  # Guardar el ID del trabajo asociado

    # Eliminar el informe y verificar si es el último informe
    informe.delete()
    if not Informe.objects.filter(trabajo_id=trabajo_id).exists():
        # Si no hay más informes asociados, eliminamos el trabajo
        trabajo = get_object_or_404(Trabajo, id=trabajo_id)
        trabajo.delete()
        messages.success(request, "El informe y el trabajo asociado han sido eliminados correctamente.")
        return redirect('consultar_trabajos')  # Redirigir a la lista de trabajos

    messages.success(request, "El informe ha sido eliminado correctamente.")
    return redirect(reverse('consultar_trabajos', args=[trabajo_id]))



# Consultar histórico de reparaciones (acceso solo para clientes)
@role_required("admin")
def consultar_historico_reparaciones(request, patente):
    vehiculo = get_object_or_404(Vehiculo, patente=patente)
    reparaciones = Trabajo.objects.filter(vehiculo=vehiculo)
    return render(request, "consultar_historico_reparaciones.html", {"vehiculo": vehiculo, "reparaciones": reparaciones})

@login_required_custom
@role_required("mecanico")
def dashboard_mecanico(request):
    # Recupera los trabajos asignados al mecánico autenticado
    user_id = request.session.get('user_id')  # Obtén el usuario desde la sesión
    trabajos = Trabajo.objects.filter(mecanico__registro__id=user_id)

    return render(request, 'InterfazMecanico/mecanico_panel.html', {
        'username': request.user.username,
        'trabajos': trabajos,
    })

# Listar clientes (acceso solo para mecánicos)

def listar_clientes(request):
    try:
        # Obtener el perfil del usuario y su mecánico asociado
        user_id = request.session.get("user_id")
        registro = Registro.objects.get(id=user_id)
        mecanico = registro.mecanico  # Relacionado con el mecánico actual

        # Filtrar clientes a través de las citas donde esté asignado el mecánico
        clientes = Cliente.objects.filter(citas__mecanico=mecanico).distinct().order_by('nombre')

        # Paginación
        paginator = Paginator(clientes, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        # Contexto a la plantilla
        context = {'page_obj': page_obj}
        return render(request, 'InterfazMecanico/listar_clientes.html', context)

    except Registro.DoesNotExist:
        messages.error(request, "No se encontró el perfil del usuario.")
        return redirect("login")
    except Exception as e:
        messages.error(request, f"Error inesperado: {str(e)}")
        return redirect("listar_clientes")

# Panel de cliente (acceso solo para clientes)
@role_required("cliente")
def cliente_panel(request):
    user_id = request.session.get('user_id')
    try:
        registro = Registro.objects.get(id=user_id, role='cliente')
    except Registro.DoesNotExist:
        messages.error(request, "Usuario no encontrado o no autorizado.")
        return redirect('inicio')
    
    cliente = Cliente.objects.filter(registro=registro).first()
    
    if not cliente or not cliente.datos_completos:
        if request.method == 'POST':
            if not cliente:
                cliente = Cliente(registro=registro)
            cliente.rut = request.POST.get('rut')
            cliente.nombre = request.POST.get('nombre')
            cliente.apellido = request.POST.get('apellido')
            cliente.fecha_nacimiento = request.POST.get('fecha_nacimiento')
            cliente.genero = request.POST.get('genero')
            cliente.email = request.POST.get('email')
            cliente.telefono = request.POST.get('telefono')
            cliente.direccion = request.POST.get('direccion')
            cliente.datos_completos = True
            try:
                with transaction.atomic():
                    cliente.save()
                messages.success(request, "Datos personales completados exitosamente.")
                return redirect('cliente_panel')
            except Exception as e:
                messages.error(request, f"Error al guardar los datos: {e}")
        else:
            # Renderizar la página del panel con el formulario para completar los datos
            return render(request, 'InterfazCliente/cliente_panel.html', {
                'username': registro.username,
                'cliente': cliente,
                'completar_datos': True,  # Indicador para mostrar el formulario en la plantilla
            })
    
    # Si los datos están completos, mostrar el contenido principal del panel
    return render(request, 'InterfazCliente/cliente_panel.html', {
        'username': registro.username,
        'cliente': cliente,
        'completar_datos': False,  # No se necesita completar datos
    })



@role_required("mecanico")
def agregar_vehiculo(request):
    try:
        # Obtener el mecánico asociado al usuario actual
        user_id = request.session.get("user_id")
        registro = Registro.objects.get(id=user_id)
        mecanico = registro.mecanico

        # Filtrar solo los clientes asignados al mecánico a través de las citas
        clientes = Cliente.objects.filter(citas__mecanico=mecanico).distinct()

        if request.method == 'POST':
            patente = request.POST.get('patente')
            marca = request.POST.get('marca')
            modelo = request.POST.get('modelo')
            ano = request.POST.get('ano')
            cliente_id = request.POST.get('cliente')

            # Validar que todos los campos estén completos
            if not (patente and marca and modelo and ano and cliente_id):
                messages.error(request, "Todos los campos son obligatorios.")
                return redirect("agregar_vehiculo")

            try:
                # Validar que el cliente existe en la lista filtrada
                cliente = clientes.get(rut=cliente_id)
                
                # Crear el vehículo y asociarlo al mecánico actual
                Vehiculo.objects.create(
                    patente=patente,
                    marca=marca,
                    modelo=modelo,
                    ano=ano,
                    cliente=cliente,
                    mecanico=mecanico  # Asociar al mecánico actual
                )

                messages.success(request, "Vehículo agregado exitosamente.")
                return redirect("listar_vehiculos")
            except Cliente.DoesNotExist:
                messages.error(request, "El cliente seleccionado no existe o no está asignado a usted.")
            except Exception as e:
                messages.error(request, f"Error al agregar el vehículo: {e}")

        return render(request, "InterfazMecanico/Vehiculo/ingresar_vehiculo.html", {'clientes': clientes})

    except Registro.DoesNotExist:
        messages.error(request, "No se encontró el perfil del usuario.")
        return redirect("login")
    except Exception as e:
        messages.error(request, f"Error inesperado: {str(e)}")
        return redirect("agregar_vehiculo")




@role_required("mecanico")
def modificar_vehiculo(request, patente):
    # Obtener el vehículo a modificar o retornar 404 si no existe
    vehiculo = get_object_or_404(Vehiculo, patente=patente)

    if request.method == 'POST':
        # Capturar los datos enviados desde el formulario
        vehiculo.marca = request.POST.get('marca', '').strip()
        vehiculo.modelo = request.POST.get('modelo', '').strip()
        vehiculo.ano = request.POST.get('ano', '').strip()
        cliente_id = request.POST.get('cliente')

        # Validar que todos los campos sean completados
        if not (vehiculo.marca and vehiculo.modelo and vehiculo.ano and cliente_id):
            messages.error(request, "Todos los campos son obligatorios.")
            return redirect("modificar_vehiculo", patente=patente)

        try:
            # Validar si el cliente existe y asignarlo
            cliente = Cliente.objects.get(rut=cliente_id)
            vehiculo.cliente = cliente
            vehiculo.save()  # Guardar los cambios en la base de datos

            # Mostrar mensaje de éxito y redirigir al listado de vehículos
            messages.success(request, "Vehículo modificado exitosamente.")
            return redirect("listar_vehiculos")

        except Cliente.DoesNotExist:
            # Si el cliente no existe, mostrar un error
            messages.error(request, "El cliente seleccionado no existe.")
        except Exception as e:
            # Manejo de cualquier otro error
            messages.error(request, f"Error al modificar el vehículo: {e}")

    # Obtener la lista de clientes para mostrarla en el formulario
    clientes = Cliente.objects.all()

    # Renderizar el formulario con el vehículo y los clientes
    return render(request, "InterfazMecanico/Vehiculo/modificar_vehiculo.html", {
        'vehiculo': vehiculo,
        'clientes': clientes
    })




@role_required("mecanico")
def eliminar_vehiculo(request, patente):
    vehiculo = get_object_or_404(Vehiculo, patente=patente)

    if request.method == 'POST':
        vehiculo.delete()
        messages.success(request, "Vehículo eliminado exitosamente.")
        return redirect("listar_vehiculos")


@role_required("mecanico")
def listar_vehiculos(request):
    try:
        # Obtener el mecánico autenticado
        user_id = request.session.get("user_id")
        if not user_id:
            messages.error(request, "Usuario no autenticado. Por favor, inicie sesión.")
            return redirect("login")
        
        registro = Registro.objects.get(id=user_id)
        mecanico = registro.mecanico

        # Filtrar vehículos asociados a clientes que tengan citas con este mecánico
        vehiculos = Vehiculo.objects.filter(cliente__citas__mecanico=mecanico).distinct()

        # Paginación
        paginator = Paginator(vehiculos, 10)  # Mostrar 10 vehículos por página
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        # Renderizar plantilla
        return render(request, 'InterfazMecanico/Vehiculo/listar_vehiculo.html', {
            'page_obj': page_obj, 
            'vehiculos': page_obj.object_list
        })

    except Registro.DoesNotExist:
        messages.error(request, "No se encontró el perfil del mecánico. Por favor, contacte al administrador.")
        return redirect("login")
    except Exception as e:
        messages.error(request, f"Ocurrió un error inesperado: {str(e)}")
        return redirect("listar_vehiculos")



# App_TallerMecanico/views.py

from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from .forms import TrabajoForm
from .models import Trabajo
from .decoradores import role_required  # Asegúrate de que el decorador soporte múltiples roles


@role_required("mecanico")
def ingresar_trabajo(request):
    try:
        # Obtener el mecánico autenticado
        user_id = request.session.get("user_id")
        registro = Registro.objects.get(id=user_id)
        mecanico = registro.mecanico

        # Filtrar los vehículos creados por el mecánico actual y sus clientes asociados
        vehiculos = Vehiculo.objects.filter(
            cliente__citas__mecanico=mecanico
        ).distinct()

        if request.method == 'POST':
            form = TrabajoForm(request.POST)

            # Limitar la selección del formulario a vehículos filtrados
            form.fields['vehiculo'].queryset = vehiculos

            if form.is_valid():
                vehiculo = form.cleaned_data.get('vehiculo')
                estado = form.cleaned_data.get('estado')

                # Estados activos a verificar
                estados_activos = ['pendiente', 'en_progreso']

                # Validar si existe un trabajo activo para el vehículo
                existe_trabajo = Trabajo.objects.filter(
                    vehiculo=vehiculo,
                    estado__in=estados_activos
                ).exists()

                if existe_trabajo:
                    messages.error(request, "Ya existe un trabajo activo para este vehículo.")
                else:
                    try:
                        with transaction.atomic():
                            trabajo = form.save(commit=False)
                            trabajo.mecanico = mecanico  # Asignar el mecánico actual al trabajo
                            trabajo.save()
                        messages.success(request, "Trabajo ingresado exitosamente.")
                        return redirect('dashboard_mecanico')
                    except Exception as e:
                        messages.error(request, f"Error al ingresar el trabajo: {e}")
            else:
                messages.error(request, "Por favor, corrige los errores en el formulario.")
        else:
            form = TrabajoForm()
            # Limitar la selección del formulario a vehículos filtrados
            form.fields['vehiculo'].queryset = vehiculos

        return render(request, 'InterfazMecanico/Trabajo/ingresar_trabajo.html', {
            'form': form
        })

    except Registro.DoesNotExist:
        messages.error(request, "No se encontró el perfil del mecánico.")
        return redirect("login")
    except Exception as e:
        messages.error(request, f"Error inesperado: {e}")
        return redirect("ingresar_trabajo")


from django.db.models import Sum
from django.shortcuts import render

def consultar_trabajos(request):
    trabajos = Trabajo.objects.all()  # Obtiene todos los trabajos inicialmente

    # Captura los parámetros de filtro enviados desde el formulario
    vehiculo = request.GET.get('vehiculo')
    estado = request.GET.get('estado')
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')

    # Filtra por vehículo si se proporciona
    if vehiculo:
        trabajos = trabajos.filter(vehiculo__patente__icontains=vehiculo)

    # Filtra por estado si se proporciona
    if estado:
        trabajos = trabajos.filter(estado__icontains=estado)

    # Filtra por rango de fechas si se proporciona
    if fecha_inicio:
        trabajos = trabajos.filter(fecha_ingreso__date__gte=fecha_inicio)
    if fecha_fin:
        trabajos = trabajos.filter(fecha_ingreso__date__lte=fecha_fin)

    # Agregar el total de reparaciones para cada trabajo
    for trabajo in trabajos:
        trabajo.total_reparaciones = trabajo.informes.aggregate(total=Sum('costo'))['total'] or 0.00

    # Paginación
    paginator = Paginator(trabajos, 10)  # Mostrar 10 trabajos por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Renderiza la plantilla con los trabajos filtrados y la paginación
    return render(request, 'InterfazMecanico/Trabajo/consultar_trabajo.html', {
        'page_obj': page_obj,
        'trabajos': page_obj.object_list,  # Los trabajos en la página actual
        'vehiculo': vehiculo,
        'estado': estado,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
    })
    
    
def registrar_reparaciones(request, trabajo_id):
    # Obtener el trabajo o lanzar un 404 si no existe
    trabajo = get_object_or_404(Trabajo, id=trabajo_id)
    
    if request.method == 'POST':
        form = InformeForm(request.POST)
        if form.is_valid():
            try:
                # Iniciar una transacción para garantizar la integridad de los datos
                with transaction.atomic():
                    # Crear la reparación sin guardarla todavía
                    reparacion = form.save(commit=False)
                    reparacion.trabajo = trabajo
                    reparacion.mecanico = trabajo.mecanico
                    
                    # Verificar si todos los campos requeridos están llenos
                    if not reparacion.descripcion or reparacion.costo is None:
                        raise ValueError("Todos los campos de la reparación deben estar completos.")
                    
                    # Guardar la reparación en la base de datos
                    reparacion.save()
                    
                    # Actualizar el costo total del trabajo
                    trabajo.costo_total_reparaciones += reparacion.costo
                    trabajo.save()
                    
                    messages.success(request, "Reparación registrada exitosamente.")
                    return redirect('registrar_reparaciones', trabajo_id=trabajo.id)
            except Exception as e:
                messages.error(request, f"Error al registrar la reparación: {e}")
        else:
            messages.error(request, "Por favor, corrige los errores en el formulario.")
    else:
        form = InformeForm()
    
    # Obtener todas las reparaciones relacionadas con el trabajo, ordenadas por fecha
    reparaciones = trabajo.informes.all().order_by('-fecha_informe')
    
    # Configuración de la paginación
    paginator = Paginator(reparaciones, 5)  # Mostrar 5 reparaciones por página
    page_number = request.GET.get('page')
    reparaciones_paginadas = paginator.get_page(page_number)
    
    context = {
        'trabajo': trabajo,
        'form': form,
        'reparaciones': reparaciones_paginadas,
    }
    
    return render(request, 'InterfazMecanico/registrar_reparaciones.html', context)




def detalles_reparaciones(request, trabajo_id):
    trabajo = get_object_or_404(Trabajo, id=trabajo_id)
    trabajos = Trabajo.objects.filter(mecanico=trabajo.mecanico).order_by('fecha_ingreso')

    if request.method == "POST":
        trabajo_id_seleccionado = request.POST.get('trabajo_id')
        descripcion = request.POST.get('descripcion')
        costo = request.POST.get('costo')

        if trabajo_id_seleccionado and descripcion and costo:
            trabajo_seleccionado = get_object_or_404(Trabajo, id=trabajo_id_seleccionado)
            Informe.objects.create(
                mecanico=trabajo_seleccionado.mecanico,
                trabajo=trabajo_seleccionado,
                descripcion=descripcion,
                costo=costo,
                fecha_informe=timezone.now()
            )
            # Actualizar el costo total del trabajo
            trabajo_seleccionado.costo_total_reparaciones += float(costo)
            trabajo_seleccionado.save()

            messages.success(request, "Reparación registrada exitosamente.")
            return redirect('trabajos_detalles_reparaciones', trabajo_id=trabajo_id)

    reparaciones = trabajo.informes.all().order_by('-fecha_informe')
    return render(request, 'InterfazMecanico/detalles_reparaciones.html', {
        'trabajo': trabajo,
        'trabajos': trabajos,
        'reparaciones': reparaciones,
    })
    

def reset_password(request, rut):
    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if new_password != confirm_password:
            messages.error(request, "Las contraseñas no coinciden.")
            return redirect(reverse('listar_mecanicos'))

        mecanico = get_object_or_404(Mecanico, rut=rut)
        registro = mecanico.registro
        registro.password = new_password  # Ensure password encryption in production
        registro.save()

        messages.success(request, f"Contraseña restablecida exitosamente para el mecánico con RUT {rut}.")
        return redirect('listar_mecanicos')
    
    
    
from django.shortcuts import render, redirect
from .forms import CitaForm


@login_required_custom
def solicitar_cita(request):
    if request.method == 'POST':
        form = CitaForm(request.POST)
        if form.is_valid():
            cita = form.save(commit=False)  # No guardes todavía
            # Asocia la cita al cliente autenticado
            registro = get_object_or_404(Registro, id=request.session.get('user_id'))
            cliente = get_object_or_404(Cliente, registro=registro)
            cita.cliente = cliente
            cita.save()  # Ahora guarda la cita con el cliente asignado
            return redirect('cita_exitosa')  # Cambia a una página de éxito
    else:
        form = CitaForm()

    return render(request, 'InterfazCliente/Funciones/solicitar_cita.html', {'form': form})

def cita_exitosa(request):
    return render(request, 'InterfazCliente/Funciones/cita_exitosa.html')  # Crea una plantilla para el éxito




    
@login_required_custom
@role_required("mecanico")
def asignar_cita(request, cita_id):
    try:
        # Verificar si el usuario tiene un perfil de mecánico
        user_id = request.session.get("user_id")
        registro = Registro.objects.get(id=user_id)
        mecanico = registro.mecanico  # Obtener el mecánico relacionado

        # Obtener la cita específica
        cita = get_object_or_404(Cita, id=cita_id)

        # Verificar si la cita ya tiene un mecánico asignado
        if cita.mecanico:
            messages.error(request, "Esta cita ya está asignada a otro mecánico.")
            return redirect("mis_citas")

        # Asignar el mecánico a la cita
        cita.mecanico = mecanico
        cita.save()

        messages.success(request, "Cita asignada exitosamente.")
        return redirect("mis_citas")

    except Registro.DoesNotExist:
        messages.error(request, "No se encontró el perfil del usuario.")
        return redirect("login")
    except Exception as e:
        messages.error(request, f"Error inesperado: {str(e)}")
        return redirect("mis_citas")
    
@login_required_custom
@role_required("mecanico")
def citas_asignadas_mecanico(request):
    try:
        # Obtener el perfil del usuario y su mecánico asociado
        user_id = request.session.get("user_id")
        registro = Registro.objects.get(id=user_id)
        mecanico = registro.mecanico

        # Filtrar las citas asignadas a este mecánico
        citas = Cita.objects.filter(mecanico=mecanico)

        return render(request, "citas_asignadas.html", {"citas": citas})

    except Registro.DoesNotExist:
        messages.error(request, "No se encontró el perfil del usuario.")
        return redirect("login")
    except Exception as e:
        messages.error(request, f"Error inesperado: {str(e)}")
        return redirect("citas_asignadas_mecanico")

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Cita

@login_required
def lista_citas(request):
    citas = Cita.objects.filter(mecanico__isnull=True).order_by('fecha', 'hora')  # Solo citas sin mecánico
    return render(request, 'InterfazMecanico/Trabajo/lista_citas.html', {'citas': citas})

@login_required
def tomar_cita(request, cita_id):
    cita = Cita.objects.get(id=cita_id)
    if cita.mecanico is None:  # Verifica que la cita no esté asignada
        cita.mecanico = request.user
        cita.save()
    return redirect('lista_citas')


@login_required_custom
def mis_citas(request):
    try:
        # Obtiene todas las citas sin filtrar por mecánico
        citas = Cita.objects.all().order_by('fecha', 'hora')  # Ordena por fecha y hora
    except Exception as e:
        citas = []  # Si ocurre algún error, devuelve una lista vacía

    return render(request, 'InterfazMecanico/Trabajo/mis_citas.html', {'citas': citas})



def estado_vehiculo(request):
    return render(request, 'InterfazCliente/Funciones/estado_vehiculo.html')

def solicitud_trabajo(request):
    return render(request, 'InterfazCliente/Funciones/solicitud_trabajo.html')

def progreso_vehiculo(request):
    return render(request, 'InterfazCliente/Funciones/progreso_vehiculo.html')

def ver_estado(request):
    return render(request, 'InterfazCliente/Funciones/ver_estado.html')

def informacion_mecanico(request):
    return render(request, 'InterfazCliente/Funciones/informacion_mecanico.html')

def trabajo_tecnico_taller(request):
    # Datos de ejemplo (estos podrían provenir de la base de datos
    trabajo = {
        'vehiculo': 'Toyota Corolla',
        'marca': 'Toyota',
        'modelo': 'Corolla',
        'anio': 2020,
        'fecha_entrada': '2024-12-05',
        'fecha_salida': '2024-12-10',
        'servicios': [
            'Cambio de aceite',
            'Revisión de frenos',
            'Alineación de ruedas'
        ],
        'piezas_reemplazadas': [
            'Filtro de aceite',
            'Pastillas de freno',
            'Aceite del motor'
        ],
        'descripcion': 'Se realizó un mantenimiento completo del motor y los frenos, además de alinear las ruedas para mejorar la conducción.',
        'costo_total': 200.00,
    }

    return render(request, 'InterfazCliente/Funciones/trabajo_tecnico_taller.html', {'trabajo': trabajo})



def metodo_pago(request):
    return render(request, 'InterfazCliente/Funciones/metodo_pago.html')
