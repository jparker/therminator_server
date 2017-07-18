import unittest
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError
import uuid
from base import TestCase
from factories import build_home, build_sensor, create_sensor, build_reading
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

    def test_latest_reading(self):
        now = datetime.utcnow()
        sensor = build_sensor()
        readings = [
            build_reading(sensor=sensor, timestamp=now-timedelta(minutes=n))
            for n in range(2)
        ]
        db.session.add_all(readings)
        db.session.commit()
        self.assertEqual(sensor.latest_reading, readings[0])

if __name__ == '__main__':
    unittest.main()
