from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError

# Opciones de rol para el usuario
ROLE_CHOICES = [
    ('cliente', 'Cliente'),
    ('admin', 'Administrador'),
    ('mecanico', 'Mecánico'),
]

# Opciones de género para el usuario
GENDER_CHOICES = [
    ('M', 'Masculino'),
    ('F', 'Femenino'),
    ('O', 'Otro'),
]

# Modelo para Registro de usuario
class Registro(models.Model):
    username = models.CharField(max_length=150, unique=True)  # Nombre de usuario único
    password = models.CharField(max_length=128)  # Contraseña sin encriptación
    role = models.CharField(max_length=100, choices=ROLE_CHOICES, default='cliente')
    registro = models.DateTimeField(default=timezone.now)  # Fecha de registro

    def __str__(self):
        return f"{self.username} - {self.get_role_display()} - Registrado en {self.registro}"

    def is_mecanico(self):
        """Retorna True si el registro corresponde a un mecánico"""
        return self.role == 'mecanico'

# Modelo para Login de usuario
class Login(models.Model):
    user = models.ForeignKey(Registro, on_delete=models.CASCADE)  # Usuario registrado
    ultima_conexion = models.DateTimeField(null=True, blank=True)  # Última conexión
    ultima_desconexion = models.DateTimeField(null=True, blank=True)  # Última desconexión

    def __str__(self):
        return f"{self.user.username} - Última conexión: {self.ultima_conexion}"

# Clase abstracta Persona (base para Administrador, Mecanico y Cliente)
class Persona(models.Model):
    rut = models.CharField(max_length=12, primary_key=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    fecha_nacimiento = models.DateField()
    genero = models.CharField(max_length=1, choices=GENDER_CHOICES)
    email = models.EmailField(unique=True)

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

# Modelo Administrador
class Administrador(Persona):
    clave_unica = models.CharField(max_length=10, default='123')  # Clave predeterminada

    def __str__(self):
        return f"Administrador: {self.nombre} {self.apellido} - Clave Única: {self.clave_unica}"

# Modelo Mecánico
class Mecanico(Persona):
    registro = models.OneToOneField(Registro, on_delete=models.CASCADE, null=False, related_name='mecanico')
    pin = models.CharField(max_length=4, unique=True)  # PIN único de 4 dígitos para mecánicos

    def __str__(self):
        return f"Mecánico: {self.nombre} {self.apellido} - PIN: {self.pin}"

    def clean(self):
        """Validación para asegurar que el registro asociado tenga rol de mecánico"""
        if not self.registro.is_mecanico():
            raise ValidationError("El registro asociado debe tener el rol de 'mecánico'.")

    def save(self, *args, **kwargs):
        # Ejecutar validaciones antes de guardar
        self.clean()
        super().save(*args, **kwargs)

# Modelo Cliente
class Cliente(Persona):
    registro = models.OneToOneField(Registro, on_delete=models.CASCADE, null=True, blank=True, related_name='cliente')

    telefono = models.CharField(max_length=15, blank=True, null=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    datos_completos = models.BooleanField(default=False)

    def __str__(self):
        return f"Cliente: {self.nombre} {self.apellido} - Teléfono: {self.telefono}"

# Modelo Vehículo
class Vehiculo(models.Model):
    patente = models.CharField(max_length=10, primary_key=True)
    marca = models.CharField(max_length=50)
    modelo = models.CharField(max_length=50)
    ano = models.IntegerField()
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.marca} {self.modelo} ({self.patente}) - Cliente: {self.cliente.nombre}"

# Modelo Trabajo
class Trabajo(models.Model):
    fecha_ingreso = models.DateTimeField(default=timezone.now)
    fecha_entrega = models.DateTimeField(blank=True, null=True)
    estado = models.CharField(max_length=50)
    costo_total_reparaciones = models.FloatField()
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.CASCADE)
    mecanico = models.ForeignKey(Mecanico, on_delete=models.CASCADE)

    def __str__(self):
        return f"Trabajo en {self.vehiculo.patente} - Estado: {self.estado}"

# Modelo Informe para registrar detalles adicionales de un trabajo
class Informe(models.Model):
    mecanico = models.ForeignKey(Mecanico, on_delete=models.CASCADE)
    trabajo = models.ForeignKey(Trabajo, on_delete=models.CASCADE, related_name='informes')
    descripcion = models.TextField()
    costo = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    fecha_informe = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Informe de {self.mecanico.nombre} - Trabajo en {self.trabajo.vehiculo.patente}"
