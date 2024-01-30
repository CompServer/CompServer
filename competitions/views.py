from django.contrib import messages
from django.shortcuts import render
from django.views.generic.edit import FormView, UpdateView
from .forms import JudgeMatchForm

def not_implemented(request, *args, **kwargs):
    messages.error(request, "This feature is not yet implemented.")
    return render(request, 'skeleton.html')

class JudgeMatchUpdateView(FormView):
    template_name = 'match_judge.html'
    form_class = JudgeMatchForm

