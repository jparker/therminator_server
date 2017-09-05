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

    def test_validate_timestamp(self):
        with self.assertRaises(ValueError) as cm:
            build_reading(timestamp=None)
        self.assertEqual(cm.exception.args, ("timestamp can't be blank",))

    def test_validate_int_temp(self):
        pass

    def test_validate_ext_temp(self):
        with self.assertRaises(ValueError) as cm:
            build_reading(ext_temp=None)
        self.assertEqual(cm.exception.args, ("ext_temp can't be blank",))
        # Make sure 0.0 is treated as "present".
        build_reading(ext_temp=0.0)

    def test_validate_humidity(self):
        with self.assertRaises(ValueError) as cm:
            build_reading(humidity=-1.0)
        self.assertEqual(
            cm.exception.args,
            ('humidity must be between 0 and 100',)
        )
        with self.assertRaises(ValueError) as cm:
            build_reading(humidity=100.1)
        self.assertEqual(
            cm.exception.args,
            ('humidity must be between 0 and 100',)
        )

    def test_validate_resistance(self):
        reading = build_reading(resistance=-1.0)
        self.assertEqual(0.0, reading.resistance)

if __name__ == '__main__':
    unittest.main()
