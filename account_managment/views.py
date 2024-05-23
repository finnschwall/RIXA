import json
import os

from django.contrib.auth.decorators import login_required
from django.db.models import Avg, F
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseForbidden, HttpResponseServerError
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.contrib.auth import logout
from django.urls import reverse

from account_managment.models import RixaUser
from dashboard.models import PluginScope
from .models import User, Invitation
from django.conf import settings
from django.utils import translation
import pandas as pd
import plotly.graph_objects as go

@login_required
def user_statistics_view(request):
    import plotly.express as px
    try:
        df = pd.read_csv(settings.WORKING_DIRECTORY + "/statistics/user_info.csv", sep=";")
        df_statistics = pd.read_csv(settings.WORKING_DIRECTORY + "/statistics/user_statistics.csv", sep=";")
        df_sessions = pd.read_csv(settings.WORKING_DIRECTORY + "/statistics/session_statistics.csv", sep=";")
    except FileNotFoundError:
        return HttpResponse("No data available")
    # df statistics: statistics_names = [f"users_per_{timedelta}", f"total_time_per_{timedelta}"]
    cols = df_statistics.columns
    avg_data = RixaUser.objects.aggregate(
        avg_messages=Avg('total_messages'),
        avg_time_spent=Avg('total_time_spent'),
        avg_sessions=Avg('total_sessions')
    )
    # Cumulative time spent: {df['visit_time'].sum()} minutes < br >
    data = RixaUser.objects.annotate(messages_json=F('messages_per_session')).values_list('messages_json', flat=True)
    all_messages = []
    for item in data:
        if item:
            all_messages += json.loads(item)


    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_sessions['time'], y=df_sessions['user_count'], mode='markers', name='Real Users'))
    fig.add_trace(
        go.Scatter(x=df_sessions['time'], y=df_sessions['total_msg_count'], mode='markers', name='Total Messages'))
    fig.add_trace(
        go.Scatter(x=df_sessions['time'], y=df_sessions['total_time_spent'], mode='markers', name='Total time spent'))
    fig.update_layout(
        title='User and Message Count Over Time',
        xaxis_title='Time',
        yaxis_title='Count',
        legend_title='Legend'
    )
    fig.update_layout(title_text='Session Metrics Comparison', xaxis_title='Time')


    fig2 = go.Figure()
    # Add the first trace for user count
    fig2.add_trace(go.Scatter(x=df_sessions['time'], y=df_sessions['user_count'], mode='markers', name='Real Users'))
    fig2.add_trace(
        go.Scatter(x=df_sessions['time'], y=df_sessions['avg_msg_count'], mode='markers', name='Avg. Total Messages'))
    fig2.add_trace(
        go.Scatter(x=df_sessions['time'], y=df_sessions['avg_time_spent'], mode='markers', name='Avg. Total time spent'))
    fig2.update_layout(
        title='Average User and Message Count Over Time',
        xaxis_title='Time',
        yaxis_title='Avg. Count',
        legend_title='Legend'
    )
    fig2.update_layout(title_text='Average Session Metrics Comparison', xaxis_title='Time')

    html_content = f"""<script src="https://rixa.ai/static/js/plotly-2.20.0.min.js"></script>
    <h1>User statistics</h1>
    Total visits {len(df['visit_time'])}<br>
    Total average messages per user: {avg_data['avg_messages']:.2f}<br>
    Total average time spent per user: {avg_data['avg_time_spent']:.2f} minutes<br>
    Total average sessions per user: {avg_data['avg_sessions']:.2f}<br><br>
    {fig2.to_html(include_plotlyjs=False, default_height='50%')}
    {fig.to_html(include_plotlyjs=False, default_height='50%')}
    RIXA CPU core utilization:<br>
    {px.scatter(df_sessions, y='core_utilization', x='time').to_html(include_plotlyjs=False, default_height='50%')}<br>
    Session times distribution:<br>
    {px.histogram(all_messages, nbins=20).to_html(include_plotlyjs=False, default_height='50%')}<br>
    
    Unique server connections per time:<br>
    {px.scatter(df_statistics, y=cols[0], x=cols[2]).to_html(include_plotlyjs=False, default_height='50%')}<br>
    <br>Last 20 connection entries:<br><br>
    {df.drop(['is_user', 'touch_capable'],axis=1).head(20).to_html()}"""
    return HttpResponse(html_content)

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
    if request.method == 'POST':
        if "delete_account" in request.POST:
            request.user.delete()
            return HttpResponse("Account deleted. Other fun activity on the internet includes e.g. <a href='https://random.cat'>random cats</a>.")
        if "deactivate_account" in request.POST:
            request.user.is_active = False
            request.user.save()
            return HttpResponse("Account deactivated. Deletion will happen in 1-2 weeks.")
        download_id = request.POST["download_id"]
        scope_write_user = list(request.user.rixauser.scope_write.values_list('name', flat=True))
        if len(scope_write_user) != 0:
            scope_write_user += ["server public key"]
        if download_id not in scope_write_user:
            return HttpResponse("You are not allowed to download this key!", status=403)
        if download_id == "server public key":
            filename = "server.key"
            path = os.path.join(settings.AUTH_KEY_LOC, "server.key")
        else:
            filename = "client.key_secret"
            path = os.path.join(settings.AUTH_KEY_LOC, download_id+".key_secret")
        with open(path, "r") as file:
            file_content = file.read()
        if file_content is None:
            return HttpResponseServerError("Could not read file. Please contact the administrator.")
        else:
            response = HttpResponse(file_content, content_type="application/x-rixaplugin-encryption-key")
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
    user_dic = dict(request.user._wrapped.__dict__)
    rixa_user_dic = dict(request.user.rixauser.__dict__)
    for i in ["_state", "password", "id", "first_name", "last_name", "user_id", "messages_per_session"]:
        rixa_user_dic.pop(i, None)
        user_dic.pop(i, None)
    scope_names = list(request.user.rixauser.scope_write.values_list('name', flat=True))
    if len(scope_names) !=0:
        scope_names.append("server public key")

    rixa_user_dic["available scopes (write)"] = scope_names
    context = {"user_info": user_dic | rixa_user_dic, "downloadable_keys": scope_names}
    return render(request, 'home_account.html', context)



