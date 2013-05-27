def uni_convert(input):
    """Convert unicode input to utf-8

    Arguments:
    ----------
    input - the unicode input to convert
    """
    if isinstance(input, dict):
        ret = {}
        for k, v in input.iteritems():
            ret[uni_convert(k)] = uni_convert(v)
        return ret
    elif isinstance(input, list):
        return [uni_convert(element) for element in input]
    elif isinstance(input, unicode):
        return input.encode('utf-8')
    else:
        return input

def md5sum(filename, n_blocks=128):
    import hashlib
    md5 = hashlib.md5()
    with open(filename,'rb') as f:
        for chunk in iter(lambda: f.read(n_blocks*md5.block_size), b''):
            md5.update(chunk)
    return md5.hexdigest()

