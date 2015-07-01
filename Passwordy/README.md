Passwordy
======

Generates randomized strings, useful for making passwords and such.

     ---------------------------------------------------------------
    |Generates a randomized password.                               |
    |                                                               |
    |> passwordy [length] ["p"] ["d"]                               |
    |                                                               |
    |   length : How many characters. Default 032.                  |
    |   p      : If present, the password will contain punctuation  |
    |            characters. Otherwise not.                         |
    |   d      : If present, the password will contain digits.      |
    |            Otherwise not.                                     |
    |                                                               |
    |   The password can always contain upper and lowercase         |
    |   letters.                                                    |
     ---------------------------------------------------------------
     ---------------------------------------------------------------
    |Generates a randomized sentence                                |
    |                                                               |
    |> passwordy sent [length] [join]                               |
    |                                                               |
    |   length : How many words to retrieve. Default 005.           |
    |   join   : The character that will join the words together.   |
    |            Default space.                                     |
     ---------------------------------------------------------------


To use the `sentence` function, you can download [this dictionary](https://github.com/voussoir/else/tree/master/Dictionary)