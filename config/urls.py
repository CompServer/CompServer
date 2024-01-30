from django.contrib import admin
from django.urls import path
from .views import *

urlpatterns = [
    path('admin/', admin.site.urls),
    path('team/<id:team_id>/, views.team_page', name="team-page"),
    # path('coach/<id:coach_id>/', views.coach_page, name="coach-page"),
]
