# Generated by Django 5.0 on 2024-12-13 16:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('App_TallerMecanico', '0006_informe_costo_alter_cliente_registro_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Cita',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('servicio', models.CharField(max_length=100)),
                ('fecha', models.DateField()),
                ('hora', models.TimeField()),
            ],
        ),
    ]
