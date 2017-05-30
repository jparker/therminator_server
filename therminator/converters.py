from datetime import datetime
import re
import uuid
from werkzeug.routing import BaseConverter, ValidationError

class DateConverter(BaseConverter):
    def to_python(self, value):
        try:
            return datetime.strptime(value, '%Y-%m-%d').date()
        except ValueError as e:
            raise ValidationError from e

    def to_url(self, value):
        return value.isoformat()

class UUIDConverter(BaseConverter):
    def to_python(self, value):
        try:
            uuid.UUID(value)
        except ValueError as e:
            raise ValidationError from e
        return value

    def to_url(self, value):
        return str(value)