def register_user(request):
    if request.user.is_authenticated:
        messages.info(request, "You are already logged in.")
        return HttpResponseRedirect(reverse("account_main"))

    if request.method == 'POST':

        code = request.POST["registration_id"]
        try:
            invitation = Invitation.objects.get(code=code)
        except Invitation.DoesNotExist:
            return HttpResponse("Invalid invitation code!", status=400)

        if not invitation.is_available:
            return HttpResponse("This invitation link has been exhausted.", status=400)


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

        user = User.objects.create_user(username, password=password)

        if user is not None:

            if user.is_active:
                # if invitation.tags.exists():
                #     print(dir(user))
                #     user.rixauser.tags.add(*invitation.tags.all())
                user.save()
                rixa_user = RixaUser(user=user)
                rixa_user.save()
                if invitation.tags.exists():
                    rixa_user.allowed_tags.add(*invitation.tags.all())
                    rixa_user.save()
                invitation.uses += 1
                invitation.save()
                login(request, user)
                return HttpResponseRedirect(reverse("account_main"))
            else:
                user.save()
                invitation.uses += 1
                invitation.save()
                messages.warning(request, "Thanks for registering!\nYour account should get activated within a day.")
                return HttpResponseRedirect(reverse("game_home"))
        else:
            messages.error(request, "Something went wrong...")
            return render(request, 'register.html', {'form': UserCreationForm})
    else:
        if not request.is_secure():
            messages.warning(request, "Do not use a password you use on another site under any circumstances! "
                                      "The server can not verify the security of the connection.")
        return render(request, 'register.html', {'form': UserCreationForm})


# def register_user(request):
#     if request.method == 'POST':
#         if request.POST['password1'] != request.POST['password2']:
#             messages.error(request, "Passwords don't match")
#             return render(request, 'register.html', {'form': UserCreationForm})
#
#         username = request.POST['username']
#         user_exists = True
#         try:
#             User.objects.get_by_natural_key(username)
#         except:
#             user_exists = False
#         if user_exists:
#             messages.error(request, "Username already exists")
#             return render(request, 'register.html', {'form': UserCreationForm})
#         password = request.POST['password1']
#         additional_info = request.POST["additional_info"]
#         user = User.objects.create_user(username, password=password)
#         user.is_active = False
#         if user is not None:
#             if user.is_active:
#                 login(request, user)
#                 return HttpResponseRedirect(reverse("account_main"))
#             else:
#                 messages.warning(request, "Thanks for registering!\nYour account should get activated within a day.")
#                 return HttpResponseRedirect(reverse("game_home"))
#         else:
#             messages.error(request, "Something went wrong...")
#             return render(request, 'register.html', {'form': UserCreationForm})
#     else:
#         if not request.is_secure():
#             messages.warning(request, "Do not use a password you use on another site under any circumstances! "
#                                       "The server can not verify the security of the connection. (This error probably"
#                                       " won't get resolved in the near future)")
#         return render(request, 'register.html', {'form': UserCreationForm})


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
