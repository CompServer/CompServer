from django.urls import path

from . import views

app_name = "competitions"
urlpatterns = [
    path('notimplemented/', views.not_implemented, name='not_implemented'),
    path('match/<int:pk>/judge/', views.JudgeMatchUpdateView.as_view, name='judge_match'),
]
