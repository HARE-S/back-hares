"""Campos Marshmallow tolerantes para el contrato de la API.

Los servicios serializan fechas como string ISO (BaseModel.to_dict → isoformat),
pero algunos flujos devuelven el objeto date original. Estos campos aceptan ambos
en serialización para no romper la respuesta de los endpoints.
"""

import datetime

from marshmallow import fields


class DateOrString(fields.Date):
    """Serializa objetos date y strings ISO por igual."""

    def _serialize(self, value, attr, obj, **kwargs):
        if isinstance(value, str):
            return value
        if isinstance(value, datetime.date) and not isinstance(value, datetime.datetime):
            return value.isoformat()
        if isinstance(value, datetime.datetime):
            return value.date().isoformat()
        return super()._serialize(value, attr, obj, **kwargs)


class DateTimeOrString(fields.DateTime):
    """Serializa objetos datetime y strings ISO por igual."""

    def _serialize(self, value, attr, obj, **kwargs):
        if isinstance(value, str):
            return value
        return super()._serialize(value, attr, obj, **kwargs)