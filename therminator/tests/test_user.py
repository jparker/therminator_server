import unittest
import re
from sqlalchemy.exc import IntegrityError
from base import TestCase
from factories import build_user
from therminator import db
from therminator.models import User

class TestUser(TestCase):
    def test_password_verification(self):
        user = build_user(password='secret')
        assert user.is_correct_password('secret')
        assert not user.is_correct_password('bogus')

    def test_generate_api_key_on_insert(self):
        user = build_user()
        db.session.add(user)
        db.session.commit()
        assert user.api_key, 'unexpected api_key: {}'.format(user.api_key)

    def test_email_must_be_unique(self):
        users = [build_user(email='alice@example.com') for _ in range(2)]
        db.session.add_all(users)
        with self.assertRaises(IntegrityError) as cm:
            db.session.commit()
        self.assertRegex(
            cm.exception.args[0],
            r'Key \(email\)=\(alice@example\.com\) already exists',
        )

if __name__ == '__main__':
    unittest.main()
