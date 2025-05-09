import re

from django.core.validators import validate_email
from django.core.exceptions import ValidationError

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from .models import *
import datetime

from django.db.utils import IntegrityError
from django.contrib import messages

from django.core.mail import send_mail
from django.core.mail import EmailMessage
from django.conf import settings

from .utils import *
from django.utils import timezone

from PIL import Image

import secrets
import base64
from django.core.signing import TimestampSigner
from django.core.signing import BadSignature, SignatureExpired

from django.db.models import Sum

#para factura pdf
from django.template.loader import render_to_string
from weasyprint import HTML





# Create your views here.



def carrito_vista(request):
    carrito = request.session.get('carrito', {})
    servicios = list(carrito.values())

    total_general = sum(item['total'] for item in servicios)

    contexto = {
        'servicios': servicios,
        'total': total_general,
    }

    return render(request, 'carrito.html', contexto)




def agregar_carrito(request, id_servicio):
    servicio = get_object_or_404(Servicio, id=id_servicio)


    errores = []


    try:
        cantidad = int(request.POST.get('cantidad', 1))
        if cantidad < 1 or cantidad > 4:
            errores.append("La cantidad debe estar entre 1 y 4")
    except (ValueError, TypeError):
        errores.append("Debe ingresar una cantidad válida")

    if errores:
        for error in errores:
            messages.error(request, error)
        return render(request, 'evento_especifico.html', {'servicio_especifico': servicio})

    if servicio.fecha < timezone.now() or servicio.cupos_vendidos >= servicio.cupo_maximo:
        servicio.estado = 'indisponible'
        servicio.save()
        messages.error(request, 'Este servicio ya no está disponible.')
        return redirect('evento_especifico', id_servicio=id_servicio)


    try:
        cliente_id = request.session["auth"]["id"]
    except:
        messages.error(request, "Debes iniciar sesión para agregar eventos al carrito.")
        return redirect("login")

    cliente = Cliente.objects.get(id=cliente_id)

    facturas_cliente = Factura.objects.filter(idCliente=cliente)

    # Sumar la cantidad total comprada del mismo servicio
    compras_anteriores = DetalleFactura.objects.filter(
        idFactura__in=facturas_cliente, idServicio=servicio
    ).aggregate(total=models.Sum("cantidad"))["total"] or 0

    # Calcular total acumulado con lo que está intentando agregar
    cantidad_total = compras_anteriores + cantidad

    if cantidad_total > 4:
        restante = 4 - compras_anteriores
        if restante <= 0:
            messages.error(request, "Ya has comprado el máximo permitido de este evento (4 unidades).")
        else:
            messages.error(request, f"Solo puedes comprar {restante} unidad(es) más de este evento.")
        return redirect('evento_especifico', id_servicio=id_servicio)


    precio = servicio.precio
    comision = precio * float(servicio.comision)
    comisionTotal = comision * cantidad
    subtotal = precio + comision
    totalSinComision = precio * cantidad
    total = subtotal * cantidad

    carrito = request.session.get('carrito', {})

    cupos_disponibles = servicio.cupo_maximo - servicio.cupos_vendidos

    if cantidad > cupos_disponibles:
        messages.warning(request, f'Solo hay {cupos_disponibles} cupos disponibles para este evento.')
        return redirect('evento_especifico', id_servicio=id_servicio)
    
    if str(id_servicio) in carrito:
        carrito[str(id_servicio)]['cantidad'] = cantidad
    else:
        carrito[str(id_servicio)] = {
            'id': id_servicio,
            'titulo': servicio.titulo,
            'precio': servicio.precio,
            'imagen': servicio.imagen.url,
            'cantidad': cantidad,
            'comision':comisionTotal,
            'totalSinComision':totalSinComision,
            'subtotal': round(subtotal, 2),
            'total': round(total, 2)
        }

    request.session['carrito'] = carrito
    messages.success(request, 'Evento agregado al carrito correctamente.')
    return redirect('carrito_vista')




def eliminar_carrito(request, id_servicio):
    carrito = request.session.get('carrito', {})

    if str(id_servicio) in carrito:
        del carrito[str(id_servicio)]
        request.session['carrito'] = carrito

    messages.success(request, "se elimino el evento correctamente")

    return redirect('carrito_vista')




def actualizar_cantidad(request, id_servicio):
    if request.method == 'POST':
        cantidad_input = request.POST.get('cantidad')

        errores = []

        try:
            nueva_cantidad = int(cantidad_input)
            if nueva_cantidad < 1 or nueva_cantidad > 4:
                errores.append("La cantidad debe estar entre 1 y 4.")

        except ValueError:
            errores.append("La cantidad debe ser un número válido.")

        if errores:
            for error in errores:
                messages.error(request, error)
            return redirect('carrito_vista')  



        carrito = request.session.get('carrito', {})

        if str(id_servicio) in carrito:
            servicio = get_object_or_404(Servicio, id=id_servicio)

            cupos_disponibles = servicio.cupo_maximo - servicio.cupos_vendidos

            if nueva_cantidad > cupos_disponibles:
                messages.warning(request, f'Solo hay {cupos_disponibles } cupos disponibles para este evento.')
                return redirect('carrito_vista')
            

            precio = servicio.precio
            comision = precio * float(servicio.comision)
            comisionTotal = comision * nueva_cantidad
            totalSinComision = precio * nueva_cantidad
            subtotal = precio + comision
            total = subtotal * nueva_cantidad

            carrito[str(id_servicio)].update({
                'cantidad': nueva_cantidad,
                'comision': round(comisionTotal),
                'totalSinComision': round(totalSinComision),
                'subtotal': round(subtotal),
                'total': round(total)
            })


        
            carrito[str(id_servicio)]['cantidad'] = nueva_cantidad
            request.session['carrito'] = carrito
            messages.success(request, "Cantidad actualizada correctamente.")

        else:
            messages.error(request, "El servicio no está en el carrito.")
            return redirect('carrito_vista')
            

    return redirect('carrito_vista')



def compra_directa(request, id_servicio):
    servicio = get_object_or_404(Servicio, id=id_servicio)

    errores = []


    try:
        cantidad = int(request.POST.get('cantidad', 1))
        if cantidad < 1 or cantidad > 4:
            errores.append("La cantidad debe estar entre 1 y 4")
    except (ValueError, TypeError):
        errores.append("Debe ingresar una cantidad válida")

    if errores:
        for error in errores:
            messages.error(request, error)
        return render(request, 'evento_especifico.html', {'servicio_especifico': servicio})

    if servicio.fecha < timezone.now() or servicio.cupos_vendidos >= servicio.cupo_maximo:
        servicio.estado = 'indisponible'
        servicio.save()
        messages.error(request, 'Este servicio ya no está disponible.')
        return redirect('evento_especifico', id_servicio=id_servicio)
    
    

    try:
        cliente_id = request.session["auth"]["id"]
    except:
        messages.error(request, "Debes iniciar sesión para comprar eventos.")
        return redirect("login")

    cliente = Cliente.objects.get(id=cliente_id)

    facturas_cliente = Factura.objects.filter(idCliente=cliente)

    # Sumar la cantidad total comprada del mismo servicio
    compras_anteriores = DetalleFactura.objects.filter(
        idFactura__in=facturas_cliente, idServicio=servicio
    ).aggregate(total=models.Sum("cantidad"))["total"] or 0

    # Calcular total acumulado con lo que está intentando agregar
    cantidad_total = compras_anteriores + cantidad

    if cantidad_total > 4:
        restante = 4 - compras_anteriores
        if restante <= 0:
            messages.error(request, "Ya has comprado el máximo permitido de este evento (4 unidades).")
        else:
            messages.error(request, f"Solo puedes comprar {restante} unidad(es) más de este evento.")
        return redirect('evento_especifico', id_servicio=id_servicio)


    
    precio = servicio.precio
    comision = precio * float(servicio.comision)
    comisionTotal = comision * cantidad
    totalSinComision = precio * cantidad
    subtotal = precio + comision
    total = subtotal * cantidad

    # se quita todo en el para que solo se haga la compra directa
    request.session['carrito'] = {}  # Borra todo lo que había en el carrito

    carrito = request.session.get('carrito', {})

    cupos_disponibles = servicio.cupo_maximo - servicio.cupos_vendidos

    if cantidad > cupos_disponibles:
        messages.warning(request, f'Solo hay {cupos_disponibles} cupos disponibles para este evento.')
        return redirect('evento_especifico', id_servicio=id_servicio)
        

    carrito[str(id_servicio)] = {
        'id': id_servicio,
        'titulo': servicio.titulo,
        'precio': servicio.precio,
        'imagen': servicio.imagen.url,
        'cantidad': cantidad,
        'comision':comisionTotal,
        'totalSinComision':totalSinComision,
        'subtotal': round(subtotal, 2),
        'total': round(total, 2)
    }

    request.session['carrito'] = carrito

    return redirect('formulario_pago')





