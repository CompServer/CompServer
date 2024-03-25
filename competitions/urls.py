from django.urls import path
from . import views
from django.views.generic.base import RedirectView

app_name = "competitions"
urlpatterns = [
    path('', views.home, name="home"),
    path("competition/", views.competitions, name="competitions"),
    path("competition/<int:competition_id>/", views.competition, name="competition"),
    path("competition/<int:competition_id>/", RedirectView.as_view(url='competition'), name="competition_score"), # legacy so they can be hyperlinked to
    path("competition/<int:competition_id>/results", views.results, name="results"), # legacy so they can be hyperlinked to
    path("team/<int:team_id>/", views.team, name="team"),
    path("tournament/", views.tournaments, name="tournaments"),
    path("tournament/<int:tournament_id>/", views.tournament, name="tournament"),
    path("tournament/<int:tournament_id>/", RedirectView.as_view(url='tournament'), name="round_robin_tournament"), # both legacy so they can be hyperlinked to
    path("tournament/<int:tournament_id>/", RedirectView.as_view(url='tournament'), name="single_elimination_tournament"), # both legacy so they can be hyperlinked to
    path("tournament/<int:tournament_id>/generate/", views.generate_tournament_matches, name="generate_matches"),
    # path("coach/<int:coach_id>/", views.coach, name="coach-page"),
    # path("match/<int:match_id>/", views.match, name="match"),
    path("match/<int:match_id>/judge/", views.judge_match, name="judge_match"),
    path("competition/profile/<int:profile_id>/", views.profile, name="user_profile"),
    path('credits/', views.credits, name="credits"),
    path('settings/timezone/',views.set_timezone_view, name='set_timezone'),
]
