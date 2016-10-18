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

import importlib


def _importClass(classPath):
    lastDot = classPath.rfind('.')
    dataModule = classPath[:lastDot]
    dataClass = classPath[lastDot+1:]
    return importlib.import_module(dataModule).__dict__[dataClass]

DATA_LIST = {}
PROJECT_TYPES = {}


class DataManager(object):

    _instance = None

    def __init__(self):
        if DataManager._instance is not None:
            raise TypeError('DataManager has already an instance.\
                    Use DataManager.get() to get the instance.')

        # Static parameters
        DataManager._instance = self

        # Object parameters
        self.projectTypes = []
        for proj_type in PROJECT_TYPES.keys():
            self.projectTypes.append((proj_type, PROJECT_TYPES[proj_type]))

        self.dataList = {}
        for proj_type in DATA_LIST.keys():
            k_array = [data[data.rfind('.')+1:-4].lower()
                       for data in DATA_LIST[proj_type]]
            v_array = [_importClass(data) for data in DATA_LIST[proj_type]]
            self.dataList[proj_type] = {k: v for k, v in zip(k_array, v_array)}

    @staticmethod
    def get():
        if DataManager._instance is None:
            return DataManager()
        else:
            return DataManager._instance
