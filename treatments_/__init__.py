# -*- coding: utf-8 -*-
import traceback

def getTreatment(code):
    try:
        module = __import__(code, globals(), locals(), [code, ])
    except:
        print traceback.format_exc()
    return getattr(module, code)