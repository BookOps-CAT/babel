"""
Datastore table values that are inserted during database setup
"""


SYSTEM = [(1, "BPL"), (2, "NYP")]

LIBRARY = [
    (1, "c", "branches"),
    (2, "r", "research"),
]

AUDN = [("j", "juvenile"), ("y", "young adult"), ("a", "adult")]

LANG = [
    ("ara", "Arabic"),
    ("ben", "Bengali"),
    ("chi", "Chinese"),
    ("eng", "English"),
    ("fre", "French"),
    ("ger", "German"),
    ("heb", "Hebrew"),
    ("hin", "Hindi"),
    ("hun", "Hungarian"),
    ("ita", "Italian"),
    ("jpn", "Japanese"),
    ("kor", "Korean"),
    ("pan", "Panjabi"),
    ("pol", "Polish"),
    ("por", "Portuguese"),
    ("rus", "Russian"),
    ("san", "Sanskrit"),
    ("spa", "Spanish"),
    ("ukr", "Ukrainian"),
    ("und", "Undetermined"),
    ("urd", "Urdu"),
    ("yid", "Yiddish"),
    ("zxx", "No linguistic content"),
    ("hat", "Haitian French Creole"),
    ("alb", "Albanian"),
]

# did, code, name, is_research
BRANCH = [
    (1, "02", "Central Juv Children's Room", None),
    (1, "03", "Central YA Young Teens", None),
    (1, "04", "Central BKLYN Collection", None),
    (1, "11", "Central AMMS Art & Music", None),
    (1, "12", "Central Pop Audiovisual (Multimedia)", None),
    (1, "13", "Central HBR (Hist/Biog/Rel)", None),
    (1, "14", "Central Literature & Languages", None),
    (1, "16", "Central SST", None),
    (1, "21", "Arlington", None),
    (1, "22", "Bedford", None),
    (1, "23", "Business Library", None),
    (1, "24", "Brighton Beach", None),
    (1, "25", "Borough Park", None),
    (1, "26", "Stone Avenue", None),
    (1, "27", "Brownsville", None),
    (1, "28", "Bay Ridge", None),
    (1, "29", "Bushwick", None),
    (1, "30", "Crown Heights", None),
    (1, "31", "Carroll Gardens", None),
    (1, "32", "Coney Island", None),
    (1, "33", "Clarendon", None),
    (1, "34", "Canarsie", None),
    (1, "35", "DeKalb", None),
    (1, "36", "East Flatbush", None),
    (1, "37", "Eastern Parkway", None),
    (1, "38", "Flatbush", None),
    (1, "39", "Flatlands", None),
    (1, "40", "Fort Hamilton", None),
    (1, "41", "Greenpoint", None),
    (1, "42", "Highlawn", None),
    (1, "43", "Kensington", None),
    (1, "44", "Kings Bay", None),
    (1, "45", "Kings Highway", None),
    (1, "46", "Leonard", None),
    (1, "47", "Macon", None),
    (1, "48", "Midwood", None),
    (1, "49", "Mapleton", None),
    (1, "50", "Brooklyn Heights", None),
    (1, "51", "New Utrecht", None),
    (1, "52", "New Lots", None),
    (1, "53", "Park Slope", None),
    (1, "54", "Rugby", None),
    (1, "55", "Sunset Park", None),
    (1, "56", "Sheepshead Bay", None),
    (1, "57", "Saratoga", None),
    (1, "59", "Marcy", None),
    (1, "60", "Williamsburgh", None),
    (1, "61", "Washington Irving", None),
    (1, "62", "Walt Whitman", None),
    (1, "63", "Kidsmobile", None),
    (1, "64", "BiblioBus", None),
    (1, "65", "Cypress Hills", None),
    (1, "66", "Gerritsen Beach", None),
    (1, "67", "McKinley Park", None),
    (1, "68", "Mill Basin", None),
    (1, "69", "Pacific", None),
    (1, "70", "Red Hook", None),
    (1, "71", "Ulmer Park", None),
    (1, "72", "Bookmobile", None),
    (1, "74", "Gravesend", None),
    (1, "76", "Homecrest", None),
    (1, "77", "Windsor Terrace", None),
    (1, "78", "Paerdegat", None),
    (1, "79", "Brower Park", None),
    (1, "80", "Ryder", None),
    (1, "81", "Jamaica Bay", None),
    (1, "82", "Dyker", None),
    (1, "83", "Clinton Hill", None),
    (1, "85", "Spring Creek", None),
    (1, "87", "Cortelyou", None),
    (1, "89", "BookOps", None),
    (1, "90", "Service to the Aging SAGE/SOA", None),
    (1, "94", "Central Literacy", None),
    (2, "ag", "Aguilar", False),
    (2, "al", "Allerton", False),
    (2, "ba", "Baychester", False),
    (2, "bc", "Bronx Library Center", False),
    (2, "be", "Belmont", False),
    (2, "bl", "Bloomingdale", False),
    (2, "br", "George Bruce", False),
    (2, "bt", "Battery Park", False),
    (2, "ca", "Cathedral, T. C. Cooke", False),
    (2, "ch", "Chatham Square", False),
    (2, "ci", "City Island", False),
    (2, "cl", "Morningside Heights", False),
    (2, "cn", "Charleston", False),
    (2, "cp", "Clason's Point", False),
    (2, "cs", "Columbus", False),
    (2, "ct", "Castle Hill", False),
    (2, "dh", "Dongan Hills", False),
    (2, "dy", "Spuyten Duyvil", False),
    (2, "ea", "Eastchester", False),
    (2, "ed", "Library Service Center Educator Coll.", False),
    (2, "ep", "Epiphany", False),
    (2, "ew", "Edenwald", False),
    (2, "fe", "58th Street", False),
    (2, "ft", "53rd Street", False),
    (2, "fw", "Fort Washington", False),
    (2, "fx", "Francis Martin", False),
    (2, "gc", "Grand Central", False),
    (2, "gd", "Grand Concourse", False),
    (2, "gk", "Great Kills", False),
    (2, "go", "Google Books Project", True),
    (2, "hb", "High Bridge", False),
    (2, "hd", "125th Street", False),
    (2, "hf", "Hamilton Fish Park", False),
    (2, "hg", "Hamilton Grange", False),
    (2, "hk", "Huguenot Park", False),
    (2, "hl", "Harlem", False),
    (2, "hp", "Hudson Park", False),
    (2, "hs", "Hunt's Point", False),
    (2, "ht", "Countee Cullen", False),
    (2, "hu", "115th Street (temp)", False),
    (2, "ia", "Electronic Materials for Adults", None),
    (2, "ij", "Electronic Materials for Children", False),
    (2, "in", "Inwood", False),
    (2, "jm", "Jefferson Market", False),
    (2, "jp", "Jerome Park", False),
    (2, "kb", "Kingsbridge", False),
    (2, "kp", "Kips Bay", False),
    (2, "lb", "Andrew Heiskell", False),
    (2, "lm", "New Amsterdam", False),
    (2, "ls", "Library Services Center", None),
    (2, "ma", "S.A. Schwarzman Bldg.", True),
    (2, "mb", "Macomb's Bridge", False),
    (2, "me", "Melrose", False),
    (2, "mh", "Mott Haven", False),
    (2, "ml", "Mulberry Street", False),
    (2, "mn", "Mariner's Harbor", False),
    (2, "mo", "Mosholu", False),
    (2, "mp", "Morris Park", False),
    (2, "mr", "Morrisania", False),
    (2, "mu", "Muhlenberg", False),
    (2, "my", "Performing Arts", True),
    (2, "nb", "West New Brighton", False),
    (2, "nd", "New Dorp", False),
    (2, "ns", "96th Street", False),
    (2, "ot", "Ottendorfer", False),
    (2, "pk", "Parkchester", False),
    (2, "pm", "Pelham Bay", False),
    (2, "pr", "Port Richmond", False),
    (2, "qc", "Temporary Storage", True),
    (2, "rc", "Offsite - Research", True),
    (2, "rd", "Riverdale", False),
    (2, "ri", "Roosevelt Island", False),
    (2, "rs", "Riverside", False),
    (2, "rt", "Richmondtown", False),
    (2, "sa", "St. Agnes", False),
    (2, "sb", "South Beach", False),
    (2, "sc", "Schomburg", True),
    (2, "sd", "Sedgwick", False),
    (2, "se", "Seward Park", False),
    (2, "sg", "St. George Library Center", False),
    (2, "sn", "S.Niarchos Found. Library", False),
    (2, "ss", "67th Street", False),
    (2, "st", "Stapleton", False),
    (2, "sv", "Soundview", False),
    (2, "tg", "Throg's Neck", False),
    (2, "th", "Todt Hill-Westerleigh", False),
    (2, "tm", "Tremont", False),
    (2, "ts", "Tompkins Square", False),
    (2, "tv", "Tottenville", False),
    (2, "vc", "Van Cortlandt", False),
    (2, "vn", "Van Nest", False),
    (2, "wb", "Webster", False),
    (2, "wf", "West Farms", False),
    (2, "wh", "Washington Heights", False),
    (2, "wk", "Wakefield", False),
    (2, "wl", "Woodlawn Heights", False),
    (2, "wo", "Woodstock", False),
    (2, "wt", "Westchester Square", False),
    (2, "yv", "Yorkville", False),
    (2, "x0", "Research Holds", True),
    (2, "xf", "Inter-Library Loan", True),
    (2, "xr", "Collection Rebalancing", False),
    (2, "xx", "Research - On Order", True),
    (2, "zz", "Branches - On Order", False),
]

MATERIAL = [
    ("print", ("BPL", "a", "b"), ("NYPL", "a", "b")),
    ("dvd", ("BPL", "h", "a"), ("NYPL", "v", "v")),
    ("audiobook", ("BPL", "i", "i"), ("NYPL", "u", "i")),
    ("music CD", ("BPL", "j", "z"), ("NYPL", "y", "w")),
    ("graphic novel", ("BPL", "a", "g"), ("NYPL", "a", "b")),
    ("board book", ("BPL", "a", "d"), ("NYPL", "a", "b")),
]


USERS = [("generic", ("BPL", "-"), ("NYPL", "-"))]

STATUS = [
    (1, "in-works"),  # add background color value?
    (2, "finalized"),
    (3, "on-hold"),
    (4, "archived"),
]
