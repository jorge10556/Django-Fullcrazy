# Generated by Django 4.0.6 on 2025-04-04 16:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fullcrazy', '0005_remove_carrito_idcliente_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='servicio',
            name='fecha',
            field=models.DateTimeField(help_text='AAAA-MM-DD'),
        ),
    ]
