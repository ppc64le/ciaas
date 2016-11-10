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

from project.projectdata.base import AbstractProjectData
from models import ProjectJenkinsfileModel


class ProjectJenkinsfileData(AbstractProjectData):
    """Project data implementing pipeline project with Jenkinsfile scm
    script. Not working due to JenkinsJobBuilder limitations."""

    def __init__(self, parent, formData):
        """Constructor.

        Args:
            parent(Project): Project that owns this data.
            formData(dict): Dict with this project data field's value.

        Returns:
            ProjectJenkinsfileData: this object holding the form data.
        """
        self.form = ProjectJenkinsfileForm(formData)
        self.model = None
        self.parent = parent

    def getModel(self):
        """Get the database model representation of project Jenkinsfile
        data."""
        if self.model is not None:
            return self.model
        else:
            self.model = self.form.save(commit=False)
            self.model.parent = self.parent
            self.model.type = 'projectjenkinsfilemodel'
            return self.model

    def getForm(self):
        """Get the form representation of project Jenkinsfiel data."""
        return self.form

    @staticmethod
    def getBlankForm():
        """Get a blank form of project Jenkinsfile data."""
        return ProjectJenkinsfileForm()

    def getData(self):
        pass


class ProjectJenkinsfileForm(forms.ModelForm):
    """Form representation of project Jenkinsfile data."""

    class Meta:
        model = ProjectJenkinsfileModel
        fields = ['gitUrl', 'branch', 'scriptPath']
