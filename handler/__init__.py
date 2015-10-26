# -*- coding: utf-8 -*-
import traceback

def getHandler(type, handler):
    if type == 'player':
        name = '.'.join(('playerhandler_', handler))
    elif type == 'host':
        name = '.'.join(('hosthandler_', handler))
    elif type == 'group':
        name = '.'.join(('grouphandler_', handler))
    else:
        raise Exception('type error: type must be player, host or group')

    try:
        module = __import__(name, globals(), locals(), [handler, ])
    except:
        print traceback.format_exc()
    return getattr(module, handler)