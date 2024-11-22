
import decimal
import json

class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            # Convert decimal instances into strings for JSON compatibility
            return str(obj)
        return super(JSONEncoder, self).default(obj)