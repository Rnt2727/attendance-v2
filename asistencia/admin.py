from django.contrib import admin
from .models import Estudiante, RegistroAsistencia

@admin.register(Estudiante)
class EstudianteAdmin(admin.ModelAdmin):
    list_display = ('codigo_barras', 'dni', 'nombre', 'apellidos', 'nombre_padre', 
                   'celular_padre', 'activo', 'fecha_registro')
    list_filter = ('activo', 'fecha_registro')
    search_fields = ('codigo_barras', 'dni', 'nombre', 'apellidos', 'nombre_padre')
    ordering = ('apellidos', 'nombre')

@admin.register(RegistroAsistencia)
class RegistroAsistenciaAdmin(admin.ModelAdmin):
    list_display = ('estudiante', 'fecha', 'usuario', 'notificacion_enviada')
    list_filter = ('fecha', 'notificacion_enviada', 'usuario')
    search_fields = ('estudiante__nombre', 'estudiante__apellidos', 'estudiante__dni')
    date_hierarchy = 'fecha'
    ordering = ('-fecha',)