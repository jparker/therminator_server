import unittest
from sqlalchemy.exc import IntegrityError
import uuid
from base import TestCase
from factories import build_home, build_sensor, create_sensor
from therminator import db
from therminator.models import Sensor

class TestSensor(TestCase):
    def test_generate_uuid_on_insert(self):
        sensor = create_sensor()
        assert uuid.UUID(sensor.uuid)

    def test_name_is_unique_to_home_id(self):
        home = build_home()
        sensors = [build_sensor(home=home, name='Sensor') for _ in range(2)]
        db.session.add_all(sensors)
        with self.assertRaises(IntegrityError) as cm:
            db.session.commit()
        self.assertRegex(
            cm.exception.args[0],
            r'Key \(home_id, name\)=\(\d+, Sensor\) already exists',
        )

if __name__ == '__main__':
    unittest.main()
