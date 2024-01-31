from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls.i18n import i18n_patterns

urlpatterns = [
    path('', include("competitions.urls")), 
    path('admin/', admin.site.urls),
    path('hijack/', include('hijack.urls')),
    path('__debug__/', include("debug_toolbar.urls")),
    path('i18n/', include('django.conf.urls.i18n')),
    *static(settings.STATIC_URL, document_root=settings.STATIC_ROOT),
    *staticfiles_urlpatterns(),
]
