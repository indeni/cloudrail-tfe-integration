def recover_from_dict(cls):
    if hasattr(cls, '_from_dict'):
        setattr(cls, 'from_dict', getattr(cls, '_from_dict'))
    return cls
