# Generated by Django 4.2 on 2025-04-04 02:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fullcrazy', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='servicio',
            name='estado',
            field=models.CharField(choices=[('disponible', 'Disponible'), ('indisponible', 'Indisponible')], default='disponible', max_length=15),
        ),
    ]
