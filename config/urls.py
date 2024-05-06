from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns = [
    path('', include("competitions.urls")), 
    path('', include('social_django.urls', namespace='social')),
    path('api/v1/', include('api.urls')),
    path('admin/', admin.site.urls),
    path('hijack/', include('hijack.urls')),
    path('__debug__/', include("debug_toolbar.urls")),
    path('i18n/', include('django.conf.urls.i18n')),
    path('accounts/', include('django.contrib.auth.urls')),
    #path('tz_detect/', include('tz_detect.urls')),
    *static(settings.STATIC_URL, document_root=settings.STATIC_ROOT),
    *staticfiles_urlpatterns(),
    *static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),
]
