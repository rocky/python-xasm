#!/usr/bin/python
"""Greatest Common Divisor

Some characterstics of this program used for testing check_args() does
not have a 'return' statement.

check_args() raises an uncaught exception when given the wrong number
of parameters.

"""
def gcd(a,b):
    """ GCD. We assume positive numbers"""

    # Make: a <= b
    if a > b:
       (a, b) = (b, a)
       pass

    if a <= 0:
        return None
    if a == 1 or a == b:
        return a
    return gcd(b-a, a)

if __name__=='__main__':
    a, b = 3, 5
    print("The GCD of %d and %d is %d" % (a, b, gcd(a, b)))
    pass
