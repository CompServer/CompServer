from django.contrib import admin
from .models import __all__

for cls in __all__:
    admin.site.register(cls)

# admin.site.register(Organization)
# admin.site.register(Team)
# admin.site.register(Competition)
# admin.site.register(Event)
# admin.site.register(Ranking)
# admin.site.register(SingleEliminationTournament)
# # admin.site.register(DoubleEliminationTournament)
# # admin.site.register(MultilevelTournament)
# # admin.site.register(RoundRobinTournament)
# admin.site.register(Match)
