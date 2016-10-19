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

"""Project url routing."""

from django.conf.urls import url
from . import views

app_name = 'project'
urlpatterns = [
    url(r'^$', views.list, name='list'),
    url(r'^list$', views.list, name='list_full_url'),
    url(r'^create$', views.selectProjectType, name='select_project_type'),
    url(r'^create/(?P<projType>.+)$', views.create, name='create'),
    url(r'^update$', views.update, name='update'),
    url(r'^(?P<projName>.+)/delete$', views.delete, name='delete'),
    url(r'^(?P<projName>.+)/build$', views.buildProject, name='build'),
    url(r'^(?P<projName>.+)/abort$', views.abortBuild, name='abort'),
]
