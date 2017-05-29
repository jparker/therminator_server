from . import app, db, bcrypt
from flask_login import UserMixin
from sqlalchemy.orm import validates

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

    def __init__(self, name, email, password):
        self.name = name
        self.email = email
        self.password = password

    def __repr__(self):
        return '<User id={} email={}>'.format(self.id, self.email)

    def is_correct_password(self, plaintext):
        return bcrypt.check_password_hash(self.password, plaintext)

    @validates('name')
    def validates_name(self, key, value):
        if not value:
            raise ValueError("name can't be blank")
        return value

    @validates('password')
    def validates_password(self, key, value):
        return bcrypt.generate_password_hash(
            value,
            app.config['BCRYPT_LOG_ROUNDS'],
        ).decode()
