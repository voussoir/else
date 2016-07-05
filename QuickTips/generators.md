Generators
==========


# What are they

Generators are a type of iterable that create their contents on-the-fly. Unlike a list, whose entire contents are available before beginning any loops or manipulations, generators don't know how many items they will produce or when they will stop.


# Writing one

Writing a generator looks like writing a function, but instead of `return`, you use `yield`. The object which is yielded is what you'll get when you do a loop over the generator. This generator lets you count to a billion:

    def billion():
        x = 0
        while x < 1000000000:
            yield x
            x += 1

Note that, unlike a `return` statement, you can include more code after a `yield` statement. Also notice that generators keep track of their internal state. The `billion` generator has an `x` that it increments every time you loop over it.


# Using one

Although generators look like a function when you're writing them, they feel more like objects when using them. Remember that generators don't calculate their contents until they are actually used in a loop, so simply doing:

    numbers = billion()

does **not** create a list of a billion numbers. It creates a new instance of the generator that is ready to be iterated over, like this:

    numbers = billion()
    for number in numbers:
        print(number)

This might remind you of:

    for number in range(1000000000):
        print(number)

because `range` is simply a generator.


Generators are excellent for cases where using a list is infeasible or unnecessary. If you wanted to count to a billion using a list, you would first have to create a list of every number, which is a huge waste of time and memory. With a generator, the item is created, used, and trashed.

To get a single item from a generator without looping, use `next(generator)`.


# StopIteration

When a generator is all finished, it will raise a `StopIteration` exception every time you try to do `next()`. `for` loops will detect this automatically and stop themselves.


# More examples

Suppose you're getting data from an imaginary website which sends you items in groups of 100. You want to let the user loop over every item without having to worry about the groups themselves.

    def item_generator(url):
        page = 0
        while True:
            # get_items is a pretend method that collects the 100 items from that page
            batch = get_items(url, page=page)

            if not batch:
                # for this imaginary website, the batch will be empty when that page
                # doesn't have any items on it.
                break

            for item in batch:
                # by yielding individual items, the user can just do a for loop
                # over this generator and get them all one by one.
                yield item

            page += 1

        # When the while loop breaks, we reach the end of the function body,
        # and a StopIteration will be raised and handled automatically,
        # ending the for-loop.

    comments = item_generator('http://website.com/user/voussoir/comments')
    for comment in comments:
        print(comment.body)
