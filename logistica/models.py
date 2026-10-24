# logistica/models.py
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
import qrcode
from io import BytesIO
from django.core.files import File


# ==========================================
# MODELOS ORIGINALES (Equipos, QR, Perfil)
# ==========================================
class Equipo(models.Model):
    OPCIONES_EQUIPO = [
        ('bently_nevada', 'Sistemas Bently Nevada'),
        ('ccc', 'Sistemas de Control Compressor Controls Corporation (CCC)'),
        ('compresor_aire', 'Compresor de aire'),
        ('transportador_faja', 'Transportador de faja'),
        ('bomba_centrifuga', 'Bomba centrífuga'),
        ('transformador_potencia', 'Transformador de potencia'),
        ('interruptor_potencia', 'Interruptor de potencia'),
        ('tablero_electrico', 'Tablero eléctrico'),
        ('puesta_tierra', 'Sistema de puesta a tierra'),
        ('banco_bateria', 'Banco de batería'),
        ('rectificadores', 'Rectificadores'),
        ('sistema_das', 'Sistema DAS (Pararrayos)'),
        ('analizador_fire_gas', 'Analizador Fire & Gas'),
        ('transmisor_radar', 'Transmisor tipo radar'),
        ('sis', 'Sistema Instrumentado de Seguridad (SIS)'),
    ]

    OPCIONES_CLIENTE = [
        ('pdvsa', 'PDVSA'),
        ('pequiven', 'Pequiven'),
        ('sinovensa', 'Sinovensa'),
        ('petrocedeno', 'Petrocedeño'),
        ('petromonagas', 'Petromonagas'),
        ('petropiar', 'Petropiar'),
        ('otros', 'Otros'),
    ]

    nombre = models.CharField(max_length=100, choices=OPCIONES_EQUIPO, verbose_name="Nombre del Equipo")
    codigo_serial = models.CharField(max_length=50, unique=True, verbose_name="Código Serial")
    cliente = models.CharField(max_length=100, choices=OPCIONES_CLIENTE, default='pdvsa', verbose_name="Cliente")
    estado = models.CharField(max_length=50, default='Activo', verbose_name="Estado")
    qr_code = models.ImageField(upload_to='qrcodes/', blank=True, null=True, verbose_name="Código QR")
    foto_equipo = models.ImageField(upload_to='equipos/', blank=True, null=True, verbose_name="Foto del Equipo")

    def save(self, *args, **kwargs):
        if not self.qr_code and self.codigo_serial:
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(f'Equipo: {self.get_nombre_display()} | Cliente: {self.get_cliente_display()} | Serial: {self.codigo_serial}')
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            filename = f'qr_{self.codigo_serial}.png'
            self.qr_code.save(filename, File(buffer), save=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_nombre_display()} - {self.codigo_serial}"

    class Meta:
        verbose_name = "Equipo"
        verbose_name_plural = "Equipos"


