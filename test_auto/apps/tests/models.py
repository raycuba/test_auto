from django.db import models

# Create your models here.

class RespuestaTest(models.Model):
    test = models.CharField(max_length=100)
    pregunta_numero = models.IntegerField()
    respuesta_seleccionada = models.CharField(max_length=100)
    fecha_respuesta = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Test: {self.test}, Pregunta: {self.pregunta_numero}, Respuesta: {self.respuesta_seleccionada}"
