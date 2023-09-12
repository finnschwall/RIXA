from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseForbidden, HttpResponseServerError
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.contrib.auth import logout
from django.urls import reverse
from .models import User
from django.conf import settings
from django.utils import translation


def maintenance_mode(request):
    return render(request, 'maintenance.html', {})


def logout_user(request):
    logout(request)
    return HttpResponseRedirect("/")


@login_required
def account_managment(request):
    if request.user.is_anonymous:
        messages.info(request, "Login required before changing account settings.")
        return redirect(user_login)
    user_dic = dict(request.user._wrapped.__dict__)
    for i in ["_state", "password", "id"]:
        user_dic.pop(i)
    context = {"user_info": user_dic}
    return render(request, 'home_account.html', context)


def register_user(request):
    return HttpResponseServerError("This is currently disabled.")
    if request.method == 'POST':
        if request.POST['password1'] != request.POST['password2']:
            messages.error(request, "Passwords don't match")
            return render(request, 'register.html', {'form': UserCreationForm})

        username = request.POST['username']
        user_exists = True
        try:
            User.objects.get_by_natural_key(username)
        except:
            user_exists = False
        if user_exists:
            messages.error(request, "Username already exists")
            return render(request, 'register.html', {'form': UserCreationForm})
        password = request.POST['password1']
        additional_info = request.POST["additional_info"]
        user = User.objects.create_user(username, password=password)
        user.is_active = False
        if user is not None:
            if user.is_active:
                login(request, user)
                return HttpResponseRedirect(reverse("account_main"))
            else:
                messages.warning(request, "Thanks for registering!\nYour account should get activated within a day.")
                return HttpResponseRedirect(reverse("game_home"))
        else:
            messages.error(request, "Something went wrong...")
            return render(request, 'register.html', {'form': UserCreationForm})
    else:
        if not request.is_secure():
            messages.warning(request, "Do not use a password you use on another site under any circumstances! "
                                      "The server can not verify the security of the connection. (This error probably"
                                      " won't get resolved in the near future)")
        return render(request, 'register.html', {'form': UserCreationForm})


def user_login(request):
    if request.user.is_authenticated:
        messages.info(request, "You are already logged in.")
        return HttpResponseRedirect(reverse("account_main"))
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                if "next" in request.GET:
                    return HttpResponseRedirect(request.GET.get('next'))
                return HttpResponseRedirect(reverse("account_main"))
            else:
                messages.error(request, "Your account is not (yet) activated.")
                return render(request, 'login.html', {'form': AuthenticationForm})
        else:
            messages.error(request, "Invalid username or password")
            return render(request, 'login.html', {'form': AuthenticationForm})
    else:
        return render(request, 'login.html', {'form': AuthenticationForm})


def update_session(request):
    if "js_req" not in request.GET:
        return HttpResponseForbidden("FORBIDDEN")
    response = HttpResponse('ok')
    if "clear_everything" in request.GET:
        for i in request.COOKIES:
            response.delete_cookie(i)
        request.session.flush()
    elif "set_message_level" in request.GET:
        level = int(request.GET["set_message_level"])
        request.session["message_level"] = level
    elif "change_language" in request.GET:
        lang_code = request.GET["change_language"]
        response.set_cookie(settings.LANGUAGE_COOKIE_NAME, lang_code)
        translation.activate(lang_code)
    return response