def cliente(request):
    if "auth" not in request.session:
        messages.error(request, "Debes iniciar sesión para acceder a esta sección.")
        return redirect("login")

    id_cliente = request.session["auth"]["id"]

    try:
        cliente = Cliente.objects.get(pk=id_cliente)
    except Cliente.DoesNotExist:
        messages.error(request, "Tu cuenta no existe.")
        return redirect("login")

    if cliente.rol != "cliente":
        messages.error(request, "No tienes permisos para acceder a esta sección.")
        return redirect("index") 


    c = Cliente.objects.get(pk=id_cliente)

    contexto = {
        "cliente": c
    }
    return render(request, 'cliente.html', contexto)



def editar_perfil(request, id_cliente):
    if "auth" not in request.session:
        messages.error(request, "Debes iniciar sesión para acceder.")
        return redirect("login")

    if request.session["auth"]["id"] != id_cliente:
        messages.error(request, "No tienes permiso para editar este perfil.")
        return redirect("index")
    

    if request.method == "POST":
        nombre = request.POST.get("nombre").strip()
        apellido = request.POST.get("apellido").strip()
        numero_contacto = request.POST.get("numero_contacto").strip()
        correo_electronico = request.POST.get("correo_electronico").strip()
        crear_contrasena = request.POST.get("crear_contrasena").strip()
        confirmar_contrasena = request.POST.get("confirmar_contrasena").strip()
        aceptar = request.POST.get("aceptar")

        errores = []

        try:
            c = Cliente.objects.get(pk=id_cliente)
            contexto = {
                "datos": c
            }
        except Cliente.DoesNotExist:
            errores.append("Cliente no encontrado.")
            return redirect("listar_clientes")
        
        
        if correo_electronico:            
            try:
                validate_email(correo_electronico)
                if len(correo_electronico) > 244:
                    errores.append("El correo debe contener menos de 244 caracteres.")
            except ValidationError:
                errores.append("El correo electrónico no es válido.")
            else:
                # Verifica si el correo es diferente y si ya existe otro cliente con ese correo
                if correo_electronico != c.email and Cliente.objects.filter(email=correo_electronico).exists():
                    errores.append("Ya existe un usuario registrado con ese correo.")
        else:
            errores.append("Debe ingresar un correo electrónico.")


        if nombre:
            if not re.match(r'^[A-Za-záéíóúÁÉÍÓÚñÑ\s]+$', nombre):
                errores.append("el nombre debe contener solo letras")
            else:
                if len(nombre) > 244:
                    errores.append("el nombre debe contener menos de 244 caracteres")
        else:
            errores.append("se debe ingresar un nombre")


        if apellido:
            if not re.match(r'^[A-Za-záéíóúÁÉÍÓÚñÑ\s]+$', apellido):
                errores.append("el apellido debe contener solo letras")
            else:
                if len(apellido) > 244:
                    errores.append("el apellido debe contener menos de 244 caracteres")
        else:
            errores.append("se debe ingresar un apellido")


        if crear_contrasena:
            if len(crear_contrasena) < 5:
                errores.append("La contraseña debe tener minimo 5 caracteres.")
        else:
            errores.append("debe ingresar una contraseña")

        if confirmar_contrasena:
            if crear_contrasena != confirmar_contrasena:
                errores.append("Las contraseñas no coinciden.")
        else:
            errores.append("debe ingresar el confirmar contraseña")

        if numero_contacto:
            if not numero_contacto.isdigit():
                errores.append("El número de contacto debe contener solo números.")
            else:
                if int(numero_contacto) < 0:
                    errores.append("el numero no puede ser negativo")
        else:
            errores.append("debe ingresar un numero de contacto")

        if not aceptar:
            errores.append("debes aceptar terminos y condiciones")


        if errores:
            for error in errores:
                messages.error(request, error)
            return render(request, "registro.html", contexto) 


        try:
            c = Cliente.objects.get(pk=id_cliente)
            c.nombre = request.POST.get("nombre")
            c.apellido = request.POST.get("apellido")
            c.telefono = request.POST.get("numero_contacto")
            c.email = request.POST.get("correo_electronico")
            c.contrasena = hash_password(request.POST.get("crear_contrasena"))
            c.save()
            messages.success(request, "Cliente actualizado correctamente!")
            if c.rol == 'director':
                return redirect("director")
            elif c.rol == 'cliente':
                return redirect("cliente")
        except Exception as e:
            messages.error(request, f"Error: {e}")
            if c.rol == 'director':
                return redirect("editar_perfil", id_cliente=id_cliente)
            elif c.rol == 'cliente':
                return redirect("editar_perfil", id_cliente=id_cliente)
    else:
        c = Cliente.objects.get(pk=id_cliente)
        contexto = {
            "datos": c
            }
        return render(request, "registro.html", contexto)





def historial_eventos(request):
    if "auth" not in request.session:
        messages.error(request, "Debes iniciar sesión para acceder.")
        return redirect("login")

    if request.session["auth"]["rol"] != "director":
        messages.error(request, "No tienes permiso para ingresar aqui.")
        return redirect("index")
    
    idCliente = request.session["auth"]["id"]
    servicios_de_cliente = Servicio.objects.filter(idCliente=idCliente)
    contexto = {
        "servicios": servicios_de_cliente
    }
    return render(request, 'historial_eventos.html', contexto)




def crear_evento(request):
    if "auth" not in request.session:
        messages.error(request, "Debes iniciar sesión para crear un evento.")
        return redirect("login")
    
    fecha_actual = timezone.now().strftime('%Y-%m-%dT%H:%M')

    contexto = {
        "fecha_actual": fecha_actual
    }  

    if request.method == "POST":
        titulo = request.POST.get("titulo")
        informacion = request.POST.get("informacion")
        precio = request.POST.get("precio")
        categoria = request.POST.get("categoria")
        requisito = request.POST.get("requisito")
        fecha = request.POST.get("fecha")
        cupo_maximo = request.POST.get("cupo_maximo")
        imagen = request.FILES.get("imagen")
        direccion = request.POST.get("direccion")
        aceptar = request.POST.get("aceptar")
        idCliente = request.session["auth"]["id"]
        cliente = Cliente.objects.get(id=idCliente)


        errores = []

        if titulo:
            if len(titulo) > 244:
                errores.append("el titulo no puede tener mas de 244 caracteres")
        else:
            errores.append("debe ingresar un titulo")

        if informacion:
            if len(informacion) > 500:
                errores.append("la informacion no debe tener mas de 500 caracteres")
        else:
            errores.append("debe ingresar la informacion de su evento")
        
        if precio:
            if not precio.isdigit():
                errores.append("el precio debe contener solo numeros")
            else:
                if float(precio) < 0:
                    errores.append("el precio no puede contener valores negativos")
        else:
            errores.append("debe ingresar un precio")

        if categoria:
            if len(categoria) > 244:
                errores.append("la categoria no puede tener mas de 244 caracteres")
        else:
            errores.append("debe ingresar la categoria")

        if requisito:
            if len(requisito) > 500:
                errores.append("los requisitos no pueden sobrepasar los 500 caracteres")
        else:
            errores.append("debe ingresar un requisito")

        if imagen:
            try:
                validate_image_file(imagen)
            except ValidationError as e:
                errores.append(str(e))
        else:
            errores.append("debes subir una imagen del evento")

        
        if fecha:
            try:
                fecha = datetime.datetime.strptime(fecha, "%Y-%m-%dT%H:%M")

                if fecha < datetime.datetime.today():
                    errores.append("La fecha no puede ser anterior a hoy.")
            except ValueError:
                errores.append("La fecha debe tener el formato YYYY-MM-DDTHH:MM.")
        else:
            errores.append("El campo fecha es obligatorio.")

        if cupo_maximo:
            if not cupo_maximo.isdigit():
                errores.append("la cantidad maxima debe contener solo numeros")
            else:
                if int(cupo_maximo) <= 0:
                    errores.append("la cantidad maxima debe contener numeros positivos")
        else:
            errores.append("el campo de cupos maximos es obligatorio")


        if direccion:
            if len(direccion) > 244:
                errores.append("la direccion no puede contener mas de 244 caracteres")
        else:
            errores.append("el campo direccion es obligatorio")


        if not aceptar:
            errores.append("se deben aceptar terminos y condiciones") 

        contexto = {
            "form_data":request.POST,
            "fecha_actual": fecha_actual
        }

        if errores:
            for error in errores:
                messages.error(request, error)
            return render(request, "crear_evento.html", contexto)

        try:
            s = Servicio(
                titulo=titulo,
                informacion=informacion,
                precio=precio,
                categoria=categoria,
                requisito=requisito,
                fecha=fecha,
                cupo_maximo=cupo_maximo,
                imagen=imagen,
                direccion=direccion,
                idCliente=cliente,
            )
            s.save()
            

            if cliente.rol == "cliente":
                cliente.rol = "director"
                cliente.save()

            
            messages.success(request, "Servicio agregado correctamente!")
            return redirect("historial_eventos")
        except Exception as e:
            messages.error(request, f"Error: {e}")
            return redirect("crear_evento")
    else:
        return render(request, "crear_evento.html", contexto)


