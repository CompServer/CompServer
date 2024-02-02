from django.urls import path
from . import views

app_name = "competitions"
urlpatterns = [
    path("", views.BracketView, name="bracket"),
    path("competition", views.competitions, name="competitions"),
    path("competition/<int:competition_id>", views.competition, name="competition"),
    path("team/<int:team_id>/", views.team_page, name="team-page"),
    # path("coach/<int:coach_id>/", views.coach_page, name="coach-page"),
]
