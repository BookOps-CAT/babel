"""
Datastore table values that are inserted during database setup
"""


SYSTEM = [
    (1, 'BPL'),
    (2, 'NYP')
]

LIBRARY = [
    (1, 'branches'),
    (2, 'research'),
]

AUDN = [
    ('j', 'juvenile'),
    ('y', 'young adult'),
    ('a', 'adult')
]

LANG = [
    ('ara', 'Arabic'),
    ('ben', 'Bengali'),
    ('chi', 'Chinese'),
    ('eng', 'English'),
    ('fre', 'French'),
    ('ger', 'German'),
    ('heb', 'Hebrew'),
    ('hin', 'Hindi'),
    ('hun', 'Hungarian'),
    ('ita', 'Italian'),
    ('jpn', 'Japanese'),
    ('kor', 'Korean'),
    ('pan', 'Panjabi'),
    ('pol', 'Polish'),
    ('por', 'Portuguese'),
    ('rus', 'Russian'),
    ('san', 'Sanskrit'),
    ('spa', 'Spanish'),
    ('ukr', 'Ukrainian'),
    ('und', 'Undetermined'),
    ('urd', 'Urdu'),
    ('yid', 'Yiddish'),
    ('zxx', 'No linguistic content'),
    ('hat', 'Haitian French Creole'),
    ('alb', 'Albanian')
]

