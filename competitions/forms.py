

from django import forms
from django.contrib import messages

from competitions.models import Team, Match


class JudgeForm(forms.ModelForm):
    possible_advancers = None

    def __init__(self, *args, possible_advancers, **kwargs):
        super().__init__(*args, **kwargs)
        if possible_advancers:
            self.fields['advancers'].queryset = possible_advancers
        
        self.possible_advancers = possible_advancers

    def is_valid(self):
        assert isinstance(self.instance, Match)
        #print(self.instance.advancers.all())
        #print(self.possible_advancers)
        for team in self.instance.advancers.all():
            if team not in self.possible_advancers.all():
                return False
        return super().is_valid()

    class Meta:
        model = Match
        fields = ['advancers']
        template_name = 'competitions/match_judge.html'
        success_url = "/"
