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

def file_stats(path, human_readable=False):
    import os
    md5 = md5sum(path)
    size = os.path.getsize(path)
    if human_readable:
        size = sizeof_fmt(size)
    return (md5,size)

def md5sum(filename, n_blocks=128):
    import hashlib
    md5 = hashlib.md5()
    with open(filename,'rb') as f:
        for chunk in iter(lambda: f.read(n_blocks*md5.block_size), b''):
            md5.update(chunk)
    return md5.hexdigest()

from math import log
unit_list = zip(['bytes', 'kB', 'MB', 'GB', 'TB', 'PB'], [0, 0, 1, 2, 2, 2])
def sizeof_fmt(num):
    """Human friendly file size"""
    if num > 1:
        exponent = min(int(log(num, 1024)), len(unit_list) - 1)
        quotient = float(num) / 1024**exponent
        unit, num_decimals = unit_list[exponent]
        format_string = '{:.%sf}{}' % (num_decimals)
        return format_string.format(quotient, unit)
    if num == 0:
        return '0 bytes'
    if num == 1:
        return '1 byte'
