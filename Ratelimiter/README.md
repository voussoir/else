Ratelimiter
===========

Provides a `Ratelimiter` class to regulate timing. Create an instance with the appropriate allowance and timing rules, then just call `limiter.limit()` in your loop.

Note that allowance=10, period=10 is not the same as allowance=1, period=1. The first allows for more "burstiness" because all 10 operations can happen in the first second, as long as you wait for the other 9.