import os


def realpath(path):
    return os.path.abspath(os.path.realpath(path))


def join(*components):
    if any((isinstance(p, bytes) for p in components)):
        return os.path.join(*[
            p if isinstance(p, bytes) else p.encode('ascii')
            for p in components
        ])
    else:
        return os.path.join(*components)
