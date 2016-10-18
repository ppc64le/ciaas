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

from __future__ import unicode_literals

from django.db import models
from django import forms
from django.contrib.auth.models import User
import collections
import datetime
import random
import time

from multipleselection.models import MultipleSelectionField
from project import utils
from projectdata.settings import DataManager
import partner.utils


def _vessel(data):
    if isinstance(data, list):
        return []
    elif isinstance(data, dict):
        return {}
    else:
        raise TypeError('Vessels are created just for lists and dicts.')


def _fill(vessel, content):
    if isinstance(content, list):
        vessel.extend(content)
    elif isinstance(content, dict):
        vessel.update(content)
    else:
        raise TypeError('Vessels are filled just with lists and dicts.')


def _convert(data):
    if isinstance(data, basestring):
        return str(data)
    elif isinstance(data, collections.Mapping):
        return dict(map(_convert, data.iteritems()))
    elif isinstance(data, collections.Iterable):
        return type(data)(map(_convert, data))
    else:
        return data


def _compairBuildsTimestamp(x, y):
    if x['timestamp'] == y['timestamp']:
        return 0
    elif x['timestamp'] < y['timestamp']:
        return 1
    else:
        return -1


# Create your models here.
class Project(models.Model):

    NODE_CHOICES = (
        ('any', 'Any'),
        ('ppc64le_debian_jessie', 'ppc64le/debian:jessie'),
        ('ppc64le_ubuntu_16_04',  'ppc64le/ubuntu:16.04'),
    )

    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100,
                            unique=True)
    nodes = MultipleSelectionField(max_length=150, choices=NODE_CHOICES)
    builds = None
    lastBuildRefresh = None

    def lastBuild(self):
        self._refreshBuildInformation()
        try:
            lastStatus = self.builds[0]['result']
        except IndexError:
            lastStatus = None
        return lastStatus

    def builds(self):
        self._refreshBuildInformation()
        return self.builds

    def getData(self):
        dataRepresentation = {
            'job': {
                'name': self.name,
                'concurrent': True,
                'node': str(' || '.join(self.nodes))
            }
        }
        for data in self.data_set.all():
            info = data.getData()
            parent = dataRepresentation
            # Find insertion point.
            for key in data.getPath().split('.'):
                if key not in parent:
                    parent[key] = _vessel(info)
                parent = parent[key]
            # Fill the vessel with data.
            _fill(parent, info)

        # Convert all data to basestring.
        return [_convert(dataRepresentation)]

    def _refreshBuildInformation(self):
        if self.lastBuildRefresh is None or \
                (datetime.datetime.today() -
                 self.lastBuildRefresh).seconds >= 4:
            self.builds = partner.utils.getBuildInformation(self.name)
            self.lastBuildRefresh = datetime.datetime.today()

    def triggerBuild(self):
        gclient = utils.getGearClientConnection()

        if len(self.nodes) == 0 or \
                (len(self.nodes) == 1 and self.nodes[0] == 'any'):
            job = utils.gearJobFactory('build', self.name)
            time.sleep(random.uniform(0.05, 0.2))
            gclient.submitJob(job, True)
        else:
            for node in self.nodes:
                job = utils.gearJobFactory('build', self.name, node)
                time.sleep(random.uniform(0.05, 0.2))
                gclient.submitJob(job, True)

        gclient.shutdown()

    @staticmethod
    def getForms(projType):
        dataManager = DataManager.get()
        forms = [ProjectForm()]
        forms.extend(
            [data.getBlankForm()
             for data in dataManager.dataList[projType].values()]
        )
        return forms


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'nodes']


class Data(models.Model):
    parent = models.ForeignKey(Project, on_delete=models.CASCADE)
    type = models.CharField(max_length=40)

    def getPath(self):
        return getattr(self, self.type).getPath()

    def getData(self):
        return getattr(self, self.type).getData()
