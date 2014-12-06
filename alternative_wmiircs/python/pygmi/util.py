from functools import partial, update_wrapper, wraps
import os
from os.path import join, sep
import signal
import subprocess

import pygmi

__all__ = ('call', 'message', 'program_list', 'curry', 'find_script', '_',
           'prop', 'find')

def _():
    pass

def call(*args, **kwargs):
    background = kwargs.pop('background', False)
    input = kwargs.pop('input', None)
    if not background:
        p = subprocess.Popen(args, stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                cwd=os.environ['HOME'], close_fds=True, **kwargs)
        return p.communicate(input)[0].rstrip('\n')
    return subprocess.Popen(args, cwd=os.environ['HOME'],
            close_fds=True, **kwargs)

def message(message):
    args = ['xmessage', '-file', '-'];
    font = pygmi.wmii['font']
    if not font.startswith('xft:'):
        args += ['-fn', font.split(',')[0]]
    call(*args, input=message)

def program_list(path):
    names = set()
    for d in path:
        try:
            for f in os.listdir(d):
                p = '%s/%s' % (d, f)
                if (f not in names and os.access(p, os.X_OK) and
                    os.path.isfile(p)):
                    names.add(f)
        except Exception:
            pass
    return sorted(names)

def curry(func, *args, **kwargs):
    if _ in args:
        blank = [i for i in range(0, len(args)) if args[i] is _]
        @wraps(func)
        def curried(*newargs, **newkwargs):
            ary = list(args)
            for k, v in zip(blank, newargs):
                ary[k] = v
            ary = tuple(ary) + newargs[len(blank):]
            return func(*ary, **dict(kwargs, **newkwargs))
    else:
        curried = update_wrapper(partial(func, *args, **kwargs), func)
    curried.__name__ += '__curried__'
    return curried

def find_script(name):
    for path in pygmi.confpath:
        if os.access('%s/%s' % (path, name), os.X_OK):
            return '%s/%s' % (path, name)

def prop(**kwargs):
    def prop_(wrapped):
        kwargs['fget'] = wrapped
        return property(**kwargs)
    return prop_

def find(path, target, depth=-1, followlinks=False):
    if hasattr(target, 'search'):
        def _re_check(files):
            for f in files:
                if target.search(f): return f
        check = _re_check
    else:
        def _fixed_check(files):
            if target in files: return target
        check = _fixed_check
    initial_depth = len(path)
    for root, dirs, files in os.walk(path, followlinks=followlinks):
        f = check(files)
        if f:
            return join(root, f)
        if root[initial_depth:].count(sep) == depth:
            dirs[:] = []
    return None

# vim:se sts=4 sw=4 et:
