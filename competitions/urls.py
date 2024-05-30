from django.urls import path
from django.urls import reverse_lazy
from django.views.generic.base import RedirectView

from config.settings import DEMO

from . import views

app_name = "competitions"
urlpatterns = [
    path("arena/<int:arena_id>/", views.arena, name="arena"),
    path("competition/<int:competition_id>/new_judge/", views.new_judge, name="new_judge"),
    path("competition/", views.competitions, name="competitions"),
    path("competition/create/", views.create_competition, name="create_competition"),
    path("competition/<int:competition_id>/", views.competition, name="competition"),
    path("competition/<int:competition_id>/", RedirectView.as_view(url='competition'), name="competition_score"), # legacy so they can be hyperlinked to
    path("competition/<int:competition_id>/results", views.results, name="results"), # legacy so they can be hyperlinked to
    path("organization/<int:organization_id>/", views.organization, name="organization"),
    path("team/<int:team_id>/", views.team, name="team"),
    path("tournament/create/legacy/", views.create_tournament_legacy, name="create_tournament_legacy"), # so it passes tests
    path("tournament/create/", views.create_tournament_htmx, name="create_tournament"),
    path("tournament/<int:tournament_id>/edit/", views.edit_tournament, name="edit_tournament"),
    path("tournament/<int:tournament_id>/", views.tournament, name="tournament"),
    path("tournament/<int:tournament_id>/", RedirectView.as_view(url='tournament'), name="round_robin_tournament"), # both legacy so they can be hyperlinked to
    path("tournament/<int:tournament_id>/", RedirectView.as_view(url='tournament'), name="single_elimination_tournament"), # both legacy so they can be hyperlinked to
    path("tournament/<int:tournament_id>/generate/", views.generate_tournament_matches, name="_generate_matches"),
    path("tournament/<int:tournament_id>/swap/", views.swap_matches, name="swap_matches"),
    path("tournament/swap_teams/<int:match1_id>/<int:match2_id>/", views.swap_teams, name="swap_teams"),
    path("competition/<int:competition_id>/color/", views.arena_color, name="arena_color"),
    path("match/<int:match_id>/judge/", views.judge_match, name="judge_match"),
    path("profile/<int:profile_id>/", views.profile, name="profile"),
    path('credits/', views.credits, name="credits"),
    path('_error/', views._raise_error_code, name="_error"), # for testing error pages
    path('settings/timezone/',views.set_timezone_view, name='set_timezone'),
]

if DEMO:
    # show information about this webapp
    urlpatterns += [path('', views.home, name="home")]
else:
    # go directly to the competitions page
    urlpatterns += [path('', RedirectView.as_view(url=reverse_lazy("competitions:competitions")), name="home")]