def evento_especifico(request, id_servicio):
    se = get_object_or_404(Servicio, id=id_servicio)
    sg = Servicio.objects.filter(estado='disponible')

    if se.fecha < timezone.now() or se.cupos_vendidos >= se.cupo_maximo:
        se.estado = 'indisponible'
        se.save()

    contexto = {
        "servicio_especifico": se,
        "servicios_generales": sg.order_by('?')
    }

    return render(request, 'evento_especifico.html', contexto)


def eventos_generales(request):
    servicios = Servicio.objects.all()

    for servicio in servicios:
        if servicio.fecha < timezone.now() or servicio.cupos_vendidos >= servicio.cupo_maximo:
            if servicio.estado != 'indisponible':
                servicio.estado = 'indisponible'
                servicio.save()

    servicio_filtro = Servicio.objects.filter(estado='disponible').order_by('?')
    contexto = {
        "datos_servicios": servicio_filtro
    }
    return render(request, 'eventos_generales.html', contexto)




def factura(request, id_factura):

    if "auth" not in request.session:
        messages.error(request, "Debes iniciar sesión para acceder.")
        return redirect("login")

    factura = get_object_or_404(Factura, id=id_factura)

    if request.session["auth"]["id"] != factura.idCliente.id:
        messages.error(request, "No tienes permiso para ver esta factura.")
        return redirect("index")

    detalles = DetalleFactura.objects.filter(idFactura=factura)

    contexto = {
        "factura": factura,
        "detalles": detalles
    }
    return render(request, "factura.html", contexto)





 
 
def gestion_evento(request):
    if "auth" not in request.session:
        messages.error(request, "Debes iniciar sesión para acceder.")
        return redirect("login")

    if request.session["auth"]["rol"] == "cliente":
        messages.error(request, "No tienes permiso para ingresar aqui.")
        return redirect("index")
    

    idCliente = request.session["auth"]["id"]

    # Primero buscamos los eventos del cliente ordenados del más nuevo al más viejo
    servicios = Servicio.objects.filter(idCliente=idCliente).order_by('-id')  # orden descendente por ID (los nuevos primero)

    datos_ganancias = []  # Para el gráfico de ganancias
    datos_participantes = []  # Para el gráfico de participantes

    for servicio in servicios:
        # Sumamos los totalNoComision de los detalles de este servicio
        total_ganado = DetalleFactura.objects.filter(idServicio=servicio).aggregate(total=Sum('totalNoComision'))['total'] or 0 
        datos_ganancias.append([servicio.titulo, total_ganado])

        # Participantes (cupos vendidos)
        datos_participantes.append([servicio.titulo, servicio.cupos_vendidos])

    # Limitar solo a los primeros 10
    contexto = {
        'datos_eventos': datos_ganancias[:10],
        'datos_participantes': datos_participantes[:10],
    }

    return render(request, 'gestion_evento.html', contexto)





def eventos_comprados(request):
    if "auth" not in request.session:
        messages.error(request, "Debes iniciar sesión para acceder.")
        return redirect("login")


    id_cliente = request.session["auth"]["id"]

    cliente = Cliente.objects.get(id = id_cliente)

    factura = Factura.objects.filter(idCliente = cliente)

    detalleFactura = DetalleFactura.objects.filter(idFactura__in = factura)

    contexto = {
        "cliente":cliente,
        "factura":factura,
        "detalle_factura":detalleFactura
    }


    return render(request, 'eventos_comprados.html', contexto)


def index(request):
    s = Servicio.objects.all()
    for servicio in s:
        if servicio.fecha < timezone.now() or servicio.cupos_vendidos >= servicio.cupo_maximo:
            if servicio.estado != 'indisponible':
                servicio.estado = 'indisponible'
                servicio.save()
        elif servicio.fecha > timezone.now() or servicio.cupos_vendidos < servicio.cupo_maximo:
            if servicio.estado != 'disponible':
                servicio.estado = 'disponible'
                servicio.save

    servicio_filtro = Servicio.objects.filter(estado='disponible').order_by('?')[:5] #se ponen solo 5 y van rotando
    contexto = {
        "vista_servicios": servicio_filtro
    }
    return render(request, 'index.html', contexto)


def login(request):
    if request.method == "POST":
        email = request.POST.get("email")
        contrasena = request.POST.get("contrasena")
    
        errores = []

        if email:
            try:
                validate_email(email)
            except ValidationError:
                errores.append("el campo del correo no tiene la estructura correcta")
        else:
            errores.append("debe ingresar un correo")

        if contrasena:
            pass
        else:
            errores.append("se debe llenar el campo contraseña")

        contexto = {
            "form_data": request.POST  
        }

        if errores:
            for error in errores:
                messages.error(request, error)
            return render(request, "login.html", contexto)

        try:
            c = Cliente.objects.get(email=email)
            if verify_password(contrasena, c.contrasena):            
                # Crear variable de sesión ========
                request.session["auth"] = {
                    "id": c.id,
                    "nombre": c.nombre,
                    "rol": c.rol,
                    "nombre_rol": c.get_rol_display(),
                }
                return redirect("index")
            else:
                raise Cliente.DoesNotExist()
        except Cliente.DoesNotExist:
            messages.warning(request, "Email o contraseña no válidos..")
            request.session["auth"] = None
            return render(request, "login.html", contexto)

        except Exception as e:
            messages.error(request, f"Error: {e}")
            request.session["auth"] = None
            return render(request, "login.html", contexto) 
    else:
        verificar = request.session.get("auth", False)

        if verificar:
            return redirect("index")
        else:
            return render(request, "login.html")


def logout(request):
    try:
        del request.session["auth"]
        return redirect("login")
    except Exception as e:
        messages.info(request, "No se pudo cerrar sesión, intente de nuevo")
        return redirect("index")


def director(request):
    if "auth" not in request.session:
        messages.error(request, "Debes iniciar sesión para acceder a esta sección.")
        return redirect("login")

    id_cliente = request.session["auth"]["id"]

    try:
        cliente = Cliente.objects.get(pk=id_cliente)
    except Cliente.DoesNotExist:
        messages.error(request, "Tu cuenta no existe.")
        return redirect("login")

    if cliente.rol != "director":
        messages.error(request, "No tienes permisos para acceder a esta sección.")
        return redirect("index") 

    contexto = {
        "director": cliente
    }
    return render(request, 'director.html', contexto)


 


signer = TimestampSigner()  # Firma con fecha

def recuperar_cuenta(request):
    if "auth" in request.session:
        messages.error(request, "No puedes acceder aquí.")
        return redirect("login")

    if request.method == 'POST':
        email = request.POST.get("correo_electronico")

        if email:
            try:
                validate_email(email)
                if len(email) > 244:
                    messages.error("el correo debe contener menos de 244 caracteres")
            except ValidationError:
                messages.error("el correo electronico no es valido")
        else:
            messages.error("debe ingresar un correo")

        try:
            cliente = Cliente.objects.get(email=email)
            token = secrets.token_urlsafe(32)
            user_id_encoded = base64.urlsafe_b64encode(str(cliente.id).encode()).decode()
            signed_token = signer.sign(token)  # Firma el token con tiempo

            enlace = request.build_absolute_uri(
                f"/cambiar_contrasena/?id={user_id_encoded}&token={signed_token}"
            )

            html_messages = f"""
                <h2>Recuperación de Contraseña</h2>
                <p>Haz clic en el siguiente enlace para restablecer tu contraseña:</p>
                <a href="{enlace}">Recuperar Contraseña</a>
                <p>Si no solicitaste esto, ignora este mensaje.</p>   
            """
            send_mail(
                "FullCrazy - Recuperar contraseña",
                "",
                settings.EMAIL_HOST_USER, 
                [email],  
                fail_silently=False,
                html_message=html_messages
            )
            messages.success(request, "Se ha enviado un enlace a tu correo.")
            return render(request, "recuperar_cuenta.html")
        except Cliente.DoesNotExist:
            messages.error(request, "Correo no registrado")
            return render(request, "recuperar_cuenta.html")
    return render(request, 'recuperar_cuenta.html')






