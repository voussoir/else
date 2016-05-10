import time


class Ratelimiter:
    def __init__(self, allowance_per_period, period, operation_cost=1, mode='sleep'):
        '''
        allowance_per_period:
            The number of operations we can perform per `period` seconds.

        period:
            The number of seconds over which we can perform `allowance_per_period` operations.

        operation_cost:
            The default amount to remove from our balance after each operation.
            Pass a `cost` parameter to `self.limit` to use a nondefault value.

        mode:
            'sleep':  If we do not have the balance for an operation, sleep until we do.
                      Return True every time.
            'reject': If we do not have the balance for an operation, return False.
        '''
        if mode not in ('sleep', 'reject'):
            raise ValueError('Invalid mode %s' % repr(mode))
        self.allowance_per_period = allowance_per_period
        self.period = period
        self.operation_cost = operation_cost
        self.mode = mode

        self.last_operation = time.time()
        self.balance = 0
        self.gain_rate = allowance_per_period / period

    def limit(self, cost=None):
        if cost is None:
            cost = self.operation_cost
        timediff = time.time() - self.last_operation
        self.balance += timediff * self.gain_rate
        self.balance = min(self.balance, self.allowance_per_period)
        successful = False

        deficit = cost - self.balance
        if deficit > 0 and self.mode == 'sleep':
            time_needed = (deficit / self.gain_rate)
            #print(self.balance, deficit, 'Need to sleep %f' % time_needed)
            time.sleep(time_needed)
            self.balance = cost

        #print(self.balance)
        if self.balance >= cost:
            #print('pass')
            self.balance -= cost
            successful = True

        self.last_operation = time.time()

        return successful
