from django.urls import path
from . import views

app_name = "competitions"
urlpatterns = [
    path("", views.BracketView, name="bracket"),
    path("competition", views.competitions, name="competitions"),
    path("competition/<int:competition_id>", views.competition, name="competition")
]
