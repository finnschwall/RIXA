from django.urls import path
from django.views.generic.base import RedirectView

from . import views

urlpatterns = [
    path(r'home', views.home, name='home'),
    # path(r'userstudy', views.user_study, name='user_study'),
    path(r'test', views.test, name='test'),
    path('', RedirectView.as_view(url=r'home'))
]