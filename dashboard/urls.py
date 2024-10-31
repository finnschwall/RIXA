from django.urls import path
from django.views.generic.base import RedirectView

from . import views

urlpatterns = [
    path(r'home', views.home, name='home'),
    path(r'home_new', views.home_new, name='home_new'),
    path(r'edit_chat_configuration', views.edit_chat_configuration, name='edit_chat_configuration'),
    path(r'about', views.about, name='about'),
    path(r'test', views.test, name='test'),
    path('', RedirectView.as_view(url=r'home'))
]