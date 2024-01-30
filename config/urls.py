from django.contrib import admin
from django.urls import include, path
from django.views.generic.base import TemplateView
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', include('competitions.urls')),
    path('admin/', admin.site.urls),
    path('hijack/', include('hijack.urls')),
    path('__debug__/', include("debug_toolbar.urls")),
]