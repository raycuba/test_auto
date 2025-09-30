from django.urls import path
from django.urls import include

from . import views

app_name = "tests"

urlpatterns = [
    path('', views.list, name='list'),
    path('pregunta_view/<str:test>/<int:numero>/', views.pregunta_view, name='pregunta_view'),
    path('respuesta/', views.registrar_respuesta, name='registrar_respuesta'),
    path('clean_respuestas/<str:test>/', views.clean_respuestas, name='clean_respuestas'),
    path('resultado/<str:test>/', views.resultado_view, name='resultado_view'),
]
