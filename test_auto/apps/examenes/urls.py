from django.urls import path
from django.urls import include

from . import views

app_name = "examenes"

urlpatterns = [
    path('', views.list, name='list')
]
