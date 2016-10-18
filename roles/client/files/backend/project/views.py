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
from django.contrib.auth.decorators import login_required
from django.core import urlresolvers
from django.shortcuts import render, redirect
from django.http import Http404, HttpResponse
from jenkins_jobs.builder import Builder as JenkinsJobBuilder
from tempfile import TemporaryFile
import gear
import simplejson
import uuid
import yaml

from client import settings
from projectdata.settings import DataManager
from synccontrol import SyncControl
import account.utils
import partner.utils
import models


def _updateJenkinsJob(jobDescription):
    nodes = partner.utils.getOnlineNodes()

    tempFile = TemporaryFile()
    tempFile.write(yaml.dump(jobDescription))

    for node in nodes:
        tempFile.seek(0)
        jenkinsUrl = 'http://%(ip)s:%(port)s/' \
                     % {'ip': node.host, 'port': node.port}
        jUser, jPassword, hash = partner.utils.getJenkinsUser(node.site)
        builder = JenkinsJobBuilder(jenkinsUrl,
                                    jUser,
                                    jPassword,
                                    ignore_cache=True)
        builder.update_jobs(tempFile)
        account.utils.changePassword(settings.LDAP_USER_DN_TEMPLATE % jUser,
                                     hash,
                                     account.utils.hashPassword(
                                         account.utils.randomPassword()))
    tempFile.close()


@login_required
def selectProjectType(request):
    dataManager = DataManager.get()
    context = {
        'project_types': dataManager.projectTypes,
    }
    return render(request, 'project/select_project_type.html', context)


@login_required
def create(request, projType):
    keys = request.POST.keys()
    if len(keys) == 0:
        return _createBlankForm(request, projType)
    else:
        dataManager = DataManager.get()
        if projType not in dataManager.dataList.keys():
            # TODO: Properly notify the error with the right status code.
            return HttpResponse("ERROR: Invalid project type: %s" % projType)

        projectForm = models.ProjectForm(request.POST)
        project = projectForm.save(commit=False)
        project.owner = request.user
        project.save()

        thisDataList = [projectForm]
        for data in dataManager.dataList[projType].values():
            d = data(project, request.POST)
            thisDataList.append(d)

        _updateJenkinsJob(project.getData())

        return render(request,
                      'project/create_successful.html',
                      {'project': project,
                       'forms': [data if isinstance(data, forms.ModelForm)
                                 else data.getForm()
                                 for data in thisDataList]})


def _createBlankForm(request, projType):
    context = {
        'forms': models.Project.getForms(projType),
    }
    return render(request, 'project/create.html', context)


@login_required
def list(request):
    tabs = request.GET.get('tabs', "").split('!')
    active = request.GET.get('active', "")
    try:
        tabs.remove('')
    except ValueError:
        pass
    context = {'projects': request.user.project_set.all(),
               'tabs': tabs,
               'active': active}
    return render(request, 'project/list.html', context)


@login_required
def update(request):
    return Http404()


def _compairBuildsTimestamp(x, y):
    if x['timestamp'] == y['timestamp']:
        return 0
    elif x['timestamp'] < y['timestamp']:
        return 1
    else:
        return -1


@login_required
def delete(request, projName):
    nodes = partner.utils.getOnlineNodes()

    for node in nodes:
        jConn = node.connect()

        if jConn.job_exists(projName):
            jConn.delete_job(projName)

        node.disconnect()

    project = models.Project.objects.get(name=projName)
    project.delete()
    return redirect(urlresolvers.reverse('project:list'))


@login_required
def buildProject(request, projName):
    proj = models.Project.objects.get(name=projName)
    assert proj is not None, "No project found with name %s." % projName
    proj.triggerBuild()

    SyncControl.sync(proj)

    return HttpResponse('ok')


# Does not working
def abortBuild(request, projName):
    gclient = gear.Client()
    gclient.addServer(settings.GEARMAN_HOST)
    gclient.waitForServer()

    jobId = uuid.uuid4().hex
    job = gear.Job('stop:' + settings.GEARMAN_HOST,
                   simplejson.dumps({'OFFLINE_NODE_WHEN_COMPLETE': 'false',
                                     'name': projName}),
                   unique=jobId)
    gclient.submitJob(job, True)
    gclient.shutdown()

    return HttpResponse('ok')
