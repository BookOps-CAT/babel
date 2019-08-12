# Used by pyinstaller to expose hidden imports
# works only for keyring < 12.0.0

import entrypoints


hiddenimports = [
    ep.module_name
    for ep in entrypoints.get_group_all('keyring.backends')
]
