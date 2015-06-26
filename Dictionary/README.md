Dictionary
=======

I made this so that I could more easily acess a list of words. Previousy I had to open() a text file each time. Now, I can:

    import dictionary.common as common
    import random

    print(random.choice(common.words))