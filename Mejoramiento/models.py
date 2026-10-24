from django.db import models

class TareaMejoramiento(models.Model):
    titulo = models.CharField(max_length=100, verbose_name="Título de la Mejora")
    descripcion = models.TextField(verbose_name="Descripción")

    def __str__(self):
        return self.titulo
