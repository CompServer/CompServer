from datetime import date, timedelta
from django.contrib import admin
from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone
from . import models
from .models import *
from .urls import *


class SanityTests(TestCase):
    ''' Make sure all our pages come up without server errors '''
    @classmethod
    def setUpTestData(cls):
        cls.today = date.today()
        cls.yesterday = cls.today - timedelta(days=1)
        cls.tomorrow = cls.today + timedelta(days=1)
        cls.sport = Sport.objects.create(name="Robotics")
        cls.event = Event.objects.create(name="Sumo", sport=cls.sport)
        cls.non_judge = User.objects.create(username="norm")
        cls.admin = User.objects.create(username="albert", password="adminPass")
        cls.admin.is_superuser = True
        cls.admin.is_staff = True
        cls.admin.save()
        cls.open_old_competition = Competition.objects.create(name='open_old_competition', status=Status.OPEN, start_date=cls.yesterday, end_date=cls.yesterday)
        cls.open_current_competition = Competition.objects.create(name='open_current_competition', status=Status.OPEN, start_date=cls.yesterday, end_date=cls.tomorrow)
        cls.open_future_competition = Competition.objects.create(name='open_future_competition', status=Status.OPEN, start_date=cls.tomorrow, end_date=cls.tomorrow)
        cls.open_tournament = SingleEliminationTournament.objects.create(status=Status.OPEN, event=cls.event, competition=cls.open_current_competition)
        cls.closed_tournament = SingleEliminationTournament.objects.create(status=Status.CLOSED, event=cls.event, competition=cls.open_current_competition)
        cls.tournament_judge = User.objects.create(username="terry", password="tournamentPass")
        cls.open_tournament.judges.add(cls.tournament_judge)
        cls.competition_judge = User.objects.create(username="carl")
        cls.open_old_competition.plenary_judges.add(cls.competition_judge)
        cls.open_current_competition.plenary_judges.add(cls.competition_judge)
        cls.open_future_competition.plenary_judges.add(cls.competition_judge)
        cls.team_no_competition = Team.objects.create(name="Ninjas")
        cls.team_in_competition_but_no_tournament = Team.objects.create(name="Cobras")
        cls.team_in_competition_and_tournament = Team.objects.create(name="Tridents")
        cls.team1_in_competition_and_tournament_and_match = Team.objects.create(name="Maroons1")
        cls.team2_in_competition_and_tournament_and_match = Team.objects.create(name="Maroons2")
        cls.open_current_competition.teams.add(cls.team_in_competition_but_no_tournament)
        cls.open_current_competition.teams.add(cls.team_in_competition_and_tournament)
        cls.open_current_competition.teams.add(cls.team1_in_competition_and_tournament_and_match)
        cls.open_current_competition.teams.add(cls.team2_in_competition_and_tournament_and_match)
        cls.open_tournament.teams.add(cls.team_in_competition_and_tournament)
        cls.open_tournament.teams.add(cls.team1_in_competition_and_tournament_and_match)
        cls.open_tournament.teams.add(cls.team2_in_competition_and_tournament_and_match)
        cls.match = Match.objects.create(tournament=cls.open_tournament)
        cls.match.starting_teams.add(cls.team1_in_competition_and_tournament_and_match)
        cls.match.starting_teams.add(cls.team2_in_competition_and_tournament_and_match)
        # cls.admin = User.objects.create(username="albert", password="adminPass")
        # cls.client = Client()
        # cls.client.login(username="albert", password="adminPass")

    def setUp(self):
        self.admin_client = Client()
        self.admin_client.login(username="albert", password="adminPass")
        self.competition_judge_client = Client()
        self.competition_judge_client.login(username="albert", password="adminPass")
        self.tournament_judge_client = Client()
        self.tournament_judge_client.login(username="albert", password="adminPass")
        
    def test_all_url_patterns(self):
        # pass
        for path in urlpatterns:
            url = None
            try:
                url = reverse(app_name+":"+path.name)
            except:
                try:
                    url = reverse(app_name+":"+path.name, args=[1])
                except:
                    pass
            if url:
                print(url, flush=True)
                response = self.admin_client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_all_admin_pages(self):
        pass
        # for model in admin.site._registry:
        #     if model.__module__[:12] == "competitions":
        #         response = SanityTests.client.get('/admin/competitions/'+model.__name__.lower())
        #         self.assertEqual(response.status_code, 200, "Could not view admin page for model " + model.__name__)
    

class JudgeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        pass
        # cls.today = datetime.date.today()
        # cls.yesterday = cls.today - datetime.timedelta(days = 1)
        # cls.tomorrow = cls.today + datetime.timedelta(days = 1)
        # cls.non_judge = User.objects.create(username="norm")
        # cls.tournament_judge = User.objects.create(username="terry")
        # cls.open_old_competition = Competition.objects.create(name='open_old_competition', status=Status.OPEN, start_date=cls.yesterday, end_date=cls.yesterday)
        # cls.open_current_competition = Competition.objects.create(name='open_current_competition', status=Status.OPEN, start_date=cls.yesterday, end_date=cls.tomorrow)
        # cls.open_future_competition = Competition.objects.create(name='open_future_competition', status=Status.OPEN, start_date=cls.tomorrow, end_date=cls.tomorrow)
        # cls.competition_judge = User.objects.create(username="carl")
        # cls.competition_judge.competition_set.add(cls.open_old_competition)
        # cls.competition_judge.competition_set.add(cls.open_current_competition)
        # cls.competition_judge.competition_set.add(cls.open_future_competition)
        # cls.admin = User.objects.create(username="albert")

    def test_judge_but_not_logged_in(self):
        pass

    def test_judge_but_not_for_this_competition(self):
        pass
    
    def test_judge_for_this_competition_but_not_this_tournament(self):
        pass

    def test_judge_is_plenary_judge(self):
        pass

    def test_judge_is_tournament_judge(self):
        pass

    def test_judge_but_competition_not_open(self):
        pass

    def test_judge_but_tournament_not_open(self):
        pass

    def test_judge_but_tournament_not_open(self):
        pass


class JudgingTests(TestCase):
    ''' Assumes the judge is valid; Check the content of the judging page '''
    def test_advance_options_are_all_competitors(self):
        pass

    def test_advance_options_are_only_competitors(self):
        pass

    def test_single_can_advance(self):
        pass

    def test_multiple_can_advance(self):
        pass

    def test_only_competitors_can_advance(self):
        pass
        # c = Client()
        # c.login(username="admin", password="admin")
        # response = c.post("/match/85/judge/", {"advancers": 25})
        # print(response)


