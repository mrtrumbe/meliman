import unicodedata


def unicode_to_ascii(to_translate):
    return unicodedata.normalize('NFKD', unicode(to_translate)).encode('ascii', 'ignore')


# returns a tuple (file, extension)
def split_file_name(file):
    last_dot_location = file.rfind('.')

    to_return = (file, '')
    if last_dot_location > 0:
        to_return = (file[0:last_dot_location], file[last_dot_location+1: len(file)])

    return to_return


def strip_extension(file):
    return split_file_name(file)[0]


