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

RUN echo "deb http://ftp.de.debian.org/debian jessie-backports main" >> /etc/apt/sources.list
RUN apt-get -q update &&\
    DEBIAN_FRONTEND="noninteractive" apt-get -q upgrade -y -o Dpkg::Options::="--force-confnew" --no-install-recommends &&\
    DEBIAN_FRONTEND="noninteractive" apt-get -q install -y -o Dpkg::Options::="--force-confnew"  --no-install-recommends \
    build-essential \
    git-core \
    openssh-server \
    openjdk-8-jdk &&\
    apt-get -q autoremove &&\
    apt-get -q clean -y && rm -rf /var/lib/apt/lists/* && rm -f /var/cache/apt/*.bin

# Jenkins user
RUN useradd -m -s /bin/bash -u 1000 jenkins \
    && echo "jenkins:jenkins" | chpasswd

# Add public key for Jenkins login
RUN mkdir /home/jenkins/.ssh
# ADD authorized_keys /home/jenkins/.ssh/authorized_keys
# RUN chown -R jenkins:jenkins /home/jenkins \
#     && chmod 600 /home/jenkins/.ssh/* \
#     && chmod 700 /home/jenkins/.ssh

# Add jenkins to sudoers
RUN echo "jenkins  ALL=(ALL)  ALL" >> /etc/sudoers

# Set SSH Configuration to allow remote logins without /proc write access
# According to http://stackoverflow.com/questions/21391142/why-is-it-needed-to-set-pam-loginuid-to-its-optional-value-with-docker
RUN sed -i 's|session required pam_loginuid.so|session optional pam_loginuid.so|g' /etc/pam.d/sshd

# SSHD privilege error
# http://askubuntu.com/questions/53463/ssh-problem-after-update
RUN mkdir /var/run/sshd \
    && chmod 0755 /var/run/sshd

# Run SSHD
EXPOSE 22
CMD ["/usr/sbin/sshd", "-D"]

# vim:set ft=dockerfile:
