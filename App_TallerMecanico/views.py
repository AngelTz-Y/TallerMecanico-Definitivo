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

# Vista para la página de inicio (sin restricciones)
def inicio_view(request):
    return render(request, "inicio.html")

# Vista de registro (sin restricciones)
def registro_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        confirm_password = request.POST.get("repassword")
        role = request.POST.get("role", "cliente")

        if Registro.objects.filter(username=username).exists():
            messages.error(request, "El nombre de usuario ya está en uso.")
            return redirect("registro")

        if password != confirm_password:
            messages.error(request, "Las contraseñas no coinciden.")
            return redirect("registro")

        try:
            registro = Registro(username=username, password=password, role=role)
            registro.save()
            messages.success(request, "Registro exitoso. Puedes iniciar sesión.")
            return redirect("login")
        except Exception as e:
            print("Error al guardar el registro:", e)
            messages.error(request, "Ocurrió un error al intentar registrarte. Inténtalo nuevamente.")
            return redirect("registro")

    return render(request, "registro.html")

# Vista de inicio de sesión (sin restricciones)
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        admin_key = request.POST.get("admin_key")

        user = Registro.objects.filter(username=username, password=password).first()
        if user:
            if user.role == 'admin' and username == 'admin':
                administrador = Administrador.objects.filter(nombre="Admin").first()
                if administrador and administrador.clave_unica == admin_key:
                    messages.success(request, "Inicio de sesión como Administrador.")
                    Login.objects.update_or_create(user=user, defaults={'ultima_conexion': timezone.now()})
                    request.session['user_id'] = user.id
                    return redirect("admin_panel")
                else:
                    messages.error(request, "Clave de seguridad incorrecta para Administrador.")
                    return redirect("login")

            elif user.role == 'mecanico':
                messages.success(request, "Inicio de sesión como Mecánico.")
                Login.objects.update_or_create(user=user, defaults={'ultima_conexion': timezone.now()})
                request.session['user_id'] = user.id
                return redirect("dashboard_mecanico")
            else:
                messages.success(request, "Inicio de sesión como Cliente.")
                Login.objects.update_or_create(user=user, defaults={'ultima_conexion': timezone.now()})
                request.session['user_id'] = user.id
                return redirect("cliente_panel")
        else:
            messages.error(request, "Credenciales incorrectas. Inténtalo de nuevo.")

    return render(request, "login.html")

# Vista para logout (sin restricciones)
def logout_view(request):
    user_id = request.session.get('user_id')
    if user_id:
        user = Registro.objects.get(id=user_id)
        Login.objects.filter(user=user).update(ultima_desconexion=timezone.now())
        del request.session['user_id']
    return redirect("inicio")

