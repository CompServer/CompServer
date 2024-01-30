from django.urls import path

from . import views

app_name = "competitions"
urlpatterns = [
    path(r'notimplemented/', views.not_implemented, name="hub"),
]

handler404 = 'competitions.views.not_implemented'
