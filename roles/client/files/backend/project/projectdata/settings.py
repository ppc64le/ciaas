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

"""Controls settings of new project data."""

import importlib


def _importClass(classPath):
    """Import a class from path."""
    lastDot = classPath.rfind('.')
    dataModule = classPath[:lastDot]
    dataClass = classPath[lastDot+1:]
    return importlib.import_module(dataModule).__dict__[dataClass]

DATA_LIST = {}
"""List of project data classes to import, grouped by project type.

Example:
    DATA_LIST = {
        'project_type_1': [
            'package.path.ProjectDataClass1',
            'another.package.path.ProjectDataClass2',
        ],
        'project_type_2': [
            'package.path.ProjectDataClass1',
            'package.path.ProjectDataClass3',
            'another.package.path.ProjectDataClass4',
        ],
    }
"""

PROJECT_TYPES = {}
"""Available project types and its descriptions.

Example:
    PROJECT_TYPES = {
        'project_type_1': 'Create project using inline shell script.',
        'project_type_2': 'Create project using maven project.',
    }
"""


class DataManager(object):
    """Manages project data."""

    _instance = None

    def __init__(self):
        """Constructor."""
        if DataManager._instance is not None:
            raise TypeError('DataManager has already an instance.\
                    Use DataManager.get() to get the instance.')

        # Static parameters
        DataManager._instance = self

        # Object parameters

        # Bring PROJECT_TYPES inside the DataManager.
        self.projectTypes = []
        for proj_type in PROJECT_TYPES.keys():
            self.projectTypes.append((proj_type, PROJECT_TYPES[proj_type]))

        # Import project data.
        self.dataList = {}
        for proj_type in DATA_LIST.keys():
            k_array = [data[data.rfind('.')+1:-4].lower()
                       for data in DATA_LIST[proj_type]]
            v_array = [_importClass(data) for data in DATA_LIST[proj_type]]
            self.dataList[proj_type] = {k: v for k, v in zip(k_array, v_array)}

    @staticmethod
    def get():
        """Singleton instance getter."""
        if DataManager._instance is None:
            return DataManager()
        else:
            return DataManager._instance