def registro(request):
    if request.method == "POST":
        nombre = request.POST.get("nombre").strip()
        apellido = request.POST.get("apellido").strip()
        tipo_documento = request.POST.get("tipo_documento")
        numero_documento = request.POST.get("numero_documento").strip()
        numero_contacto = request.POST.get("numero_contacto").strip()
        correo_electronico = request.POST.get("correo_electronico").strip()
        crear_contrasena = request.POST.get("crear_contrasena").strip()
        confirmar_contrasena = request.POST.get("confirmar_contrasena").strip()
        aceptar = request.POST.get("aceptar")

        errores = []

        if correo_electronico:
            try:
                validate_email(correo_electronico)
                if len(correo_electronico) > 244:
                    errores.append("el correo debe contener menos de 244 caracteres")
            except ValidationError:
                errores.append("el correo electronico no es valido")
            else:
                if Cliente.objects.filter(email=correo_electronico).exists():
                    errores.append("Ya existe un usuario registrado con ese correo.")
        else:
            errores.append("se debe ingresar un correo electronico")

        if nombre:
            if not re.match(r'^[A-Za-záéíóúÁÉÍÓÚñÑ\s]+$', nombre):
                errores.append("el nombre debe contener solo letras")
            else:
                if len(nombre) > 244:
                    errores.append("el nombre debe contener menos de 244 caracteres")
        else:
            errores.append("se debe ingresar un nombre")

        if apellido:
            if not re.match(r'^[A-Za-záéíóúÁÉÍÓÚñÑ\s]+$', apellido):
                errores.append("el apellido debe contener solo letras")
            else:
                if len(apellido) > 244:
                    errores.append("el apellido debe contener menos de 244 caracteres")
        else:
            errores.append("se debe ingresar un apellido")

        if tipo_documento:
            if tipo_documento not in ["1", "2", "3", "4"]:
                errores.append("Selecciona un tipo de documento válido.")
        else:
            errores.append("debe elegir un tipo de documento")

        if crear_contrasena:
            if len(crear_contrasena) < 5 :
                errores.append("La contraseña debe tener minimo 5 caracteres")
        else:
            errores.append("debe ingresar una contraseña")

        if confirmar_contrasena:
            if crear_contrasena != confirmar_contrasena:
                errores.append("Las contraseñas no coinciden.")
        else:
            errores.append("debe ingresar el confirmar contraseña")

        if numero_documento:    
            if not numero_documento.isdigit():
                errores.append("el numero de documento solo debe tener numeros")
            else:
                if int(numero_documento) < 0:
                    errores.append("el numero de documento debe contener solo numeros positivos")
        else:
            errores.append("debe ingresar un numero de documento")

        if numero_contacto:
            if not numero_contacto.isdigit():
                errores.append("El número de contacto debe contener solo números.")
            else:
                if int(numero_contacto) < 0:
                    errores.append("el numero no puede ser negativo")
        else:
            errores.append("debe ingresar un numero de contacto")

        if not aceptar:
            errores.append("Debes aceptar los términos y condiciones.")
            
        
                
        contexto = {
            "form_data": request.POST  
        }


        if errores:
            for error in errores:
                messages.error(request, error)
            return render(request, "registro.html", contexto)


        c = Cliente(
            nombre=nombre,
            apellido=apellido,
            tipoDocumento=tipo_documento,
            numeroDocumento=numero_documento,
            telefono=numero_contacto,
            email=correo_electronico,
            contrasena=hash_password(crear_contrasena),
        )

        c.save()
        messages.success(request, "¡Registro exitoso!")
        return redirect("login")

    else:
        verificar = request.session.get("auth", False)

        if verificar:
            return redirect("index")
        else:
            return render(request, "registro.html",)





def terminos(request):
    return render(request, 'terminos.html')






# crud de clientes
def listar_clientes(request):
    if "auth" not in request.session:
        messages.error(request, "Debes iniciar sesión para acceder a esta sección.")
        return redirect("login")

    id_cliente = request.session["auth"]["id"]

    try:
        cliente = Cliente.objects.get(pk=id_cliente)
    except Cliente.DoesNotExist:
        messages.error(request, "Tu cuenta no existe.")
        return redirect("login")

    if cliente.rol != "administrador":
        messages.error(request, "No tienes permisos para acceder a esta sección.")
        return redirect("index") 
    
    d = Cliente.objects.get(pk=id_cliente)
    c = Cliente.objects.all()

    f = Factura.objects.filter(idCliente__id=id_cliente).exists()
    s = Servicio.objects.filter(idCliente__id=id_cliente).exists()


    contexto = {
        "datos_clientes": c,
        "administrador":d,
        "servicio":s,
        "factura":f,
        "id_cliente":id_cliente
    }

    return render(request, 'clientes/listar_clientes.html', contexto)



def eliminar_clientes(request, id_cliente):
    if "auth" not in request.session:
        messages.error(request, "Debes iniciar sesión para acceder.")
        return redirect("login")

    if request.session["auth"]["rol"] != "administrador":
        messages.error(request, "No tienes permiso para ingresar aqui.")
        return redirect("index")
    
    try:
        c = Cliente.objects.get(pk=id_cliente)

        if c.id == request.session["auth"]["id"]:
            messages.error(request, "No puedes eliminar tu propio usuario mientras estás logueado.")
            return redirect("listar_clientes")

        c.delete()
        messages.success(request, "Eliminado correctamente!")
    except IntegrityError:
        messages.warning(
            request, "Error: no se puede eliminar el cliente")
    except Exception as e:
        messages.error(request, f"Error: {e}")
    return redirect("listar_clientes")



def agregar_clientes(request):
    if "auth" not in request.session:
        messages.error(request, "Debes iniciar sesión para acceder.")
        return redirect("login")

    if request.session["auth"]["rol"] != "administrador":
        messages.error(request, "No tienes permiso para ingresar aqui.")
        return redirect("index")
    
    if request.method == "POST":
        nombre = request.POST.get("nombre").strip()
        apellido = request.POST.get("apellido").strip()
        rol = request.POST.get("rol")
        tipo_documento = request.POST.get("tipo_documento")
        numero_documento = request.POST.get("numero_documento").strip()
        numero_contacto = request.POST.get("numero_contacto").strip()
        correo_electronico = request.POST.get("correo_electronico").strip()
        crear_contrasena = request.POST.get("crear_contrasena").strip()
        confirmar_contrasena = request.POST.get("confirmar_contrasena").strip()
        aceptar = request.POST.get("aceptar")

        errores = []

        if correo_electronico:            
            try:
                validate_email(correo_electronico)
                if len(correo_electronico) > 244:
                    errores.append("el correo debe contener menos de 244 caracteres")
            except ValidationError:
                errores.append("el correo electronico no es valido")
            else:
                if Cliente.objects.filter(email=correo_electronico).exists():
                    errores.append("Ya existe un usuario registrado con ese correo.")
        else:
            errores.append("debe ingresar un correo electronico")


        if nombre:
            if not re.match(r'^[A-Za-záéíóúÁÉÍÓÚñÑ\s]+$', nombre):
                errores.append("el nombre debe contener solo letras")
            else:
                if len(nombre) > 244:
                    errores.append("el nombre debe contener menos de 244 caracteres")
        else:
            errores.append("se debe ingresar un nombre")


        if apellido:
            if not re.match(r'^[A-Za-záéíóúÁÉÍÓÚñÑ\s]+$', apellido):
                errores.append("el apellido debe contener solo letras")
            else:
                if len(apellido) > 244:
                    errores.append("el apellido debe contener menos de 244 caracteres")
        else:
            errores.append("se debe ingresar un apellido")

        if tipo_documento:
            if tipo_documento not in ["1", "2", "3", "4"]:
                errores.append("Selecciona un tipo de documento válido.")
        else:
            errores.append("debe elegir un tipo de documento")

        if crear_contrasena:
            if len(crear_contrasena) < 5:
                errores.append("La contraseña debe tener minimo 5 caracteres.")
        else:
            errores.append("debe ingresar una contraseña")

        if confirmar_contrasena:
            if crear_contrasena != confirmar_contrasena:
                errores.append("Las contraseñas no coinciden.")
        else:
            errores.append("debe ingresar el confirmar contraseña")

        if numero_documento:    
            if not numero_documento.isdigit():
                errores.append("el numero de documento solo debe tener numeros")
            else:
                if int(numero_documento) < 0:
                    errores.append("el numero de documento debe contener solo numeros positivos")
        else:
            errores.append("debe ingresar un numero de documento")

        if numero_contacto:
            if not numero_contacto.isdigit():
                errores.append("El número de contacto debe contener solo números.")
            else:
                if int(numero_contacto) < 0:
                    errores.append("el numero no puede ser negativo")
        else:
            errores.append("debe ingresar un numero de contacto")

        if not aceptar:
            errores.append("Debes aceptar los términos y condiciones.")

        if rol:
            if rol not in ["cliente", "director", "administrador"]:
                errores.append("Selecciona un rol válido.")
        else:
            errores.append("debe elegir un rol")

        contexto = {
            "form_data":request.POST
        }

        if errores:
            for error in errores:
                messages.error(request, error)
            return render(request, "clientes/formulario_clientes.html", contexto)  


        try:
            c = Cliente(
                nombre=nombre,
                apellido=apellido,
                rol = rol,
                telefono=numero_contacto,
                tipoDocumento=tipo_documento,
                numeroDocumento=numero_documento,
                email=correo_electronico,
                contrasena=hash_password(crear_contrasena)
            )
            c.save()
            messages.success(request, "Cliente agregado correctamente!")
            return redirect("listar_clientes")
        except Exception as e:
            errores.append(str(e))
            return render(request, "clientes/formulario_clientes.html", contexto)

    else:
        return render(request, "clientes/formulario_clientes.html")




