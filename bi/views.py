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
    - Por defecto, TODOS los KPIs aparecen en 0 y en ROJO.
    - Solo se calculan cuando el usuario presiona "Filtrar" (parámetro ?aplicar=1).
    - KPI Calibraciones y Órdenes de Vibración: % de cumplimiento según checkboxes.
    - KPI Tiempo de Informe: promedio en horas (≤ 2h).
    - KPI Tiempo de Diagnóstico: promedio en minutos (≤ 30 min).
    """
    # ==========================================
    # FILTROS DINÁMICOS
    # ==========================================
    cliente_filtro = request.GET.get('cliente', '')
    equipo_filtro = request.GET.get('equipo', '')
    aplicar = request.GET.get('aplicar', '0')  # Bandera para saber si se presionó Filtrar

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
        if reg.equipo:
            equipos_disponibles.add(reg.equipo)
    for ord_v in orden_qs:
        if ord_v.equipo:
            equipos_disponibles.add(ord_v.equipo)
    for diag in diag_qs:
        if diag.equipo:
            equipos_disponibles.add(diag.equipo)
    for inf in inf_qs:
        if inf.equipo:
            equipos_disponibles.add(inf.equipo)

    equipos_disponibles = sorted(
        [(code, mapa_equipos.get(code, code)) for code in equipos_disponibles],
        key=lambda x: x[1]
    )

    # ==========================================
    # VALORES POR DEFECTO (0 y ROJO)
    # ==========================================
    kpis = {
        'informe': {
            'nombre': 'Tiempo de Informe',
            'valor': 0, 'unidad': 'h', 'criterio': '≤ 2 h',
            'cumple': False, 'total': 0,
        },
        'calibracion': {
            'nombre': 'Calibraciones Efectivas',
            'valor': 0, 'unidad': '%', 'criterio': '≥ 95%',
            'cumple': False, 'aprobados': 0, 'total': 0,
        },
        'orden': {
            'nombre': 'Órdenes de Vibración',
            'valor': 0, 'unidad': '%', 'criterio': '≥ 95%',
            'cumple': False, 'aprobados': 0, 'total': 0,
        },
        'diagnostico': {
            'nombre': 'Tiempo de Diagnóstico',
            'valor': 0, 'unidad': 'min', 'criterio': '≤ 30 min',
            'cumple': False, 'total': 0,
        },
    }

    # ==========================================
    # CALCULAR SOLO SI SE PRESIONÓ FILTRAR Y HAY CLIENTE + EQUIPO
    # ==========================================
    if aplicar == '1' and cliente_filtro and equipo_filtro:
        calibraciones = RegistroCalibracion.objects.filter(
            cliente=cliente_filtro, equipo=equipo_filtro
        )
        ordenes = OrdenVibracion.objects.filter(
            cliente=cliente_filtro, equipo=equipo_filtro
        )
        diagnosticos = DiagnosticoPredictivo.objects.filter(
            cliente=cliente_filtro
        ).filter(
            Q(equipo__iexact=equipo_filtro) | Q(equipo__icontains=equipo_filtro)
        )
        informes = RegistroInforme.objects.filter(
            cliente=cliente_filtro, equipo=equipo_filtro
        )

        # ==========================================
        # KPI 1: TIEMPO DE INFORME (promedio en HORAS)
        # ==========================================
        total_informes = informes.count()
        promedio_horas = informes.filter(
            tiempo_generacion_horas__gt=0
        ).aggregate(prom=Avg('tiempo_generacion_horas'))['prom'] or 0
        promedio_horas = round(promedio_horas, 2)
        kpi_informe_ok = (total_informes > 0 and promedio_horas <= 2)

        # ==========================================
        # KPI 2: CALIBRACIONES EFECTIVAS (% por checkboxes)
        # ==========================================
        total_calibraciones = calibraciones.count()
        if total_calibraciones > 0:
            suma_calib = 0
            for reg in calibraciones:
                if reg.tiene_precision: suma_calib += 1
                if reg.tiene_confiabilidad: suma_calib += 1
                if reg.cumple_estandares: suma_calib += 1
            total_posibles = total_calibraciones * 3
            pct_calibraciones = round((suma_calib / total_posibles * 100), 1)
            calibraciones_ok = calibraciones.filter(es_efectiva=True).count()
        else:
            pct_calibraciones = 0
            calibraciones_ok = 0
        kpi_calibracion_ok = (total_calibraciones > 0 and pct_calibraciones >= 95)

        # ==========================================
        # KPI 3: ÓRDENES DE VIBRACIÓN EFECTIVAS (% por checkboxes)
        # ==========================================
        total_ordenes = ordenes.count()
        if total_ordenes > 0:
            suma_orden = 0
            for reg in ordenes:
                if reg.diagnostico_completo: suma_orden += 1
                if reg.cumple_estandares: suma_orden += 1
                if reg.registro_estructurado: suma_orden += 1
            total_posibles = total_ordenes * 3
            pct_ordenes = round((suma_orden / total_posibles * 100), 1)
            ordenes_ok = ordenes.filter(es_efectiva=True).count()
        else:
            pct_ordenes = 0
            ordenes_ok = 0
        kpi_orden_ok = (total_ordenes > 0 and pct_ordenes >= 95)

        # ==========================================
        # KPI 4: TIEMPO DE DIAGNÓSTICO (promedio en MINUTOS)
        # 🔧 CORRECCIÓN: El campo tiempo_total_minutos YA está en minutos
        # ==========================================
        total_diagnosticos = diagnosticos.count()
        promedio_minutos = diagnosticos.filter(
            tiempo_total_minutos__gt=0
        ).aggregate(prom=Avg('tiempo_total_minutos'))['prom'] or 0
        promedio_minutos = round(promedio_minutos, 1)
        kpi_diagnostico_ok = (total_diagnosticos > 0 and promedio_minutos <= 30)

        # ---- Actualizar KPIs ----
        kpis['informe'].update({
            'valor': promedio_horas, 'cumple': kpi_informe_ok, 'total': total_informes,
        })
        kpis['calibracion'].update({
            'valor': pct_calibraciones, 'cumple': kpi_calibracion_ok,
            'aprobados': calibraciones_ok, 'total': total_calibraciones,
        })
        kpis['orden'].update({
            'valor': pct_ordenes, 'cumple': kpi_orden_ok,
            'aprobados': ordenes_ok, 'total': total_ordenes,
        })
        kpis['diagnostico'].update({
            'valor': promedio_minutos, 'cumple': kpi_diagnostico_ok, 'total': total_diagnosticos,
        })

    # ==========================================
    # CONTEXTO
    # ==========================================
    context = {
        'filtros': {
            'cliente_seleccionado': cliente_filtro,
            'equipo_seleccionado': equipo_filtro,
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