class PerfilUsuario(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    foto = models.ImageField(upload_to='perfiles/', blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True, verbose_name="Teléfono")
    nombre_completo = models.CharField(max_length=150, blank=True, null=True, verbose_name="Nombre completo")

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name = "Perfil de Usuario"
        verbose_name_plural = "Perfiles de Usuarios"


# ==========================================
# MODELOS NUEVOS PARA EL CAPITULO IV
# ==========================================

class RegistroCalibracion(models.Model):
    OPCIONES_EQUIPO_CALIBRACION = [
        ('transmisor_presion', 'Transmisor de presión'),
        ('transmisor_caudal', 'Transmisor de caudal (flujo)'),
        ('transmisor_nivel', 'Transmisor de nivel'),
        ('transmisor_temperatura', 'Transmisor de temperatura'),
        ('analizador_fire_gas', 'Analizador de Fire & Gas'),
        ('transmisor_radar', 'Transmisor tipo radar (medición de nivel)'),
        ('valvula_seguridad', 'Válvula de seguridad'),
        ('valvula_control', 'Válvula de control'),
        ('sis', 'Sistema Instrumentado de Seguridad (SIS)'),
    ]

    OPCIONES_CLIENTE_CALIBRACION = [
        ('pdvsa', 'PDVSA'),
        ('pequiven', 'Pequiven'),
        ('sinovensa', 'Sinovensa'),
        ('petrocedeno', 'Petrocedeño'),
        ('petromonagas', 'Petromonagas'),
        ('petropiar', 'Petropiar'),
        ('otros', 'Otros'),
    ]

    equipo = models.CharField(max_length=100, choices=OPCIONES_EQUIPO_CALIBRACION, verbose_name="Equipo", default='transmisor_presion')
    codigo_serial = models.CharField(max_length=50, verbose_name="Código Serial")
    cliente = models.CharField(max_length=100, choices=OPCIONES_CLIENTE_CALIBRACION, verbose_name="Cliente", default='pdvsa')
    
    tiene_precision = models.BooleanField(default=False, verbose_name="¿Tiene precisión?")
    tiene_confiabilidad = models.BooleanField(default=False, verbose_name="¿Tiene confiabilidad?")
    cumple_estandares = models.BooleanField(default=False, verbose_name="¿Cumple estándares?")
    es_efectiva = models.BooleanField(default=False, editable=False)

    def save(self, *args, **kwargs):
        if self.tiene_precision and self.tiene_confiabilidad and self.cumple_estandares:
            self.es_efectiva = True
        else:
            self.es_efectiva = False
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_equipo_display()} - {self.get_cliente_display()} - S/N {self.codigo_serial or 'N/A'}"

    class Meta:
        verbose_name = "Registro de Calibración"
        verbose_name_plural = "Registro de Calibraciones"


class OrdenVibracion(models.Model):
    OPCIONES_EQUIPO_VIBRACION = [
        ('bently_nevada', 'Sistemas Bently Nevada'),
        ('ccc', 'Sistemas de Control Compressor Controls Corporation (CCC)'),
        ('compresor_aire', 'Compresor de aire'),
        ('transportador_faja', 'Transportador de faja'),
        ('bomba_centrifuga', 'Bomba centrífuga'),
        ('motor_electrico', 'Motor eléctrico'),
        ('turbina', 'Turbina'),
        ('ventilador_extractor', 'Ventilador / Extractor'),
        ('valvula_control', 'Válvula de control'),
    ]

    OPCIONES_CLIENTE_VIBRACION = [
        ('pdvsa', 'PDVSA'),
        ('pequiven', 'Pequiven'),
        ('sinovensa', 'Sinovensa'),
        ('petrocedeno', 'Petrocedeño'),
        ('petromonagas', 'Petromonagas'),
        ('petropiar', 'Petropiar'),
        ('otros', 'Otros'),
    ]

    equipo = models.CharField(max_length=100, choices=OPCIONES_EQUIPO_VIBRACION, verbose_name="Equipo", default='bently_nevada')
    codigo_serial = models.CharField(max_length=50, verbose_name="Código Serial")
    cliente = models.CharField(max_length=100, choices=OPCIONES_CLIENTE_VIBRACION, verbose_name="Cliente", default='pdvsa')

    # CAMPOS DE CHECKLIST (Basados en Fase II - Cuadros 14, 15 y 18)
    diagnostico_completo = models.BooleanField(default=False, verbose_name="¿El diagnóstico está completo?")
    cumple_estandares = models.BooleanField(default=False, verbose_name="¿Cumple con los estándares establecidos?")
    registro_estructurado = models.BooleanField(default=False, verbose_name="¿El técnico realizó un registro estructurado del servicio?")
    
    es_efectiva = models.BooleanField(default=False, editable=False, verbose_name="¿Orden Efectiva?")

    def save(self, *args, **kwargs):
        if self.diagnostico_completo and self.cumple_estandares and self.registro_estructurado:
            self.es_efectiva = True
        else:
            self.es_efectiva = False
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_equipo_display()} - {self.get_cliente_display()} - S/N {self.codigo_serial or 'N/A'}"

    class Meta:
        verbose_name = "Orden de Vibración"
        verbose_name_plural = "Órdenes de Vibración"


# ==========================================
# MODELO PARA DIAGNÓSTICO PREDICTIVO
# ==========================================

