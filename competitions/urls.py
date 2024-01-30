from django.urls import path
from .views import *


app_name = "PictoWall"
urlpatterns = [
    path("", BracketView, name="bracket"),
]