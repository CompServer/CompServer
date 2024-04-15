from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from competitions.models import Sport, Team

# Create your views here.

def teams(request: HttpRequest):
    sport = request.GET.get('sport')
    html = ''

    sport = get_object_or_404(Sport, pk=sport)

    for team in Team.objects.filter(sport=sport):
        html += f'<option value="{team.id}">{team.name}</option>\n'
    
    return HttpResponse(content=html)