class DiagnosticoPredictivo(models.Model):
    """Modelo para diagnósticos predictivos de equipos con control de tiempo"""
    
    OPCIONES_CLIENTE = [
        ('pdvsa', 'PDVSA'),
        ('pequiven', 'Pequiven'),
        ('sinovensa', 'Sinovensa'),
        ('petrocedeno', 'Petrocedeño'),
        ('petromonagas', 'Petromonagas'),
        ('petropiar', 'Petropiar'),
        ('otros', 'Otros'),
    ]

    OPCIONES_SERVICIO = [
        ('calibracion', 'Servicio de Calibración'),
        ('vibracion', 'Orden de Vibración'),
    ]

    equipo = models.CharField(max_length=150, verbose_name="Equipo")
    codigo_serial = models.CharField(max_length=50, verbose_name="Código Serial", blank=True, null=True)
    cliente = models.CharField(max_length=100, choices=OPCIONES_CLIENTE, verbose_name="Cliente", default='pdvsa')
    servicio = models.CharField(max_length=20, choices=OPCIONES_SERVICIO, verbose_name="Servicio", default='calibracion')

    fecha_inicio = models.DateTimeField(verbose_name="Fecha y Hora de Inicio", help_text="Marque el día y la hora exacta en que comenzó el diagnóstico.")
    fecha_fin = models.DateTimeField(verbose_name="Fecha y Hora de Fin", help_text="Marque el día y la hora en que finalizó el diagnóstico.")

    # 🔧 Campo cambiado a minutos
    tiempo_total_minutos = models.FloatField(default=0, editable=False, verbose_name="Tiempo total (Minutos)")

    def save(self, *args, **kwargs):
        if self.fecha_inicio and self.fecha_fin:
            diferencia = self.fecha_fin - self.fecha_inicio
            # Convertir segundos a minutos
            self.tiempo_total_minutos = round(diferencia.total_seconds() / 60, 2)
        else:
            self.tiempo_total_minutos = 0
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Diagnóstico: {self.equipo} ({self.codigo_serial or 'S/N'}) - {self.get_cliente_display()}"

    class Meta:
        verbose_name = "Diagnóstico Predictivo"
        verbose_name_plural = "Diagnósticos Predictivos"


# ==========================================
# MODELO PARA REGISTRO DE INFORMES (KPI DINÁMICO)
# ==========================================

class RegistroInforme(models.Model):
    """Modelo para registrar el tiempo de generación de informes"""
    
    OPCIONES_CLIENTE = [
        ('pdvsa', 'PDVSA'),
        ('pequiven', 'Pequiven'),
        ('sinovensa', 'Sinovensa'),
        ('petrocedeno', 'Petrocedeño'),
        ('petromonagas', 'Petromonagas'),
        ('petropiar', 'Petropiar'),
        ('otros', 'Otros'),
    ]

    OPCIONES_SERVICIO = [
        ('calibracion', 'Servicio de Calibración'),
        ('vibracion', 'Orden de Vibración'),
    ]

    titulo = models.CharField(max_length=200, verbose_name="Título del informe")
    equipo = models.CharField(max_length=150, verbose_name="Equipo", blank=True)
    codigo_serial = models.CharField(max_length=50, verbose_name="Código Serial")
    cliente = models.CharField(max_length=100, choices=OPCIONES_CLIENTE, verbose_name="Cliente", default='pdvsa')
    servicio = models.CharField(max_length=20, choices=OPCIONES_SERVICIO, verbose_name="Servicio", default='calibracion')
    
    diagnostico_previo = models.ForeignKey(
        DiagnosticoPredictivo, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Diagnóstico Previo"
    )

    hora_inicio = models.DateTimeField(default=timezone.now, verbose_name="Hora de inicio")
    hora_fin = models.DateTimeField(verbose_name="Hora de fin")
    tiempo_generacion_horas = models.FloatField(default=0, editable=False, verbose_name="Tiempo de generación (h)")

    def save(self, *args, **kwargs):
        if self.hora_fin:
            diferencia = self.hora_fin - self.hora_inicio
            self.tiempo_generacion_horas = round(diferencia.total_seconds() / 3600, 2)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.titulo

    class Meta:
        verbose_name = "Registro de Informe"
        verbose_name_plural = "Registros de Informes"