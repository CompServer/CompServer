

from django import forms
from django.contrib import messages

from competitions.models import Team, Match


class JudgeForm(forms.ModelForm):
    def __init__(self, *args, possible_advancers, **kwargs):
        super().__init__(*args, **kwargs)
        if possible_advancers:
            self.fields['advancers'].queryset = possible_advancers

    def is_valid(self):
        assert isinstance(self.instance, Match)
        print(self.instance.advancers.all())
        print(self.fields['advancers'].queryset)
        for team in self.instance.advancers.all():
            if team not in self.fields['advancers'].queryset:
                return False
        return super().is_valid()

    class Meta:
        model = Match
        fields = ['advancers']
        template_name = 'competitions/match_judge.html'
        success_url = "/"
