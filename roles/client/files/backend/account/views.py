# Copyright IBM Corp, 2016
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied. See the License for the specific language governing
# permissions and limitations under the License.

"""Account views."""

from django.contrib.auth.decorators import login_required
from django.contrib import auth
from django.core import urlresolvers
from django.shortcuts import render, redirect
from django.views.decorators.csrf import ensure_csrf_cookie
import ldap.modlist as modlist
import ldap

from client import settings, secret
import forms
import utils


@login_required
def profile(request):
    """Respond the request to a user profile.

    The user profile is composed of user's attributes (username, first name,
    last name and e-mail) and his projects. The profile also allow the user to
    edit his attributes, change the password, sign out and go to all projects
    page.

    Args:
        request (HttpRequest): The user request.

    Returns:
        HttpResponse: The rendered user profile.
    """
    context = {
        'projects': request.user.project_set.all(),
    }
    return render(request, 'account/profile.html', context)


def signup(request):
    """Register a new user.

    This view has multiple behaviours based on the request composition. When
    some user is already signed in, the response ask the user to first sign
    out. When the request has no data about the new user, then the response
    carries the registration form. When the request has valid data about the
    new user, the response informs him the registration success.

    Args:
        request (HttpRequest): the user request.

    Returns:
        HttpResponse: The response accordingly to the request composition.
    """
    keys = request.POST.keys()
    if request.user.is_authenticated():
        return render(request, 'account/signup_already_signedin.html', None)
    elif len(keys) == 0:
        return render(request, 'account/signup.html', None)
    else:
        username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        # confirm_password = request.POST.get('confirm_password')

        # TODO: Check password and confirmation.

        ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_DEMAND)
        ldap.set_option(ldap.OPT_X_TLS_CACERTFILE, settings.LDAP_CACERTFILE)
        l = ldap.initialize(secret.LDAP_URI)
        l.protocol_version = ldap.VERSION3
        l.start_tls_s()
        l.simple_bind_s(secret.LDAP_BIND_DN, secret.LDAP_BIND_PASSWORD)

        dn = settings.LDAP_USER_DN_TEMPLATE % str(username)
        user = {
            'cn': str(first_name),
            'sn': str(last_name),
            'mail': str(email),
            'userPassword': str(utils.hashPassword(password)),
            'objectClass': ['person', 'organizationalPerson', 'inetOrgPerson']
        }

        ldif = modlist.addModlist(user)
        l.add_s(dn, ldif)
        l.unbind_s()
        context = {'username': username}
        return render(request, 'account/signup_successful.html', context)


def login(request):
    """Redirect to sign in url."""
    return redirect(urlresolvers.reverse('account:signin'))


@ensure_csrf_cookie
def signin(request):
    """Authenticates a user sign in.

    This view has multiple behaviours based on the request composition. When
    the user is already signed in the response asks him to first sign out. If
    the request has no login data then this views renders and returns the sign
    in form. If the request has valid login data the user is authenticated in
    the system and properly notified about the success.

    Args:
        request (HttpRequest): The user request.

    Returns:
        HttpResponse: The response accordingly to the request composition.
    """
    if request.user.is_authenticated():
        return render(request, 'account/signin_already_signedin.html', None)
    elif len(request.POST.keys()) > 0:
        signin_form = forms.SignInForm(request.POST)
        if not signin_form.is_valid():
            return render(request,
                          'account/signin.html',
                          {'signin_form': signin_form})

        try:
            user = auth.authenticate(**signin_form.cleaned_data)
        except:
            user = None

        if user is not None:
            user.is_staff = utils.isUserStaff(user.username)
            user.save()
            auth.login(request, user)
        else:
            context = {'error': 'Incorrect username or password',
                       'signin_form': signin_form}
            return render(request, 'account/signin.html', context)

        next = request.GET.get('next', None)
        if next is not None:
            return redirect(next)
        else:
            return redirect(urlresolvers.reverse('account:profile'))
    else:
        return render(request,
                      'account/signin.html',
                      {'signin_form': forms.SignInForm()})


@login_required
def logout(request):
    """Redirect to sign out url."""
    return redirect(urlresolvers.reverse('account:signout'))


@login_required
def signout(request):
    """Logout the active user and redirect to home page."""
    auth.logout(request)
    return redirect(urlresolvers.reverse('home'))
