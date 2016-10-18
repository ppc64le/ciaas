What is CiaaS?
==============

CI as a Service is a distributed multi Jenkins-master infrastructure for
continuous integration. At this point, it is focused on POWER architecture.
It is composed of two main parts: the main-node and the satellite-node. The
main-node consists of a web-client, a LDAP server and a Gearman distributed
queue server. The satellite-node consists of a Jenkins instance connected to
several slaves. In this arrangement you can connect as many “satellite-nodes”
instances as desired.

Setup Guide
===========

The CIaaS infrastructure setup is done with Ansible playbooks, so the only
action needed is settings some variables and firing the playbooks!

The Hosts File
--------------

Ansible uses an inventory to keep information about the managed hosts, this is
the hosts file. The hosts file is divided in five sections: gearmand, ldap,
client, jenkins and slave. Each section is composed of one or more lines. Each
line describes a host. The line syntax is as follows:

```
[host or IP] ansible_user=[user_id]
```

where [host or IP] is the host or IP of the target machine and [user_id] is the
user Ansible will use on the target machine. More variables can be added in the
same line, setting some host specific behaviours. Follows a list of available
variables:

Host specific variables
-----------------------

All the following variables are REQUIRED to Ansible playlists. If you don't
know how to set some of them you can use the provided examples as default
values.

### gearmand
* gearmand_port
  * Port gearman daemon will listen.
  * Example: gearmand_port=4730
* ssh_port
  * Specify what port use for ssh.
  * Example: ssh_port=2200
  * Important! This is not the ssh port Ansible will use. This setting will be used by web-client to connect through ssh to gearmand.

### ldap
* ldap_port
  * Port used for LDAP unencrypted communication
  * Example: ldap_port=389
  * Important! Even under unencrypted socket all the communication is encrypted due to StartTLS LDAP feature.
* ldaps_port
  * Port used for LDAP encrypted communication.
  * Example: ldaps_port=636
* ldap_root_dn
  * Root distinguished name for LDAP database.
  * Example: ldap_root_dn=”dc=example,dc=com”

### client
* client_port
  * Port to serve web-client pages.
  * Example: client_port=8000

### jenkins
* jenkins_port
  * Port to serve jenkins REST API.
  * Example: jenkins_port=8080

### slave
* debian_ports
  * Ports used by debian slaves to accept Jenkins connection.
  * There will be one slave per port. If two ports declared then there will be two slaves. If five ports declared then there will be five slaves.
  * Example: debian_ports='[22000,22001]'
* ubuntu_ports
  * Ports used by ubuntu slaves to accept Jenkins connection.
  * There will be one slave per port. If two ports declared then there will be two slaves. If five ports declared then there will be five slaves.
  * Example: ubuntu_ports='[22002,22003]'

### Full hosts file example
This is an example of how a full hosts file should looks like.
```ini
[gearmand]
192.168.122.231 ansible_user=ubuntu gearmand_port=4730 ssh_port=2200 ssh_user=client

[ldap]
192.168.122.231 ansible_user=ubuntu ldap_port=389 ldaps_port=636 ldap_root_dn="dc=example,dc=com" ca_domain="example.com"

[jenkins]
192.168.122.203 ansible_connection=local ansible_user=ubuntu jenkins_port=8080

[client]
192.168.122.231 ansible_user=ubuntu client_port=8000

[slave]
192.168.122.203 ansible_connection=local debian_ports='[22000]' ubuntu_ports='[22001,22002]'
192.168.122.231 ansible_user=ubuntu debian_ports='[22000]'
```

The Secret File
---------------
Avoiding to leak sensitive information the CIaaS depends on secret file that is
not tracked by git. This file has LDAP manager account information, admin
information and the django secret key, for the web-client.
The following listing is an example of the secret file:

```yaml
---
ldap_manager:
   cn: cn=Manager
   passwd: admin

admin:
   uid: admin
   cn: Adilson
   sn: Mindel
   mail: admin@nowhere.com
   sha1_passwd: "{SSHA}bc7Wp5GU2tFgCL5cFt2N3/7pXkKvNH1g"

django_secret_key: "@i3(5b7atjfu&*-%_7nxcdop_pfr(yf*m1g+b$(5-)sq$10=i"
```

Always keep passwords hashed in order to improve security. The slappasswd
command with no arguments prompts you for a password and hashes it for you.

```
$ slappasswd
New password:
Re-enter new password:
{SSHA}HoJZTBpZC7RI5w4fv4cijAO3AYkpAXQ6
```

The Secret Role
---------------
The secret role keeps sensitive files away of the repository. The files that
needs extra security are the LDAP certificate and the web-client certificate
(both carries its private keys). So you need to request a certificate or use a
self-signed certificate. If you use a self-signed certificate, you must put a
copy of the ca certificate in ```roles/ldap/files/ca-chain.cert.pem```.

Main Node Playbook
------------------
The main node playbook is responsible to setup all main node components
(gearmand, LDAP, web-client). To run the playbook:

```
$ sudo ansible-playbook main_node_playbook.yml --ask-sudo-pass
```

Once the playbook ends with no error we have the three containers running. In
order to run the next playbook we need to add a partner in the web-client.

Manage Partners in the web-client
---------------------------------

In the CIaaS architecture just registered partners can execute the satellite
node playbook. So this section intend to walk you through the register partner
process.

In the previous session we put up the CIaaS web-client, together with the LDAP
user database and the gearman distributed queue server. So now you can access
the web-client using any browser, just request the page
```https://[your_client_host_or_ip]:[your_client_port]```. Don't forget the
https protocol, as we don't redirect from http to https. Now lets register a
new partner.

### Register partner

The register partner process is described in the following list:

1. Access the web-client and sign in with the admin user
2. Click at the username, in the upper-right corner.
3. On the drop-down menu, select Partners.
4. Click the NEW button just below the top bar.
5. Fill the form and submit.

Upon success you'll be redirected to Partners page and the partner should be
shown in the list. Now you can download its artifacts (pre-requisite to run the
satellite node playbook).

### Download partner's artifacts
The partner's artifacts is an Ansible encrypted vars_file. It is a prerequisite
to run the satellite_node_playbook and contains private data about the partner.
To download the partner's artifacts go to the Partners page and hit the actions
button of the desired partner (three vertical dots at the right of the partner's
name) and select Download artifacts in the drop-down menu.

The partner's artifacts is an encrypted file so it needs a password to encrypt
and decrypt data. Thus you may provide a password in the downloading pop-up and
click the download button. The pop-up also warns you that each download
invalidates the older files.

Satellite Node Playbook
-----------------------

The satellite node playbook setup one jenkins instance with several slaves
(accordingly to hosts file description). The satellite node playbook has a
prerequisite, the partner's artifacts downloaded in the previous section. As
the partner's artifacts is encrypted the password used in its generation is
required to run the playbook. To run the playbook:

```
$ sudo ansible-playbook satellite_node_playbook.yml --ask-sudo-pass --ask-vault-pass
```

Once the playbook ends with no error we have the jenkins-master with all its
slaves setup and running.
