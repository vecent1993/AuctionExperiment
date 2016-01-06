# -*- coding: utf-8 -*-
import traceback

def get_handler(type, handler):
    if type == 'player':
        name = '.'.join(('playerhandler', handler))
    elif type == 'host':
        name = '.'.join(('hosthandler', handler))
    elif type == 'group':
        name = '.'.join(('grouphandler', handler))
    elif type == 'train':
        name = '.'.join(('trainhandler', handler))
    else:
        raise Exception('type error: type must be player, host or group')

    try:
        module = __import__(name, globals(), locals(), [handler, ])
    except:
        print traceback.format_exc()
    return getattr(module, handler)