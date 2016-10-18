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

"""Account utils functions."""

from os import urandom
import collections
import hashlib
import ldap
import ldap.modlist as modlist
import random

from client import settings, secret


def _assertUserDict(user):
    """Assert if the dict is in user ldiff format."""
    assert isinstance(user, collections.Mapping), \
        "user is not a mapping: %r" % user
    userKeys = user.keys()
    assert 'uid' in userKeys, "mapping has no uid key: %r" % user
    assert 'ou' in userKeys, "mapping has no ou key: %r" % user
    assert user['ou'] == 'Users', \
        "user organizational unit is not Users: %r" % user
    assert 'userPassword' in userKeys, \
        "mapping has no userPassword key: %r" % user
    assert 'objectClass' in userKeys, \
        "mapping has no objectClass key: %r" % user


def randomPassword(length=32):
    """Generates a random password.

    Args:
        length (int): Password length. Defaults to 32.

    Returns:
        str: The generated password.
    """
    charbag = "abcdefghijklmnopqrstuvwxyz" + \
              "ABCDEFGHIJKLMNOPQRSTUVWXYZ" + \
              "0123456789^!\$%&/()=?{[]}+~#-_.:,;<>|\\"
    passwd = ''
    random.seed()
    for i in xrange(length):
        passwd = passwd + random.choice(charbag)
    return passwd


def hashPassword(password):
    """Encrypts a password and returns a string formated to LDAP database."""
    salt = str(urandom(4))
    hash = hashlib.sha1(password)
    hash.update(salt)
    salted_digest = '{}{}'.format(hash.digest(), salt).encode('base64').strip()
    return '{{SSHA}}{}'.format(salted_digest)


def createUser(user):
    """Creates a new user in LDAP database.

    Args:
        user (dict): User ldiff representation. A dict containing the keys:
            * uid: username as unique identification.
            * cn: first name.
            * sn: last name.
            * mail: e-mail.
    """
    _assertUserDict(user)

    ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_DEMAND)
    ldap.set_option(ldap.OPT_X_TLS_CACERTFILE, settings.LDAP_CACERTFILE)
    l = ldap.initialize(secret.LDAP_URI)
    l.protocol_version = ldap.VERSION3
    l.start_tls_s()
    l.simple_bind_s(secret.LDAP_BIND_DN, secret.LDAP_BIND_PASSWORD)

    dn = settings.LDAP_USER_DN_TEMPLATE % user['uid']
    ldif = modlist.addModlist(user)
    l.add_s(dn, ldif)
    l.unbind_s()


def changePassword(dn, oldHash, newHash):
    """Change an user password.

    Args:
        dn (str): User distinguished name in the LDAP database.
        oldHash (str): Old password hash.
        newHash (str): New password hash.
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


def isUserStaff(username):
    """Check if an user has staff permission.

    Args:
        username (str): Username of the user.

    Returns:
        bool: True if the user has staff permission. False otherwise.
    """
    ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_DEMAND)
    ldap.set_option(ldap.OPT_X_TLS_CACERTFILE, settings.LDAP_CACERTFILE)
    l = ldap.initialize(secret.LDAP_URI)
    l.protocol_version = ldap.VERSION3
    l.start_tls_s()
    l.simple_bind_s(secret.LDAP_BIND_DN, secret.LDAP_BIND_PASSWORD)
    dn = settings.LDAP_GROUP_DN_TEMPLATE % 'staff'
    result = l.search_s(dn, ldap.SCOPE_SUBTREE)
    userdn = (settings.LDAP_USER_DN_TEMPLATE % username).lower()
    return userdn in result[0][1]['member']
