# logistica/urls.py
from django.urls import path
from . import views

app_name = 'logistica'

urlpatterns = [
    path('dashboard/', views.dashboard_bi, name='dashboard'),
    path('registro/', views.registro_usuario, name='registro'),
    path('registro/exitoso/', views.registro_exitoso, name='registro_exitoso'),
    path('ajax/obtener-cliente/', views.obtener_cliente_por_equipo, name='obtener_cliente_por_equipo'),
    # 🆕 NUEVA URL para verificar si un equipo tiene diagnóstico
    path('ajax/obtener-diagnostico/', views.obtener_diagnostico, name='obtener_diagnostico'),
]