# logistica/admin.py
# logistica/admin.py
from django.utils.safestring import mark_safe
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html

# Importamos los modelos
from .models import (
    Equipo, PerfilUsuario, RegistroCalibracion, 
    OrdenVibracion, DiagnosticoPredictivo, RegistroInforme
)

# Importamos los formularios personalizados
from .forms import DiagnosticoPredictivoForm, RegistroInformeForm


# ==========================================
# 1. CONFIGURACIÓN DE LA FOTO DE PERFIL
# ==========================================
class PerfilUsuarioInline(admin.StackedInline):
    model = PerfilUsuario
    can_delete = False
    verbose_name_plural = 'Información de Perfil (Foto)'
    fields = ('foto', 'telefono', 'nombre_completo')


class UserAdmin(BaseUserAdmin):
    inlines = (PerfilUsuarioInline,)
    list_display = list(BaseUserAdmin.list_display) + ['ver_foto']

    def ver_foto(self, obj):
        if hasattr(obj, 'perfil') and obj.perfil.foto:
            return format_html('<img src="{}" width="40" height="40" style="border-radius:50%;" />', obj.perfil.foto.url)
        return "Sin foto"
    ver_foto.short_description = "Foto"

admin.site.unregister(User)
admin.site.register(User, UserAdmin)


# ==========================================
# 2. REGISTROS NORMALES (CAPITULO IV)
# ==========================================
@admin.register(RegistroCalibracion)
class RegistroCalibracionAdmin(admin.ModelAdmin):
    list_display = ('equipo', 'codigo_serial', 'cliente', 'tiene_precision', 'tiene_confiabilidad', 'cumple_estandares', 'es_efectiva')
    list_editable = ('tiene_precision', 'tiene_confiabilidad', 'cumple_estandares')
    list_filter = ('es_efectiva', 'cliente')

    def changelist_view(self, request, extra_context=None):
        total = RegistroCalibracion.objects.count()
        efectivas = RegistroCalibracion.objects.filter(es_efectiva=True).count()
        no_efectivas = RegistroCalibracion.objects.filter(es_efectiva=False).count()
        
        if total > 0:
            porcentaje = round((efectivas / total) * 100, 2)
        else:
            porcentaje = 0
        
        mensaje = mark_safe(
            f'<div style="background-color: #f0f8ff; padding: 10px; border: 1px solid #ccc; margin-bottom: 10px;">'
            f'<strong>Resumen Automático (Fase I):</strong><br>'
            f'Total de calibraciones registradas: <strong>{total}</strong><br>'
            f'Calibraciones Efectivas: <strong style="color: green;">{efectivas}</strong><br>'
            f'Calibraciones No Efectivas: <strong style="color: red;">{no_efectivas}</strong><br>'
            f'Porcentaje de efectividad actual: <strong>{porcentaje}%</strong>'
            f'</div>'
        )
        
        extra_context = extra_context or {}
        extra_context['resumen_automatico'] = mensaje
        return super().changelist_view(request, extra_context=extra_context)


@admin.register(OrdenVibracion)
class OrdenVibracionAdmin(admin.ModelAdmin):
    list_display = (
        'equipo', 
        'codigo_serial', 
        'cliente', 
        'diagnostico_completo', 
        'cumple_estandares', 
        'registro_estructurado', 
        'es_efectiva'
    )
    list_editable = ('diagnostico_completo', 'cumple_estandares', 'registro_estructurado')
    list_filter = ('es_efectiva', 'cliente')

    def changelist_view(self, request, extra_context=None):
        total = OrdenVibracion.objects.count()
        efectivas = OrdenVibracion.objects.filter(es_efectiva=True).count()
        no_efectivas = OrdenVibracion.objects.filter(es_efectiva=False).count()
        
        if total > 0:
            porcentaje = round((efectivas / total) * 100, 2)
        else:
            porcentaje = 0
        
        mensaje = mark_safe(
            f'<div style="background-color: #fff8e1; padding: 10px; border: 1px solid #ffc107; margin-bottom: 10px;">'
            f'<strong>Resumen Automático (Fase II - Órdenes de Vibración):</strong><br>'
            f'Total de órdenes registradas: <strong>{total}</strong><br>'
            f'Órdenes Efectivas (cumplen los 3 indicadores): <strong style="color: green;">{efectivas}</strong><br>'
            f'Órdenes No Efectivas: <strong style="color: red;">{no_efectivas}</strong><br>'
            f'Porcentaje de efectividad actual: <strong>{porcentaje}%</strong> '
            f'(Criterio esperado: 95%)'
            f'</div>'
        )
        
        extra_context = extra_context or {}
        extra_context['resumen_automatico'] = mensaje
        return super().changelist_view(request, extra_context=extra_context)


@admin.register(DiagnosticoPredictivo)
class DiagnosticoPredictivoAdmin(admin.ModelAdmin):
    form = DiagnosticoPredictivoForm
    list_display = ('id', 'equipo', 'codigo_serial', 'cliente', 'servicio', 'fecha_inicio', 'fecha_fin', 'tiempo_total_minutos')
    list_filter = ('cliente', 'servicio', 'fecha_inicio')
    search_fields = ('equipo', 'cliente', 'codigo_serial')
    readonly_fields = ('tiempo_total_minutos',)
    date_hierarchy = 'fecha_inicio'


# ==========================================
# 3. ADMIN DE REGISTROS DE INFORMES (KPI DINÁMICO)
# ==========================================
@admin.register(RegistroInforme)
class RegistroInformeAdmin(admin.ModelAdmin):
    form = RegistroInformeForm
    
    list_display = (
        'id', 
        'titulo', 
        'equipo', 
        'codigo_serial',
        'cliente', 
        'servicio', 
        'fecha_inicio_display',
        'fecha_fin_display',
        'tiempo_generacion_horas'
    )
    list_filter = ('cliente', 'servicio', 'hora_inicio')
    search_fields = ('titulo', 'equipo', 'cliente', 'codigo_serial')
    readonly_fields = ('tiempo_generacion_horas',)
    date_hierarchy = 'hora_inicio'

    def fecha_inicio_display(self, obj):
        return obj.hora_inicio
    fecha_inicio_display.short_description = "Fecha de y Hora Inicio"

    def fecha_fin_display(self, obj):
        return obj.hora_fin
    fecha_fin_display.short_description = "Fecha y Hora de Fin"