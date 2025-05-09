from django.contrib import admin
from .models import *

# Register your models here.
from django.utils.html import mark_safe


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ["id", "nombre", "apellido", "email", "rol", "telefono" , "tipoDocumento"]
    search_fields = ["nombre", "apellido", "email", "tipoDocumento"]
    list_filter = ["rol", "tipoDocumento"]
    list_editable = ["rol"]

@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    list_display = ["id", "ver_imagen" ,"titulo", "precio", "comision", "estado", "fecha" , "cupo_maximo", "cupos_vendidos"]
    search_fields = ["titulo", "precio"]
    list_filter = ["estado"]
    list_editable = ["estado"]

    def ver_imagen(self, obj):
        return mark_safe(f"<img src='{obj.imagen.url}' width='40%'>")

@admin.register(DetalleFactura)
class DetalleFacturaAdmin(admin.ModelAdmin):
    list_display = ["id", "idServicio" ,"subtotal", "cantidad", "precioUnitario", "idFactura"]
    search_fields = ["idServicio", "idFacturas"]


@admin.register(Factura)
class FacturaAdmin(admin.ModelAdmin):
    list_display = ["id", "idCliente" ,"fecha", "total", "metodoPago"]
    search_fields = ["idCliente", "metodoPago"]
    list_filter = ["metodoPago"]



    
