from django.urls import path
from django.views.generic.base import RedirectView

from . import views

urlpatterns = [
    path(r'home', views.home, name='home'),
    path(r'home_old', views.home_old, name='home_old'),
    path(r'edit_chat_configuration', views.edit_chat_configuration, name='edit_chat_configuration'),
    path(r'about', views.about, name='about'),
    path(r'test', views.test, name='test'),
    path(r'dashboard', views.dashboard, name='dashboard'),
    path(r'dashboard2', views.dashboard2, name='dashboard2'),
path(r'study_status', views.study_status, name='study_status'),
    path(r"impressum", views.impressum, name="impressum"),
    path('', RedirectView.as_view(url=r'home'))
]