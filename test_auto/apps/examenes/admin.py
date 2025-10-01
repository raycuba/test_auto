from django.contrib import admin
from .models import RespuestaExamen

# Register your models here.

@admin.register(RespuestaExamen)
class RespuestaExamenAdmin(admin.ModelAdmin):
    list_display = ('user', 'examen', 'pregunta_numero', 'respuesta_seleccionada')
    search_fields = ('examen',)
