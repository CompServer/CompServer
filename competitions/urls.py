from django.urls import path
from . import views

app_name = "competitions"
urlpatterns = [
    path('', views.not_implemented, name="index"),
    path("bracket/", views.BracketView, name="bracket"),
    path("competition/", views.competitions, name="competitions"),
    path("competition/<int:competition_id>", views.competition, name="competition"),
    path("team/<int:team_id>/", views.team, name="team"),
    path("tournament/", views.not_implemented, name="tournaments"),
    path("tournament/<int:tournament_id>/", views.not_implemented, name="tournament"),
    # path("coach/<int:coach_id>/", views.coach, name="coach-page"),
    path("match/<int:match_id>/judge/", views.judge_match, name="match"),
    #path('match/<int:pk>/judge/', views.JudgeMatchUpdateView.as_view(), name='judge_match'),
]
