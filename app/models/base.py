import datetime
import uuid
from app.extensions import db


class BaseModel(db.Model):
    __abstract__ = True

    def to_dict(self):
        result = {}
        for c in self.__table__.columns:
            val = getattr(self, c.name)
            if isinstance(val, uuid.UUID):
                result[c.name] = str(val)
            elif isinstance(val, (datetime.date, datetime.datetime)):
                result[c.name] = val.isoformat()
            else:
                result[c.name] = val
        return result
