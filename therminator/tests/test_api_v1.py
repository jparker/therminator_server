import unittest
from flask import json, url_for
from flask_testing import TestCase
from http import HTTPStatus
import logging
from therminator import app, db
from therminator.models import User
from base import TherminatorTestCase

class TestAPI(TherminatorTestCase):
    def test_api_test_with_invalid_authorization_header(self):
        with self.client as c:
            response = c.get(
                url_for('api_v1_test'),
                headers={'Accept': 'application/json'},
            )
            self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED)
            self.assertDictEqual(
                json.loads(response.data),
                {'error': 'Please include a valid API key in the Authorization header.'}
            )

    def test_api_test_with_valid_authorization_header(self):
        user = User(name='Alice', email='alice@example.com', password='secret')
        db.session.add(user)
        db.session.commit()
        with self.client as c:
            response = c.get(
                url_for('api_v1_test'),
                headers={'Authorization': user.api_key, 'Accept': 'application/json'},
            )
            self.assertEqual(response.status_code, HTTPStatus.OK)


if __name__ == '__main__':
    unittest.main()
