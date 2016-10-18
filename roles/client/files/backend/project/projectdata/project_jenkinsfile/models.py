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


class ProjectJenkinsfileModel(pmodels.Data):
    gitUrl = models.URLField('Git URL')
    branch = models.CharField(max_length=60)
    scriptPath = models.CharField('Script path',
                                  max_length=30,
                                  default="Jenkinsfile")

    @staticmethod
    def getPath():
        return 'job'

    def getData(self):
        rawxml = \
            '<properties><org.jenkinsci.plugins.workflow.job.properties.PipelineTriggersJobProperty><triggers/></org.jenkinsci.plugins.workflow.job.properties.PipelineTriggersJobProperty></properties><definition class="org.jenkinsci.plugins.workflow.cps.CpsScmFlowDefinition" plugin="workflow-cps@2.12"><scm class="hudson.plugins.git.GitSCM" plugin="git@2.5.3"><configVersion>2</configVersion><userRemoteConfigs><hudson.plugins.git.UserRemoteConfig><url>%(git_url)s</url></hudson.plugins.git.UserRemoteConfig></userRemoteConfigs><branches><hudson.plugins.git.BranchSpec><name>%(branch)s</name></hudson.plugins.git.BranchSpec></branches><doGenerateSubmoduleConfigurations>false</doGenerateSubmoduleConfigurations><submoduleCfg class="list"/><extensions/></scm><scriptPath>%(script_path)s</scriptPath></definition>' % {  # NOQA
                'git_url': self.gitUrl,
                'branch': self.branch,
                'script_path': self.scriptPath
            }

        return {
            'project-type': 'workflow',
            'sandbox': 'true',
            'dsl': '',
            'raw': {'xml': rawxml},
        }
