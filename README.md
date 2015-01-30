# Simple web server to do automatic deployments.

This is a very simple web server that can be used to automate your deployments
from Github repositories.

## Setup

Basically, go to your repository and add a webhook.  Configure it enabling the
following individual elements:

 * Deployment status
 * Deployment
 * Pull Request

NOTE: it's important to add a secret to protect your deployments. Don't use
something easy.

Copy the config.py.template and rename to config.py. Add your own values.

## Customizing the commands

You can add as many commands as you want. Just, add a new list, and you will be
done. The commands are executed one after another.
