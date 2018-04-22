def bounded_int(minX, maxX, **kwargs):
    return {
        'type': 'integer',
        'min': minX,
        'max': maxX,
        **kwargs
    }


def delay(**kwargs):
    return bounded_int(1, 30, default=10, **kwargs)


def cost(**kwargs):
    return bounded_int(1, 30, default=10, **kwargs)


def percentage(minX=0, **kwargs):
    return bounded_int(minX, 100, default=minX, **kwargs)


def strkey_dict(**kwargs):
    prop = {
        'type': 'dict',
        'keyschema': {
            'type': 'string',
            'empty': False,
        },
    }
    if 'required' not in kwargs and 'default' not in kwargs:
        prop['default_setter'] = lambda doc: {},
    prop.update(kwargs)
    return prop

