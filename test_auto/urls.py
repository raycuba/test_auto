"""
URL configuration for test_auto project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.urls import include

from test_auto.apps.main.urls import urlpatterns as main_urls
from test_auto.apps.tests.urls import urlpatterns as test_urls
from test_auto.apps.examenes.urls import urlpatterns as examenes_urls

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('test_auto.apps.main.urls', namespace='home')),
    path('tests/', include('test_auto.apps.tests.urls', namespace='tests')),
    path('examenes/', include('test_auto.apps.examenes.urls', namespace='examenes')),
]

