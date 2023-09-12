"""RIXAWebserver URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.shortcuts import redirect
from django.urls import re_path, path, include
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.views.generic.base import RedirectView
from account_managment.views import logout_user, user_login, maintenance_mode, update_session

import dashboard.views
from django.contrib import admin

if settings.MAINTENANCE_MODE:
    urlpatterns = i18n_patterns(
        re_path(r'^.*$', maintenance_mode)
    )
else:
    urlpatterns = i18n_patterns(
        path('admin/', admin.site.urls),
        path("dashboard/", include("dashboard.urls")),
        path("account_managment/", include("account_managment.urls")),
        path('login/', lambda request: redirect('/account_managment/user_login/')),
        path('logout/', lambda request: redirect('/account_managment/user_logout/')),
        path('', RedirectView.as_view(url='dashboard/'))
    )
    if 'rosetta' in settings.INSTALLED_APPS:
        urlpatterns += [
            re_path(r'^rosetta/', include('rosetta.urls'))
    ]