# Generated by Django 5.0 on 2024-11-07 01:34

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('App_TallerMecanico', '0002_administrador_cliente_mecanico_trabajo_informe_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='mecanico',
            name='registro',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='App_TallerMecanico.registro'),
        ),
    ]
