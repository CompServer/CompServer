from datetime import date, timedelta
from django.contrib import admin
from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone
from . import models
from .models import *
from .views import *
from .urls import *


class SanityTests(TestCase):
    ''' Make sure all our pages come up without server errors '''
    @classmethod
    def setUpTestData(cls):
        cls.today = date.today()
        cls.yesterday = cls.today - timedelta(days=1)
        cls.tomorrow = cls.today + timedelta(days=1)
        cls.organization = Organization.objects.create(name="University of Chicago Laboratory Schools")
        cls.sport = Sport.objects.create(name="Robotics")
        cls.event = Event.objects.create(name="Sumo", sport=cls.sport)
        cls.non_judge = User.objects.create(username="norm")
        cls.admin = User.objects.create(username="albert")
        cls.admin.set_password("adminPass")
        cls.admin.is_superuser = True
        cls.admin.is_staff = True
        cls.admin.save()
        cls.open_old_competition = Competition.objects.create(name='open_old_competition', status=Status.OPEN, start_date=cls.yesterday, end_date=cls.yesterday)
        cls.open_current_competition = Competition.objects.create(name='open_current_competition', status=Status.OPEN, start_date=cls.yesterday, end_date=cls.tomorrow)
        cls.open_future_competition = Competition.objects.create(name='open_future_competition', status=Status.OPEN, start_date=cls.tomorrow, end_date=cls.tomorrow)
        cls.open_tournament = SingleEliminationTournament.objects.create(status=Status.OPEN, event=cls.event, competition=cls.open_current_competition)
        cls.closed_tournament = SingleEliminationTournament.objects.create(status=Status.CLOSED, event=cls.event, competition=cls.open_current_competition)
        cls.tournament_judge = User.objects.create(username="terry")
        cls.tournament_judge.set_password("tournamentPass")
        cls.tournament_judge.save()
        cls.open_tournament.judges.add(cls.tournament_judge)
        cls.competition_judge = User.objects.create(username="carl")
        cls.competition_judge.set_password("competitionPass")
        cls.competition_judge.save()
        cls.open_old_competition.plenary_judges.add(cls.competition_judge)
        cls.open_current_competition.plenary_judges.add(cls.competition_judge)
        cls.open_future_competition.plenary_judges.add(cls.competition_judge)
        cls.team_no_competition = Team.objects.create(name="Ninjas")
        cls.team_in_competition_but_no_tournament = Team.objects.create(name="Cobras")
        cls.team_in_competition_and_tournament_but_no_match = Team.objects.create(name="Tridents")
        cls.team1_in_competition_and_tournament_and_match = Team.objects.create(name="Maroons1")
        cls.team2_in_competition_and_tournament_and_match = Team.objects.create(name="Maroons2")
        cls.open_current_competition.teams.add(cls.team_in_competition_but_no_tournament)
        cls.open_current_competition.teams.add(cls.team_in_competition_and_tournament_but_no_match)
        cls.open_current_competition.teams.add(cls.team1_in_competition_and_tournament_and_match)
        cls.open_current_competition.teams.add(cls.team2_in_competition_and_tournament_and_match)
        cls.open_tournament.teams.add(cls.team_in_competition_and_tournament_but_no_match)
        cls.open_tournament.teams.add(cls.team1_in_competition_and_tournament_and_match)
        cls.open_tournament.teams.add(cls.team2_in_competition_and_tournament_and_match)
        cls.match_rank1 = Ranking.objects.create(tournament=cls.open_tournament, team=cls.team1_in_competition_and_tournament_and_match, rank=1)
        cls.match_rank1 = Ranking.objects.create(tournament=cls.open_tournament, team=cls.team2_in_competition_and_tournament_and_match, rank=2)
        cls.match = Match.objects.create(tournament=cls.open_tournament)
        cls.match.starting_teams.add(cls.team1_in_competition_and_tournament_and_match)
        cls.match.starting_teams.add(cls.team2_in_competition_and_tournament_and_match)

    def setUp(self):
        self.admin_client = Client()
        success = self.admin_client.login(username="albert", password="adminPass")
        self.assertTrue(success, "Failed to login admin")
        self.competition_judge_client = Client()
        success = self.competition_judge_client.login(username="carl", password="competitionPass")
        self.assertTrue(success, "Failed to login competition judge")
        self.tournament_judge_client = Client()
        success = self.tournament_judge_client.login(username="terry", password="tournamentPass")
        self.assertTrue(success, "Failed to login tournament judge")

    def test_all_url_patterns(self):
        # Admin should be able to get to all pages
        for path in urlpatterns:
            if 'generate' not in path.name:
                url = None
                try:
                    url = reverse(app_name+":"+path.name)
                except:
                    try:
                        url = reverse(app_name+":"+path.name, args=[1]) # try the first one
                    except:
                        continue
                if url:
                    response = self.admin_client.get(url)
                    self.assertEqual(response.status_code, 200, "For "+str(url))

    def test_all_admin_pages(self):
        for model in admin.site._registry:
            if model.__module__[:12] == "competitions":
                # try the list page
                response = self.admin_client.get('/admin/competitions/'+model.__name__.lower()+"/")
                self.assertEqual(response.status_code, 200, "Could not view admin list page for model " + model.__name__)
                # try the change page
                response = self.admin_client.get('/admin/competitions/'+model.__name__.lower()+"/1/change/")
                self.assertEqual(response.status_code, 200, "Could not view admin change page for model " + model.__name__)
    
    def test_public_pages(self):
        # All pages except judging should be accessible to an anonymous user (without being redirected to login)
        anon_client = Client()
        for path in urlpatterns:
            if 'judg' not in path.name and 'generate' not in path.name:
                url = None
                try:
                    url = reverse(app_name+":"+path.name)
                except:
                    try:
                        url = reverse(app_name+":"+path.name, args=[1]) # try the first one
                    except:
                        continue
                if url:
                    response = anon_client.get(url)
                    self.assertEqual(response.status_code, 200, "For "+str(url))


class JudgeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.today = date.today()
        cls.yesterday = cls.today - timedelta(days=1)
        cls.tomorrow = cls.today + timedelta(days=1)
        cls.organization = Organization.objects.create(name="University of Chicago Laboratory Schools")
        cls.sport = Sport.objects.create(name="Robotics")
        cls.event = Event.objects.create(name="Sumo", sport=cls.sport)
        cls.non_judge = User.objects.create(username="norm")
        cls.admin = User.objects.create(username="albert")
        cls.admin.set_password("adminPass")
        cls.admin.is_superuser = True
        cls.admin.is_staff = True
        cls.admin.save()
        cls.open_old_competition = Competition.objects.create(name='open_old_competition', status=Status.OPEN, start_date=cls.yesterday, end_date=cls.yesterday)
        cls.open_current_competition = Competition.objects.create(name='open_current_competition', status=Status.OPEN, start_date=cls.yesterday, end_date=cls.tomorrow)
        cls.other_open_current_competition = Competition.objects.create(name='other_open_current_competition', status=Status.OPEN, start_date=cls.yesterday, end_date=cls.tomorrow)
        cls.open_future_competition = Competition.objects.create(name='open_future_competition', status=Status.OPEN, start_date=cls.tomorrow, end_date=cls.tomorrow)
        cls.closed_current_competition = Competition.objects.create(name='closed_current_competition', status=Status.CLOSED, start_date=cls.yesterday, end_date=cls.tomorrow)
        cls.open_tournament = SingleEliminationTournament.objects.create(status=Status.OPEN, event=cls.event, competition=cls.open_current_competition)
        cls.other_tournament = SingleEliminationTournament.objects.create(status=Status.OPEN, event=cls.event, competition=cls.open_current_competition)
        cls.closed_tournament = SingleEliminationTournament.objects.create(status=Status.CLOSED, event=cls.event, competition=cls.open_current_competition)
        
        cls.tournament_judge = User.objects.create(username="terry")
        cls.tournament_judge.set_password("tournamentPass")
        cls.tournament_judge.save()
        cls.open_tournament.judges.add(cls.tournament_judge)
        cls.closed_tournament.judges.add(cls.tournament_judge)

        cls.other_tournament_judge = User.objects.create(username="other_terry")
        cls.other_tournament_judge.set_password("tournamentPass")
        cls.other_tournament_judge.save()
        cls.other_tournament.judges.add(cls.other_tournament_judge)

        cls.competition_judge = User.objects.create(username="carl")
        cls.competition_judge.set_password("competitionPass")
        cls.competition_judge.save()
        cls.open_old_competition.plenary_judges.add(cls.competition_judge)
        cls.open_current_competition.plenary_judges.add(cls.competition_judge)
        cls.open_future_competition.plenary_judges.add(cls.competition_judge)

        cls.other_competition_judge = User.objects.create(username="other_carl")
        cls.other_competition_judge.set_password("competitionPass")
        cls.other_competition_judge.save()
        cls.other_open_current_competition.plenary_judges.add(cls.other_competition_judge)

        cls.team_no_competition = Team.objects.create(name="Ninjas")
        cls.team_in_competition_but_no_tournament = Team.objects.create(name="Cobras")
        cls.team_in_competition_and_tournament_but_no_match = Team.objects.create(name="Tridents")
        cls.team1_in_competition_and_tournament_and_match = Team.objects.create(name="Maroons1")
        cls.team2_in_competition_and_tournament_and_match = Team.objects.create(name="Maroons2")
        cls.open_current_competition.teams.add(cls.team_in_competition_but_no_tournament)
        cls.open_current_competition.teams.add(cls.team_in_competition_and_tournament_but_no_match)
        cls.open_current_competition.teams.add(cls.team1_in_competition_and_tournament_and_match)
        cls.open_current_competition.teams.add(cls.team2_in_competition_and_tournament_and_match)
        cls.open_tournament.teams.add(cls.team_in_competition_and_tournament_but_no_match)
        cls.open_tournament.teams.add(cls.team1_in_competition_and_tournament_and_match)
        cls.open_tournament.teams.add(cls.team2_in_competition_and_tournament_and_match)
        cls.closed_tournament.teams.add(cls.team1_in_competition_and_tournament_and_match)
        cls.closed_tournament.teams.add(cls.team2_in_competition_and_tournament_and_match)
        
        cls.match_rank1 = Ranking.objects.create(tournament=cls.open_tournament, team=cls.team1_in_competition_and_tournament_and_match, rank=1)
        cls.match_rank1 = Ranking.objects.create(tournament=cls.open_tournament, team=cls.team2_in_competition_and_tournament_and_match, rank=2)
        cls.match = Match.objects.create(tournament=cls.open_tournament)
        cls.match.starting_teams.add(cls.team1_in_competition_and_tournament_and_match)
        cls.match.starting_teams.add(cls.team2_in_competition_and_tournament_and_match)
        cls.match_closed_tournament = Match.objects.create(tournament=cls.closed_tournament)
        cls.match_closed_tournament.starting_teams.add(cls.team1_in_competition_and_tournament_and_match)
        cls.match_closed_tournament.starting_teams.add(cls.team2_in_competition_and_tournament_and_match)

    def setUp(self):
        self.admin_client = Client()
        success = self.admin_client.login(username="albert", password="adminPass")
        self.assertTrue(success, "Failed to login admin")
        self.competition_judge_client = Client()
        success = self.competition_judge_client.login(username="carl", password="competitionPass")
        self.assertTrue(success, "Failed to login competition judge")
        self.other_competition_judge_client = Client()
        success = self.other_competition_judge_client.login(username="other_carl", password="competitionPass")
        self.assertTrue(success, "Failed to login competition judge")
        self.tournament_judge_client = Client()
        success = self.tournament_judge_client.login(username="terry", password="tournamentPass")
        self.assertTrue(success, "Failed to login tournament judge")
        self.other_tournament_judge_client = Client()
        success = self.other_tournament_judge_client.login(username="other_terry", password="tournamentPass")
        self.assertTrue(success, "Failed to login tournament judge")
 
    def test_judge_but_not_logged_in(self):
        anon_client = Client()
        url = reverse("competitions:judge_match", args=[self.__class__.match.id])
        response = anon_client.post(url, {"advancers": self.__class__.team1_in_competition_and_tournament_and_match.id})
        self.assertNotEqual(response.status_code, 200, "Shouldn't have been able to judge a match if you're not logged in")

    def test_judge_but_not_for_this_competition(self):
        url = reverse("competitions:judge_match", args=[self.__class__.match.id])
        response = self.other_competition_judge_client.post(url, {"advancers": self.__class__.team1_in_competition_and_tournament_and_match.id})
        self.assertNotEqual(response.status_code, 200, "Shouldn't have been able to judge a match if you're not a judge for this competition")
    
    def test_judge_for_this_competition_but_not_this_tournament(self):
        url = reverse("competitions:judge_match", args=[self.__class__.match.id])
        response = self.other_tournament_judge_client.post(url, {"advancers": self.__class__.team1_in_competition_and_tournament_and_match.id})
        self.assertNotEqual(response.status_code, 200, "Shouldn't have been able to judge a match if you're not a judge for this competition or this tournament")

    def test_judge_is_plenary_judge(self):
        pass

    def test_judge_is_tournament_judge(self):
        pass

    def test_judge_but_competition_not_open(self):
        pass

    def test_judge_but_tournament_not_open(self):
        url = reverse("competitions:judge_match", args=[self.__class__.match_closed_tournament.id])
        response = self.tournament_judge_client.post(url, {"advancers": self.__class__.team1_in_competition_and_tournament_and_match.id})
        self.assertNotIn(response.status_code, range(200,400), "Shouldn't have been able to judge a match in a closed tournament")
        # failing for the wrong reasons...



