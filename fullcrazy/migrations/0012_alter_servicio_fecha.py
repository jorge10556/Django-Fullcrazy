# Generated by Django 4.0.6 on 2025-04-04 17:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fullcrazy', '0011_administrador_carrito_remove_detallefactura_cantidad_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='servicio',
            name='fecha',
            field=models.DateField(help_text='AAAA-MM-DD'),
        ),
    ]
