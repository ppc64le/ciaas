#! /bin/bash

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

python /home/client/backend/manage.py makemigrations
python /home/client/backend/manage.py migrate
uwsgi --chdir /home/client/backend \
      --module client.wsgi:application \
      --env DJANGO_SETTINGS_MODULE=client.settings \
      --master --pidfile /tmp/project-master.pid \
      --socket /home/client/backend/client.sock \
      --processes 5 \
      --harakiri 120 \
      --max-requests 5000 \
      --vacuum \
      --thunder-lock \
      --enable-threads \
      -b 32768 \
      --daemonize /var/log/uwsgi/powerci_client.log      # background the process
sudo nginx
tail -f /var/log/uwsgi/powerci_client.log
