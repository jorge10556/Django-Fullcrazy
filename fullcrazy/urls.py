from django.urls import path, include
from . import views

urlpatterns = [
    # path('administrador/', views.administrador ,name='administrador' ),
    path('carrito_vista/', views.carrito_vista ,name='carrito_vista' ),
    path('agregar_carrito/<int:id_servicio>/', views.agregar_carrito, name='agregar_carrito'),
    path('eliminar_carrito/<int:id_servicio>/', views.eliminar_carrito, name='eliminar_carrito'),
    path('actualizar_cantidad/<int:id_servicio>/', views.actualizar_cantidad, name='actualizar_cantidad'),

    path('compra_directa/<int:id_servicio>/', views.compra_directa, name='compra_directa'),



    path('evento_especifico/<int:id_servicio>/', views.evento_especifico ,name='evento_especifico' ),
    path('eventos_generales/', views.eventos_generales ,name='eventos_generales' ),
    path('factura/<int:id_factura>/', views.factura ,name='factura' ),
    path('gestion_evento/', views.gestion_evento ,name='gestion_evento' ),
    path('cliente/', views.cliente ,name='cliente' ),
    path('editar_perfil/<int:id_cliente>/', views.editar_perfil, name='editar_perfil'),


    path('eventos_comprados/', views.eventos_comprados ,name='eventos_comprados' ),


    path('', views.index ,name='index' ),
    path('login/', views.login ,name='login' ),
    path('director/', views.director ,name='director' ),
    path('recuperar_cuenta/', views.recuperar_cuenta ,name='recuperar_cuenta' ),
    path('registro/', views.registro ,name='registro' ),
    path('terminos/', views.terminos ,name='terminos' ),
    path('cambiar_contrasena/', views.cambiar_contrasena,name='cambiar_contrasena'),
    path('logout/', views.logout, name='logout'),
    path('formulario_pago/', views.formulario_pago, name='formulario_pago'),
    path('procesar_pago/', views.procesar_pago, name='procesar_pago'),

    #crud de clientes
    path('listar_clientes/', views.listar_clientes, name='listar_clientes'),
    path('eliminar_clientes/<int:id_cliente>/', views.eliminar_clientes, name='eliminar_clientes'),
    path('agregar_clientes/', views.agregar_clientes, name='agregar_clientes'),
    path('editar_clientes/<int:id_cliente>/', views.editar_clientes, name='editar_clientes'),


    #crud de directores
    path('eliminar_eventos_director/<int:id_servicio>/', views.eliminar_eventos_director, name='eliminar_eventos_director'),
    path('editar_eventos_director/<int:id_servicio>/', views.editar_eventos_director, name='editar_eventos_director'),
    path('crear_evento/', views.crear_evento,name='crear_evento' ),
    path('historial_eventos/', views.historial_eventos ,name='historial_eventos' ),

    path('participantes/<int:id_servicio>/', views.participantes ,name='participantes' ),


    #crud de eventos
    path('listar_eventos/', views.listar_eventos, name='listar_eventos' ), 
    path('crear_formulario_evento/', views.crear_formulario_evento, name='crear_formulario_evento'),
    path('editar_formulario_eventos/<int:id_servicio>/', views.editar_formulario_eventos, name='editar_formulario_eventos'),
    path('eliminar_eventos_administrador/<int:id_servicio>/', views.eliminar_eventos_administrador, name='eliminar_eventos_administrador'),


    #crud de facturas
    path('listar_facturas/', views.listar_facturas, name='listar_facturas' ), 



    #crud de detalle facturas
    path('listar_detalle_facturas/', views.listar_detalle_facturas, name='listar_detalle_facturas' ), 



    path('contactanos/', views.contactanos ,name='contactanos' ),
    path('buscador/', views.buscador ,name='buscador' ),


    path("factura_pdf/<int:id_factura>/pdf/", views.factura_pdf, name="factura_pdf"),


]


