from . import app, db, bcrypt
from flask_login import UserMixin
from functools import wraps
from sqlalchemy.orm import validates
import sqlalchemy.dialects.postgresql as psql

def validates_presence(f):
    @wraps(f)
    def validator(self, key, value):
        if value is None:
            raise ValueError("{} can't be blank".format(key))
        return f(self, key, value)
    return validator


class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    api_key = db.Column(
        db.String(255),
        nullable=False,
        server_default=db.func.encode(db.func.gen_random_bytes(32), 'hex'),
        unique=True
    )
    homes = db.relationship(
        'Home',
        backref='user',
        lazy='dynamic',
        order_by='Home.name'
    )

    def __init__(self, name, email, password):
        self.name = name
        self.email = email
        self.password = password

    def __repr__(self):
        return '<User id={} email={}>'.format(self.id, self.email)

    def is_correct_password(self, plaintext):
        return bcrypt.check_password_hash(self.password, plaintext)

    @validates('password')
    def validates_password(self, key, value):
        return bcrypt.generate_password_hash(
            value,
            app.config['BCRYPT_LOG_ROUNDS'],
        ).decode()


class Home(db.Model):
    __tablename__ = 'homes'
    __table_args__ = (
        db.UniqueConstraint('user_id', 'name', name='user_id_name_unq'),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    timezone = db.Column(db.String(255), nullable=False, server_default='UTC')
    sensors = db.relationship(
        'Sensor',
        backref='home',
        lazy='dynamic',
        order_by='Sensor.name',
    )

    def __init__(self, user, name, timezone):
        self.user = user
        self.name = name
        self.timezone = timezone

    def __repr__(self):
        return '<Home id={} name={} timezone={}>' \
            .format(self.id, self.name, self.timezone)


class Sensor(db.Model):
    __tablename__ = 'sensors'
    __table_args__ = (
        db.UniqueConstraint('home_id', 'name', name='home_id_name_unq'),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    home_id = db.Column(db.Integer, db.ForeignKey('homes.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    uuid = db.Column(
        psql.UUID,
        nullable=False,
        server_default=db.func.gen_random_uuid(),
        unique=True,
    )
    readings = db.relationship(
        'Reading',
        backref='sensor',
        lazy='dynamic',
        order_by='Reading.timestamp',
    )
    latest_reading = db.relationship(
        'Reading',
        order_by='Reading.timestamp.desc()',
        uselist=False,
    )

    def __init__(self, home, name):
        self.home = home
        self.name = name

    def __repr__(self):
        return '<Sensor id={} name={}>'.format(self.id, self.name)


class Reading(db.Model):
    __tablename__ = 'readings'
    __table_args__ = (
        db.UniqueConstraint(
            'sensor_id', 'timestamp',
            name='sensor_id_timestamp_unq'
        ),
        db.CheckConstraint(
            'humidity >= 0 AND humidity <= 100',
            name='humidity_between_0_and_100',
        ),
        db.CheckConstraint(
            'resistance >= 0',
            name='resistance_must_be_positive',
        ),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sensor_id = db.Column(db.Integer, db.ForeignKey('sensors.id'), nullable=False)
    timestamp = db.Column(db.DateTime, index=True, nullable=False)
    int_temp = db.Column(db.Float, nullable=False, server_default='0.0')
    ext_temp = db.Column(db.Float, nullable=False, index=True)
    humidity = db.Column(db.Float, nullable=False, server_default='0.0')
    resistance = db.Column(db.Float, nullable=False, server_default='0.0')

    def __init__(
            self,
            sensor,
            timestamp=None,
            int_temp=None,
            ext_temp=None,
            humidity=None,
            resistance=None,
    ):
        self.sensor = sensor
        self.timestamp = timestamp
        self.int_temp = int_temp
        self.ext_temp = ext_temp
        self.humidity = humidity
        self.resistance = resistance

    def __repr__(self):
        return '<Reading timestamp={} ext_temp={} humidity={} resistance={}>' \
            .format(
                self.timestamp,
                self.ext_temp,
                self.humidity,
                self.resistance,
            )

    def as_dict(self):
        return dict(
            timestamp=self.timestamp.strftime('%Y-%m-%dT%H:%MZ'),
            int_temp=self.int_temp,
            ext_temp=self.ext_temp,
            humidity=self.humidity,
            resistance=self.resistance,
        )

    def int_temp_f(self):
        return self.int_temp * 9/5 + 32

    def ext_temp_f(self):
        return self.ext_temp * 9/5 + 32

    def luminosity(self):
        if self.resistance > 0:
            return 10**6 / self.resistance
        else:
            return None

    @validates('timestamp')
    @validates_presence
    def validate_timestamp(self, key, value):
        return value

    @validates('ext_temp')
    @validates_presence
    def validate_ext_temp(self, key, value):
        return value

    @validates('humidity')
    @validates_presence
    def validate_humidity(self, key, value):
        try:
            value = float(value)
            if value < 0 or value > 100:
                raise ValueError('humidity must be between 0 and 100')
        except TypeError as e:
            raise ValueError('humidity must be a number') from e
        return value

    @validates('resistance')
    @validates_presence
    def validate_resistance(self, key, value):
        if value < 0:
            raise ValueError('resistance must be greater than or equal to 0')
        return value
