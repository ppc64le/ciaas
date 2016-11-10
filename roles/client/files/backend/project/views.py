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

"""Project views."""

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
import pprint

from client import settings
from projectdata.settings import DataManager
from synccontrol import SyncControl
import account.utils
import partner.utils
import models


def _updateJenkinsJob(jobDescription):
    """Update a project in all Jenkins instances.

    Args:
        jobDescription(dict): Description of the project in dict form.
    """
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
    """Allow user to select a project type.

    Args:
        request(HttpRequest): The user request.

    Returns:
        HttpRestponse: The rendered list of project types.
    """
    dataManager = DataManager.get()
    context = {
        'project_types': dataManager.projectTypes,
    }
    return render(request, 'project/select_project_type.html', context)


@login_required
def create(request, projType):
    """Create a new project.

    If the request contains no data about the project so the view returns a
    blank project form to the user. But if the request has data related to a
    project so the new project is created on the local database and on all
    registered Jenkins instances.

    Args:
        request(HttpRequest): The user request.
        projType(string): The type of the project.

    Returns:
        HttpResponse: A blank project form if request has no project data or
            a success message if request has valid project data.
    """
    keys = request.POST.keys()
    dataManager = DataManager.get()

    if len(keys) == 0:
        # Return a blank form.
        context = {
            'forms': models.Project.getForms(projType),
            'description': dataManager.dataList[projType].description
        }
        return render(request, 'project/create.html', context)
    else:
        forms_are_valid = True
        if projType not in dataManager.dataList.keys():
            # TODO: Properly notify the error with the right status code.
            return HttpResponse("ERROR: Invalid project type: %s" % projType)

        project = None
        projectForm = models.ProjectForm(request.POST)
        try:
            project = projectForm.save(commit=False)
            project.owner = request.user
        except ValueError:
            forms_are_valid = False

        thisDataList = []
        for data in dataManager.dataList[projType].packages.values():
            d = data(project, request.POST)
            forms_are_valid = forms_are_valid and d.getForm().is_valid()
            thisDataList.append(d)

        if forms_are_valid:
            project.save()
            for data in thisDataList:
                data.getModel().save()
        else:
            # Return form with errors.
            pprint.pprint(projectForm)
            pprint.pprint(thisDataList)
            pprint.pprint([data.getForm() for data in thisDataList])
            context = {
                'forms': [projectForm] + [data.getForm()
                                          for data in thisDataList],
                'description': dataManager.dataList[projType].description
            }
            pprint.pprint(context)
            return render(request,
                          'project/create.html',
                          context)

        _updateJenkinsJob(project.getData())

        # Return success page.
        return render(request,
                      'project/create_successful.html',
                      {'project': project})


@login_required
def list(request):
    """List all projects of active user.

    Args:
        request(HttpRequest): The user request.

    Returns:
        HttpResponse: Rendered project list.
    """
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
    """Not implemented yet."""
    return Http404()


@login_required
def delete(request, projName):
    """Delete a project from local database and all registered Jenkins
    instances.

    Args:
        request(HttpRequest): The user request.
        projName(string): Name of the project to delete.

    Returns:
        HttpResponseRedirect: Redirects user to project list page.
    """
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
    """Manually trigger a project build.

    Args:
        request(HttpRequest): The user request.
        projName(string): The name of the project to build.

    Returns:
        HttpResponse: Just an ok.
    """
    proj = models.Project.objects.get(name=projName)
    assert proj is not None, "No project found with name %s." % projName
    proj.triggerBuild()

    SyncControl.sync(proj)

    return HttpResponse('ok')


# Does not working
def abortBuild(request, projName):
    """Aborts a project build. Not working.

    Args:
        request(HttpRequest): The user request.
        projName(string): Name of the project to abort build.

    Returns:
        HttpResponse: Just an ok.
    """
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
