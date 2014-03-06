import json


class JSONEncoder(json.JSONEncoder):
    """
    JSONEncoder subclass that knows how to encode generators.
    """
    def default(self, o):
        if hasattr(o, 'tolist'):
            return o.tolist()
        elif hasattr(o, '__getitem__'):
            try:
                return dict(o)
            except:
                pass
        elif hasattr(o, '__iter__'):
            return [i for i in o]
        return super(JSONEncoder, self).default(o)
