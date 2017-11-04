def bind_properties(properties, callback):
    """ Bind multiple properties to a callback.

    `properties`: a list of tuples indicating the objects and their properties
    to bind. The first element of each tuple is an EventDispatcher instance. The
    remaining elements of the tuple are the names of the properties of that
    EventDispatcher to bind.

    `callback`: a function that will be called whenever any of the properties
    change. The EventDispatchers will be passed as positional arguments.
    """
    dispatchers = [p[0] for p in properties]

    def bound_callback(*args):
        callback(*dispatchers)

    for p in properties:
        dispatcher, prop_names = p[0], p[1:]
        for prop_name in prop_names:
            dispatcher.bind(**{prop_name: bound_callback})
