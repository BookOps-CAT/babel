from datetime import date


def create_blanketPO(vendor_codes=[], sequence=0):
    if vendor_codes:
        if type(vendor_codes) is not list:
            raise TypeError(
                'vendor_codes param must be a list')

        date_today = date.strftime(date.today(), '%Y%m%d')
        codes = '-'.join(vendor_codes)
        return f'{codes}-{date_today}-{sequence}'
