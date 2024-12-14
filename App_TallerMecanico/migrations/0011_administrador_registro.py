# Generated by Django 5.0 on 2024-12-13 23:23

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('App_TallerMecanico', '0010_cita_cliente_alter_cita_mecanico'),
    ]

    operations = [
        migrations.AddField(
            model_name='administrador',
            name='registro',
            field=models.OneToOneField(default=2, on_delete=django.db.models.deletion.CASCADE, related_name='administrador', to='App_TallerMecanico.registro'),
            preserve_default=False,
        ),
    ]