Bytestring
==========

Given an integer number of bytes, return a string that best represents it:

    >>> import bytestring
    >>> bytestring.bytestring(1)
    '1.000 b'
    >>> bytestring.bytestring(100)
    '100.000 b'
    >>> bytestring.bytestring(1024)
    '1.000 KiB'
    >>> bytestring.bytestring(2 ** 10)
    '1.000 KiB'
    >>> bytestring.bytestring(2 ** 20)
    '1.000 MiB'
    >>> bytestring.bytestring(2 ** 30)
    '1.000 GiB'
    >>> bytestring.bytestring(2 ** 40)
    '1.000 TiB'
    >>> bytestring.bytestring(123456789)
    '117.738 MiB'
    >>> bytestring.bytestring(753429186)
    '718.526 MiB'
    >>> bytestring.bytestring(7534291860)
    '7.017 GiB'
    >>> bytestring.bytestring(75342918600)
    '70.169 GiB'

Given a string, return the number of bytes it represents:

    >>> bytestring.parsebytes('100')
    100.0
    >>> bytestring.parsebytes('1k')
    1024.0
    >>> bytestring.parsebytes('1kb')
    1024.0
    >>> bytestring.parsebytes('1kib')
    1024.0
    >>> bytestring.parsebytes('200 mib')
    209715200.0
    >>> bytestring.parsebytes('2 GB')
    2147483648.0
    >>> bytestring.parsebytes('0.5 GIB')
    536870912.0
    >>> bytestring.parsebytes('512M')
    536870912.0
    >>> bytestring.parsebytes('99 Y')
    1.1968365614184829e+26