Generators
==========


# What are they

Generators are a type of iterable that create their contents on-the-fly. Unlike a list, whose entire contents are available before beginning any loops or manipulations, generators don't know how many items they will produce or when they will stop. They can even go on forever.

&nbsp;

# Writing one

Writing a generator looks like writing a function, but instead of `return`, you use `yield`. The object which is yielded is what you'll get when you do a loop over the generator. This one lets you count to a billion:

    def billion():
        x = 0
        while x < 1000000000:
            yield x
            x += 1

Note that, unlike a `return` statement, you can include more code after a `yield` statement. Also notice that generators keep track of their internal state -- the `billion` generator has an `x` that it increments every time you loop over it. You can imagine the code pausing after the `yield` line, and resuming when you come back for the next cycle. Try this with some extra print statements to help visualize.

Generators can also take arguments. Here's a generator that counts to a custom amount:

    def count_to(y):
        x = 0
        while x < y:
            yield x
            x += 1


&nbsp;

# Using one

Although generators look like functions when you're writing them, they feel more like objects when using them. Remember that generators don't calculate their contents until they are actually used in a loop, so simply doing:

    numbers = count_to(100)

does **not** create a list of 100 numbers. It creates a new instance of the generator that is ready to be iterated over, like this:

    numbers = count_to(100)
    for number in numbers:
        print(number)

or this:

    for number in count_to(100):
        print(number)

This should remind you of:

    for number in range(100):
        print(number)

because the `range` class behaves a lot like a generator ([but not exactly](http://stackoverflow.com/a/13092317)).


Generators are excellent for cases where using a list is infeasible or unnecessary. In order to loop over a list, you have to generate the entire thing first. If you're only going to use each item once, storing the entire list can be a big memory waste when a generator could take its place. With a generator, the items are created, used, and trashed, so memory can be recycled.

Since generators can go on forever, they're great for abstracting out ugly `while` loops, so you can get down to business faster.

To get a single item from a generator without looping, use `next(generator)`.

&nbsp;

# StopIteration

Generators pause and resume a lot, but they still flow like normal functions. As long as there is no endless `while` loop inside, they'll come to an end at some point. When a generator is all finished, it will raise a `StopIteration` exception every time you try to do `next()`. Luckily, `for` loops will detect this automatically and stop themselves.

Earlier, I said that generators use `yield` instead of `return`, but in fact you can include a return statement. If it is encountered, it will raise a `StopIteration`, and the generator will not resume even if there is more code.

    >>> def generator():
    ...     yield 1
    ...     return 2
    ...     yield 3
    ...
    >>>
    >>> g = generator()
    >>> next(g)
    1
    >>> next(g)
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
    StopIteration: 2
    >>> next(g)
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
    StopIteration
    >>>

In general, I don't like to use `return` in generators. I prefer to `break` from their internal loops and conclude naturally.

&nbsp;

# Minor notes

- You cannot access the items of a generator by index, because only one item exists at a time. Once you do a loop over a generator, those items are gone forever unless you kept them somewhere else.

&nbsp;


# More examples

#### Yielding individual items from batches

Suppose you're getting data from an imaginary website which sends you items in groups of 100. You want to let the user loop over every item without having to worry about the groups themselves.

    def item_generator(url):
        page = 0
        while True:
            # get_items is a pretend method that collects the 100 items from that page
            batch = get_items(url, page=page)

            if len(batch) == 0:
                # for this imaginary website, the batch will be empty when that page
                # doesn't have any items on it.
                break

            for item in batch:
                # by yielding individual items, the user can just do a for loop
                # over this generator and get them all one by one.
                yield item

            page += 1

        # When the while loop breaks, we reach the end of the function body,
        # concluding the generator.

    comments = item_generator('http://website.com/user/voussoir/comments')
    for comment in comments:
        print(comment.body)

&nbsp;

#### Sqlite3 fetch generator

This is one that I almost always include in my program when I'm doing lots of sqlite work. Sqlite cursors don't allow you to simply do a for-loop over the results of a SELECT, so this generator is very handy:

    def fetch_generator(cur):
        while True:
            item = cur.fetchone()
            if item is None:
                break
            yield item

    cur.execute('SELECT * FROM table')
    for item in fetch_generator(cur):
        print(item)

&nbsp;

# Further reading

[Stack Overflow - What are the main uses for `yield from`?](http://stackoverflow.com/questions/9708902/in-practice-what-are-the-main-uses-for-the-new-yield-from-syntax-in-python-3) -- If you like recursive functions, how about recursive generators? The only time I've ever used this is to [iterate over a tree's nodes](https://github.com/voussoir/reddit/blob/2069c3bd731cc8f90401ee49a9fc4d0dbf436cfc/Prawtimestamps/timesearch.py#L756-L761).

[Stack Overflow - Python generator `send` function purpose?](http://stackoverflow.com/questions/19302530/python-generator-send-function-purpose) -- This quickly dives out of "quick tips" territory.