CIaaS
=====
CI as a Service is a distributed multi Jenkins-master infrastructure for
continuous integration. At this point, it is focused on POWER architecture.

It is composed of two main parts: the master front-end and the compute nodes.
The master front-end consists of a web-client, a LDAP server and a gearman
distributed queue server. The compute node consists of a Jenkins instance
connected to several slaves. In this arregement, you can connect as many
"compute node" instances as desired.

License
-------
This project is licensed under the terms of Apache-v2 accordingly to the
[LICENSE file](./LICENSE).

Contributing
------------
Any contribution to this project is under the terms in the
[CONTRIBUTING file](./CONTRIBUTING).
