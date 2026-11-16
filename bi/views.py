# bi/views.py
from django.shortcuts import render
from django.db.models import Avg, Q
from django.contrib.auth.decorators import login_required
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
    Dashboard BI con 4 KPIs.
    - Los filtros (Cliente, Equipo y Fechas) son opcionales e independientes.
    """
    # ==========================================
    # FILTROS DINÁMICOS
    # ==========================================
    cliente_filtro = request.GET.get('cliente', '')
    equipo_filtro = request.GET.get('equipo', '')
    fecha_inicio_filtro = request.GET.get('fecha_inicio', '')
    fecha_fin_filtro = request.GET.get('fecha_fin', '')
    aplicar = request.GET.get('aplicar', '0') 

    # ==========================================
    # CLIENTES DISPONIBLES
    # ==========================================
    clientes_disponibles = set()
    mapa_clientes = dict(DiagnosticoPredictivo.OPCIONES_CLIENTE)

    for reg in RegistroCalibracion.objects.all():
        clientes_disponibles.add(reg.cliente)
    for ord_v in OrdenVibracion.objects.all():
        clientes_disponibles.add(ord_v.cliente)
    for diag in DiagnosticoPredictivo.objects.all():
        clientes_disponibles.add(diag.cliente)
    for inf in RegistroInforme.objects.all():
        clientes_disponibles.add(inf.cliente)

    clientes_disponibles = sorted(
        [(code, mapa_clientes.get(code, code)) for code in clientes_disponibles],
        key=lambda x: x[1]
    )

    # ==========================================
    # EQUIPOS DISPONIBLES
    # ==========================================
    equipos_disponibles = set()
    mapa_equipos = {}
    mapa_equipos.update(dict(RegistroCalibracion.OPCIONES_EQUIPO_CALIBRACION))
    mapa_equipos.update(dict(OrdenVibracion.OPCIONES_EQUIPO_VIBRACION))

    calib_qs = RegistroCalibracion.objects.all()
    orden_qs = OrdenVibracion.objects.all()
    diag_qs = DiagnosticoPredictivo.objects.all()
    inf_qs = RegistroInforme.objects.all()

    if cliente_filtro:
        calib_qs = calib_qs.filter(cliente=cliente_filtro)
        orden_qs = orden_qs.filter(cliente=cliente_filtro)
        diag_qs = diag_qs.filter(cliente=cliente_filtro)
        inf_qs = inf_qs.filter(cliente=cliente_filtro)

    for reg in calib_qs:
        if reg.equipo: equipos_disponibles.add(reg.equipo)
    for ord_v in orden_qs:
        if ord_v.equipo: equipos_disponibles.add(ord_v.equipo)
    for diag in diag_qs:
        if diag.equipo: equipos_disponibles.add(diag.equipo)
    for inf in inf_qs:
        if inf.equipo: equipos_disponibles.add(inf.equipo)

    equipos_disponibles = sorted(
        [(code, mapa_equipos.get(code, code)) for code in equipos_disponibles],
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
        # Iniciamos con todos los registros
        calibraciones = RegistroCalibracion.objects.all()
        ordenes = OrdenVibracion.objects.all()
        diagnosticos = DiagnosticoPredictivo.objects.all()
        informes = RegistroInforme.objects.all()

        # Filtro por Cliente (Opcional)
        if cliente_filtro:
            calibraciones = calibraciones.filter(cliente=cliente_filtro)
            ordenes = ordenes.filter(cliente=cliente_filtro)
            diagnosticos = diagnosticos.filter(cliente=cliente_filtro)
            informes = informes.filter(cliente=cliente_filtro)

        # Filtro por Equipo (Opcional)
        if equipo_filtro:
            calibraciones = calibraciones.filter(Q(equipo__iexact=equipo_filtro) | Q(equipo__icontains=equipo_filtro))
            ordenes = ordenes.filter(Q(equipo__iexact=equipo_filtro) | Q(equipo__icontains=equipo_filtro))
            diagnosticos = diagnosticos.filter(Q(equipo__iexact=equipo_filtro) | Q(equipo__icontains=equipo_filtro))
            informes = informes.filter(Q(equipo__iexact=equipo_filtro) | Q(equipo__icontains=equipo_filtro))

        # Filtro por Fechas (CORREGIDO CON SUBCONSULTAS POR SERIAL)
        if fecha_inicio_filtro or fecha_fin_filtro:
            # 1. Filtramos los diagnósticos e informes por su propia fecha (Ellos sí tienen el campo)
            if fecha_inicio_filtro:
                diagnosticos = diagnosticos.filter(fecha_inicio__date__gte=fecha_inicio_filtro)
                informes = informes.filter(hora_inicio__date__gte=fecha_inicio_filtro)
            if fecha_fin_filtro:
                diagnosticos = diagnosticos.filter(fecha_inicio__date__lte=fecha_fin_filtro)
                informes = informes.filter(hora_inicio__date__lte=fecha_fin_filtro)

            # 2. Para Calibraciones y Órdenes, extraemos los seriales de los diagnósticos en ese rango de fechas
            # Filtramos por servicio='calibracion' o 'vibracion' y evitamos seriales nulos
            serials_calibracion = diagnosticos.filter(servicio='calibracion', codigo_serial__isnull=False).values_list('codigo_serial', flat=True)
            serials_vibracion = diagnosticos.filter(servicio='vibracion', codigo_serial__isnull=False).values_list('codigo_serial', flat=True)

            # 3. Filtramos las tablas usando los seriales obtenidos
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
        # KPI 2: CALIBRACIONES EFECTIVAS
        # ==========================================
        total_calibraciones = calibraciones.count()
        if total_calibraciones > 0:
            suma_calib = sum(1 for reg in calibraciones if reg.tiene_precision) + \
                         sum(1 for reg in calibraciones if reg.tiene_confiabilidad) + \
                         sum(1 for reg in calibraciones if reg.cumple_estandares)
            pct_calibraciones = round((suma_calib / (total_calibraciones * 3) * 100), 1)
            calibraciones_ok = calibraciones.filter(es_efectiva=True).count()
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
        # KPI 3: ÓRDENES DE VIBRACIÓN
        # ==========================================
        total_ordenes = ordenes.count()
        if total_ordenes > 0:
            suma_orden = sum(1 for reg in ordenes if reg.diagnostico_completo) + \
                         sum(1 for reg in ordenes if reg.cumple_estandares) + \
                         sum(1 for reg in ordenes if reg.registro_estructurado)
            pct_ordenes = round((suma_orden / (total_ordenes * 3) * 100), 1)
            ordenes_ok = ordenes.filter(es_efectiva=True).count()
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


@login_required
def dashboard_calibraciones(request):
    total = RegistroCalibracion.objects.count()
    efectivas = RegistroCalibracion.objects.filter(es_efectiva=True).count()
    porcentaje = (efectivas / total * 100) if total else 0
    context = {
        'porcentaje': porcentaje,
        'total': total,
        'efectivas': efectivas,
        'top_tecnicos': [],
        'alertas': {'pendientes_verificacion': 0, 'criticas': 0},
    }
    return render(request, 'bi/dashboard_calibraciones.html', context)


@login_required
def dashboard_ordenes(request):
    total = OrdenVibracion.objects.count()
    completadas_ok = OrdenVibracion.objects.filter(diagnostico_completo=True).count()
    porcentaje = (completadas_ok / total * 100) if total else 0
    context = {
        'porcentaje': porcentaje,
        'total': total,
        'efectivas': completadas_ok,
        'distribucion_estados': [],
        'distribucion_prioridad': [],
        'alertas': {'sin_asignar': 0, 'retrasadas': 0},
    }
    return render(request, 'bi/dashboard_ordenes.html', context)


@login_required
def kanban_ordenes(request):
    pendientes = OrdenVibracion.objects.filter(es_efectiva=False)
    completadas = OrdenVibracion.objects.filter(es_efectiva=True).order_by('-id')[:20]
    context = {
        'pendientes': pendientes,
        'asignadas': [],
        'en_diagnostico': [],
        'completadas': completadas,
    }
    return render(request, 'bi/kanban_ordenes.html', context)


def generar_alertas(request):
    return render(request, 'bi/dashboard_general.html')
