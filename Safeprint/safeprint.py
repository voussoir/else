'''
This function is slow and ugly, but I need a way to safely print unicode strings
on systems that don't support it without crippling those who do.
'''
def safeprint(text, file_handle=None):
    for character in text:
        try:
            if file_handle:
                file_handle.write(character)
            else:
                print(character, end='', flush=False)
        except UnicodeError:
            if file_handle:
                file_handle.write('?')
            else:
                print('?', end='', flush=False)
    if not file_handle:
        print()
