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

"""Partner views."""

from ansible.parsing.vault import VaultLib
from django.contrib.admin.views.decorators import staff_member_required
from django.core import urlresolvers
from django.http import HttpResponse, Http404
from django.shortcuts import render, redirect
from django.views.decorators.csrf import ensure_csrf_cookie
from paramiko.client import SSHClient
import paramiko
import simplejson
import yaml

from client import settings
import account.utils
import models
import utils


@staff_member_required
def block(request, pid):
    """Blocks a partners in CIaaS network.

    Args:
        request(HttpRequest): The user request.
        pid(int): Partner database id number.

    Returns:
        HttpResponseRedirect: Redirects to partner list page.
    """
    partner = models.Partner.objects.get(id=pid)
    if partner.active:
        partner.active = False
        partner.save()
    return redirect(urlresolvers.reverse('partner:list'))


@staff_member_required
def unblock(request, pid):
    """Unblocks a partners in CIaaS network.

    Args:
        request(HttpRequest): The user request.
        pid(int): Partner database id number.

    Returns:
        HttpResponseRedirect: Redirects to partner list page.
    """
    partner = models.Partner.objects.get(id=pid)
    if not partner.active:
        partner.active = True
        partner.save()
    return redirect(urlresolvers.reverse('partner:list'))


@ensure_csrf_cookie
def registerNode(request):
    """Register a Jenkins instance in database.

    If the user does a GET request this view just send back the csfr_token
    in the cookies. If the user does a POST request and send in the request
    body the node properties so the node is registered on the database.

    Args:
        request(HttpRequest): The user request.

    Returns:
        If the user does a GET or a POST request, it returns an HttpResponse
            with 'ok' message and csfr_token in the cookies.
        If it is neither a GET nor a POST request an Http404 is returned.
    """
    if request.method == 'GET':
        return HttpResponse('ok')
    elif request.method != 'POST':
        return Http404()

    post = {}
    if request.method == 'POST' and len(request.POST.keys()) == 0:
        post = simplejson.loads(request.body)
    else:
        post = request.POST

    token = post['token']
    host = post['host']
    port = post['port']

    # TODO: Check host:port pair.
    node = models.Node.objects.get(token=token)
    node.host = host
    node.port = port
    node.save()

    # TODO: whitelist node at gearman firewall
    sshClient = SSHClient()
    sshClient.load_system_host_keys()
    sshClient.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    sshClient.connect(settings.GEARMAN_HOST,
                      int(settings.GEARMAN_SSH_PORT),
                      settings.GEARMAN_SSH_USER)
    command = 'sudo /sbin/iptables -vnL | awk \'{print $8}\''
    stdin, stdout, stderr = sshClient.exec_command(command)

    ips = [str(ip).strip() for ip in stdout.readlines()]

    if node.host not in ips:
        command = 'sudo /sbin/iptables -A INPUT -s %(host)s -j ACCEPT' \
                  % {'host': node.host}
        stdin, stdout, stderr = sshClient.exec_command(command)
    sshClient.close()

    return HttpResponse('ok')


# The artifacts term here is ambiguous given the artifacts term used with
# the encrypted yaml with credentials information. Here is not the generation
# of the file, but the very first generation of the credentials itself.
def _generatePartnerArtifacts(partner, nodeAmount):
    """Creates partner credentials on LDAP database and create the nodes.

    Args:
        partner(Partner): New partner instance.
        nodeAmount(int): How many Jenkins nodes this partner will keep.

    Returns:
        bool: Always returns True.
    """
    # Create partner jenkins account
    passwd = account.utils.randomPassword()
    passwd = account.utils.hashPassword(passwd)
    user = {
        'uid': "%s_jenkins" % str(partner.shortName),
        'ou': 'Users',
        'description': 'Jenkins user account for partner',
        'userPassword': str(passwd),
        'objectClass': ['account', 'simpleSecurityObject']
    }
    account.utils.createUser(user)

    passwd = str(models._getToken())[:15]
    passwd = account.utils.hashPassword(passwd)
    user = {
        'uid': "%s_jenkins_admin" % str(partner.shortName),
        'ou': 'Users',
        'description': 'Jenkins user account for partner',
        'userPassword': str(passwd),
        'objectClass': ['account', 'simpleSecurityObject']
    }
    account.utils.createUser(user)

    # Create empty nodes
    for i in xrange(nodeAmount):
        partner.node_set.create(token=models._getToken())

    return True


# Security fault :( try to allow only requests under https.
# This method publishs all partner's jenkins addresses
def whitelist(request):
    """Generates a list with all Jenkins addresses.

    Args:
        request(HttpRequest): The user request.

    Returns:
        HttpResponse: list of Jenkins addresses.
    """
    # TODO: Filter nodes of blocked partners.
    nodes = models.Node.objects.all()
    ips = []
    for node in nodes:
        ip = str(node.host)
        if ip != '0.0.0.0' and ip not in ips:
            ips.append(ip)
    ips = '\n'.join(ips)
    return HttpResponse(ips)


@staff_member_required
def newPartner(request):
    """Creates a new partner.

    If the request contains no data about the partner so the view returns a
    blank partner form to the user. But if the request has valid data related
    to the partner so the new parner is created and its credentials are saved
    to the LDAP database.

    Args:
        request(HttpRequest): The user request.

    Returns:
        HttpResponse: A blank partner form if request has no partner related
            data or a success message if the request has a valid partner data.
    """
    keys = request.POST.keys()
    if len(keys) == 0:
        context = {
            'form': models.PartnerForm()
        }
        return render(request, 'partner/new.html', context)
    else:
        form = models.PartnerForm(request.POST)

        try:
            partner = form.save()
        except ValueError:
            context = {'form': form}
            return render(request, 'partner/new.html', context)

        nodeAmount = int(request.POST.get('node_amount'))
        _generatePartnerArtifacts(partner, nodeAmount)
        context = {'partner': partner}
        return render(request, 'partner/new_successful.html', context)


@staff_member_required
def list(request):
    """List all partners.

    Args:
        request(HttpRequest): The user request.

    Returns:
        HttpResponse: Rendered list with all partners.
    """
    context = {
        'partners': models.Partner.objects.all(),
    }
    return render(request, 'partner/list.html', context)


@staff_member_required
def artifacts(request, pid):
    """Generates a new partner artifacts file.

    Args:
        request(HttpsRequest): The user request.
        pid(int): The partner database id number.

    Returns:
        HttpResponse: An encrypted yaml file with partner's credentials to
            access Jenkins.
    """
    if len(request.POST.keys()) > 0:
        vaultPasswd = str(request.POST.get('vault_password'))
    else:
        return Http404()

    print vaultPasswd

    partner = models.Partner.objects.get(id=pid)
    passwd = str(models._getToken())[:32]
    admin, passwd, hash = utils.getJenkinsUser(partner, passwd, isAdmin=True)
    del hash

    artifacts = {
        'tokens': [str(node.token) for node in partner.node_set.all()],
        'partner_user': "%s_jenkins" % str(partner.shortName),
        'admin_user': str(admin),
        'admin_password': str(passwd)
    }

    ansibleVault = VaultLib(vaultPasswd)
    ansibleVault.cipher_name = 'AES256'
    encArtifacts = ansibleVault.encrypt(yaml.dump(artifacts))

    return HttpResponse(encArtifacts, content_type='application/yml')
