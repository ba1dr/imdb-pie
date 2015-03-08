# -*- coding: utf-8 -*-


def try_get_unicode(st):
    if isinstance(st, str):
        try:
            st = st.decode('utf-8')
        except:
            st = st.decode('iso-8859-1')
    return st