BRANCH = [
    (1, '02', "Central Juv Children's Room"),
    (1, '03', "Central YA Young Teens"),
    (1, '04', "Central BKLYN Collection"),
    (1, '11', "Central AMMS Art & Music"),
    (1, '12', "Central Pop Audiovisual (Multimedia)"),
    (1, '13', "Central HBR (Hist/Biog/Rel)"),
    (1, '14', "Central Literature & Languages"),
    (1, '16', "Central SST"),
    (1, '21', "Arlington"),
    (1, '22', "Bedford"),
    (1, '23', "Business Library"),
    (1, '24', "Brighton Beach"),
    (1, '25', "Borough Park"),
    (1, '26', "Stone Avenue"),
    (1, '27', "Brownsville"),
    (1, '28', "Bay Ridge"),
    (1, '29', "Bushwick"),
    (1, '30', "Crown Heights"),
    (1, '31', "Carroll Gardens"),
    (1, '32', "Coney Island"),
    (1, '33', "Clarendon"),
    (1, '34', "Canarsie"),
    (1, '35', "DeKalb"),
    (1, '36', "East Flatbush"),
    (1, '37', "Eastern Parkway"),
    (1, '38', "Flatbush"),
    (1, '39', "Flatlands"),
    (1, '40', "Fort Hamilton"),
    (1, '41', "Greenpoint"),
    (1, '42', "Highlawn"),
    (1, '43', "Kensington"),
    (1, '44', "Kings Bay"),
    (1, '45', "Kings Highway"),
    (1, '46', "Leonard"),
    (1, '47', "Macon"),
    (1, '48', "Midwood"),
    (1, '49', "Mapleton"),
    (1, '50', "Brooklyn Heights"),
    (1, '51', "New Utrecht"),
    (1, '52', "New Lots"),
    (1, '53', "Park Slope"),
    (1, '54', "Rugby"),
    (1, '55', "Sunset Park"),
    (1, '56', "Sheepshead Bay"),
    (1, '57', "Saratoga"),
    (1, '59', "Marcy"),
    (1, '60', "Williamsburgh"),
    (1, '61', "Washington Irving"),
    (1, '62', "Walt Whitman"),
    (1, '63', "Kidsmobile"),
    (1, '64', "BiblioBus"),
    (1, '65', "Cypress Hills"),
    (1, '66', "Gerritsen Beach"),
    (1, '67', "McKinley Park"),
    (1, '68', "Mill Basin"),
    (1, '69', "Pacific"),
    (1, '70', "Red Hook"),
    (1, '71', "Ulmer Park"),
    (1, '72', "Bookmobile"),
    (1, '74', "Gravesend"),
    (1, '76', "Homecrest"),
    (1, '77', "Windsor Terrace"),
    (1, '78', "Paerdegat"),
    (1, '79', "Brower Park"),
    (1, '80', "Ryder"),
    (1, '81', "Jamaica Bay"),
    (1, '82', "Dyker"),
    (1, '83', "Clinton Hill"),
    (1, '85', "Spring Creek"),
    (1, '87', "Cortelyou"),
    (1, '89', "BookOps"),
    (1, '90', "Service to the Aging SAGE/SOA"),
    (1, '94', "Central Literacy"),
    (2, 'ag', "Aguilar"),
    (2, 'al', "Allerton"),
    (2, 'ba', "Baychester"),
    (2, 'bc', "Bronx Library Center"),
    (2, 'be', "Belmont"),
    (2, 'bl', "Bloomingdale"),
    (2, 'br', "George Bruce"),
    (2, 'bt', "Battery Park"),
    (2, 'ca', "Cathedral, T. C. Cooke"),
    (2, 'cc', "SASB Children's Center"),
    (2, 'ch', "Chatham Square"),
    (2, 'ci', "City Island"),
    (2, 'cl', "Morningside Heights"),
    (2, 'cp', "Clason's Point"),
    (2, 'cs', "Columbus"),
    (2, 'ct', "Castle Hill"),
    (2, 'dh', "Dongan Hills"),
    (2, 'dy', "Spuyten Duyvil"),
    (2, 'ea', "Eastchester"),
    (2, 'ep', "Epiphany"),
    (2, 'ew', "Edenwald"),
    (2, 'fe', "58th Street"),
    (2, 'fw', "Fort Washington"),
    (2, 'fx', "Francis Martin"),
    (2, 'gc', "Grand Central"),
    (2, 'gd', "Grand Concourse"),
    (2, 'gk', "Great Kills"),
    (2, 'hb', "High Bridge"),
    (2, 'hd', "125th Street"),
    (2, 'hf', "Hamilton Fish Park"),
    (2, 'hg', "Hamilton Grange"),
    (2, 'hk', "Huguenot Park"),
    (2, 'hl', "Harlem"),
    (2, 'hp', "Hudson Park"),
    (2, 'hs', "Hunt's Point"),
    (2, 'ht', "Countee Cullen"),
    (2, 'hu', "115th Street (temp)"),
    (2, 'in', "Inwood"),
    (2, 'jm', "Jefferson Market"),
    (2, 'jp', "Jerome Park"),
    (2, 'kb', "Kingsbridge"),
    (2, 'kp', "Kips Bay"),
    (2, 'lb', "Andrew Heiskell"),
    (2, 'lm', "New Amsterdam"),
    (2, 'ma', "S.A. Schwarzman Bldg."),
    (2, 'mb', "Macomb's Bridge"),
    (2, 'me', "Melrose"),
    (2, 'mh', "Mott Haven"),
    (2, 'ml', "Mulberry Street"),
    (2, 'mm', "Mid-Manhattan"),
    (2, 'mn', "Mariner's Harbor"),
    (2, 'mo', "Mosholu"),
    (2, 'mp', "Morris Park"),
    (2, 'mr', "Morrisania"),
    (2, 'mu', "Muhlenberg"),
    (2, 'my', "Performing Arts"),
    (2, 'nb', "West New Brighton"),
    (2, 'nd', "New Dorp"),
    (2, 'ns', "96th Street"),
    (2, 'ot', "Ottendorfer"),
    (2, 'pk', "Parkchester"),
    (2, 'pm', "Pelham Bay"),
    (2, 'pr', "Port Richmond"),
    (2, 'rd', "Riverdale"),
    (2, 'ri', "Roosevelt Island"),
    (2, 'rs', "Riverside"),
    (2, 'rt', "Richmondtown"),
    (2, 'sa', "St. Agnes"),
    (2, 'sb', "South Beach"),
    (2, 'sc', "Schomburg"),
    (2, 'sd', "Sedgwick"),
    (2, 'se', "Seward Park"),
    (2, 'sg', "St. George Library Center"),
    (2, 'sl', "Science, Industry & Business"),
    (2, 'ss', "67th Street"),
    (2, 'st', "Stapleton"),
    (2, 'sv', "Soundview"),
    (2, 'tg', "Throg's Neck"),
    (2, 'th', "Todt Hill-Westerleigh"),
    (2, 'tm', "Tremont"),
    (2, 'ts', "Tompkins Square"),
    (2, 'tv', "Tottenville"),
    (2, 'vc', "Van Cortlandt"),
    (2, 'vn', "Van Nest"),
    (2, 'wb', "Webster"),
    (2, 'wf', "West Farms"),
    (2, 'wh', "Washington Heights"),
    (2, 'wk', "Wakefield"),
    (2, 'wl', "Woodlawn Heights"),
    (2, 'wo', "Woodstock"),
    (2, 'wt', "Westchester Square"),
    (2, 'yv', "Yorkville"),
    (2, 'ft', "53rd Street"),
    (2, 'ls', "Library Services Center")
]

MATERIAL = [
    ('print', ('BPL', 'a', 'b'), ('NYPL', 'a', 'b')),
    ('dvd', ('BPL', 'h', 'a'), ('NYPL', 'v', 'v')),
    ('audiobook', ('BPL', 'i', 'i'), ('NYPL', 'u', 'i')),
    ('music CD', ('BPL', 'j', 'z'), ('NYPL', 'y', 'w')),
    ('graphic novel', ('BPL', 'a', 'g'), ('NYPL', 'a', 'b')),
    ('board book', ('BPL', 'a', 'd'), ('NYPL', 'a', 'b'))
]


USERS = [
    ('generic', ('BPL', '-'), ('NYPL', '-'))
]

STATUS = [
    (1, 'in-works'),  # add background color value?
    (2, 'finalized'),
    (3, 'on-hold'),
    (4, 'archived')]
