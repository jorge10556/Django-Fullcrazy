# Generated by Django 4.0.6 on 2025-04-04 17:15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('fullcrazy', '0010_alter_servicio_fecha'),
    ]

    operations = [
        migrations.CreateModel(
            name='Administrador',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=244)),
                ('apellido', models.CharField(max_length=244)),
                ('telefono', models.CharField(max_length=10)),
                ('tipoDocumento', models.IntegerField(choices=[(1, 'TI'), (2, 'CC'), (3, 'CE'), (4, 'PA')], default=1)),
                ('numeroDocumento', models.IntegerField(unique=True)),
                ('email', models.CharField(max_length=244)),
                ('contrasena', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Carrito',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('total', models.IntegerField()),
                ('cantidad', models.IntegerField()),
                ('fecha', models.DateTimeField(help_text='AAAA-MM-DD')),
            ],
        ),
        migrations.RemoveField(
            model_name='detallefactura',
            name='cantidad',
        ),
        migrations.AlterField(
            model_name='cliente',
            name='rol',
            field=models.CharField(choices=[('cliente', 'Cliente'), ('director', 'Director de Evento')], default='cliente', max_length=20),
        ),
        migrations.AlterField(
            model_name='detallefactura',
            name='idFactura',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='fk10_detalleFactura_factura', to='fullcrazy.factura'),
        ),
        migrations.AlterField(
            model_name='detallefactura',
            name='idServicio',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='fk9_detalleFactura_servicio', to='fullcrazy.servicio'),
        ),
        migrations.AlterField(
            model_name='factura',
            name='idCliente',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='fk11_facturas_cliente', to='fullcrazy.cliente'),
        ),
        migrations.AlterField(
            model_name='servicio',
            name='fecha',
            field=models.DateField(default='2025-04-03', help_text='AAAA-MM-DD'),
        ),
        migrations.AlterField(
            model_name='servicio',
            name='idCliente',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='fk6_servicio_Cliente', to='fullcrazy.cliente'),
        ),
        migrations.AlterField(
            model_name='servicio',
            name='idMunicipio',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='fk7_servicio_municipio', to='fullcrazy.municipio'),
        ),
        migrations.CreateModel(
            name='Peticion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipoPeticion', models.CharField(max_length=100)),
                ('fecha', models.DateTimeField(help_text='AAAA-MM-DD')),
                ('descripcion', models.TextField()),
                ('valor', models.IntegerField()),
                ('idCliente', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='fk8_peticion_cliente', to='fullcrazy.cliente')),
            ],
        ),
        migrations.CreateModel(
            name='DetalleCarrito',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('precioUnitario', models.IntegerField()),
                ('idCarrito', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='fk3_detalleCarrito_carrito', to='fullcrazy.carrito')),
                ('idServicio', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='fk2_detalleCarrito_servicio', to='fullcrazy.servicio')),
            ],
        ),
        migrations.CreateModel(
            name='DetalleAdministrador',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('idAdministrador', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='fk5_detalleAdministrador_administrador', to='fullcrazy.administrador')),
                ('idPeticion', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='fk4_detalleAdministrador_peticion', to='fullcrazy.peticion')),
            ],
        ),
        migrations.AddField(
            model_name='carrito',
            name='idCliente',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='fk1_Carrito_cliente', to='fullcrazy.cliente'),
        ),
    ]
