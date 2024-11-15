from django.urls import path
from django.views.generic.base import RedirectView

from . import views

urlpatterns = [
    path(r'update_session', views.update_session, name='update_session'),
    path('user_logout/', views.logout_user, name='account_user_logout'),
    path('user_login/', views.user_login, name='account_user_login'),
    path('signup/', views.register_user, name='account_signup'),
    path('user_info_dump', views.user_info_dump, name='user_info_dump'),
    path("help", views.help_view, name="help"),
    path(r'main', views.account_managment, name='account_main'),
    path('statistics/', views.statistics_view, name='statistics'),
    path('statistics/plot/', views.get_plot_data, name='statistics_plot'),
    # path(r"statistics", views.user_statistics_view, name=""),
    path('', RedirectView.as_view(url='main'))
]