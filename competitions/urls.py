from django.urls import path
from . import views

app_name = "competitions"
urlpatterns = [
    path("bracket/<int:bracket_id>/", views.BracketView, name="bracket")
]
