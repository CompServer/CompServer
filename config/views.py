from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
from instanastics.models import Gymnast, Gym
# from .models import Question

from .models import Gymnast
def index(request):
    return HttpResponse("Hello, world. You're at the instanastics index.")

def home (request):
    currentUser = Gymnast.objects.filter(user_id = request.user.id).first()
    gym = Gym.objects.filter(gymnast = currentUser).first()
    context = {"user": currentUser,
               "club": gym} 

    return render(request, "home.html", context)

# we need to have gymnast and recruiter extend user


