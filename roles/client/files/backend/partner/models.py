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

"""Partner models."""

from __future__ import unicode_literals
from os import urandom
from django import forms
from django.db import models
import hashlib
import jenkins
import threading
import uuid

from client import settings
import account.utils
import utils


def _getToken():
    """Return a unique multi purpose token."""
    uniqueid = str(uuid.uuid4()) + str(urandom(4))
    token = str(hashlib.sha1(uniqueid).hexdigest())
    return token


class Partner(models.Model):
    """Models a partner."""
    shortName = models.CharField(max_length=20,
                                 unique=True,
                                 verbose_name="Short Name")

    name = models.CharField(max_length=150,
                            unique=True,
                            verbose_name="Name")

    active = models.BooleanField(default=True)


class PartnerForm(forms.ModelForm):
    """Auto generates HTML forms for partner model."""

    class Meta:
        model = Partner
        fields = ['shortName', 'name']


class Node(models.Model):
    """Models a partner node with processing power."""

    locks = {}

    token = models.CharField(max_length=40, unique=True)
    host = models.URLField(default='0.0.0.0')
    port = models.IntegerField(default=0)
    site = models.ForeignKey(Partner, on_delete=models.CASCADE)

    conn = None

    # TODO: Secure nodes connections as mutex.
    def connect(self):
        """Connect to the node.

        Returns:
            Jenkins: Jenkins instance to manage a Jenkins servers using its
                REST API.
        """
        assert self.conn is None, "There are already open connections"

        # self._lock()

        jUser, jPassword, passwdHash = utils.getJenkinsUser(self.site)
        jConn = jenkins.Jenkins(utils.JENKINS_URL
                                % {'host': self.host,
                                   'port': self.port},
                                jUser, jPassword)
        self.conn = {
            'user': jUser,
            'passwd': jPassword,
            'hash': passwdHash,
            'conn': jConn
        }
        return jConn

    def disconnect(self):
        """Disconnect from the node."""
        userdn = settings.LDAP_USER_DN_TEMPLATE % self.conn['user']
        newHash = account.utils.hashPassword(account.utils.randomPassword())
        account.utils.changePassword(userdn, self.conn['hash'], newHash)

        # self._unlock()

        self.conn = None

    def status(self):
        """Return node availability ('online' or 'offline')."""
        jConn = self.connect()
        try:
            jConn.get_version()
        except:
            return "offline"
        finally:
            self.disconnect()
        return "online"

    def _lock(self):
        try:
            Node.locks[self.id].acquire(True)
        except:
            Node.locks[self.id] = threading.Lock()
            Node.locks[self.id].acquire()

    def _unlock(self):
        Node.locks[self.id].release()
