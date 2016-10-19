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
from models import ProjectWorkflowModel


class ProjectWorkflowData(AbstractProjectData):
    """Project data implementing workflow job with inline DSL script.
    Not working due to incompatibility with gearman."""

    def __init__(self, parent, formData):
        """Constructor.

        Args:
            parent(Project): Project that owns this data.
            formData(dict): Dict with this project data field's value.

        Returns:
            ProjectWorkflowData: thie object holdingthe form data.
        """
        self.form = ProjectWorkflowForm(formData)
        self.model = self.form.save(commit=False)
        self.model.parent = parent
        self.model.type = 'projectworkflowmodel'
        self.model.save()

    def getModel(self):
        """Get the database model representation of project workflow data."""
        return self.model

    def getForm(self):
        """Get the form representation of project workflow data."""
        return self.form

    @staticmethod
    def getBlankForm():
        """Get a blank form of project workflow data."""
        return ProjectWorkflowForm()

    def getData(self):
        pass


class ProjectWorkflowForm(forms.ModelForm):
    """Form representation of project workflow data."""

    class Meta:
        model = ProjectWorkflowModel
        fields = ['script']
        widgets = {
            'script': forms.Textarea(attrs={'class': 'materialize-textarea'}),
        }
