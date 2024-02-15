from django.contrib import admin
from .models import *

class MatchAdmin(admin.ModelAdmin):
    list_filter = ["tournament"]

class TeamAdmin(admin.ModelAdmin):
    list_filter = ["sport"]

admin.site.register(Sport)
admin.site.register(Organization)
admin.site.register(Team, TeamAdmin)
admin.site.register(Competition)
admin.site.register(Event)
admin.site.register(Ranking)
admin.site.register(SingleEliminationTournament)
# admin.site.register(DoubleEliminationTournament)
# admin.site.register(MultilevelTournament)
# admin.site.register(RoundRobinTournament)
admin.site.register(Match, MatchAdmin)
