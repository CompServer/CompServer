from django.shortcuts import render

def team_page(team_id):
    context = {
        team: Team.objects.all().filter(Team.id == team_id), #get a team from the team id passed into the view
    }
    return render("competitions/team-page.html")
