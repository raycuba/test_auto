from django.urls import path
from django.urls import include

from . import views

app_name = "examenes"

urlpatterns = [
    path('', views.list, name='list'),
    path('pregunta_view/<str:examen>/<int:numero>/', views.pregunta_view, name='pregunta_view'),
]
