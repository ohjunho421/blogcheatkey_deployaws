"""
Simple URL configuration for testing Django deployment
"""
from django.contrib import admin
from django.urls import path
from django.http import HttpResponse

def home_view(request):
    return HttpResponse("Django is working on Elastic Beanstalk!")

def health_check(request):
    return HttpResponse("OK")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_view, name='home'),
    path('health/', health_check, name='health'),
]