def editar_clientes(request, id_cliente):
    if "auth" not in request.session:
        messages.error(request, "Debes iniciar sesión para acceder.")
        return redirect("login")

    if request.session["auth"]["rol"] != "administrador":
        messages.error(request, "No tienes permiso para ingresar aqui.")
        return redirect("index")
    
    if request.method == "POST":
        nombre = request.POST.get("nombre").strip()
        apellido = request.POST.get("apellido").strip()
        rol = request.POST.get("rol")
        tipo_documento = request.POST.get("tipo_documento")
        numero_documento = request.POST.get("numero_documento").strip()
        numero_contacto = request.POST.get("numero_contacto").strip()
        correo_electronico = request.POST.get("correo_electronico").strip()
        crear_contrasena = request.POST.get("crear_contrasena").strip()
        confirmar_contrasena = request.POST.get("confirmar_contrasena").strip()

        errores = []

        try:
            c = Cliente.objects.get(pk=id_cliente)
        except Cliente.DoesNotExist:
            errores.append("Cliente no encontrado.")
            return redirect("listar_clientes")

        if correo_electronico:            
            try:
                validate_email(correo_electronico)
                if len(correo_electronico) > 244:
                    errores.append("El correo debe contener menos de 244 caracteres.")
            except ValidationError:
                errores.append("El correo electrónico no es válido.")
            else:
                # Verifica si el correo es diferente y si ya existe otro cliente con ese correo
                if correo_electronico != c.email and Cliente.objects.filter(email=correo_electronico).exists():
                    errores.append("Ya existe un usuario registrado con ese correo.")
        else:
            errores.append("Debe ingresar un correo electrónico.")


        if nombre:
            if not re.match(r'^[A-Za-záéíóúÁÉÍÓÚñÑ\s]+$', nombre):
                errores.append("el nombre debe contener solo letras")
            else:
                if len(nombre) > 244:
                    errores.append("el nombre debe contener menos de 244 caracteres")
        else:
            errores.append("se debe ingresar un nombre")


        if apellido:
            if not re.match(r'^[A-Za-záéíóúÁÉÍÓÚñÑ\s]+$', apellido):
                errores.append("el apellido debe contener solo letras")
            else:
                if len(apellido) > 244:
                    errores.append("el apellido debe contener menos de 244 caracteres")
        else:
            errores.append("se debe ingresar un apellido")

        if tipo_documento:
            if tipo_documento not in ["1", "2", "3", "4"]:
                errores.append("Selecciona un tipo de documento válido.")
        else:
            errores.append("debe elegir un tipo de documento")

        if crear_contrasena:
            if len(crear_contrasena) < 5:
                errores.append("La contraseña debe tener minimo 5 caracteres.")
        else:
            errores.append("debe ingresar una contraseña")

        if confirmar_contrasena:
            if crear_contrasena != confirmar_contrasena:
                errores.append("Las contraseñas no coinciden.")
        else:
            errores.append("debe ingresar el confirmar contraseña")

        if numero_documento:    
            if not numero_documento.isdigit():
                errores.append("el numero de documento solo debe tener numeros")
            else:
                if int(numero_documento) < 0:
                    errores.append("el numero de documento debe contener solo numeros positivos")
        else:
            errores.append("debe ingresar un numero de documento")

        if numero_contacto:
            if not numero_contacto.isdigit():
                errores.append("El número de contacto debe contener solo números.")
            else:
                if int(numero_contacto) < 0:
                    errores.append("el numero no puede ser negativo")
        else:
            errores.append("debe ingresar un numero de contacto")

        if rol:
            if rol not in ["cliente", "director", "administrador"]:
                errores.append("Selecciona un rol válido.")
        else:
            errores.append("debe elegir un rol")

        if errores:
            for error in errores:
                messages.error(request, error)
            return render(request, "clientes/formulario_clientes.html") 


        try:
            c = Cliente.objects.get(pk=id_cliente)

            c.nombre = request.POST.get("nombre")
            c.apellido = request.POST.get("apellido")
            c.rol = request.POST.get("rol")
            c.telefono = request.POST.get("numero_contacto")
            c.tipoDocumento = request.POST.get("tipo_documento")
            c.numeroDocumento = request.POST.get("numero_documento")
            c.email = request.POST.get("correo_electronico")
            c.contrasena = hash_password(request.POST.get("crear_contrasena"))

            c.save()
            messages.success(request, "Cliente actualizado correctamente!")
            return redirect("listar_clientes")
        except Exception as e:
            messages.error(request, f"Error: {e}")
            return redirect("editar_clientes", id_cliente=id_cliente)
    else:
        c = Cliente.objects.get(pk=id_cliente)
        contexto = {"datos": c}
        return render(request, "clientes/formulario_clientes.html", contexto)






def eliminar_eventos_director(request, id_servicio):
    if "auth" not in request.session:
        messages.error(request, "Debes iniciar sesión para acceder.")
        return redirect("login")

    if request.session["auth"]["rol"] != "director":
        messages.error(request, "No tienes permiso para ingresar aqui.")
        return redirect("index")
    
    
    try:
        s = Servicio.objects.get(pk=id_servicio)
        
        if request.session["auth"]["id"] != s.idCliente.id:
            messages.error(request, "No tienes permiso para eliminar este evento")
            return redirect("historial_eventos")
        
        s.delete()
        messages.success(request, "Servicio eliminado con exito!")
        return redirect("historial_eventos")
    except IntegrityError:
        messages.warning(
            request, "Error: No puede eliminar el servicio.")
    except Exception as e:
        messages.error(request, f"Error: {e}")
    return redirect("historial_eventos")




