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

"""Models for multiple selection package."""

from django import forms
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import capfirst
from django.utils.translation import ugettext_lazy as _
import django

from multipleselection import validators


class MultipleSelectionField(models.CharField):
    """ Stores multiple choices as list.

    The default separator is ',' (comma). Remember that choices must not
    contain the separator inside its value. To change separator use
    MultipleSelectionField(separator=';'). """

    DEFAULT_MAX_LENGTH = 150
    DEFAULT_SEPARATOR = ','

    def __init__(self, *args, **kwargs):
        defaults = {'max_length': self.DEFAULT_MAX_LENGTH}
        defaults.update(kwargs)
        defaults['validators'] = defaults.get('validators', []) \
            .append(validators.listOrStringValidator)
        super(MultipleSelectionField, self).__init__(*args, **kwargs)
        self.separator = kwargs.get('separator', self.DEFAULT_SEPARATOR)

    def from_db_value(self, value, expression, connection, context):
        return self.to_python(value)

    def to_python(self, value):
        if isinstance(value, list):
            return value
        elif isinstance(value, basestring):
            return value.split(self.separator)
        elif value is None:
            return None
        else:
            raise ValidationError(_("Invalid value: %(value)r"),
                                  params={'value': value})

    def get_prep_value(self, value):
        if isinstance(value, list):
            return self.separator.join(value)
        elif isinstance(value, basestring):
            return value
        else:
            raise ValidationError(_("Invalid value: %(value)r"),
                                  params={'value': value})

    def value_to_string(self, obj):
        value = self.value_from_object(obj)
        return self.get_prep_value(value)

    def formfield(self, **kwargs):
        defaults = {'required': not self.blank,
                    'label': capfirst(self.verbose_name),
                    'help_text': self.help_text,
                    'choices': self.choices}
        defaults.update(kwargs)
        return forms.MultipleChoiceField(**defaults)

    def validate(self, value, model_instance):
        choices = [choice[0] for choice in
                   self.get_choices(include_blank=False)]
        for selection in value:
            if (selection not in choices):
                if django.VERSION[0] >= 1 and django.VERSION[1] >= 6:
                    raise ValidationError(
                        self.error_messages['invalid_choice']
                        % {"value": value})
                else:
                    raise ValidationError(
                        self.error_messages['invalid_choice'] % value)
