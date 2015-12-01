# Events retrieval API
def fetchEvents(startTime, endTime, tags):
    from ..app import app
    from ..utils import epoch
    node = None

    for finder in app.store.finders:
        if hasattr(finder, '__fetch_events__'):
            node = finder
            break

    startTime = int(epoch(startTime))
    endTime = int(epoch(endTime))
    r = node.getEvents(startTime, endTime, tags)
    return r

