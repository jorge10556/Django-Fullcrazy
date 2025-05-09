from django.db import models

# Create your models here.


class Servicio(models.Model):
    titulo = models.CharField(max_length=244)
    informacion = models.TextField()
    precio = models.IntegerField()
    categoria = models.CharField(max_length=244)
    requisito = models.TextField()
    comision = models.DecimalField(
        max_digits=3, decimal_places=2, default=0.10)
    imagen = models.ImageField(upload_to='imagen_servicios/', default='default.jpg')
    direccion = models.CharField(max_length=244, default="agregar direccion")
    ESTADO = (
        ("disponible", "Disponible"),
        ("indisponible", "Indisponible"),
    )
    estado = models.CharField(choices=ESTADO, default="disponible", max_length=15)
    fecha = models.DateTimeField()
    cupo_maximo = models.IntegerField(default=30)  
    cupos_vendidos = models.IntegerField(default=0)  

    idCliente = models.ForeignKey(
        "Cliente", on_delete=models.DO_NOTHING, related_name="fk1_servicio_cliente"
    )

    def __str__(self):
        return f"{self.titulo}  //  {self.idCliente}"




class Cliente(models.Model):
    nombre = models.CharField(max_length=244)
    apellido = models.CharField(max_length=244)
    ROLES = (
        ("cliente", "Cliente"),
        ("director", "Director de Evento"),
        ("administrador", "Administrador"),

    )
    rol = models.CharField(max_length=20, choices=ROLES, default="cliente")
    telefono = models.CharField(max_length=10, blank=True)
    TIPODOCUMENTO = (
        (1, "TI"),
        (2, "CC"),
        (3, "CE"),
        (4, "PA"),
    )
    tipoDocumento = models.IntegerField(
        choices=TIPODOCUMENTO, default=1)
    numeroDocumento = models.IntegerField(unique=True)
    email = models.EmailField(max_length=254, unique=True)
    contrasena = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.nombre}  //  {self.apellido}  //  {self.numeroDocumento}"



class DetalleFactura(models.Model):
    precioUnitario = models.IntegerField()
    precioComision = models.IntegerField()
    cantidad = models.IntegerField()
    subtotal = models.IntegerField()
    totalNoComision = models.IntegerField()
    idServicio = models.ForeignKey(
        "Servicio", on_delete=models.DO_NOTHING, related_name="fk2_detalleFactura_servicio"
    )
    idFactura = models.ForeignKey(
        "Factura", on_delete=models.DO_NOTHING, related_name="fk3_detalleFactura_factura"
    )

    def __str__(self):
        return f"{self.idServicio.titulo}  //  {self.cantidad}  //  {self.subtotal}"


class Factura(models.Model):
    fecha = models.DateTimeField(help_text="AAAA-MM-DD")
    total = models.IntegerField()
    METODOPAGO = (
        (1, "Tarjeta de Credito"),
        (2, "Tarjeta de Debito"),
    )
    metodoPago = models.IntegerField(
        choices=METODOPAGO, default=1)
    idCliente = models.ForeignKey(
        "Cliente", on_delete=models.DO_NOTHING, related_name="fk4_facturas_cliente"
    )

    def __str__(self):
        return f"Factura #{self.id}  //  {self.fecha}  //  {self.total}"