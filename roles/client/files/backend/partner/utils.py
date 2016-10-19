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

"""Utils functions when dealing with nodes and partners"""

import datetime
import gear
import ldap
import ldap.modlist as modlist
import pytz
import threading
import time

from account.utils import randomPassword, hashPassword
from client import settings, secret
import models


JENKINS_URL = 'http://%(host)s:%(port)s/'


def getJenkinsUser(partner, usingPassword=None, isAdmin=False):
    """Get the Jenkins credentials of a partner.

    Args:
        partner(Partner): The partner that owns the credential.
        usingPassword(string, optional): Desired password to use.
            Defaults to None.
        idAdmin(bool, optional): Whether return the admin user or regular user.
            Defaults to None.

    Returns:
        Tuple(string, string, string): This method returns a tuple following:
            username, password, hashedPassword.
    """
    jUser = None
    jPassword = None

    if isAdmin:
        dn = settings.LDAP_USER_DN_TEMPLATE \
             % str(partner.shortName + '_jenkins_admin')
    else:
        dn = settings.LDAP_USER_DN_TEMPLATE \
             % str(partner.shortName + '_jenkins')

    ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_DEMAND)
    ldap.set_option(ldap.OPT_X_TLS_CACERTFILE, settings.LDAP_CACERTFILE)
    l = ldap.initialize(secret.LDAP_URI)
    l.protocol_version = ldap.VERSION3
    l.start_tls_s()
    l.simple_bind_s(secret.LDAP_BIND_DN, secret.LDAP_BIND_PASSWORD)
    result = l.search_s(dn, ldap.SCOPE_SUBTREE)
    l.unbind_s()

    jUser = result[0][1]['uid'][0]
    oldHash = result[0][1]['userPassword'][0]

    if usingPassword is not None:
        jPassword = usingPassword
    else:
        jPassword = randomPassword()
    newHash = hashPassword(jPassword)
    _changePassword(dn, oldHash, newHash)

    return jUser, jPassword, newHash


def _changePassword(dn, oldHash, newHash):
    """Changes an user password.

    Args:
        dn(string): User full distinguished name in LDAP database.
        oldHash(string): The password hash already in the database.
        newHash(string): The new hash to save on database.
    """
    ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_DEMAND)
    ldap.set_option(ldap.OPT_X_TLS_CACERTFILE, settings.LDAP_CACERTFILE)
    l = ldap.initialize(secret.LDAP_URI)
    l.protocol_version = ldap.VERSION3
    l.start_tls_s()
    l.simple_bind_s(secret.LDAP_BIND_DN, secret.LDAP_BIND_PASSWORD)
    ldif = modlist.modifyModlist({'userPassword': oldHash},
                                 {'userPassword': newHash})
    l.modify_s(dn, ldif)
    l.unbind_s


class WorkersAdminRequest(gear.AdminRequest):
    """A "workers" administrative request.

    The response from gearman may be found in the **response** attribute.
    """

    command = b'workers'

    def __init__(self):
        super(WorkersAdminRequest, self).__init__()


def getOnlineNodes():
    """Get a list of online and unblocked nodes."""
    nodes = models.Node.objects.filter(site__active=True)
    onlineNodes = []

    for node in nodes:
        if node.status() == 'online':
            onlineNodes.append(node)

    return onlineNodes


def getBuildInformation(jobName):
    """Get all builds info of a project.

    Get all builds information of a project from all nodes ordered by build
    timestamp.

    Args:
        jobName(string): Name of project.

    Returns:
        list: List of build info organized in dicts.
    """
    nodes = getOnlineNodes()
    bvalues = []
    builds = {}

    for i, node in zip(xrange(len(nodes)), nodes):
        jconn = node.connect()

        if jconn.job_exists(jobName):
            jobJSON = jconn.get_job_info(jobName)
        else:
            continue

        nodeName = 'jenkins' + str(i)
        nodeLock = threading.Lock()

        asyncGetBuildInfo = AsyncGetBuildInfo(
            nodeName, jobName, jobJSON['builds'], builds, jconn, nodeLock)
        asyncGetBuildInfo.start()

        asyncGetBuildConsoleOutput = AsyncGetBuildConsoleOutput(
            nodeName, jobName, jobJSON['builds'], builds, jconn, nodeLock)
        asyncGetBuildConsoleOutput.start()

        asyncGetBuildInfo.join()
        asyncGetBuildConsoleOutput.join()

        node.disconnect()

        bvalues.extend(builds.values())
        builds.clear()

    # Sort builds by timestamp descending.
    # Sorting by first element is faster than using a compair function.
    sort_aux = [(b['timestamp'], b) for b in bvalues]
    sort_aux.sort(reverse=True)
    bvalues = [b for (timestamp, b) in sort_aux]
    return bvalues


class AsyncBuildInfoGetter(threading.Thread):

    def __init__(self, nodeName, jobName, rawbuilds, builds, jconn, lock):
        super(AsyncBuildInfoGetter, self).__init__()
        self.nodeName = nodeName
        self.jobName = jobName
        self.jconn = jconn
        self.rawbuilds = rawbuilds
        self.builds = builds
        self.lock = lock

    def updateBuildData(self, buildKey, buildData):
        self.lock.acquire(True)
        try:
            self.builds[buildKey].update(buildData)
        except:
            self.builds[buildKey] = buildData
        self.lock.release()


class AsyncGetBuildInfo(AsyncBuildInfoGetter):
    """Asynchronously downloads build information."""

    def run(self):
        for b in self.rawbuilds:
            build = self.jconn.get_build_info(self.jobName, b['number'])

            # Gets timestamp and convert from Java representation to python
            # representation.
            build['timestamp'] = pytz.utc.localize(
                datetime.datetime(
                    *time.gmtime(build['timestamp'] / 1000.0)[:6]))

            buildData = {'name': self.nodeName + 'build' +
                         str(build['number']),
                         'timestamp': build['timestamp'],
                         'result': build['result']}

            self.updateBuildData(b['number'], buildData)


class AsyncGetBuildConsoleOutput(AsyncBuildInfoGetter):
    """Asynchronously downloads build logs."""

    def run(self):
        for b in self.rawbuilds:
            # Get build console output.
            consoleOutput = self.jconn.get_build_console_output(self.jobName,
                                                                b['number'])

            buildData = {'consoleOutput': consoleOutput}

            self.updateBuildData(b['number'], buildData)
