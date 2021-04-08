from dataclasses import field
from datetime import datetime

from marshmallow import fields


def datetime_field():
    return field(
        default_factory=datetime.utcnow,
        metadata={'dataclasses_json': {
            'encoder': datetime.isoformat,
            'decoder': datetime.fromisoformat,
            'mm_field': fields.DateTime(format='iso')
        }})
