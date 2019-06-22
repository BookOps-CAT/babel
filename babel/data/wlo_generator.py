# unique Babel wlo number generator

def wlo_pool(last_wlo_number, quantity):
    """
    unique Babel wlo id generator
    args:
        last_wlo_number: str, format 'wlo0000001'
    yields:
        next_wlo: str, follwoing wlo number in sequence
    """

    if last_wlo_number is None:
        digits = 0
    else:
        if len(last_wlo_number) != 13:
            raise ValueError('invalid wlo number passed')
        digits = int(last_wlo_number[3:])

    for wlo in range(quantity):
        digits += 1
        if digits > 9999999999:
            raise StopIteration('wlo numbers grew too large!')
        digits_as_str = str(digits).zfill(10)

        yield f'wlo{digits_as_str}'
