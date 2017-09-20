# temporary patches for location changes, etc.


def mm_patch(locations):
    """
    changes location codes for MM to temporary location codes
    """
    replacements = {
        'mma0f': 'mm1af',
        'mma0n': 'mm2an',
        'mma5l': 'mm2al',
        'mmy0f': 'mm2yf',
        'mmy0n': 'mm2yn',
        'mma0v': 'mm3av',
        'mmy0v': 'mm3yv'
    }
    for key, value in replacements.iteritems():
        if key in locations:
            locations = locations.replace(key, value)
    return locations
