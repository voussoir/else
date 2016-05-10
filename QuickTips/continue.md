Continue
========

Discards the current iteration, and restarts the loop using the next item.


    >>> for x in range(6):
    ...     if x == 3:
    ...             continue
    ...     print(x)
    ...
    0
    1
    2
    4
    5



####Continue is great for cleaning code with lots of conditions:

#####Without continue:


    for submission in submissions:
        if submission.author is not None:
            if submission.over_18 is False:
                if 'suggestion' in submission.title.lower():
                    print('Found:', submission.id)

&nbsp;

    for submission in submissions:
        if submission.author is not None and submission.over_18 is False and 'suggestion' in submission.title.lower():
            print('Found:', submission.id)



#####With continue:

    for submission in submissions:
        if submission.author is None:
            continue
        if submission.over_18:
            continue
        if 'suggestion' not in submission.title.lower():
            continue

        print('Found:', submission.id)
        
The mentality changes from "keep only the items with the right properties" to "discard the items with the wrong properties".