# Generated by Django 5.0 on 2024-12-17 02:48

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('App_TallerMecanico', '0013_informe_cita_informe_cliente_alter_informe_mecanico'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='informe',
            name='cita',
        ),
        migrations.RemoveField(
            model_name='informe',
            name='cliente',
        ),
        migrations.AlterField(
            model_name='informe',
            name='mecanico',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='App_TallerMecanico.mecanico'),
        ),
    ]
