from django.shortcuts import render
from django.db.models import Avg, Q, Count
from django.contrib.auth.decorators import login_required
from django.utils.dateparse import parse_date
from logistica.models import (
    RegistroCalibracion,
    OrdenVibracion,
    DiagnosticoPredictivo,
    RegistroInforme,
)
from .models import Alerta

@login_required
def dashboard_general(request):
    """
    Dashboard BI con 4 KPIs optimizado.
    - Filtros dinámicos por Cliente, Equipo y Fechas.
    """
    # ==========================================
    # CAPTURA Y VALIDACIÓN DE FILTROS
    # ==========================================
    cliente_filtro = request.GET.get('cliente', '').strip()
    equipo_filtro = request.GET.get('equipo', '').strip()
    aplicar = request.GET.get('aplicar', '0') 

    # Parseo seguro de fechas
    fecha_inicio_filtro = request.GET.get('fecha_inicio', '')
    fecha_fin_filtro = request.GET.get('fecha_fin', '')
    f_inicio = parse_date(fecha_inicio_filtro) if fecha_inicio_filtro else None
    f_fin = parse_date(fecha_fin_filtro) if fecha_fin_filtro else None

    # ==========================================
    # OBTENER CLIENTES Y EQUIPOS (Optimizado)
    # ==========================================
    clientes_disponibles = set()
    mapa_clientes = dict(DiagnosticoPredictivo.OPCIONES_CLIENTE)

    # Usamos values_list().distinct() para no traer toda la tabla a la memoria
    clientes_disponibles.update(RegistroCalibracion.objects.values_list('cliente', flat=True).distinct())
    clientes_disponibles.update(OrdenVibracion.objects.values_list('cliente', flat=True).distinct())
    clientes_disponibles.update(DiagnosticoPredictivo.objects.values_list('cliente', flat=True).distinct())
    clientes_disponibles.update(RegistroInforme.objects.values_list('cliente', flat=True).distinct())

    clientes_disponibles = sorted(
        [(code, mapa_clientes.get(code, code)) for code in clientes_disponibles if code],
        key=lambda x: x[1]
    )

    equipos_disponibles = set()
    mapa_equipos = {}
    mapa_equipos.update(dict(RegistroCalibracion.OPCIONES_EQUIPO_CALIBRACION))
    mapa_equipos.update(dict(OrdenVibracion.OPCIONES_EQUIPO_VIBRACION))

    # Base QuerySets (sin filtros aún)
    calib_qs = RegistroCalibracion.objects.all()
    orden_qs = OrdenVibracion.objects.all()
    diag_qs = DiagnosticoPredictivo.objects.all()
    inf_qs = RegistroInforme.objects.all()

    # Filtrar dropdowns por cliente si el usuario ya seleccionó uno
    if cliente_filtro:
        calib_qs = calib_qs.filter(cliente=cliente_filtro)
        orden_qs = orden_qs.filter(cliente=cliente_filtro)
        diag_qs = diag_qs.filter(cliente=cliente_filtro)
        inf_qs = inf_qs.filter(cliente=cliente_filtro)

    equipos_disponibles.update(calib_qs.values_list('equipo', flat=True).distinct())
    equipos_disponibles.update(orden_qs.values_list('equipo', flat=True).distinct())
    equipos_disponibles.update(diag_qs.values_list('equipo', flat=True).distinct())
    equipos_disponibles.update(inf_qs.values_list('equipo', flat=True).distinct())

    equipos_disponibles = sorted(
        [(code, mapa_equipos.get(code, code)) for code in equipos_disponibles if code],
        key=lambda x: x[1]
    )

    # ==========================================
    # VALORES POR DEFECTO (0 y ROJO)
    # ==========================================
    kpis = {
        'informe': {'nombre': 'Tiempo de Informe', 'valor': 0, 'unidad': 'h', 'criterio': '≤ 2 h', 'cumple': False, 'total': 0},
        'calibracion': {'nombre': 'Calibraciones Efectivas', 'valor': 0, 'unidad': '%', 'criterio': '≥ 95%', 'cumple': False, 'aprobados': 0, 'total': 0},
        'orden': {'nombre': 'Órdenes de Vibración', 'valor': 0, 'unidad': '%', 'criterio': '≥ 95%', 'cumple': False, 'aprobados': 0, 'total': 0},
        'diagnostico': {'nombre': 'Tiempo de Diagnóstico', 'valor': 0, 'unidad': 'min', 'criterio': '≤ 30 min', 'cumple': False, 'total': 0},
    }

    # ==========================================
    # CALCULAR SOLO SI SE PRESIONÓ FILTRAR
    # ==========================================
    if aplicar == '1':
        calibraciones = RegistroCalibracion.objects.all()
        ordenes = OrdenVibracion.objects.all()
        diagnosticos = DiagnosticoPredictivo.objects.all()
        informes = RegistroInforme.objects.all()

        # --- FILTROS COMUNES ---
        if cliente_filtro:
            calibraciones = calibraciones.filter(cliente=cliente_filtro)
            ordenes = ordenes.filter(cliente=cliente_filtro)
            diagnosticos = diagnosticos.filter(cliente=cliente_filtro)
            informes = informes.filter(cliente=cliente_filtro)

        if equipo_filtro:
            # Usamos icontains para evitar fallos por mayúsculas/minúsculas
            calibraciones = calibraciones.filter(equipo__icontains=equipo_filtro)
            ordenes = ordenes.filter(equipo__icontains=equipo_filtro)
            diagnosticos = diagnosticos.filter(equipo__icontains=equipo_filtro)
            informes = informes.filter(equipo__icontains=equipo_filtro)

        # --- FILTROS POR FECHAS (Lógica de Seriales) ---
        if f_inicio or f_fin:
            if f_inicio:
                diagnosticos = diagnosticos.filter(fecha_inicio__date__gte=f_inicio)
                informes = informes.filter(hora_inicio__date__gte=f_inicio)
            if f_fin:
                diagnosticos = diagnosticos.filter(fecha_inicio__date__lte=f_fin)
                informes = informes.filter(hora_inicio__date__lte=f_fin)

            # Extraemos los seriales usando subconsultas
            serials_calibracion = diagnosticos.filter(servicio='calibracion', codigo_serial__isnull=False).values_list('codigo_serial', flat=True)
            serials_vibracion = diagnosticos.filter(servicio='vibracion', codigo_serial__isnull=False).values_list('codigo_serial', flat=True)

            # Cruzamos los seriales
            calibraciones = calibraciones.filter(codigo_serial__in=serials_calibracion)
            ordenes = ordenes.filter(codigo_serial__in=serials_vibracion)

        # ==========================================
        # KPI 1: TIEMPO DE INFORME
        # ==========================================
        total_informes = informes.count()
        promedio_horas = informes.filter(tiempo_generacion_horas__gt=0).aggregate(prom=Avg('tiempo_generacion_horas'))['prom'] or 0
        promedio_horas = round(promedio_horas, 2)
        
        kpis['informe'].update({
            'valor': promedio_horas, 
            'cumple': (total_informes > 0 and promedio_horas <= 2), 
            'total': total_informes,
        })

        # ==========================================
        # KPI 2: CALIBRACIONES EFECTIVAS (Optimizado con Count)
        # ==========================================
        total_calibraciones = calibraciones.count()
        if total_calibraciones > 0:
            # Calculamos el total de "True" en los 3 campos en una sola consulta a la BD
            conteos = calibraciones.aggregate(
                precision=Count('id', filter=Q(tiene_precision=True)),
                confiabilidad=Count('id', filter=Q(tiene_confiabilidad=True)),
                estandares=Count('id', filter=Q(cumple_estandares=True)),
                efectivas=Count('id', filter=Q(es_efectiva=True))
            )
            suma_calib = conteos['precision'] + conteos['confiabilidad'] + conteos['estandares']
            pct_calibraciones = round((suma_calib / (total_calibraciones * 3) * 100), 1)
            calibraciones_ok = conteos['efectivas']
        else:
            pct_calibraciones = 0
            calibraciones_ok = 0
            
        kpis['calibracion'].update({
            'valor': pct_calibraciones, 
            'cumple': (total_calibraciones > 0 and pct_calibraciones >= 95), 
            'aprobados': calibraciones_ok, 
            'total': total_calibraciones,
        })

        # ==========================================
        # KPI 3: ÓRDENES DE VIBRACIÓN (Optimizado con Count)
        # ==========================================
        total_ordenes = ordenes.count()
        if total_ordenes > 0:
            conteos_ord = ordenes.aggregate(
                completo=Count('id', filter=Q(diagnostico_completo=True)),
                estandares=Count('id', filter=Q(cumple_estandares=True)),
                estructurado=Count('id', filter=Q(registro_estructurado=True)),
                efectivas=Count('id', filter=Q(es_efectiva=True))
            )
            suma_orden = conteos_ord['completo'] + conteos_ord['estandares'] + conteos_ord['estructurado']
            pct_ordenes = round((suma_orden / (total_ordenes * 3) * 100), 1)
            ordenes_ok = conteos_ord['efectivas']
        else:
            pct_ordenes = 0
            ordenes_ok = 0
            
        kpis['orden'].update({
            'valor': pct_ordenes, 
            'cumple': (total_ordenes > 0 and pct_ordenes >= 95), 
            'aprobados': ordenes_ok, 
            'total': total_ordenes,
        })

        # ==========================================
        # KPI 4: TIEMPO DE DIAGNÓSTICO
        # ==========================================
        total_diagnosticos = diagnosticos.count()
        promedio_minutos = diagnosticos.filter(tiempo_total_minutos__gt=0).aggregate(prom=Avg('tiempo_total_minutos'))['prom'] or 0
        promedio_minutos = round(promedio_minutos, 1)
        
        kpis['diagnostico'].update({
            'valor': promedio_minutos, 
            'cumple': (total_diagnosticos > 0 and promedio_minutos <= 30), 
            'total': total_diagnosticos,
        })

    # ==========================================
    # CONTEXTO
    # ==========================================
    context = {
        'filtros': {
            'cliente_seleccionado': cliente_filtro,
            'equipo_seleccionado': equipo_filtro,
            'fecha_inicio_seleccionada': fecha_inicio_filtro,
            'fecha_fin_seleccionada': fecha_fin_filtro,
            'clientes_disponibles': clientes_disponibles,
            'equipos_disponibles': equipos_disponibles,
            'aplicar': aplicar,
        },
        'kpis': kpis,
        'alertas': Alerta.objects.filter(leida=False)[:10],
    }

    return render(request, 'bi/dashboard_general.html', context)