# Vista de perfil (acceso solo para clientes)
@role_required("cliente")
def perfil_view(request):
    user_id = request.session.get('user_id')
    user = Registro.objects.get(id=user_id)
    login_data = Login.objects.filter(user=user).first()
    context = {"user": user, "login_data": login_data}
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
            with transaction.atomic():
                registro = Registro.objects.create(
                    username=username,
                    password=password,  # Almacena la contraseña sin encriptar
                    role="mecanico",
                    registro=timezone.now()
                )
                Mecanico.objects.create(
                    rut=rut,
                    nombre=nombre,
                    apellido=apellido,
                    fecha_nacimiento=fecha_nacimiento,
                    genero=genero,
                    email=email,
                    pin=pin,
                    registro=registro
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
    trabajo = get_object_or_404(Trabajo, id=trabajo_id)
    if request.method == "POST":
        descripcion = request.POST.get("descripcion")
        Informe.objects.create(
            mecanico=trabajo.mecanico,
            trabajo=trabajo,
            descripcion=descripcion,
            fecha_informe=timezone.now()
        )
        messages.success(request, "Informe registrado exitosamente.")
        return redirect("listar_trabajos")
    return render(request, "InterfazAdministrador/registrar_informe.html", {"trabajo": trabajo})

# Consultar histórico de reparaciones (acceso solo para clientes)
@role_required("admin")
def consultar_historico_reparaciones(request, patente):
    vehiculo = get_object_or_404(Vehiculo, patente=patente)
    reparaciones = Trabajo.objects.filter(vehiculo=vehiculo)
    return render(request, "consultar_historico_reparaciones.html", {"vehiculo": vehiculo, "reparaciones": reparaciones})

@role_required("mecanico")
def dashboard_mecanico(request):
    # Recupera los trabajos asignados al mecánico autenticado
    user_id = request.session.get('user_id')  # Obtén el usuario desde la sesión
    trabajos = Trabajo.objects.filter(mecanico__registro__id=user_id)

    return render(request, 'InterfazMecanico/mecanico_panel.html', {
        'username': request.user.username,
        'trabajos': trabajos,
    })
# Ingresar cliente (acceso solo para mecánicos)

class ClienteForm(ModelForm):
    class Meta:
        model = Cliente
        fields = ['rut', 'nombre', 'apellido', 'fecha_nacimiento', 'genero', 'email', 'telefono', 'direccion']
        widgets = {
            'fecha_nacimiento': DateInput(attrs={'type': 'date', 'placeholder': 'YYYY-MM-DD'}, format='%Y-%m-%d'),
        }

    def __init__(self, *args, **kwargs):
        super(ClienteForm, self).__init__(*args, **kwargs)
        self.fields['fecha_nacimiento'].input_formats = ['%Y-%m-%d']
        
@role_required("mecanico")
def ingresar_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente ingresado exitosamente.')
            return redirect('listar_cliente')
        else:
            messages.error(request, 'Hubo un error al ingresar el cliente. Por favor, revisa los campos.')
    else:
        form = ClienteForm()

    return render(request, 'InterfazMecanico/ingresar_cliente.html', {'form': form})

# Listar clientes (acceso solo para mecánicos)
@role_required("mecanico")
def listar_clientes(request):
    clientes = Cliente.objects.all().order_by('nombre')
    paginator = Paginator(clientes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'page_obj': page_obj}
    return render(request, 'InterfazMecanico/listar_clientes.html', context)

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
    if request.method == 'POST':
        patente = request.POST.get('patente')
        marca = request.POST.get('marca')
        modelo = request.POST.get('modelo')
        ano = request.POST.get('ano')
        cliente_id = request.POST.get('cliente')

        if not (patente and marca and modelo and ano and cliente_id):
            messages.error(request, "Todos los campos son obligatorios.")
            return redirect("agregar_vehiculo")

        try:
            cliente = Cliente.objects.get(rut=cliente_id)
            Vehiculo.objects.create(
                patente=patente,
                marca=marca,
                modelo=modelo,
                ano=ano,
                cliente=cliente
            )
            messages.success(request, "Vehículo agregado exitosamente.")
            return redirect("listar_vehiculos")
        except Cliente.DoesNotExist:
            messages.error(request, "El cliente seleccionado no existe.")
        except Exception as e:
            messages.error(request, f"Error al agregar el vehículo: {e}")

    clientes = Cliente.objects.all()
    return render(request, "InterfazMecanico/Vehiculo/ingresar_vehiculo.html", {'clientes': clientes})





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
    # Recupera todos los vehículos y ordena por patente
    vehiculos = Vehiculo.objects.select_related('cliente').all().order_by('patente')
    
    # Configuración de la paginación
    paginator = Paginator(vehiculos, 10)  # Mostrar 10 vehículos por página
    page_number = request.GET.get('page')  # Obtener el número de página actual desde la URL
    page_obj = paginator.get_page(page_number)  # Obtener la página actual
    
    # Renderizar la plantilla con los vehículos y la paginación
    return render(request, 'InterfazMecanico/Vehiculo/listar_vehiculo.html', {'page_obj': page_obj, 'vehiculos': page_obj.object_list})



# App_TallerMecanico/views.py

from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from .forms import TrabajoForm
from .models import Trabajo
from .decoradores import role_required  # Asegúrate de que el decorador soporte múltiples roles


def ingresar_trabajo(request):
    if request.method == 'POST':
        form = TrabajoForm(request.POST)
        if form.is_valid():
            vehiculo = form.cleaned_data.get('vehiculo')
            estado = form.cleaned_data.get('estado')

            # Define qué estados consideras como "activos"
            estados_activos = ['pendiente', 'en_progreso']

            if estado in estados_activos:
                # Verifica si ya existe un trabajo activo para este vehículo
                existe_trabajo = Trabajo.objects.filter(
                    vehiculo=vehiculo,
                    estado__in=estados_activos
                ).exists()
                if existe_trabajo:
                    messages.error(request, "Ya existe un trabajo activo para este vehículo.")
                else:
                    try:
                        with transaction.atomic():
                            trabajo = form.save()
                        messages.success(request, "Trabajo ingresado exitosamente.")
                        return redirect('listar_trabajos')  # Asegúrate de tener esta vista y URL
                    except Exception as e:
                        messages.error(request, f"Error al ingresar el trabajo: {e}")
            else:
                # Si el estado no es activo, no necesitas verificar
                try:
                    with transaction.atomic():
                        trabajo = form.save()
                    messages.success(request, "Trabajo ingresado exitosamente.")
                    return redirect('listar_trabajos')  # Asegúrate de tener esta vista y URL
                except Exception as e:
                    messages.error(request, f"Error al ingresar el trabajo: {e}")
        else:
            messages.error(request, "Por favor, corrige los errores en el formulario.")
    else:
        form = TrabajoForm()
    return render(request, 'InterfazMecanico/Trabajo/ingresar_trabajo.html', {'form': form})


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
    
    
    
def solicitar_cita(request):
    return render(request, 'InterfazCliente/Funciones/solicitar_cita.html')

<<<<<<< HEAD



def trabajo_tecnico_taller(request):
    # Datos de ejemplo (estos podrían provenir de la base de datos)
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
=======
def estado_vehiculo(request):
    return render(request, 'InterfazCliente/Funciones/estado_vehiculo.html')
>>>>>>> f7b10935f8d290def77dd53f5e13e7d6118a30dc
