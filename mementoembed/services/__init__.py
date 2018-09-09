
def extract_urim_from_request_path(fullpath, endpoint_stem):

    urim = fullpath[len(endpoint_stem):]
    urim = urim[:-1] if urim[-1] == '?' else urim

    return urim
