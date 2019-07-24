from datetime import date


def create_blanketPO(vendor_codes=[], sequence=0):
    if vendor_codes:
        if type(vendor_codes) is not list:
            raise TypeError(
                'vendor_codes param must be a list')

        date_today = date.strftime(date.today(), '%Y%m%d')
        if len(vendor_codes) > 1:
            code = 'multi-vendor'
        else:
            code = vendor_codes[0]
        return f'{code}-{date_today}-{sequence}'
