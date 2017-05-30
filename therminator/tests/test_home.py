import unittest
from sqlalchemy.exc import IntegrityError
from base import TestCase
from factories import build_user, build_home
from therminator import db
from therminator.models import Home

class TestHome(TestCase):
    def test_name_is_unique_to_user(self):
        user = build_user()
        homes = [build_home(user=user, name='Home') for _ in range(2)]
        db.session.add_all(homes)
        with self.assertRaises(IntegrityError) as cm:
            db.session.commit()
        self.assertRegex(
            cm.exception.args[0],
            r'Key \(user_id, name\)=\(\d+, Home\) already exists',
        )

if __name__ == '__main__':
    unittest.main()
