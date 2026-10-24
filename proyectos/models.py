from django.db import models

class Proyecto(models.Model):
    ESTADOS = [
        ('borrador', 'Borrador'),
        ('en_progreso', 'En Progreso'),
        ('finalizado', 'Finalizado'),
    ]

    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(verbose_name="Descripción")
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(verbose_name="Fecha de entrega")
    estado = models.CharField(max_length=20, choices=ESTADOS, default='borrador')

    def __str__(self):
        return self.nombre