def editar_eventos_director(request, id_servicio):
    if "auth" not in request.session:
        messages.error(request, "Debes iniciar sesión para acceder.")
        return redirect("login")

    if request.session["auth"]["rol"] != "director":
        messages.error(request, "No tienes permiso para ingresar aqui.")
        return redirect("index")
    
    s = Servicio.objects.get(pk=id_servicio)
    
    if request.session["auth"]["id"] != s.idCliente.id:
            messages.error(request, "No tienes permiso para editar este evento")
            return redirect("historial_eventos")
    
    contexto = {
        "servicio": s,
    }

    if request.method == "POST":
        s = Servicio.objects.get(pk=id_servicio)
        s.titulo = request.POST.get("titulo")
        s.informacion = request.POST.get("informacion")
        s.categoria = request.POST.get("categoria")
        s.requisito = request.POST.get("requisito")
        s.cupo_maximo = request.POST.get("cupo_maximo")
        s.direccion = request.POST.get("direccion")
        aceptar = request.POST.get("aceptar")

        if request.FILES.get("imagen"):
            s.imagen = request.FILES.get("imagen")

        errores = []

        if s.titulo:
            if len(s.titulo) > 244:
                errores.append(" el titulo no puede tener mas de 244 caracteres")
        else:
            errores.append("se debe llenar el campo titulo")

        
        if s.informacion:
            if len(s.informacion) > 500:
                errores.append("la informacion no debe tener mas de 500 caracteres")
        else:
            errores.append("debes completar el campo informacion")

        
        if s.categoria:
            if len(s.categoria) > 244:
                errores.append("la categoria no puede tener mas de 244 caracteres")
        else:
            errores.append("el campo categoria se debe llenar")

        if s.requisito:
            if len(s.requisito) > 500:
                errores.append("los requisitos no pueden sobrepasar los 500 caracteres")
        else:
            errores.append("el campo requisito se debe llenar")

        
        if s.imagen:
            try:
                validate_image_file(s.imagen)
            except ValidationError as e:
                errores.append(str(e))
        else:
            errores.append("debes subir una imagen del evento")


        if s.cupo_maximo:
            if not s.cupo_maximo.isdigit():
                errores.append("la cantidad maxima debe contener solo numeros")
            else:
                if int(s.cupo_maximo) <= 0:
                    errores.append("la cantidad maxima debe contener numeros positivos")

                if int(s.cupo_maximo) < int(s.cupos_vendidos):
                    errores.append("la cantidad de cupos maximos debe ser mayor a los cupos vendidos")
                
        else:
            errores.append("el campo cupo maximo es obligatorio")
        
        if s.direccion:
            if len(s.direccion) > 244:
                errores.append("la direccion no puede contener mas de 244 caracteres")
        else:
            errores.append("el campo direccion es obligatorio")

        if not aceptar:
            errores.append("se deben aceptar terminos y condiciones") 
          

        if errores:
            for error in errores:
                messages.error(request, error)
            return render(request, "crear_evento.html", contexto)

        try:
            s.save()

            messages.success(request, "Se edito de manera correcta")
            return redirect("historial_eventos")
        except Exception as e:
            messages.error(request, f"Error: {e}")
            return redirect("editar_eventos_director", id_servicio=id_servicio)
    else:
        return render(request, "crear_evento.html", contexto)






# crud eventos
def listar_eventos(request):
    if "auth" not in request.session:
        messages.error(request, "Debes iniciar sesión para acceder a esta sección.")
        return redirect("login")

    id_cliente = request.session["auth"]["id"]

    try:
        cliente = Cliente.objects.get(pk=id_cliente)
    except Cliente.DoesNotExist:
        messages.error(request, "Tu cuenta no existe.")
        return redirect("login")

    if cliente.rol != "administrador":
        messages.error(request, "No tienes permisos para acceder a esta sección.")
        return redirect("index") 
    
    d = Cliente.objects.get(pk=id_cliente)
    s = Servicio.objects.all()

    fac = Factura.objects.filter(idCliente__id=id_cliente).exists()
    ser = Servicio.objects.filter(idCliente__id=id_cliente).exists()
    contexto = {
        "administrador": d,
        "datos_servicios": s,
        "servicio":ser,
        "factura":fac,
        "id_cliente":id_cliente
    }
    return render(request, 'eventos/listar_eventos.html', contexto)



def crear_formulario_evento(request):
    if "auth" not in request.session:
        messages.error(request, "Debes iniciar sesión para acceder.")
        return redirect("login")

    if request.session["auth"]["rol"] != "administrador":
        messages.error(request, "No tienes permiso para ingresar aqui.")
        return redirect("index")

    fecha_actual = timezone.now().strftime('%Y-%m-%dT%H:%M')


    c = Cliente.objects.all()
    contexto = {
        "clientes": c,
        "fecha_actual": fecha_actual
    }  

    if request.method == "POST":
        titulo = request.POST.get("titulo")
        informacion = request.POST.get("informacion")
        precio = request.POST.get("precio")
        categoria = request.POST.get("categoria")
        requisito = request.POST.get("requisito")
        fecha = request.POST.get("fecha")
        cupo_maximo = request.POST.get("cupo_maximo")
        imagen = request.FILES.get("imagen")
        direccion = request.POST.get("direccion")
        idCliente = request.POST.get("idCliente")
        aceptar = request.POST.get("aceptar")
        cupos_vendidos = request.POST.get("cupos_vendidos")

        errores = []

        try:
            idCliente = Cliente.objects.get(pk=idCliente)
        except Cliente.DoesNotExist:
            errores.append("seleccionar un cliente valido")

        if titulo:
            if len(titulo) > 244:
                errores.append("el titulo no puede tener mas de 244 caracteres")
        else:
            errores.append("el campo titulo es obligatorio")


        if informacion:
            if len(informacion) > 500:
                errores.append("la informacion no debe tener mas de 500 caracteres")
        else:
            errores.append("el campo informacion es obligatorio")

        if precio:
            if not precio.isdigit():
                errores.append("el precio debe contener solo numeros")
            else:
                if float(precio) < 0:
                    errores.append("el precio no puede contener valores negativos")
        else:
            errores.append("el campo precio es obligatorio")

        if categoria:
            if len(categoria) > 244:
                errores.append("la categoria no puede tener mas de 244 caracteres")
        else:
            errores.append("el campo categoria es obligatorio")

        if requisito:
            if len(requisito) > 500:
                errores.append("los requisitos no pueden sobrepasar los 500 caracteres")
        else:
            errores.append("el campo requisito es obligatorio")

        if imagen:
            try:
                validate_image_file(imagen)
            except ValidationError as e:
                errores.append(str(e))
        else:
            errores.append("debes subir una imagen del evento")

        
        if fecha:
            try:
                fecha = datetime.datetime.strptime(fecha, "%Y-%m-%dT%H:%M").date()

                if fecha < datetime.date.today():
                    errores.append("La fecha no puede ser anterior a hoy.")
            except ValueError:
                errores.append("La fecha debe tener el formato YYYY-MM-DDTHH:MM.")
        else:
            errores.append("El campo fecha es obligatorio.")


        if cupo_maximo:
            if not cupo_maximo.isdigit():
                errores.append("la cantidad maxima debe contener solo numeros")
            else:
                if int(cupo_maximo) <= 0:
                    errores.append("la cantidad maxima debe contener numeros positivos")
        else:
            errores.append("el campo cupo maximo es obligatorio")


        if cupos_vendidos:
            if cupos_vendidos:
                if not cupos_vendidos.isdigit():
                    errores.append("el campo de cupos maximos solo debe contener solo numeros")
                else:
                    if int(cupos_vendidos) < 0:
                        errores.append("la cantidad de cupos vendidos debe contener numeros positivos")
        else:
            errores.append("el campo cupos vendidos es obligatorio")
        

        if direccion:
            if len(direccion) > 244:
                errores.append("la direccion no puede contener mas de 244 caracteres")
        else:
            errores.append("el campo direccion es obligatorio")


        if not aceptar:
            errores.append("se deben aceptar terminos y condiciones") 

        contexto = {
            "clientes": c,
            "fecha_actual": fecha_actual,
            "form_data":request.POST
        } 


        if errores:
            for error in errores:
                messages.error(request, error)
            return render(request, "eventos/formulario_eventos.html", contexto)


        try:
            s = Servicio(
                titulo=titulo,
                informacion=informacion,
                precio=precio,
                categoria=categoria,
                requisito=requisito,
                fecha=fecha,
                cupo_maximo=cupo_maximo,
                imagen=imagen,
                direccion=direccion,
                idCliente=idCliente,
                cupos_vendidos=cupos_vendidos,
            )
            s.save()

            if idCliente.rol == "cliente":
                idCliente.rol = "director"
                idCliente.save()

            messages.success(request, "Servicio agregado correctamente!")
            return redirect("listar_eventos")
        except Exception as e:
            messages.error(request, f"Error: {e}")
            return redirect("crear_formulario_evento")
    else:
        return render(request, "eventos/formulario_eventos.html", contexto)



def validate_image_file(value):
    try:
        image = Image.open(value)
        if image.format not in ['JPEG', 'PNG']:
            raise ValidationError("Solo se permiten archivos .png y .jpg")
    except Exception:
        raise ValidationError("Archivo de imagen no válido")
        





