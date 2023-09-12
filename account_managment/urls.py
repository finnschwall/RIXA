from django.urls import path
from django.views.generic.base import RedirectView

from . import views

urlpatterns = [
    path(r'update_session', views.update_session, name='update_session'),
    path('user_logout/', views.logout_user, name='account_user_logout'),
    path('user_login/', views.user_login, name='account_user_login'),
    path('signup/', views.register_user, name='account_signup'),
    path(r'main', views.account_managment, name='account_main'),
    path('', RedirectView.as_view(url='main'))
]