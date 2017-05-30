import unittest
from datetime import date, datetime
from flask import json, url_for
from http import HTTPStatus
from pytz import timezone
from base import TestCase
from factories import create_user, create_home, create_sensor, create_reading

class TestApiV1(TestCase):
    def test_list_readings_by_date(self):
        home = create_home(timezone='PST8PDT')
        sensor = create_sensor(home=home)
        tz = timezone(home.timezone)
        localtime = datetime(2017, 5, 30, 23, 30).astimezone(tz)
        utctime = datetime.utcfromtimestamp(localtime.timestamp())
        reading = create_reading(sensor=sensor, timestamp=utctime)
        api_key = sensor.home.user.api_key
        with self.client:
            response = self.client.get(
                url_for(
                    'api_v1_list_readings',
                    sensor_uuid=sensor.uuid,
                    date=date(2017, 5, 30),
                ),
                headers={
                    'Authorization': api_key,
                    'Accept': 'application/json',
                },
            )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(json.loads(response.data.decode()), [reading.as_dict()])
        with self.client:
            response = self.client.get(
                url_for(
                    'api_v1_list_readings',
                    sensor_uuid=sensor.uuid,
                    date=date(2017, 5, 29),
                ),
                headers={
                    'Authorization': api_key,
                    'Accept': 'application/json',
                },
            )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(json.loads(response.data.decode()), [])

    def test_list_readings_for_another_user(self):
        user = create_user()
        home = create_home(timezone='PST8PDT')
        sensor = create_sensor(home=home)
        tz = timezone(home.timezone)
        localtime = datetime(2017, 5, 30, 23, 30).astimezone(tz)
        utctime = datetime.utcfromtimestamp(localtime.timestamp())
        reading = create_reading(sensor=sensor, timestamp=utctime)
        with self.client:
            response = self.client.get(
                url_for(
                    'api_v1_list_readings',
                    sensor_uuid=sensor.uuid,
                    date=date(2017, 5, 30),
                ),
                headers={
                    'Authorization': user.api_key,
                    'Accept': 'application/json',
                },
            )
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_create_reading(self):
        sensor = create_sensor()
        api_key = sensor.home.user.api_key
        payload = dict(
            timestamp=datetime.utcnow().isoformat(),
            int_temp=50.5,
            ext_temp=21.0,
            humidity=50.0,
            resistance=1000.0,
        )
        with self.client:
            response = self.client.post(
                url_for('api_v1_create_reading', sensor_uuid=sensor.uuid),
                headers={
                    'Authorization': api_key,
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                },
                data=json.dumps(payload),
            )
        self.assertEqual(response.status_code, HTTPStatus.CREATED)
        self.assertEqual(sensor.readings.count(), 1)

    def test_create_duplicate_reading(self):
        sensor = create_sensor()
        api_key = sensor.home.user.api_key
        payload = dict(
            timestamp=datetime.utcnow().isoformat(),
            int_temp=50.5,
            ext_temp=21.0,
            humidity=50.0,
            resistance=1000.0,
        )
        create_reading(sensor=sensor, **payload)
        with self.client:
            response = self.client.post(
                url_for('api_v1_create_reading', sensor_uuid=sensor.uuid),
                headers={
                    'Authorization': api_key,
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                },
                data=json.dumps(payload),
            )
        self.assertEqual(response.status_code, HTTPStatus.CONFLICT)

    def test_create_reading_without_authorization_header(self):
        sensor = create_sensor()
        payload = dict(
            timestamp=datetime.utcnow().isoformat(),
            int_temp=50.5,
            ext_temp=21.0,
            humidity=50.0,
            resistance=1000.0,
        )
        with self.client:
            response = self.client.post(
                url_for('api_v1_create_reading', sensor_uuid=sensor.uuid),
                headers={
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                },
                data=json.dumps(payload),
            )
        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED)

    def test_create_reading_for_another_user(self):
        user = create_user()
        sensor = create_sensor()
        payload = dict(
            timestamp=datetime.utcnow().isoformat(),
            int_temp=50.5,
            ext_temp=21.0,
            humidity=50.0,
            resistance=1000.0,
        )
        with self.client:
            response = self.client.post(
                url_for('api_v1_create_reading', sensor_uuid=sensor.uuid),
                headers={
                    'Authorization': user.api_key,
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                },
                data=json.dumps(payload),
            )
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

if __name__ == '__main__':
    unittest.main()
