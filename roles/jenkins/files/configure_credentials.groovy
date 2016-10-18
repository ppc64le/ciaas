/*
 * Copyright IBM Corp, 2016
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
 * implied. See the License for the specific language governing
 * permissions and limitations under the License.
 */

import com.cloudbees.jenkins.plugins.sshcredentials.impl.*
import com.cloudbees.jenkins.plugins.sshcredentials.impl.*;
import com.cloudbees.plugins.credentials.*
import com.cloudbees.plugins.credentials.*;
import com.cloudbees.plugins.credentials.common.*
import com.cloudbees.plugins.credentials.domains.*
import com.cloudbees.plugins.credentials.domains.*;
import com.cloudbees.plugins.credentials.impl.*
import com.cloudbees.plugins.credentials.impl.*;
import hudson.plugins.sshslaves.*;
import jenkins.model.Jenkins;

def credStore = Jenkins.instance.getExtensionList(
    'com.cloudbees.plugins.credentials.SystemCredentialsProvider')[0]
    .getStore()

username = "jenkins"
password = ""
description = "slave ssh key"

// Create credentials
BasicSSHUserPrivateKey.FileOnMasterPrivateKeySource keySource =
    new BasicSSHUserPrivateKey.FileOnMasterPrivateKeySource('/var/ssh/id_rsa')

BasicSSHUserPrivateKey newCredential = new BasicSSHUserPrivateKey(
    CredentialsScope.GLOBAL,
    username,
    username,
    keySource,
    password,
    description
)

// Search available credential with same name
def username_matcher = CredentialsMatchers.withUsername(username)
def available_credentials =
  CredentialsProvider.lookupCredentials(
    StandardUsernameCredentials.class,
    Jenkins.getInstance(),
    hudson.security.ACL.SYSTEM,
    new SchemeRequirement("ssh")
  )

def previousCredential = CredentialsMatchers.firstOrNull(
  available_credentials,
  username_matcher
)

// Update or create new credentials
if(previousCredential != null) {
  credStore.updateCredentials(
    Domain.global(),
    previousCredential,
    newCredential
  )
} else {
  credStore.addCredentials(Domain.global(), newCredential)
}
