# bi/models.py
from django.db import models
from django.contrib.auth.models import User


class Alerta(models.Model):
    TIPO_CHOICES = [
        ('DANGER', 'Crítica'),
        ('WARNING', 'Advertencia'),
        ('INFO', 'Informativa'),
        ('SUCCESS', 'Correcta'),
    ]
    
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='INFO')
    fecha = models.DateTimeField(auto_now_add=True)
    leida = models.BooleanField(default=False)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    link = models.CharField(max_length=200, blank=True)
    
    def __str__(self):
        return f"{self.titulo} - {self.fecha.strftime('%d/%m/%Y')}"
    
    class Meta:
        ordering = ['-fecha']
        verbose_name_plural = "Alertas"


class KPIRegistro(models.Model):
    """Registro histórico de KPIs para análisis de tendencias"""
    fecha = models.DateField(auto_now_add=True)
    efectividad_calibraciones = models.FloatField(default=0)
    volumen_ordenes = models.FloatField(default=0)
    tiempo_diagnostico = models.FloatField(default=0)
    tiempo_informe = models.FloatField(default=0)
    
    def __str__(self):
        return f"KPI - {self.fecha}"