def editar_formulario_eventos(request, id_servicio):
    if "auth" not in request.session:
        messages.error(request, "Debes iniciar sesión para acceder.")
        return redirect("login")

    if request.session["auth"]["rol"] != "administrador":
        messages.error(request, "No tienes permiso para ingresar aqui.")
        return redirect("index")
    
    fecha_actual = timezone.now().strftime('%Y-%m-%dT%H:%M')

    s = Servicio.objects.get(pk=id_servicio)
    c = Cliente.objects.all()
    contexto = {
        "servicio": s,
        "clientes": c,
        "cliente_seleccionado": s.idCliente.id, 
        "fecha_actual": fecha_actual
    }

    if request.method == "POST":
        s = Servicio.objects.get(pk=id_servicio)
        s.titulo = request.POST.get("titulo")
        s.informacion = request.POST.get("informacion")
        s.precio = request.POST.get("precio")
        s.categoria = request.POST.get("categoria")
        s.requisito = request.POST.get("requisito")
        s.fecha = request.POST.get("fecha")
        s.cupo_maximo = request.POST.get("cupo_maximo")
        s.cupos_vendidos = request.POST.get("cupos_vendidos")
        s.estado = request.POST.get("estado")
        s.direccion = request.POST.get("direccion")
        s.idCliente = Cliente.objects.get(pk=request.POST.get("idCliente"))
        if request.FILES.get("imagen"):
            s.imagen = request.FILES.get("imagen")
        aceptar = request.POST.get("aceptar")

        errores = []

        try: 
            id_cliente_valor = request.POST.get("idCliente")
            idCliente = Cliente.objects.get(pk=id_cliente_valor)
        except Cliente.DoesNotExist:
            errores.append("seleccionar un cliente valido")

        if s.titulo:
            if len(s.titulo) > 244:
                errores.append(" el titulo no puede tener mas de 244 caracteres")
        else:
            errores.append("se debe llenar el campo titulo")

        
        if s.informacion:
            if len(s.informacion) > 500:
                errores.append("la informacion no debe tener mas de 500 caracteres")
        else:
            errores.append("debes completar el campo informacion")

        if s.precio:
            if not s.precio.isdigit():
                errores.append("el precio debe contener solo numeros")
            else:
                if float(s.precio) < 0:
                    errores.append("el precio no puede contener valores negativos")
        else:
            errores.append("se debe llenar el campo precio")
        
        if s.categoria:
            if len(s.categoria) > 244:
                errores.append("la categoria no puede tener mas de 244 caracteres")
        else:
            errores.append("el campo categoria se debe llenar")

        if s.requisito:
            if len(s.requisito) > 500:
                errores.append("los requisitos no pueden sobrepasar los 500 caracteres")
        else:
            errores.append("el campo requisito se debe llenar")

        
        if s.imagen:
            try:
                validate_image_file(s.imagen)
            except ValidationError as e:
                errores.append(str(e))
        else:
            errores.append("debes subir una imagen del evento")

        if s.fecha:
            try:
                s.fecha = datetime.datetime.strptime(s.fecha, "%Y-%m-%dT%H:%M").date()

                if s.fecha < datetime.date.today():
                    errores.append("La fecha no puede ser anterior a hoy.")
            except ValueError:
                errores.append("La fecha debe tener el formato YYYY-MM-DDTHH:MM.")
        else:
            errores.append("El campo fecha es obligatorio.")

        if s.estado:
            if s.estado not in ["disponible", "indisponible"]:
                errores.append("Selecciona un estado válido.")
        else:
            errores.append("debe elegir estado")

        if s.cupo_maximo:
            if not s.cupo_maximo.isdigit():
                errores.append("la cantidad maxima debe contener solo numeros")
            else:
                if int(s.cupo_maximo) <= 0:
                    errores.append("la cantidad maxima debe contener numeros positivos")
        else:
            errores.append("el campo cupo maximo es obligatorio")

        if s.cupos_vendidos:
            if not s.cupos_vendidos.isdigit():
                errores.append("la cantidad maxima debe contener solo numeros")
            else:
                if int(s.cupos_vendidos) < 0:
                    errores.append("la cantidad maxima debe contener numeros positivos")
        else:
            errores.append("el campo cupo maximo es obligatorio")
        
        if s.direccion:
            if len(s.direccion) > 244:
                errores.append("la direccion no puede contener mas de 244 caracteres")
        else:
            errores.append("el campo direccion es obligatorio")
          
        if not aceptar:
            errores.append("se deben aceptar terminos y condiciones") 


        if errores:
            for error in errores:
                messages.error(request, error)
            return render(request, "eventos/formulario_eventos.html", contexto)

        try:
            s.save()

            if idCliente.rol == "cliente":
                idCliente.rol = "director"
                idCliente.save()

            messages.success(request, "Se edito de manera correcta")
            return redirect("listar_eventos")
        except Exception as e:
            messages.error(request, f"Error: {e}")
            return redirect("editar_formulario_eventos", id_servicio=id_servicio)
    else:
        return render(request, "eventos/formulario_eventos.html", contexto)



def eliminar_eventos_administrador(request, id_servicio):
    if "auth" not in request.session:
        messages.error(request, "Debes iniciar sesión para acceder.")
        return redirect("login")

    if request.session["auth"]["rol"] != "administrador":
        messages.error(request, "No tienes permiso para ingresar aqui.")
        return redirect("index")
    
    try:
        s = Servicio.objects.get(pk=id_servicio)
        s.delete()
        messages.success(request, "Servicio eliminado con exito!")
    except IntegrityError:
        messages.warning(
            request, "Error: No puede eliminar el servicio, está en uso.")
    except Exception as e:
        messages.error(request, f"Error: {e}")
    return redirect("listar_eventos")



def formulario_pago(request):
    if "auth" not in request.session:
        messages.error(request, "Debes iniciar sesión para realizar un pago.")
        return redirect("login")
    
    carrito = request.session.get("carrito", {})

    if not carrito:
        messages.error(request, "el carrito esta vacio")
        return redirect("carrito_vista")
    
    contexto = {
    "anos": range(2025, 2041),
    "meses": range(1, 13),
    }
    
    return render(request, "formulario_pago.html", contexto)



def procesar_pago(request):
    if "auth" not in request.session:
        messages.error(request, "Debes iniciar sesión para acceder.")
        return redirect("login")

    carrito = request.session.get("carrito", {})
    if not carrito:
        messages.error(request, "el carrito esta vacio")
        return redirect("carrito_vista")
    
    
    servicios = Servicio.objects.all()
    for servicio in servicios:
        if servicio.fecha < timezone.now() or servicio.cupos_vendidos >= servicio.cupo_maximo:
            if servicio.estado != 'indisponible':
                servicio.estado = 'indisponible'
                servicio.save()

    for carro in carrito.values():
        try:
            servicio = Servicio.objects.get(id=carro["id"])
            if servicio.estado != "disponible":
                messages.error(request, f"El evento '{servicio.titulo}' ya no está disponible.")
                return redirect("carrito_vista")
        except Servicio.DoesNotExist:
            messages.error(request, "Uno de los eventos en el carrito ya no existe.")
            return redirect("carrito_vista")



    contexto = {
        "anos": range(2025, 2041),
        "meses": range(1, 13),
    }

    if request.method == "POST":
        metodo_pago = request.POST.get("metodo_pago")
        titular = request.POST.get("titular")
        anos = request.POST.get("anos")
        numero_tarjeta = request.POST.get("numero_tarjeta")
        mes = request.POST.get("mes")
        ccv =  request.POST.get("ccv")
        aceptar = request.POST.get("aceptar")

        carrito = request.session.get("carrito", {})

        errores = []

        if metodo_pago:
            if not metodo_pago.isdigit():
                errores.append("debes elegir un metodo de pago valido")
            if metodo_pago not in ["1", "2"]:
                errores.append("Selecciona un metodo de pago válido.")
        else:
            errores.append("debes ingresar un metodo de pago")
    

        if titular:
            if not re.match(r'^[A-Za-záéíóúÁÉÍÓÚñÑ\s]+$', titular):
                errores.append("el titular debe contener solo letras")
        else:
            errores.append("debes ingresar un titular")


        if numero_tarjeta:
            if not numero_tarjeta.isdigit():
                errores.append("debe ingresar solo numeros")
            else:
                if len(numero_tarjeta) < 13 or len(numero_tarjeta) > 19:
                    errores.append("debe ingresar un numero de tarjeta valido")
        else:
            errores.append("debe ingresar un numero tarjeta")


        if mes:
            if not mes.isdigit():
                errores.append("El mes debe ser un número.")
            else:
                mes = int(mes)
                if mes < 1 or mes > 12:
                    errores.append("El año debe estar entre enero y diciembre")
        else:
            errores.append("Debes seleccionar un mes.")


        if anos:
            if not anos.isdigit():
                errores.append("El año debe ser un número.")
            else:
                anos = int(anos)
                if anos < 2025 or anos > 2040:
                    errores.append("El año debe estar entre 2025 y 2040.")
        else:
            errores.append("Debes seleccionar un año.")

        if ccv:
            if not ccv.isdigit():
                errores.append("El ccv debe ser un número.")
            else:
                if len(ccv) < 3 or len(ccv) > 4: 
                    errores.append("ingresar un ccv valido")
        else:
            errores.append("Debes ingresar un ccv.")

                        
        if not aceptar:
            errores.append("se debe aceptar terminos y condiciones")

        if not carrito:
            errores.append("Tu carrito está vacío.")

        if errores:
            for error in errores:
                messages.error(request, error)
            return render(request, "formulario_pago.html", contexto)

        

        try:
            id_cliente = request.session["auth"]["id"]
            cliente = Cliente.objects.get(id=id_cliente)

            total = sum(item["total"] for item in carrito.values())

            f = Factura(
                fecha=timezone.now(),
                total=total,
                metodoPago=metodo_pago,
                idCliente=cliente
            )
            f.save()

            for servicio_id, item in carrito.items():
                servicio = Servicio.objects.get(id=int(servicio_id))
                cantidad = item["cantidad"]


                d = DetalleFactura(
                    precioUnitario=item["precio"],
                    precioComision=item["comision"],
                    totalNoComision=item["totalSinComision"],
                    cantidad=cantidad,
                    subtotal=item["total"],
                    idServicio=servicio,
                    idFactura=f
                )
                d.save()
                
                servicio.cupos_vendidos += cantidad
                servicio.save()


            request.session["carrito"] = {}


            detalles = DetalleFactura.objects.filter(idFactura=f)

            contexto = {
                "factura":f,
                "detalles":detalles
            }

            # Generar HTML a partir de plantilla
            html_string = render_to_string("facturapdf.html", contexto)

            html = HTML(string=html_string)
            pdf = html.write_pdf()

            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = f'inline; filename="factura_{f.id}.pdf"'



            try:
                email = EmailMessage(
                    subject="FullCrazy - Factura",
                    body="""
                        Gracias por tu compra. Adjunto encontrarás tu factura en formato PDF.
                    """,
                    from_email=settings.EMAIL_HOST_USER,
                    to=[cliente.email],
                )
                email.attach(f"factura_{f.id}.pdf", pdf, "application/pdf")
                email.content_subtype = "html"  # Para permitir HTML en el cuerpo si usas body con HTML
                email.send(fail_silently=False)

                messages.success(request, "compra hecha correctamente, revisa el gmail para ver la factura")
                return redirect("eventos_comprados")
            
            except Exception as e:
                messages.error(request, f"error:{e}")
                return redirect("carrito_vista")

        except Exception as e:
            import traceback
            print(traceback.format_exc())
            messages.error(request, f"Hubo un error al procesar el pago: {e}")
            return redirect("carrito_vista")

    else:
        return render(request, "formulario_pago.html")
        



