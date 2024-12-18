# Generated by Django 5.0 on 2024-12-17 03:03

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('App_TallerMecanico', '0015_informe_cita_alter_informe_mecanico'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='informe',
            name='cita',
        ),
        migrations.AlterField(
            model_name='informe',
            name='mecanico',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='App_TallerMecanico.mecanico'),
        ),
    ]
