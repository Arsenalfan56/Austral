from django.urls import path
from . import views

app_name = 'bi'

urlpatterns = [
    path('', views.dashboard_general, name='dashboard_general'),
    path('calibraciones/', views.dashboard_calibraciones, name='dashboard_calibraciones'),
    path('ordenes/', views.dashboard_ordenes, name='dashboard_ordenes'),
    path('kanban/', views.kanban_ordenes, name='kanban_ordenes'),
    path('generar-alertas/', views.generar_alertas, name='generar_alertas'),
]