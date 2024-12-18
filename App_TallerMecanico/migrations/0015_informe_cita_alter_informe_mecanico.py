# Generated by Django 5.0 on 2024-12-17 02:55

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('App_TallerMecanico', '0014_remove_informe_cita_remove_informe_cliente_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='informe',
            name='cita',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='informes', to='App_TallerMecanico.cita'),
        ),
        migrations.AlterField(
            model_name='informe',
            name='mecanico',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='informes', to='App_TallerMecanico.mecanico'),
        ),
    ]