class JudgingTests(TestCase):
    ''' Assumes the judge is valid; Check the content of the judging page '''
    @classmethod
    def setUpTestData(cls):
        cls.today = date.today()
        cls.yesterday = cls.today - timedelta(days=1)
        cls.tomorrow = cls.today + timedelta(days=1)
        cls.organization = Organization.objects.create(name="University of Chicago Laboratory Schools")
        cls.sport = Sport.objects.create(name="Robotics")
        cls.event = Event.objects.create(name="Sumo", sport=cls.sport)
        cls.non_judge = User.objects.create(username="norm")
        cls.admin = User.objects.create(username="albert")
        cls.admin.set_password("adminPass")
        cls.admin.is_superuser = True
        cls.admin.is_staff = True
        cls.admin.save()
        cls.open_old_competition = Competition.objects.create(name='open_old_competition', status=Status.OPEN, start_date=cls.yesterday, end_date=cls.yesterday)
        cls.open_current_competition = Competition.objects.create(name='open_current_competition', status=Status.OPEN, start_date=cls.yesterday, end_date=cls.tomorrow)
        cls.open_future_competition = Competition.objects.create(name='open_future_competition', status=Status.OPEN, start_date=cls.tomorrow, end_date=cls.tomorrow)
        cls.open_tournament = SingleEliminationTournament.objects.create(status=Status.OPEN, event=cls.event, competition=cls.open_current_competition)
        cls.closed_tournament = SingleEliminationTournament.objects.create(status=Status.CLOSED, event=cls.event, competition=cls.open_current_competition)
        cls.tournament_judge = User.objects.create(username="terry")
        cls.tournament_judge.set_password("tournamentPass")
        cls.tournament_judge.save()
        cls.open_tournament.judges.add(cls.tournament_judge)
        cls.competition_judge = User.objects.create(username="carl")
        cls.competition_judge.set_password("competitionPass")
        cls.competition_judge.save()
        cls.open_old_competition.plenary_judges.add(cls.competition_judge)
        cls.open_current_competition.plenary_judges.add(cls.competition_judge)
        cls.open_future_competition.plenary_judges.add(cls.competition_judge)
        cls.team_no_competition = Team.objects.create(name="Ninjas")
        cls.team_in_competition_but_no_tournament = Team.objects.create(name="Cobras")
        cls.team_in_competition_and_tournament_but_no_match = Team.objects.create(name="Tridents")
        cls.team1_in_competition_and_tournament_and_match = Team.objects.create(name="Maroons1")
        cls.team2_in_competition_and_tournament_and_match = Team.objects.create(name="Maroons2")
        cls.team3_in_competition_and_tournament_and_match = Team.objects.create(name="Maroons3")
        cls.team4_in_competition_and_tournament_and_match = Team.objects.create(name="Maroons4")
        cls.open_current_competition.teams.add(cls.team_in_competition_but_no_tournament)
        cls.open_current_competition.teams.add(cls.team_in_competition_and_tournament_but_no_match)
        cls.open_current_competition.teams.add(cls.team1_in_competition_and_tournament_and_match)
        cls.open_current_competition.teams.add(cls.team2_in_competition_and_tournament_and_match)
        cls.open_tournament.teams.add(cls.team_in_competition_and_tournament_but_no_match)
        cls.open_tournament.teams.add(cls.team1_in_competition_and_tournament_and_match)
        cls.open_tournament.teams.add(cls.team2_in_competition_and_tournament_and_match)
        # Need at least one Ranking for the sanity tests
        cls.match1_undetermined_rank1 = Ranking.objects.create(tournament=cls.open_tournament, team=cls.team1_in_competition_and_tournament_and_match, rank=1)
        cls.match1_undetermined_rank2 = Ranking.objects.create(tournament=cls.open_tournament, team=cls.team2_in_competition_and_tournament_and_match, rank=2)
        # matches with 2 starting teams
        cls.match1_undetermined = Match.objects.create(tournament=cls.open_tournament)
        cls.match1_undetermined.starting_teams.add(cls.team1_in_competition_and_tournament_and_match)
        cls.match1_undetermined.starting_teams.add(cls.team2_in_competition_and_tournament_and_match)
        cls.match2_undetermined = Match.objects.create(tournament=cls.open_tournament)
        cls.match2_undetermined.starting_teams.add(cls.team3_in_competition_and_tournament_and_match)
        cls.match2_undetermined.starting_teams.add(cls.team4_in_competition_and_tournament_and_match)
        # match with 2 previous undetermined matches
        cls.match_2previous_undetermined = Match.objects.create(tournament=cls.open_tournament)
        cls.match_2previous_undetermined.prev_matches.add(cls.match1_undetermined)
        cls.match_2previous_undetermined.prev_matches.add(cls.match2_undetermined)
        # matches that have already been judged
        cls.match1_determined = Match.objects.create(tournament=cls.open_tournament)
        cls.match1_determined.starting_teams.add(cls.team1_in_competition_and_tournament_and_match)
        cls.match1_determined.starting_teams.add(cls.team2_in_competition_and_tournament_and_match)
        cls.match1_determined.advancers.add(cls.team2_in_competition_and_tournament_and_match)        
        cls.match2_determined = Match.objects.create(tournament=cls.open_tournament)
        cls.match2_determined.starting_teams.add(cls.team3_in_competition_and_tournament_and_match)
        cls.match2_determined.starting_teams.add(cls.team4_in_competition_and_tournament_and_match)
        cls.match2_determined.advancers.add(cls.team3_in_competition_and_tournament_and_match)
        # match with 2 previous determined matches
        cls.match_undetermined_but_prev_determined = Match.objects.create(tournament=cls.open_tournament)
        cls.match_undetermined_but_prev_determined.prev_matches.add(cls.match1_determined)
        cls.match_undetermined_but_prev_determined.prev_matches.add(cls.match2_determined)
        # match with 1 starting team and 1 previous determined match 
        cls.match_undetermined_with_prevd_and_start = Match.objects.create(tournament=cls.open_tournament)
        cls.match_undetermined_with_prevd_and_start.starting_teams.add(cls.team1_in_competition_and_tournament_and_match)
        cls.match_undetermined_with_prevd_and_start.prev_matches.add(cls.match2_determined)
        # match with 1 starting team and 1 previous undetermined match
        cls.match_undetermined_with_prevu_and_start = Match.objects.create(tournament=cls.open_tournament)
        cls.match_undetermined_with_prevu_and_start.starting_teams.add(cls.team2_in_competition_and_tournament_and_match)
        cls.match_undetermined_with_prevu_and_start.prev_matches.add(cls.match2_undetermined)
        # match with 1 previous determined match and 1 previous undetermined match
        cls.match_with_prevd_and_prevu = Match.objects.create(tournament=cls.open_tournament)
        cls.match_with_prevd_and_prevu.prev_matches.add(cls.match1_undetermined)
        cls.match_with_prevd_and_prevu.prev_matches.add(cls.match2_determined)

    def setUp(self):
        self.admin_client = Client()
        success = self.admin_client.login(username="albert", password="adminPass")
        self.assertTrue(success, "Failed to login admin")
        self.competition_judge_client = Client()
        success = self.competition_judge_client.login(username="carl", password="competitionPass")
        self.assertTrue(success, "Failed to login competition judge")
        self.tournament_judge_client = Client()
        success = self.tournament_judge_client.login(username="terry", password="tournamentPass")
        self.assertTrue(success, "Failed to login tournament judge")
 
    def test_advance_options_are_all_competitors(self):
        pass

    def test_advance_options_are_only_competitors(self):
        pass

    def test_single_can_advance(self):
        pass

    def test_multiple_can_advance(self):
        pass

    def test_prereqs_satisfied_before_judge_allowed(self):
        url = reverse("competitions:judge_match", args=[self.__class__.match_2previous_undetermined.id])

        response = self.admin_client.post(url, {"advancers": self.__class__.team1_in_competition_and_tournament_and_match.id})
        self.assertNotIn(response.status_code, range(300,400), "Shouldn't have been able to advance a team from a previously undetermined match")
        response = self.admin_client.post(url, {"advancers": self.__class__.team2_in_competition_and_tournament_and_match.id})
        self.assertNotIn(response.status_code, range(300,400), "Shouldn't have been able to advance a team from a previously undetermined match")
        response = self.admin_client.post(url, {"advancers": self.__class__.team3_in_competition_and_tournament_and_match.id})
        self.assertNotIn(response.status_code, range(300,400), "Shouldn't have been able to advance a team from a previously undetermined match")
        response = self.admin_client.post(url, {"advancers": self.__class__.team4_in_competition_and_tournament_and_match.id})
        self.assertNotIn(response.status_code, range(300,400), "Shouldn't have been able to advance a team from a previously undetermined match")

        url = reverse("competitions:judge_match", args=[self.__class__.match_undetermined_with_prevu_and_start.id])
        response = self.admin_client.post(url, {"advancers": self.__class__.team2_in_competition_and_tournament_and_match.id})
        self.assertNotIn(response.status_code, range(300,400), "Shouldn't have been able to advance a team when their competitor is an undetermined match")
        response = self.admin_client.post(url, {"advancers": self.__class__.team3_in_competition_and_tournament_and_match.id})
        self.assertNotIn(response.status_code, range(300,400), "Shouldn't have been able to advance a team from a previously undetermined match")
        response = self.admin_client.post(url, {"advancers": self.__class__.team4_in_competition_and_tournament_and_match.id})
        self.assertNotIn(response.status_code, range(300,400), "Shouldn't have been able to advance a team from a previously undetermined match")

        url = reverse("competitions:judge_match", args=[self.__class__.match_with_prevd_and_prevu.id])
        response = self.admin_client.post(url, {"advancers": self.__class__.team3_in_competition_and_tournament_and_match.id})
        self.assertNotIn(response.status_code, range(300,400), "Shouldn't have been able to advance a team when their competitor is an undetermined match")
        response = self.admin_client.post(url, {"advancers": self.__class__.team1_in_competition_and_tournament_and_match.id})
        self.assertNotIn(response.status_code, range(300,400), "Shouldn't have been able to advance a team from a previously undetermined match")
        response = self.admin_client.post(url, {"advancers": self.__class__.team2_in_competition_and_tournament_and_match.id})
        self.assertNotIn(response.status_code, range(300,400), "Shouldn't have been able to advance a team from a previously undetermined match")

    def test_only_competitors_can_advance(self):
        url = reverse("competitions:judge_match", args=[self.__class__.match1_undetermined.id])
        response = self.admin_client.post(url, {"advancers": self.__class__.team_no_competition.id})
        self.assertNotIn(response.status_code, range(300,400), "Shouldn't have been able to advance a team that wasn't even in the competition")
        response = self.admin_client.post(url, {"advancers": self.__class__.team_in_competition_but_no_tournament.id})
        self.assertNotIn(response.status_code, range(300,400), "Shouldn't have been able to advance a team that wasn't even in the tournament")
        response = self.admin_client.post(url, {"advancers": self.__class__.team_in_competition_and_tournament_but_no_match.id})
        self.assertNotIn(response.status_code, range(300,400), "Shouldn't have been able to advance a team that wasn't even competing in the match")
        response = self.admin_client.post(url, {"advancers": self.__class__.team1_in_competition_and_tournament_and_match.id})
        self.assertIn(response.status_code, range(300,400), "Should been able to advance the first team in the match")
        response = self.admin_client.post(url, {"advancers": self.__class__.team2_in_competition_and_tournament_and_match.id})
        self.assertIn(response.status_code, range(300,400), "Should been able to advance the second team in the match")


