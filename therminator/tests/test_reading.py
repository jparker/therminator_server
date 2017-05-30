import unittest
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from base import TestCase
from factories import build_sensor, build_reading, create_reading
from therminator import db
from therminator.models import Reading

class TestReading(TestCase):
    def test_timestamp_is_unique_to_sensor_id(self):
        sensor = build_sensor()
        now = datetime.utcnow()
        readings = [
            build_reading(sensor=sensor, timestamp=now)
            for _ in range(2)
        ]
        db.session.add_all(readings)
        with self.assertRaises(IntegrityError) as cm:
            db.session.commit()
        self.assertRegex(
            cm.exception.args[0],
            r'Key \(sensor_id, "timestamp"\)=\(\d+, .*\) already exists',
        )

    def test_humidity_is_greater_than_or_equal_to_0(self):
        with self.assertRaises(IntegrityError) as cm:
            create_reading(humidity=-1)
        self.assertRegex(
            cm.exception.args[0],
            r'violates check constraint "humidity_between_0_and_100"',
        )

    def test_humidity_is_less_than_or_equal_to_100(self):
        with self.assertRaises(IntegrityError) as cm:
            create_reading(humidity=101)
        self.assertRegex(
            cm.exception.args[0],
            r'violates check constraint "humidity_between_0_and_100"',
        )

    def test_resistance_is_greater_than_or_equal_to_0(self):
        with self.assertRaises(IntegrityError) as cm:
            create_reading(resistance=-1)
        self.assertRegex(
            cm.exception.args[0],
            r'violates check constraint "resistance_must_be_positive"',
        )

if __name__ == '__main__':
    unittest.main()
