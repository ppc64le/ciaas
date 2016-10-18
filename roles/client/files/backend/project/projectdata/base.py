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

from abc import ABCMeta, abstractmethod


class AbstractProjectData(object):
    """The AbstractProjectData base class is intended to define some base
    methods to every data related to the project definition.

    This class is not for direct use neither extension. Extend
    ProjectInformation or ProjectSection as needed."""

    __metaclass__ = ABCMeta

    @abstractmethod
    def getModel(self):
        """Gets the django model to represent this project data.
        Returns:
            django.db.models.Model: Database model representation of this
                project data."""
        pass

    @abstractmethod
    def getForm(self):
        """Gets the django form to represent this project data.
        Returns:
            django.forms.Form: Form representation of this project data."""
        pass

    @staticmethod
    @abstractmethod
    def getBlankForm():
        """Gets a blank django form representation for this project data.
        Returns:
            django.forms.Form: Blank Form representation of this project data.
        """
        pass

    @abstractmethod
    def getData(self):
        """Gets the lxml xml representation of this project data.
        Returns:
            lxml.etree.Element: Xml root node of this project data."""
        pass
