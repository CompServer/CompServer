from django.contrib import admin
#from .models import __all__
from .models import Organization, Team, Competition, Event, Ranking, SingleEliminationTournament, Match
# for cls in __all__:
#     try:
#         if not cls.Meta.abstract:
#             admin.site.register(cls)
#     except:
#         print(f"Error registering Class {cls}")

admin.site.register(Organization)
admin.site.register(Team)
admin.site.register(Competition)
admin.site.register(Event)
admin.site.register(Ranking)
admin.site.register(SingleEliminationTournament)
# admin.site.register(DoubleEliminationTournament)
# admin.site.register(MultilevelTournament)
# admin.site.register(RoundRobinTournament)
admin.site.register(Match)
