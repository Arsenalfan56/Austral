# logistica/views.py
# logistica/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.utils.html import strip_tags
from django.db.models import Avg, Q
from django.http import JsonResponse
from .models import Equipo, RegistroCalibracion, OrdenVibracion, PerfilUsuario, DiagnosticoPredictivo
from .forms import RegistroUsuarioForm


# ==========================================
# 1. DASHBOARD BI
# ==========================================
@staff_member_required
def dashboard_bi(request):
    total_equipos = Equipo.objects.count()
    total_calibraciones = RegistroCalibracion.objects.count()
    total_ordenes = OrdenVibracion.objects.count()
    
    calib_efectivas = RegistroCalibracion.objects.filter(es_efectiva=True).count()
    porcentaje_efectivas = round((calib_efectivas / total_calibraciones * 100), 1) if total_calibraciones > 0 else 0
    
    ordenes_completadas = total_ordenes
    ordenes_pendientes = 0
    
    tiempo_promedio = OrdenVibracion.objects.filter(
        tiempo_diagnostico_min__gt=0
    ).aggregate(prom=Avg('tiempo_diagnostico_min'))['prom'] or 0
    
    context = {
        'totales': {
            'equipos': total_equipos,
            'calibraciones': total_calibraciones,
            'ordenes': total_ordenes,
            'diagnosticos': 0,
            'informes': 0,
        },
        'porcentaje_efectivas': porcentaje_efectivas,
        'calib_efectivas': calib_efectivas,
        'ordenes_completadas': ordenes_completadas,
        'ordenes_pendientes': ordenes_pendientes,
        'tiempo_promedio_diag': round(tiempo_promedio, 1),
    }
    
    return render(request, 'logistica/dashboard.html', context)


# ==========================================
# 2. REGISTRO DE USUARIO
# ==========================================
def registro_usuario(request):
    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password1'],
                first_name=form.cleaned_data['nombre_completo']
            )
            
            perfil, created = PerfilUsuario.objects.get_or_create(user=user)
            perfil.telefono = form.cleaned_data['telefono']
            perfil.nombre_completo = form.cleaned_data['nombre_completo']
            perfil.save()
            
            try:
                asunto = "Nuevo registro en el Sistema ERP - Austral V&T"
                mensaje_html = f"""
                <html>
                <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
                    <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; padding: 30px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                        <h2 style="color: #4a7c9e; text-align: center; margin-top: 0;">
                            ¡Bienvenido al ERP de Austral V&T!
                        </h2>
                        <p>Hola <strong>{form.cleaned_data['nombre_completo']}</strong>,</p>
                        <p>Tu cuenta ha sido creada exitosamente en el sistema ERP de Austral V&T. 
                        A continuación, te compartimos los datos de tu cuenta:</p>
                        <div style="background-color: #f8f9fa; border-left: 4px solid #4a7c9e; padding: 15px; margin: 20px 0; border-radius: 4px;">
                            <h3 style="color: #4a7c9e; margin-top: 0;">Datos de tu cuenta</h3>
                            <ul style="list-style: none; padding: 0;">
                                <li style="padding: 5px 0;"><strong>Usuario:</strong> {form.cleaned_data['username']}</li>
                                <li style="padding: 5px 0;"><strong>Correo:</strong> {form.cleaned_data['email']}</li>
                                <li style="padding: 5px 0;"><strong>Teléfono:</strong> {form.cleaned_data['telefono']}</li>
                            </ul>
                        </div>
                        <p>Ya puedes acceder al sistema con tus credenciales cuando lo necesites. 
                        Si olvidas tu contraseña, puedes restablecerla desde la pantalla de inicio de sesión.</p>
                        <hr style="border: none; border-top: 1px solid #eee; margin: 25px 0;">
                        <p style="color: #888; font-size: 0.9em; text-align: center;">
                            Este es un correo automático, por favor no responder.
                        </p>
                        <p style="color: #888; font-size: 0.8em; text-align: center; margin-bottom: 0;">
                            <strong>Austral V&T ERP</strong> - Sistema de gestión
                        </p>
                    </div>
                </body>
                </html>
                """
                
                mensaje_texto = strip_tags(mensaje_html)
                
                send_mail(
                    asunto,
                    mensaje_texto,
                    settings.DEFAULT_FROM_EMAIL,
                    [form.cleaned_data['email']],
                    html_message=mensaje_html,
                    fail_silently=True,
                )
            except Exception as e:
                print(f"⚠️ Error enviando correo: {e}")
            
            messages.success(
                request, 
                f"¡Usuario registrado exitosamente! Se ha enviado un correo de confirmación a {form.cleaned_data['email']}."
            )
            return redirect('logistica:registro_exitoso')
    else:
        form = RegistroUsuarioForm()
    
    return render(request, 'logistica/registro.html', {'form': form})


def registro_exitoso(request):
    return render(request, 'logistica/registro_exitoso.html')


