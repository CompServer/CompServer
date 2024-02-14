from django.urls import path
from . import views
from django.views.generic.base import RedirectView

app_name = "competitions"
urlpatterns = [
    path('', views.home, name="home"),
    path('', RedirectView.as_view(url='index', permanent=True), name='index'),
    path("competition/", views.competitions, name="competitions"),
    path("competition/<int:competition_id>/", views.competition, name="competition"),
    path("team/<int:team_id>/", views.team, name="team"),
    path("tournament/", views.tournaments, name="tournaments"),
    path("tournament/<int:tournament_id>/", views.single_elim_tournament, name="single_elim_tournament"),
    # path("coach/<int:coach_id>/", views.coach, name="coach-page"),
    path('match/<int:pk>/judge/', views.judge_match, name='judge_match'),
    path('credits/', views.credits, name="credits"),
    path("match/<int:match_id>/judge/", views.judge_match, name="match"),
    #path('match/<int:pk>/judge/', views.JudgeMatchUpdateView.as_view(), name='judge_match'),


    path('settings/timezone/',views.set_timezone_view, name='set_timezone')
]
