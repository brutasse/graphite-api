# Events retrieval API
def fetchEvents(startTime, endTime, tags):
    from ..app import app
    node = None

    for finder in app.store.finders:
        if hasattr(finder, '__fetch_events__'):
            node = finder
            break

    return node.getEvents(startTime, endTime, tags)