class AutogenTests(TestCase):
    ''' Assumes the judge is valid; Check the content of the judging page '''
    @classmethod
    def setUpTestData(cls):
        cls.today = date.today()
        cls.yesterday = cls.today - timedelta(days=1)
        cls.tomorrow = cls.today + timedelta(days=1)
        cls.organization = Organization.objects.create(name="University of Chicago Laboratory Schools")
        cls.sport = Sport.objects.create(name="Robotics")
        cls.event = Event.objects.create(name="Sumo", sport=cls.sport)
        cls.admin = User.objects.create(username="albert")
        cls.admin.set_password("adminPass")
        cls.admin.is_superuser = True
        cls.admin.is_staff = True
        cls.admin.save()
        cls.competition_being_setup = Competition.objects.create(name='competition_being_setup', status=Status.SETUP, start_date=cls.tomorrow, end_date=cls.tomorrow)
        cls.tournament4 = SingleEliminationTournament.objects.create(status=Status.SETUP, event=cls.event, competition=cls.competition_being_setup)
        cls.tournament5 = SingleEliminationTournament.objects.create(status=Status.SETUP, event=cls.event, competition=cls.competition_being_setup)
        cls.tournament6 = SingleEliminationTournament.objects.create(status=Status.SETUP, event=cls.event, competition=cls.competition_being_setup)
        cls.tournament7 = SingleEliminationTournament.objects.create(status=Status.SETUP, event=cls.event, competition=cls.competition_being_setup)
        cls.tournament8 = SingleEliminationTournament.objects.create(status=Status.SETUP, event=cls.event, competition=cls.competition_being_setup)
        cls.team1 = Team.objects.create(name="Maroons1")
        cls.team2 = Team.objects.create(name="Maroons2")
        cls.team3 = Team.objects.create(name="Maroons3")
        cls.team4 = Team.objects.create(name="Maroons4")
        cls.team5 = Team.objects.create(name="Maroons5")
        cls.team6 = Team.objects.create(name="Maroons6")
        cls.team7 = Team.objects.create(name="Maroons7")
        cls.team8 = Team.objects.create(name="Maroons8")
        cls.tournament4.teams.add(cls.team1)
        cls.tournament4.teams.add(cls.team2)
        cls.tournament4.teams.add(cls.team3)
        cls.tournament4.teams.add(cls.team4)
        cls.tournament5.teams.add(cls.team1)
        cls.tournament5.teams.add(cls.team2)
        cls.tournament5.teams.add(cls.team3)
        cls.tournament5.teams.add(cls.team4)
        cls.tournament5.teams.add(cls.team5)
        cls.tournament6.teams.add(cls.team1)
        cls.tournament6.teams.add(cls.team2)
        cls.tournament6.teams.add(cls.team3)
        cls.tournament6.teams.add(cls.team4)
        cls.tournament6.teams.add(cls.team5)
        cls.tournament6.teams.add(cls.team6)
        cls.tournament7.teams.add(cls.team1)
        cls.tournament7.teams.add(cls.team2)
        cls.tournament7.teams.add(cls.team3)
        cls.tournament7.teams.add(cls.team4)
        cls.tournament7.teams.add(cls.team5)
        cls.tournament7.teams.add(cls.team6)
        cls.tournament7.teams.add(cls.team7)
        cls.tournament8.teams.add(cls.team1)
        cls.tournament8.teams.add(cls.team2)
        cls.tournament8.teams.add(cls.team3)
        cls.tournament8.teams.add(cls.team4)
        cls.tournament8.teams.add(cls.team5)
        cls.tournament8.teams.add(cls.team6)
        cls.tournament8.teams.add(cls.team7)
        cls.tournament8.teams.add(cls.team8)
        cls.team1_tournament4_rank = Ranking.objects.create(tournament=cls.tournament4, team=cls.team1, rank=1)
        cls.team1_tournament5_rank = Ranking.objects.create(tournament=cls.tournament5, team=cls.team1, rank=1)
        cls.team1_tournament6_rank = Ranking.objects.create(tournament=cls.tournament6, team=cls.team1, rank=1)
        cls.team1_tournament7_rank = Ranking.objects.create(tournament=cls.tournament7, team=cls.team1, rank=1)
        cls.team1_tournament8_rank = Ranking.objects.create(tournament=cls.tournament8, team=cls.team1, rank=1)
        cls.team2_tournament4_rank = Ranking.objects.create(tournament=cls.tournament4, team=cls.team2, rank=2)
        cls.team2_tournament5_rank = Ranking.objects.create(tournament=cls.tournament5, team=cls.team2, rank=2)
        cls.team2_tournament6_rank = Ranking.objects.create(tournament=cls.tournament6, team=cls.team2, rank=2)
        cls.team2_tournament7_rank = Ranking.objects.create(tournament=cls.tournament7, team=cls.team2, rank=2)
        cls.team2_tournament8_rank = Ranking.objects.create(tournament=cls.tournament8, team=cls.team2, rank=2)
        cls.team3_tournament4_rank = Ranking.objects.create(tournament=cls.tournament4, team=cls.team3, rank=3)
        cls.team3_tournament5_rank = Ranking.objects.create(tournament=cls.tournament5, team=cls.team3, rank=3)
        cls.team3_tournament6_rank = Ranking.objects.create(tournament=cls.tournament6, team=cls.team3, rank=3)
        cls.team3_tournament7_rank = Ranking.objects.create(tournament=cls.tournament7, team=cls.team3, rank=3)
        cls.team3_tournament8_rank = Ranking.objects.create(tournament=cls.tournament8, team=cls.team3, rank=3)
        cls.team4_tournament4_rank = Ranking.objects.create(tournament=cls.tournament4, team=cls.team4, rank=4)
        cls.team4_tournament5_rank = Ranking.objects.create(tournament=cls.tournament5, team=cls.team4, rank=4)
        cls.team4_tournament6_rank = Ranking.objects.create(tournament=cls.tournament6, team=cls.team4, rank=4)
        cls.team4_tournament7_rank = Ranking.objects.create(tournament=cls.tournament7, team=cls.team4, rank=4)
        cls.team4_tournament8_rank = Ranking.objects.create(tournament=cls.tournament8, team=cls.team4, rank=4)
        cls.team5_tournament5_rank = Ranking.objects.create(tournament=cls.tournament5, team=cls.team5, rank=5)
        cls.team5_tournament6_rank = Ranking.objects.create(tournament=cls.tournament6, team=cls.team5, rank=5)
        cls.team5_tournament7_rank = Ranking.objects.create(tournament=cls.tournament7, team=cls.team5, rank=5)
        cls.team5_tournament8_rank = Ranking.objects.create(tournament=cls.tournament8, team=cls.team5, rank=5)
        cls.team6_tournament6_rank = Ranking.objects.create(tournament=cls.tournament6, team=cls.team6, rank=6)
        cls.team6_tournament7_rank = Ranking.objects.create(tournament=cls.tournament7, team=cls.team6, rank=6)
        cls.team6_tournament8_rank = Ranking.objects.create(tournament=cls.tournament8, team=cls.team6, rank=6)
        cls.team7_tournament7_rank = Ranking.objects.create(tournament=cls.tournament7, team=cls.team7, rank=7)
        cls.team7_tournament8_rank = Ranking.objects.create(tournament=cls.tournament8, team=cls.team7, rank=7)
        cls.team8_tournament8_rank = Ranking.objects.create(tournament=cls.tournament8, team=cls.team8, rank=8)


    def setUp(self):
        self.admin_client = Client()
        success = self.admin_client.login(username="albert", password="adminPass")
        self.assertTrue(success, "Failed to login admin")
 
    def test_autogen_4teams(self):
        pass
        # should work: generate_single_elimination_matches(None, self.__class__.tournament4.id)
        # checks to make sure the appropriate matches have been generated and no more
        # self.assertTrue(Match.objects.filter(tournament=self.__class__.tournament4).count() == 3)
        # team1_matches = Match.objects.filter(tournament=self.__class__.tournament4, starting_teams__contains=self.__class__.team1)
        # self.assertTrue(team1_matches.count() == 1)
        # team1_match = team1_matches.first()
        # self.assertTrue(self.__class__.team4 in team1_match.starting_teams.all())
        # team2_matches = Match.objects.filter(tournament=self.__class__.tournament4, starting_teams__contains=self.__class__.team2)
        # self.assertTrue(team2_matches.count() == 1)
        # team2_match = team2_matches.first()
        # self.assertTrue(self.__class__.team3 in team2_match.starting_teams.all())
        # self.assertTrue(Match.objects.filter(tournament=self.__class__.tournament4, starting_teams__contains=self.__class__.team4).count() == 1)
        # self.assertTrue(Match.objects.filter(tournament=self.__class__.tournament4, starting_teams__contains=self.__class__.team3).count() == 1)

    def test_autogen_5teams(self):
        pass

    def test_autogen_6teams(self):
        pass

    def test_autogen_7teams(self):
        pass

    def test_autogen_8teams(self):
        pass
