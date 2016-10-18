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

from copy import deepcopy
from django import template


register = template.Library()


@register.filter
def reject(value, arg):
    assert isinstance(value, list), "value must be a list: %r" % value
    assert isinstance(arg, basestring), "arg must be a string: %r" % arg
    value_copy = deepcopy(value)
    try:
        value_copy.remove(arg)
    except ValueError:
        pass
    return value_copy
