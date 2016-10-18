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

FROM ppc64le/debian:jessie
MAINTAINER Davi Diorio Mendes <ddiorio@br.ibm.com>

RUN apt-get -q update \
    && DEBIAN_FRONTEND="noninteractive" apt-get -q upgrade -y -o Dpkg::Options::="--force-confnew" --no-install-recommends \
    && DEBIAN_FRONTEND="noninteractive" apt-get -q install -y -o Dpkg::Options::="--force-confnew"  --no-install-recommends \
        slapd \
        ldap-utils \
        vim \
        openssl \
        ca-certificates \
        expect \
    && mkdir /var/local/ldap_files

ADD *.pem /var/local/ldap_files/
ADD install_certificates.sh /var/local/ldap_files/install_certificates.sh

RUN bash /var/local/ldap_files/install_certificates.sh

ADD ldap.conf /etc/ldap/ldap.conf
ADD slapd.conf /etc/ldap/slapd.conf
ADD bootstrap.ldif /var/local/ldap_files/bootstrap.ldif
ADD bootstrap.sh /var/local/ldap_files/bootstrap.sh

RUN update-rc.d -f slapd remove

EXPOSE 389 636
CMD ["/bin/bash","/var/local/ldap_files/bootstrap.sh"]
