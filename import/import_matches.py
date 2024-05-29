import csv
from competitions.models import *

competition = Competition.objects.get(name="RoboMed")
event = Event.objects.get(name="Obstacle Course")
tournament = RoundRobinTournament(event=event, competition=competition, start_time=timezone.now(), matches_per_team=5, teams_per_match=4)
tournament.save()
tournament.teams.add(*list(competition.teams.all()))
tournament.judges.add(*list(competition.plenary_judges.all()))
arena1 = Arena.objects.get(name="Ring 1")
arena2 = Arena.objects.get(name="Ring 2")
arena3 = Arena.objects.get(name="Ring 3")
infile = open("/path/to/sheet.csv")
freader = csv.reader(infile)
print(freader.__next__())  # header row
for row in freader:
    print(row)
    round, time, team1a, team1b, team2a, team2b, team3a, team3b = int(row[0]), timezone.make_aware(datetime.datetime.strptime(row[1]+'/2024 '+row[2],"%m/%d/%Y %H:%M")), Team.objects.get(name=row[3]) if row[3] else None, Team.objects.get(name=row[4]) if row[4] else None, Team.objects.get(name=row[5]) if row[5] else None, Team.objects.get(name=row[6]) if row[6] else None, Team.objects.get(name=row[7]) if row[7] else None, Team.objects.get(name=row[8]) if row[8] else None 
    # Specifically for Speed Race
    # if team1a or team1b or team2a or team2b:
    #     match1 = Match(tournament=tournament, round_num=round, arena=arena1)
    #     match1.save()
    #     if team1a:
    #         match1.starting_teams.add(team1a)
    #     if team1b:
    #         match1.starting_teams.add(team1b)
    #     if team2a:
    #         match1.starting_teams.add(team2a)
    #     if team2b:
    #         match1.starting_teams.add(team2b)
    if team1a and team1b:
        match1 = Match(tournament=tournament, round_num=round, arena=arena1)
        match1.save()
        match1.starting_teams.add(team1a, team1b)
    if team2a and team2b:
        match2 = Match(tournament=tournament, round_num=round, arena=arena2)
        match2.save()
        match2.starting_teams.add(team2a, team2b)
    if team3a and team3b:
        match3 = Match(tournament=tournament, round_num=round, arena=arena3)
        match3.save()
        match3.starting_teams.add(team3a, team3b)

