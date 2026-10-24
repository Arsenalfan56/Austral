"""
Script para poblar la base de datos con datos de prueba BI.
Ejecutar con: python manage.py shell < seed_bi.py
"""
import random
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.models import User

from logistica.models import (
    EquipoBI, RegistroCalibracionBI, OrdenVibracionBI,
    DiagnosticoPredictivoBI, InformeTecnicoBI,
)

print("🌱 Iniciando carga de datos BI...")

# 1. USUARIOS TÉCNICOS
tecnicos = []
for nombre in ['carlos', 'maria', 'pedro', 'laura', 'jose']:
    user, _ = User.objects.get_or_create(
        username=nombre,
        defaults={'email': f'{nombre}@australvt.com', 'is_staff': True}
    )
    tecnicos.append(user)
print(f"  OK {len(tecnicos)} tecnicos listos")

# 2. EQUIPOS BI
tipos = ['BOMBA', 'TURBINA', 'COMPRESOR', 'RADAR', 'MOTOR']
ubicaciones = ['Planta Norte', 'Planta Sur', 'Almacen Central', 'Sala de Maquinas', 'Nave 3']
fabricantes = ['Siemens', 'ABB', 'Schneider', 'WEG', 'Caterpillar']

equipos = []
for i in range(1, 21):
    eq, _ = EquipoBI.objects.get_or_create(
        codigo=f'EQ-{i:03d}',
        defaults={
            'nombre': f'Equipo Industrial {i}',
            'tipo': random.choice(tipos),
            'fabricante': random.choice(fabricantes),
            'modelo': f'M-{random.randint(100,999)}',
            'año_fabricacion': random.randint(2015, 2024),
            'ubicacion': random.choice(ubicaciones),
            'activo': random.choice([True, True, True, False]),
        }
    )
    equipos.append(eq)
print(f"  OK {len(equipos)} equipos listos")

# 3. CALIBRACIONES BI
for i in range(40):
    equipo = random.choice(equipos)
    tecnico = random.choice(tecnicos)
    parametros = random.randint(1, 3)
    calib = RegistroCalibracionBI.objects.create(
        equipo=equipo,
        tecnico=tecnico,
        fecha_programada=timezone.now() - timedelta(days=random.randint(1, 90)),
        parametros_cumplidos=parametros,
        total_parametros=3,
        tiempo_calibracion=random.randint(30, 180),
        aprobado=(parametros == 3),
        observaciones=f"Calibracion rutinaria #{i+1}",
    )
    fecha = timezone.now() - timedelta(days=random.randint(1, 150))
    RegistroCalibracionBI.objects.filter(pk=calib.pk).update(fecha_calibracion=fecha)
print("  OK 40 calibraciones creadas")

# 4. ORDENES DE VIBRACION BI
estados = ['PENDIENTE', 'ASIGNADA', 'EN_DIAGNOSTICO', 'COMPLETADA', 'COMPLETADA', 'COMPLETADA']
prioridades = ['CRITICA', 'ALTA', 'MEDIA', 'BAJA']

for i in range(60):
    equipo = random.choice(equipos)
    estado = random.choice(estados)
    prioridad = random.choice(prioridades)
    creada = timezone.now() - timedelta(days=random.randint(0, 150))

    orden = OrdenVibracionBI.objects.create(
        cliente=random.choice(["Minera Andes", "YPF", "Pemex", "Codelco", "YPFB"]),
        equipo=equipo,
        descripcion=f'Analisis de vibraciones en {equipo.nombre}',
        estado=estado,
        prioridad=prioridad,
        tecnico_asignado=random.choice(tecnicos),
        cumplio_estandares=random.choice([True, False]),
    )

    OrdenVibracionBI.objects.filter(pk=orden.pk).update(fecha_creacion=creada)

    if estado == 'COMPLETADA':
        OrdenVibracionBI.objects.filter(pk=orden.pk).update(
            fecha_asignacion=creada + timedelta(hours=2),
            fecha_inicio=creada + timedelta(hours=4),
            fecha_completada=creada + timedelta(hours=random.randint(8, 60)),
        )
        orden.refresh_from_db()
        orden.save()

        diag = DiagnosticoPredictivoBI.objects.create(
            orden=orden,
            datos_vibracion={'vibraciones': [random.uniform(1, 15) for _ in range(20)]},
        )
        DiagnosticoPredictivoBI.objects.filter(pk=diag.pk).update(
            fecha_inicio=orden.fecha_inicio,
            fecha_fin=orden.fecha_completada,
        )
        diag.refresh_from_db()
        diag.save()

        InformeTecnicoBI.objects.create(
            diagnostico=diag,
            tamanio=random.randint(50000, 500000),
            tiempo_generacion=random.randint(1, 10),
            descargado=random.randint(0, 20),
        )

print("  OK 60 ordenes y diagnosticos creados")
print(f"\nTotal:")
print(f"   Equipos: {EquipoBI.objects.count()}")
print(f"   Calibraciones: {RegistroCalibracionBI.objects.count()}")
print(f"   Ordenes: {OrdenVibracionBI.objects.count()}")
print(f"   Diagnosticos: {DiagnosticoPredictivoBI.objects.count()}")
print(f"   Informes: {InformeTecnicoBI.objects.count()}")