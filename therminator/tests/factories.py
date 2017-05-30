from datetime import datetime
from itertools import count
from therminator import db
from therminator.models import *

GENERATORS = {
    'user.name': map(lambda n: 'User %d' % n, count()),
    'user.name': map(lambda n: "User %d" % n, count()),
    'user.email': map(lambda n: "user%d@example.com" % n, count()),
    'home.name': map(lambda n: "Home %d" % n, count()),
    'sensor.name': map(lambda n: "Sensor %d" % n, count()),
}

def build_user(name=None, email=None, password='secret'):
    if not name:
        name = next(GENERATORS['user.name'])
    if not email:
        email = next(GENERATORS['user.email'])
    return User(name=name, email=email, password=password)

def create_user(commit=True, **kwargs):
    user = build_user(**kwargs)
    db.session.add(user)
    if commit:
        db.session.commit()
    return user

def build_home(user=None, name=None, timezone='PST8PDT'):
    if not user:
        user = build_user()
    if not name:
        name = next(GENERATORS['home.name'])
    return Home(user=user, name=name, timezone=timezone)

def create_home(commit=True, **kwargs):
    home = build_home(**kwargs)
    db.session.add(home)
    if commit:
        db.session.commit()
    return home

def build_sensor(home=None, name=None):
    if not home:
        home = build_home()
    if not name:
        name = next(GENERATORS['sensor.name'])
    return Sensor(home=home, name=name)

def create_sensor(commit=True, **kwargs):
    sensor = build_sensor(**kwargs)
    db.session.add(sensor)
    if commit:
        db.session.commit()
    return sensor

def build_reading(
    int_temp=50.0,
    ext_temp=21.0,
    humidity=60.0,
    resistance=1500.0,
    **kwargs,
):
    if 'sensor' not in kwargs:
        kwargs['sensor'] = build_sensor()
    if 'timestamp' not in kwargs:
        kwargs['timestamp'] = datetime.utcnow()
    return Reading(
        int_temp=int_temp,
        ext_temp=ext_temp,
        humidity=humidity,
        resistance=resistance,
        **kwargs,
    )

def create_reading(commit=True, **kwargs):
    reading = build_reading(**kwargs)
    db.session.add(reading)
    if commit:
        db.session.commit()
    return reading
