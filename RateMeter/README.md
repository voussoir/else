RateMeter
=========

Provides a `RateMeter` class to measure the speed of something. Create an instance with the appropriate `span`, and call `meter.digest(x)` where `x` is the number of units processed. Later, call `meter.report()` to receive the current speed information.