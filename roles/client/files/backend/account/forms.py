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

from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils.translation import ugettext as _

import utils


password_validator = RegexValidator(
    r'^.*(?=.{8,})(?=.*[a-zA-Z])(?=.*\d)(?=.*[^!\$%&/()=?{\[\]}+~#-_.:,;<>|\\]).*$',       # NOQA
    'The password must be at least 8 characters long and consist of letters and numbers.'  # NOQA
)


class SignInForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput())


class SignUpForm(forms.Form):
    username = forms.SlugField()
    first_name = forms.CharField()
    last_name = forms.CharField()
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput(),
                               validators=[password_validator])
    confirm_password = forms.CharField(widget=forms.PasswordInput(),
                                       validators=[password_validator])

    def clean(self):
        super(SignUpForm, self).clean()

        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        confirm_password = self.cleaned_data.get('confirm_password')

        # Check password and its confirmation equality
        if password and confirm_password and password != confirm_password:
            err = ValidationError(
                _('The password and its confirmation does not match.')
            )
            self.add_error('password', err)
            self.add_error('confirm_password', err)

        # Check if username already exists
        if username:
            try:
                utils.getUserInfo(username)
                self.add_error(
                    'username',
                    ValidationError(_('Username already exists'))
                )
            except:
                pass
