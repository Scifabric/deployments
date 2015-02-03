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
from base import Test
from app import app
from mock import patch


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

