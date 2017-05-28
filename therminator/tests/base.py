from flask_testing import TestCase
import logging
import unittest
from therminator import app, db


class TherminatorTestCase(TestCase):
    def setUp(self):
        db.create_all()
        db.session.commit()
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def create_app(self):
        app.config.from_object('therminator.config.Test')
        return app