def contactanos(request):
    if request.method == 'POST':
        nombre = request.POST.get("nombre")
        email = request.POST.get("email")
        mensaje = request.POST.get("mensaje")

        errores = []


        if nombre:
            if len(nombre) > 244:
                errores.append("debe ingresar un nombre mas corto")
            else:
                if not re.match(r'^[A-Za-záéíóúÁÉÍÓÚñÑ\s]+$', nombre):
                    errores.append("el titular debe contener solo letras")
        else:
            errores.append("debe ingresar un nombre")

        if email:
            try:
                validate_email(email)
                if len(email) > 244:
                    errores.append("el correo debe contener menos de 244 caracteres")
            except ValidationError:
                errores.append("el correo electronico no es valido")
        else:
            errores.append("debe ingresar un correo")

        if mensaje:
            if len(mensaje) > 500:
                errores.append("debe ingresar un mensaje de menos de 500 caracteres")
        else:
            errores.append("debe ingresar un mensaje")

        if errores:
            for error in errores:
                messages.error(request, error)
            return render(request, "index.html")

        try:
            html_messages = f"""
                FullCrazy django - Contáctanos <br>
                <strong> De: </strong> {nombre} - {email} <br>

                <p>{mensaje}</p>
            """
            send_mail(
                "FullCrazy - CONTÁCTANOS",
                "",
                settings.EMAIL_HOST_USER,
                ["dmx64861@gmail.com"], 
                fail_silently=False,
                html_message=html_messages
            )
            messages.success(request, "se envio correctamente el mensaje")
            return render(request, "index.html")
        except Exception as e:
            messages.error(request, f"{e}")
            return render(request, "index.html")
    else:
        return render(request, "index.html")




def cambiar_contrasena(request):
    token = request.GET.get("token")
    user_id_encoded = request.GET.get("id")

    if not token or not user_id_encoded:
        messages.error(request, "Faltan datos en el enlace.")
        return redirect('recuperar_cuenta')

    try:
        user_id = int(base64.urlsafe_b64decode(user_id_encoded).decode())
        signer.unsign(token, max_age=3600)  # Opcional: token expira en 1 hora

        errores = []

        cliente = Cliente.objects.get(id=user_id)

        if request.method == 'POST':
            nueva_contra = request.POST.get("nueva_contrasena")
            confirmar_contrasena = request.POST.get("confirmar_contrasena")

            if nueva_contra and confirmar_contrasena:
                if nueva_contra != confirmar_contrasena:
                    errores.append("las contraseñas no coinciden")
                if len(nueva_contra) < 5 or len(confirmar_contrasena) < 5:
                    errores.append("las contraseñas deben ser mayores a 5 caracteres")
            else:
                errores.append("debe ingresar las contraseñas")

            if errores:
                for error in errores:
                    messages.error(request, error)
                return render(request, "cambiar_contrasena.html")    

            cliente.contrasena = hash_password(nueva_contra)
            cliente.save()
            messages.success(request, "Contraseña cambiada con éxito.")
            return redirect('login')

        return render(request, "cambiar_contrasena.html", {"cliente": cliente})
    
    except (Cliente.DoesNotExist, ValueError, BadSignature, SignatureExpired):
        messages.error(request, "El enlace es inválido o ha expirado.")
        return redirect('recuperar_cuenta')
    


def buscador(request):
    buscar = request.GET.get("buscar")

    if buscar:
        eventos = Servicio.objects.filter(titulo__icontains=buscar, estado = 'disponible')
    else:
        eventos = Servicio.objects.filter(estado = 'disponible')
    
    contexto = {
        "datos_servicios": eventos
    }

    return render(request, "eventos_generales.html", contexto)




def participantes(request, id_servicio):

    evento = Servicio.objects.get(id=id_servicio)

    detalle_factura = DetalleFactura.objects.filter(idServicio = evento)


    contexto = {
        "evento":evento,
        "detalle_factura":detalle_factura
    }
    return render(request, "participantes.html", contexto)





# crud facturas
def listar_facturas(request):

    if "auth" not in request.session:
        messages.error(request, "Debes iniciar sesión para acceder a esta sección.")
        return redirect("login")

    id_cliente = request.session["auth"]["id"]

    try:
        cliente = Cliente.objects.get(pk=id_cliente)
    except Cliente.DoesNotExist:
        messages.error(request, "Tu cuenta no existe.")
        return redirect("login")

    if cliente.rol != "administrador":
        messages.error(request, "No tienes permisos para acceder a esta sección.")
        return redirect("index") 
    
    facturas = Factura.objects.all()

    contexto = {
        "facturas":facturas
    }

    return render(request, "facturas/listar_facturas.html", contexto)






# crud detalle_factura
def listar_detalle_facturas(request):
    
    if "auth" not in request.session:
        messages.error(request, "debes iniciar sesion para ingresar a los paneles")
        return redirect("login")
    
    id_cliente = request.session["auth"]["id"]

    try:
        cliente = Cliente.objects.get(id = id_cliente)
    except Cliente.DoesNotExist:
        messages.error(request, "el cliente no existe debe iniciar sesion")
        return redirect("login")
    
    if cliente.rol != "administrador":
        messages.error(request, "debe ser un administrador para ingresar aqui")
        return redirect("index")
    
    datos = DetalleFactura.objects.all()

    contexto = {
        "detalle_facturas":datos
    }

    return render(request, "detalle_facturas/listar_detalle_facturas.html", contexto)




def factura_pdf(request, id_factura):
    if "auth" not in request.session:
        messages.error(request, "Debes iniciar sesión para acceder.")
        return redirect("login")

    # Buscar factura o lanzar 404
    factura = get_object_or_404(Factura, id=id_factura)

    if request.session["auth"]["id"] != factura.idCliente.id:
        messages.error(request, "No tienes permiso para ver esta factura.")
        return redirect("index")

    detalles = DetalleFactura.objects.filter(idFactura=factura)

    contexto = {
        "factura":factura,
        "detalles":detalles
    }

    # Generar HTML a partir de plantilla
    html_string = render_to_string("facturapdf.html", contexto)

    # Generar PDF usando WeasyPrint
    html = HTML(string=html_string)
    pdf = html.write_pdf()

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="factura_{id_factura}.pdf"'
    return response



