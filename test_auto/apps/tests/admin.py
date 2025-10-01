from django.contrib import admin
from .models import RespuestaTest

# Register your models here.

@admin.register(RespuestaTest)
class RespuestaTestAdmin(admin.ModelAdmin):
    list_display = ('user', 'test', 'pregunta_numero', 'respuesta_seleccionada')
    search_fields = ('test',)
