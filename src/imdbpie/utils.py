# -*- coding: utf-8 -*-


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