# ==========================================
# 3. VISTA AJAX PARA AUTOCOMPLETAR CLIENTE Y SERVICIO
# ==========================================
def obtener_cliente_por_equipo(request):
    """
    Vista AJAX que devuelve el cliente, servicio y código serial asociado a un equipo.
    El parámetro 'equipo' viene como 'equipo|cliente|codigo_serial'.
    """
    equipo_param = request.GET.get('equipo', None)
    if not equipo_param:
        return JsonResponse({'cliente': None, 'servicio': None, 'error': 'No se proporcionó un equipo'}, status=400)
    
    # Parsear "equipo|cliente|codigo_serial"
    partes = equipo_param.split('|')
    equipo = partes[0] if len(partes) > 0 else None
    cliente_esperado = partes[1] if len(partes) > 1 else None
    serial_esperado = partes[2] if len(partes) > 2 else None
    
    # 1. Buscar en RegistroCalibracion
    qs_calibracion = RegistroCalibracion.objects.filter(equipo=equipo)
    if cliente_esperado:
        qs_calibracion = qs_calibracion.filter(cliente=cliente_esperado)
    if serial_esperado:
        qs_calibracion = qs_calibracion.filter(codigo_serial=serial_esperado)
    registro = qs_calibracion.first()
    if registro:
        return JsonResponse({
            'cliente': registro.cliente,
            'servicio': 'calibracion',
            'codigo_serial': registro.codigo_serial,
            'origen': 'calibracion'
        })
    
    # 2. Buscar en OrdenVibracion
    qs_vibracion = OrdenVibracion.objects.filter(equipo=equipo)
    if cliente_esperado:
        qs_vibracion = qs_vibracion.filter(cliente=cliente_esperado)
    if serial_esperado:
        qs_vibracion = qs_vibracion.filter(codigo_serial=serial_esperado)
    orden = qs_vibracion.first()
    if orden:
        return JsonResponse({
            'cliente': orden.cliente,
            'servicio': 'vibracion',
            'codigo_serial': orden.codigo_serial,
            'origen': 'vibracion'
        })
    
    # 3. Fallback: buscar sin serial
    registro = RegistroCalibracion.objects.filter(equipo=equipo).first()
    if registro:
        return JsonResponse({
            'cliente': registro.cliente,
            'servicio': 'calibracion',
            'codigo_serial': registro.codigo_serial,
            'origen': 'calibracion'
        })
    
    orden = OrdenVibracion.objects.filter(equipo=equipo).first()
    if orden:
        return JsonResponse({
            'cliente': orden.cliente,
            'servicio': 'vibracion',
            'codigo_serial': orden.codigo_serial,
            'origen': 'vibracion'
        })
    
    return JsonResponse({'cliente': None, 'servicio': None, 'error': 'No se encontró cliente para este equipo'}, status=404)


# ==========================================
# 4. VISTA AJAX PARA VERIFICAR DIAGNÓSTICO (CORREGIDA)
# ==========================================
def obtener_diagnostico(request):
    """
    Vista AJAX que verifica si un equipo (identificado por equipo+cliente+serial)
    tiene un Diagnóstico Predictivo con fecha_fin.
    
    CORRECCIÓN: Busca tanto por el código del equipo (ej: "transmisor_temperatura")
    como por el nombre visible (ej: "Transmisor de temperatura"), ya que el campo
    'equipo' en DiagnosticoPredictivo es un CharField libre y puede guardar cualquiera
    de los dos formatos.
    """
    equipo_param = request.GET.get('equipo', None)
    if not equipo_param:
        return JsonResponse({'tiene_diagnostico': False, 'error': 'No se proporcionó un equipo'}, status=400)
    
    # Parsear "equipo|cliente|codigo_serial"
    partes = equipo_param.split('|')
    equipo_codigo = partes[0] if len(partes) > 0 else None
    cliente = partes[1] if len(partes) > 1 else None
    serial = partes[2] if len(partes) > 2 else None
    
    # 🔧 CORRECCIÓN CLAVE: Convertir el código al nombre visible
    # Los mapas de opciones nos dan la relación código -> nombre visible
    mapa_equipos = {}
    mapa_equipos.update(dict(RegistroCalibracion.OPCIONES_EQUIPO_CALIBRACION))
    mapa_equipos.update(dict(OrdenVibracion.OPCIONES_EQUIPO_VIBRACION))
    equipo_nombre = mapa_equipos.get(equipo_codigo, equipo_codigo)
    
    # 🔧 Búsqueda flexible: por código O por nombre visible
    qs = DiagnosticoPredictivo.objects.filter(
        Q(equipo=equipo_codigo) | Q(equipo=equipo_nombre),
        fecha_fin__isnull=False
    )
    
    if cliente:
        qs = qs.filter(cliente=cliente)
    
    # 🔧 Buscar el serial de forma flexible (con o sin espacios)
    if serial:
        qs = qs.filter(
            Q(codigo_serial=serial) | 
            Q(codigo_serial__iexact=serial.strip())
        )
    
    ultimo_diagnostico = qs.order_by('-fecha_fin').first()
    
    # 🔧 Fallback: si no se encuentra con serial, intentar sin él
    if not ultimo_diagnostico:
        qs_fallback = DiagnosticoPredictivo.objects.filter(
            Q(equipo=equipo_codigo) | Q(equipo=equipo_nombre),
            fecha_fin__isnull=False
        )
        if cliente:
            qs_fallback = qs_fallback.filter(cliente=cliente)
        ultimo_diagnostico = qs_fallback.order_by('-fecha_fin').first()
    
    if ultimo_diagnostico and ultimo_diagnostico.fecha_fin:
        return JsonResponse({
            'tiene_diagnostico': True,
            'fecha_fin': ultimo_diagnostico.fecha_fin.strftime('%Y-%m-%dT%H:%M'),
            'debug_equipo_encontrado': ultimo_diagnostico.equipo,
        })
    else:
        # 🔧 DEBUG: Devolver todos los diagnósticos existentes para depuración
        todos = list(DiagnosticoPredictivo.objects.values(
            'id', 'equipo', 'cliente', 'codigo_serial', 'fecha_fin'
        ))
        return JsonResponse({
            'tiene_diagnostico': False,
            'debug_buscado': {
                'equipo_codigo': equipo_codigo,
                'equipo_nombre': equipo_nombre,
                'cliente': cliente,
                'serial': serial,
            },
            'debug_existentes': todos,
        })