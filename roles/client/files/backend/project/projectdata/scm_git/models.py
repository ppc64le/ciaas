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

from django.db import models
import project.models as pmodels


class ScmGitModel(pmodels.Data):
    url = models.URLField()
    branch = models.CharField(max_length=60)

    @staticmethod
    def getPath():
        return 'job.scm'

    def getData(self):
        return [{
            'git': {
                'url': self.url,
                'branches': [self.branch],
                'credentials-id': 'ssh-jenkins',
                'skip-tag': True,
            }
        }]
