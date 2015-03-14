# -*- coding: utf-8 -*-

try:
    from urllib.parse import urlencode
    import html.parser as htmlparser
except ImportError:
    from urllib import urlencode
    import HTMLParser as htmlparser


def try_get_unicode(st):
    if isinstance(st, str):
        try:
            st = st.decode('utf-8')
        except:
            st = st.decode('iso-8859-1')
    return st


def dict_to_str(query_params):
    # convert from unicode
    query_params = dict(
        (k, v.encode('utf-8') if isinstance(v, basestring) else v)
        for k, v in query_params.items())
    return query_params


def dict_unescape(data):
    if not isinstance(data, dict):
        return data
    result = {}
    for k in data:
        if isinstance(data[k], basestring):
            data[k] = htmlparser.HTMLParser().unescape(data[k])
        elif isinstance(data[k], dict):
            data[k] = dict_unescape(data[k])
    return data
