# bi/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import Alerta, KPIRegistro


# ==========================================
# ADMIN DE ALERTAS
# ==========================================
@admin.register(Alerta)
class AlertaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'tipo', 'fecha', 'leida', 'usuario', 'link')
    list_filter = ('tipo', 'leida', 'fecha')
    search_fields = ('titulo', 'descripcion')
    list_editable = ('leida',)
    date_hierarchy = 'fecha'
    ordering = ('-fecha',)
    
    fieldsets = (
        ('Información Principal', {
            'fields': ('titulo', 'descripcion', 'tipo', 'link')
        }),
        ('Estado y Asignación', {
            'fields': ('leida', 'usuario')
        }),
    )


# ==========================================
# ADMIN DE KPIs HISTÓRICOS
# ==========================================
@admin.register(KPIRegistro)
class KPIRegistroAdmin(admin.ModelAdmin):
    list_display = (
        'fecha',
        'efectividad_calibraciones',
        'volumen_ordenes',
        'tiempo_diagnostico',
        'tiempo_informe'
    )
    list_filter = ('fecha',)
    date_hierarchy = 'fecha'
    ordering = ('-fecha',)
    readonly_fields = ('fecha',)