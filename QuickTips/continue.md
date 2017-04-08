Continue
========

Skips the rest of the current iteration, and starts the next one.


```Python
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
```

```Python
while len(directory_queue) > 0:
    directory = directory_queue.popleft()
    try:
        filenames = os.listdir(directory)
    except PermissionError:
        continue

    for filename in filenames:
        ...
```


#### Continue is great for cleaning code with lots of conditions:

##### Without continue:

Nested:

```Python
for submission in submissions:
    if submission.author is not None:
        if not submission.over_18:
            if 'suggestion' in submission.title.lower():
                print('Found:', submission.id)
```

or all grouped up:

```Python
for submission in submissions:
    if (
        submission.author is not None
        and not submission.over_18
        and 'suggestion' in submission.title.lower()
    ):
        print('Found:', submission.id)
```



##### With continue:

```Python
for submission in submissions:
    if submission.author is None:
        continue

    if submission.over_18:
        continue

    if 'suggestion' not in submission.title.lower():
        continue

    print('Found:', submission.id)
```
        
Notice that all of the checks are the opposite of the originals. The mentality changes from "keep only the items with the right properties" to "discard the items with the wrong properties", and the result is the same.
