# App_TallerMecanico/forms.py

from django import forms
from django.utils import timezone
from .models import *

class TrabajoForm(forms.ModelForm):
    # Fecha de Ingreso (con widget personalizado)
    fecha_ingreso = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={
            'type': 'datetime-local', 
            'class': 'form-control'
        }),
        label='Fecha de Ingreso'
    )

    # Fecha de Entrega (opcional)
    fecha_entrega = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={
            'type': 'datetime-local', 
            'class': 'form-control'
        }),
        label='Fecha de Entrega'
    )

    # Estado (campo de selección)
    estado = forms.ChoiceField(
        choices=[
            ('pendiente', 'Pendiente'),
            ('en_progreso', 'En Progreso'),
            ('completado', 'Completado'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Estado'
    )

    class Meta:
        model = Trabajo
        fields = ['vehiculo', 'estado', 'costo_total_reparaciones', 'fecha_ingreso', 'fecha_entrega']

        # Personalización de widgets
        widgets = {
            'costo_total_reparaciones': forms.NumberInput(attrs={
                'step': '0.01', 
                'class': 'form-control',
                'placeholder': 'Ingrese el costo total'
            }),
            'vehiculo': forms.Select(attrs={'class': 'form-select'}),
        }

        labels = {
            'vehiculo': 'Vehículo',
            'costo_total_reparaciones': 'Costo Total Reparaciones',
        }

    def __init__(self, *args, **kwargs):
        # Recibimos al mecánico actual a través de 'mecanico' en kwargs
        mecanico = kwargs.pop('mecanico', None)
        super().__init__(*args, **kwargs)

        if mecanico:
            # Filtramos los vehículos solo asociados a clientes vinculados a este mecánico
            vehiculos = Vehiculo.objects.filter(
                cliente__citas__mecanico=mecanico
            ).distinct()

            # Estados activos para verificar si el vehículo está ocupado
            estados_activos = ['pendiente', 'en_progreso']

            # Modificamos las opciones del campo 'vehiculo'
            opciones = []
            for vehiculo in vehiculos:
                # Verificar si el vehículo tiene trabajos activos
                ocupado = Trabajo.objects.filter(
                    vehiculo=vehiculo,
                    estado__in=estados_activos
                ).exists()

                # Etiqueta dinámica: "Ocupado" o "Disponible"
                etiqueta = f"{vehiculo.patente} - {vehiculo.marca} - {vehiculo.modelo} ({'Ocupado' if ocupado else 'Disponible'})"
                opciones.append((vehiculo.id, etiqueta))

            # Asignamos las opciones al campo vehiculo
            self.fields['vehiculo'].choices = opciones

        # Añadimos un placeholder para los campos de estado
        self.fields['estado'].widget.attrs.update({
            'placeholder': 'Seleccione el estado'
        })

    # Validación personalizada para 'costo_total_reparaciones'
    def clean_costo_total_reparaciones(self):
        costo = self.cleaned_data.get('costo_total_reparaciones')
        if costo < 0:
            raise forms.ValidationError("El costo total de reparaciones no puede ser negativo.")
        return costo

class InformeForm(forms.ModelForm):
    class Meta:
        model = Informe
        fields = ['descripcion', 'costo']
        widgets = {
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción de la reparación...'
            }),
            'costo': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Costo de la reparación...'
            }),
        }
        


from django import forms
from .models import Cita

class CitaForm(forms.ModelForm):
    class Meta:
        model = Cita
        fields = ['servicio', 'fecha', 'hora']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date'}),
            'hora': forms.TimeInput(attrs={'type': 'time'}),
        }