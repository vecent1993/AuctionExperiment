def getHandler(baseexp, type, handler):
    if type == 'player':
        name = '.'.join((baseexp, 'ph'))
    elif type == 'host':
        name = '.'.join((baseexp, 'hh'))
    elif type == 'group':
        name = '.'.join((baseexp, 'gh'))
    else:
        raise Exception('type error: type must be player, host or group')

    try:
        module = __import__(name, globals(), locals(), [handler, ])
    except:
        raise Exception('baseexp error: baseexp not exists')
    return getattr(module, handler)