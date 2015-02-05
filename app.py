# -*- coding: utf8 -*-
#
# Copyright (C) 2015 Daniel Lombraña González
#
# Deployments is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Deployments is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Deployments.  If not, see <http://www.gnu.org/licenses/>.
from flask import Flask, request, abort
from subprocess import Popen, PIPE, CalledProcessError
import config
import hmac
import hashlib
import json
import requests
import ansible.playbook
from ansible import callbacks
from ansible import utils
from ansible.errors import AnsibleError

app = Flask(__name__)

@app.route("/", methods=['GET', 'POST'])
def event_handler():
    """Handle deployment webhooks from Github."""
    if authorize(request, config):
        if request.method == 'POST':
            if request.headers.get('X-GitHub-Event') == 'pull_request':
                if (request.json['action'] == 'closed' and
                        request.json['pull_request']['merged'] is True):
                    print create_deployment(request.json['pull_request'], config.TOKEN)
                    return "Pull Request merged!"
                return "Pull Request created!"
            elif request.headers.get('X-GitHub-Event') == 'deployment':
                print "Process Deployment"
                if process_deployment(request.json):
                    return "Deployment done!"
                else:
                    return abort(500)
            elif request.headers.get('X-GitHub-Event') == 'deployment_status':
                print "Update Deployment Status"
                communicate_deployment(request.json)
                return "Update Deployment Status"
            else:
                return abort(501)
        else:
            return abort(501)
    else:
        return abort(403)

def run_ansible_playbook(ansible_hosts, playbook):
    """
    Run Ansible like ansible-playbook command. Similar to:
    ansible-playbook -i ansible_hosts playbook.yml
    """
    stats = callbacks.AggregateStats()
    playbook_cb = callbacks.PlaybookCallbacks(verbose=utils.VERBOSITY)
    inventory = ansible.inventory.Inventory(ansible_hosts)
    runner_cb = callbacks.PlaybookRunnerCallbacks(stats,
                                                  verbose=utils.VERBOSITY)
    pb = ansible.playbook.PlayBook(playbook=playbook,
                                   callbacks=playbook_cb,
                                   runner_callbacks=runner_cb,
                                   stats=stats, inventory=inventory)
    pb.run()

def process_deployment(deployment):
    """Process deployment."""
    try:
        for repo in config.REPOS:
            if repo['repo'] == deployment['repository']['full_name']:
                update_deployment(deployment, status='pending')
                # ansible_hosts and Playbook defined? Then run only Ansible.
                if 'ansible_hosts' in repo and 'ansible_playbook' in repo:
                    run_ansible_playbook(repo['ansible_hosts'],
                                         repo['ansible_playbook'])
                    update_deployment(deployment, status='success')
                    return True
                else:
                    for command in repo['commands']:
                        p = Popen(command, cwd=repo['folder'], stderr=PIPE)
                        return_code = p.wait()
                        if return_code != 0:
                            raise CalledProcessError(return_code,
                                                     command,
                                                     output=p.communicate())
                    update_deployment(deployment, status='success')
                    return True
    except KeyError as e:
        message = "ansible playbook or host file is missing in config file."
        update_deployment(deployment, status='error', message=message)
        return False
    except AnsibleError as e:
        update_deployment(deployment, status='error', message=str(e))
        return False
    except CalledProcessError as e:
        message = "command: %s ERROR: %s" % (e.cmd, e.output[1])
        update_deployment(deployment, status='error', message=message)
        return False
    except OSError as e:
        update_deployment(deployment, status='error', message=str(e))
        return False


def create_deployment(pull_request, token):
    """Create a deployment."""
    user = pull_request['user']['login']
    # owner = pull_request['head']['repo']['owner']['login']
    repo = pull_request['head']['repo']['full_name']
    payload = {'environment': 'production', 'deploy_user': user}
    url = 'https://api.github.com/repos/%s/deployments' % (repo)
    headers = {'Content-type': 'application/json'}
    auth = (token, '')
    data = {'ref': pull_request['head']['ref'],
            'payload': payload,
            'description': 'mydesc'}
    deployment = requests.post(url, data=json.dumps(data), headers=headers,
                               auth=auth)
    # print deployment
    return deployment


def update_deployment(deployment, status, message="ERROR"):
    """Update a deployment."""
    token = config.TOKEN
    repo = deployment['repository']['full_name']
    url = 'https://api.github.com/repos/%s/deployments/%s/statuses' % (repo, deployment['deployment']['id'])
    # print url
    headers = {'Content-type': 'application/json'}
    auth = (token, '')
    if status == 'success':
        msg = "The deployment has been successful."
    else:
        msg = message
    data = {'state': status,
            'target_url': 'http://example.com',
            'description': msg}
    r = requests.post(url, data=json.dumps(data), headers=headers, auth=auth)
    if r.status_code == 200:
        return True
    else:
        return False
    # print r.text


def communicate_deployment(deployment):
    """Communicate deployment via Slack."""
    repo = deployment['repository']['full_name']
    repo_url = deployment['repository']['url']
    status = deployment['deployment_status']['state']
    status_url = deployment['deployment']['url']
    user = deployment['deployment']['payload']['deploy_user']
    msg ='Repository <%s|%s> has been deployed by *%s* with <%s/statuses|%s>.' % (repo_url,
                                                                 repo,
                                                                 user,
                                                                 status_url,
                                                                 status)
    text = {'text': msg}
    headers = {'Content-type': 'application/json'}
    try:
        r = requests.post(config.SLACK_WEBHOOK,
                          data=json.dumps(text), headers=headers)
        return r.text
    except AttributeError:
        return msg


# See http://stackoverflow.com/questions/18168819/how-to-securely-verify-an-hmac-in-python-2-7
def compare_digest(x, y): # pragma: no cover
    """Compare to hmac digests."""
    if not (isinstance(x, bytes) and isinstance(y, bytes)):
        raise TypeError("both inputs should be instances of bytes")
    if len(x) != len(y):
        return False
    result = 0
    result = sum(a != b for a, b in zip(x, y))
    return result == 0


def authorize(request, config):
    """Authorize Github webhook."""
    x_hub_signature = request.headers.get('X-Hub-Signature')
    if x_hub_signature is None:
        return False
    try:
        sha_name, signature = x_hub_signature.split('=')
    except ValueError:
        return False
    if signature is None or signature == "":
       return False
    if sha_name != 'sha1':
        return False
    mac = hmac.new(config.SECRET, msg=request.data, digestmod=hashlib.sha1)
    if compare_digest(mac.hexdigest(), bytes(signature)):
        return True
    else:
        return False


if __name__ == "__main__": # pragma: no cover
    app.debug = config.DEBUG
    app.run()
