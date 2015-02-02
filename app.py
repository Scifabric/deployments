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
import subprocess
import config
import hmac
import hashlib
import json
import requests
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
                    print start_deployment(request.json['pull_request'])
                    return "Pull request merged!"
                return "Pull Request created!"
            else:
                return abort(501)
        else:
            return abort(501)
    else:
        return abort(403)


def start_deployment(pull_request):
    """Start a deployment."""
    print "Creating deployment"
    for repo in config.REPOS:
        if repo['repo'] == pull_request['head']['repo']['full_name']:
            for command in repo['commands']:
                p = subprocess.Popen(command, cwd=repo['folder'])
                print p
                p.wait()
            return "Deployment done!"
    return "Deployment canceled."


def create_deployment(pull_request, token):
    """Create a deployment."""
    user = pull_request['user']['login']
    owner = pull_request['head']['repo']['owner']['login']
    repo = pull_request['head']['repo']['full_name']
    payload = {'environment': 'production', 'deploy_user': user}
    url = 'https://api.github.com/repos/%s/deployments' % (repo)
    headers = {'Content-type': 'application/json'}
    auth = (token, '')
    data = {'ref': pull_request['head']['ref'],
            'payload': payload,
            'description': 'mydesc'}
    r = requests.post(url, data=json.dumps(data), headers=headers,
                      auth=auth)


# See http://stackoverflow.com/questions/18168819/how-to-securely-verify-an-hmac-in-python-2-7
def compare_digest(x, y):
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
    sha_name, signature = x_hub_signature.split('=')
    if signature is None:
       return False
    mac = hmac.new(config.SECRET, msg=request.data, digestmod=hashlib.sha1)
    if sha_name == 'sha1' and compare_digest(mac.hexdigest(), bytes(signature)):
        return True
    else:
        return False


if __name__ == "__main__":
    app.debug = config.DEBUG
    app.run()
