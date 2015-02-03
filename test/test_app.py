# -*- coding: utf8 -*-
# This file is part of deployments.
#
# Copyright (C) 2014 Daniel Lombraña González
#
# deployments is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# deployments is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with deployments. If not, see <http://www.gnu.org/licenses/>.
"""
App package for testing deployments application.

This exports:
    - Test the app

"""
import json
from base import Test
from app import app
from mock import patch
from github import pull_request_opened, pull_request_closed


class TestApp(Test):

    """Class for Testing the deployments application."""

    def setUp(self):
        """Setup method for configuring the tests."""
        self.app = app
        self.app.config['TESTING'] = True
        self.tc = self.app.test_client()

    def test_get_403(self):
        """Test GET method returns 403 for non auth."""
        res = self.tc.get('/')
        assert res.status_code == 403, self.ERR_MSG_403_STATUS_CODE

    @patch('app.authorize', return_value=True)
    def test_get_501(self, authorize):
        """Test GET method returns 501 for auth."""
        res = self.tc.get('/')
        assert res.status_code == 501, self.ERR_MSG_501_STATUS_CODE

    def test_post_403(self):
        """Test POST method return 403 for non auth."""
        res = self.tc.post('/')
        assert res.status_code == 403, self.ERR_MSG_403_STATUS_CODE

    @patch('app.authorize', return_value=True)
    def test_post_501_missing_headers(self, authorize):
        """Test POST method with missing header returns 501 for auth."""
        res = self.tc.post('/')
        assert res.status_code == 501, self.ERR_MSG_501_STATUS_CODE

    @patch('app.authorize', return_value=True)
    def test_post_501_wrong_headers_alt(self, authorize):
        """Test POST method with wrong header returns 501 for auth."""
        self.github_headers['X-GitHub-Event'] = 'wrong'
        res = self.tc.post('/', headers=self.github_headers)
        assert res.status_code == 501, self.ERR_MSG_501_STATUS_CODE

    @patch('app.authorize', return_value=True)
    def test_post_pull_request_event(self, authorize):
        """Test POST method with pull request event."""
        self.github_headers['X-GitHub-Event'] = 'pull_request'
        headers = self.github_headers.copy()
        headers.update(self.json_headers)
        res = self.tc.post('/', data=json.dumps(pull_request_opened),
                           headers=headers)
        assert res.status_code == 200, self.ERR_MSG_200_STATUS_CODE
        assert "Pull Request created!" in res.data, res.data