# (El resto de funciones: dashboard_calibraciones, dashboard_ordenes, kanban_ordenes y generar_alertas se quedan igual)
@login_required
def dashboard_calibraciones(request):
    # ... (sin cambios)
    total = RegistroCalibracion.objects.count()
    efectivas = RegistroCalibracion.objects.filter(es_efectiva=True).count()
    porcentaje = (efectivas / total * 100) if total else 0
    context = {
        'porcentaje': porcentaje, 'total': total, 'efectivas': efectivas,
        'top_tecnicos': [], 'alertas': {'pendientes_verificacion': 0, 'criticas': 0},
    }
    return render(request, 'bi/dashboard_calibraciones.html', context)

@login_required
def dashboard_ordenes(request):
    # ... (sin cambios)
    total = OrdenVibracion.objects.count()
    completadas_ok = OrdenVibracion.objects.filter(diagnostico_completo=True).count()
    porcentaje = (completadas_ok / total * 100) if total else 0
    context = {
        'porcentaje': porcentaje, 'total': total, 'efectivas': completadas_ok,
        'distribucion_estados': [], 'distribucion_prioridad': [], 'alertas': {'sin_asignar': 0, 'retrasadas': 0},
    }
    return render(request, 'bi/dashboard_ordenes.html', context)

@login_required
def kanban_ordenes(request):
    # ... (sin cambios)
    pendientes = OrdenVibracion.objects.filter(es_efectiva=False)
    completadas = OrdenVibracion.objects.filter(es_efectiva=True).order_by('-id')[:20]
    context = {
        'pendientes': pendientes, 'asignadas': [], 'en_diagnostico': [], 'completadas': completadas,
    }
    return render(request, 'bi/kanban_ordenes.html', context)

def generar_alertas(request):
    return render(request, 'bi/dashboard_general.html')
