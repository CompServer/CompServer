from typing import Optional
from django import forms
from django.db.models import QuerySet
from .models import Match

class JudgeMatchForm(forms.ModelForm):
    class Meta:
        model = Match
        fields = ['advancers']
