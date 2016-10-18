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
    partner = models.Partner.objects.get(id=pid)
    if partner.active:
        partner.active = False
        partner.save()
    return redirect(urlresolvers.reverse('partner:list'))


@staff_member_required
def unblock(request, pid):
    partner = models.Partner.objects.get(id=pid)
    if not partner.active:
        partner.active = True
        partner.save()
    return redirect(urlresolvers.reverse('partner:list'))


@ensure_csrf_cookie
def registerNode(request):
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


def _generatePartnerArtifacts(partner, nodeAmount):
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


# Security fault :(
# This method publishs all partners jenkins addresses
def whitelist(request):
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
    context = {
        'partners': models.Partner.objects.all(),
    }
    return render(request, 'partner/list.html', context)


@staff_member_required
def artifacts(request, pid):
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
