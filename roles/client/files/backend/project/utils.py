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

# Utils methods for project management
import gear
import simplejson
import uuid

from client import settings


def getGearClientConnection():
    """Get client connection to gearman."""
    gclient = gear.Client()
    gclient.addServer(settings.GEARMAN_HOST)
    gclient.waitForServer()
    return gclient


def gearJobFactory(action, projName, label=None, params=None):
    """Get gearman Job.

    Instantiates a gearman Job to do some action upon some project optionally
    using specific labels.

    Args:
        action(string): Action to take. Usually is \"build\".
        projName(string): Project affected by action.
        label(string, optional): Specific label to target the Job.
            Defaults to None.
        params(dict, optional): Dictionary with Job parameters.
            Defaults to None.

    Return:
        gear.Job: Gearman Job describing the requested function."""
    assert isinstance(action, basestring), "action is not string: %r" % action
    assert isinstance(projName, basestring), "projName is not string: %r" \
                                             % projName
    formatDict = {'action': action,
                  'projName': projName,
                  'label': label}
    jobName = "%(action)s:%(projName)s" % formatDict if label is None \
        else "%(action)s:%(projName)s:%(label)s" % formatDict

    defParams = {'OFFLINE_NODE_WHEN_COMPLETE': 'false'}
    if params is not None:
        defParams.update(params)
    jsonParams = simplejson.dumps(defParams)

    jobId = uuid.uuid4().hex

    return gear.Job(jobName, jsonParams, unique=jobId)
