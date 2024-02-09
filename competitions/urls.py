from django.urls import path
from . import views

app_name = "competitions"
urlpatterns = [
    path("", views.home, name="home"),
    path("competition/", views.competitions, name="competitions"),
    path("competition/<int:competition_id>", views.competition, name="competition"),
    path("teams/team/<int:team_id>/", views.team, name="team"),
    path("tournament/", views.tournaments, name="tournaments"),
    path("tournament/<int:tournament_id>/", views.BracketView, name="tournament"),
    # path("coach/<int:coach_id>/", views.coach, name="coach-page"),
    path('match/<int:pk>/judge/', views.JudgeMatchUpdateView.as_view(), name='judge_match'),
]
