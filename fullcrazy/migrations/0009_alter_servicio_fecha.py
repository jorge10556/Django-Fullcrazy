# Generated by Django 4.0.6 on 2025-04-04 16:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fullcrazy', '0008_alter_servicio_fecha'),
    ]

    operations = [
        migrations.AlterField(
            model_name='servicio',
            name='fecha',
            field=models.DateTimeField(help_text='AAAA-MM-DD'),
        ),
    ]
