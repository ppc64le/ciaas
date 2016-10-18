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

from django.conf import settings
from jenkins_jobs.builder import Builder as JenkinsJobBuilder
from tempfile import TemporaryFile
import datetime
# import random
import threading
# import time
import yaml

import models
import partner


class SyncProjectsThread(threading.Thread):

    def __init__(self, newProjects):
        super(SyncProjectsThread, self).__init__()
        self.jobs = [str(j.name) for j in models.Project.objects.all()]
        self.newProjects = set(newProjects)

    def run(self):
        nodes = partner.utils.getOnlineNodes()

        if settings.REMOVE_DANGLING_PROJECTS:
            for node in nodes:
                jconn = node.connect()
                self._syncRemovedProjects(jconn)
                self._syncNewProjects(node)
                node.disconnect()
        else:
            for node in nodes:
                jconn = node.connect()
                self._syncNewProjects(node)
                node.disconnect()

    def _syncRemovedProjects(self, jconn):
        nodeJobs = [str(job['name']) for job in jconn.get_jobs()]

        for nodeJob in nodeJobs:
            if nodeJob not in self.jobs:
                jconn.delete_job(nodeJob)

    def _syncNewProjects(self, node):
        jenkinsUrl = partner.utils.JENKINS_URL \
                     % {'host': node.host, 'port': node.port}

        builder = JenkinsJobBuilder(jenkinsUrl,
                                    node.conn['user'],
                                    node.conn['passwd'],
                                    ignore_cache=True)

        while self.newProjects:
            project = self.newProjects.pop()

            tempFile = TemporaryFile()
            tempFile.write(yaml.dump(project.getData()))
            tempFile.seek(0)

            builder.update_jobs(tempFile)
            tempFile.close()


class SyncControl(object):

    DEFAULT_PROJECT_SYNC_INTERVAL = 60  # 1 minute
    _instance = None

    def __init__(self):
        self.newProjects = []
        self.lastSync = datetime.datetime(1991, 10, 12, 3, 20)
        self.syncInterval = SyncControl.DEFAULT_PROJECT_SYNC_INTERVAL

    def isTimeToSync(self):
        return (datetime.datetime.today() - self.lastSync).seconds > \
            self.syncInterval

    def syncRemovedProjects(self, newProject):
        if newProject is not None:
            self.newProjects.append(newProject)

        if not self.isTimeToSync():
            return

        self.lastSync = datetime.datetime.today()

        syncThread = SyncProjectsThread(self.newProjects)
        syncThread.start()

    @classmethod
    def sync(cls, projectToSync=None):
        try:
            cls._instance.syncRemovedProjects(projectToSync)
        except:
            cls._instance = cls()
            cls._instance.syncRemovedProjects(projectToSync)
