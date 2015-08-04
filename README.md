## Github deployments for your projects
[![Build
Status](https://travis-ci.org/PyBossa/deployments.svg)](https://travis-ci.org/PyBossa/deployments)
[![Coverage
Status](https://coveralls.io/repos/PyBossa/deployments/badge.svg)](https://coveralls.io/r/PyBossa/deployments)
[![Code Health](https://landscape.io/github/PyBossa/deployments/master/landscape.svg?style=flat)](https://landscape.io/github/PyBossa/deployments/master)

This is a very simple web server that can be used to automate your deployments
from Github repositories using command lines, or Ansible.

Basically you merge a branch like this and a deployment kicks in:

![Merging](http://i.imgur.com/A7AfTbE.gif)

Then, Slack notifies you about the progress like this:

[![Slack video](http://i.imgur.com/FEhAYhe.gif)](http://imgur.com/sx6y2mW)

## Setup

Basically, go to your repository and add a webhook.  Configure it enabling the
following individual elements:

 * Deployment status
 * Deployment
 * Pull Request

NOTE: it's important to add a secret to protect your deployments. Don't use
something easy.

NOTE2: you'll need a Github OAuth token. Create one from your settings page,
and give it only deployments permissions. Paste it in the variable **TOKEN** in
the config file.

Copy the config.py.template and rename to config.py. Add your own values.

## Installation requirements

for debian based systems

```bash
sudo apt-get install python-dev libffi-dev libssl-dev
```

## Customizing the commands

You can add as many commands as you want. Just, add a new list, and you will be
done. The commands are executed one after another.

## Using Ansible

To use ansible, you only need to take a look to the ansible template. Basically
add hosts to your inventary (each repository can have its own), and specify
which playbook has to be used for doing the deployment.

## Slack notifications

The server has a Slack integration, so you can receive notifications in your
Slack channel. Just create a channel, add an *incoming webhook* integration,
and paste the URL in the config file section **SLACK_WEBHOOK**.

## Specifying Github contexts

If you want, you can force the server to wait for a deployment until i.e.
Travis-CI has a success status. This is configured via *required_contexts*
in the config file. For example:

```
    required_contexts = ['continuous-integration/travis-ci']
```
