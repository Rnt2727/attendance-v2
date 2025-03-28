from django.db import models
from django.contrib.auth.models import User

class Estudiante(models.Model):
    dni = models.CharField(max_length=8, unique=True, null=True, blank=True)
    nombre = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100, null=True, blank=True)
    nombre_padre = models.CharField(max_length=200, null=True, blank=True)
    celular_padre = models.CharField(max_length=9, null=True, blank=True)
    activo = models.BooleanField(default=True, null=True, blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    # Nuevos campos:
    NIVEL_CHOICES = [
        ('primaria', 'Primaria'),
        ('secundaria', 'Secundaria'),
    ]
    nivel = models.CharField(max_length=10, choices=NIVEL_CHOICES, default='primaria')
    grado = models.PositiveIntegerField(null=True, blank=True)
    seccion = models.CharField(max_length=1, null=True, blank=True)

    class Meta:
        verbose_name = 'Estudiante'
        verbose_name_plural = 'Estudiantes'

    def __str__(self):
        return f"{self.nombre} {self.apellidos}"

class RegistroAsistencia(models.Model):
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    notificacion_enviada = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Registro de Asistencia'
        verbose_name_plural = 'Registros de Asistencia'
        ordering = ['-fecha']

    def __str__(self):
        return f"Asistencia de {self.estudiante} - {self.fecha.strftime('%d/%m/%Y %H:%M')}"