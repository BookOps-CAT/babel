# Babel
Babel is an enhanced crosswalk mapping data from a vendor spreadsheet to brief order records in MARC21 format. Produced records follow NYPL and BPL Sierra ILS schemas.

Babel provides an interface for selectors to ingest data from a spreadsheet that includes a list of offered by a vendor titles with any accompanying information (authors, publishers, ISBNs, prices, etc.). Selectors can enhance then this data with order information such as language, audience, vendor codes, fund codes, and finally distribution - an encoded for Sierra ILS data that specifies library branches where each copy is destined for. The vendor data and selectors enrichment produces MARC21 records that can be imported to Sierra and which will create brief record with attached order records for each title. This detailed order data allows to use process within Sierra called "rapid receive" to automatically create item records when materials are received. Detailed order information also allows more granular tracking of spending by the Selection Department.

In addition to its core functionality of creation of brief order records, Babel provides means to automatically detect duplicate titles in each BPL and NYPL catalogs potentially providing time and cost savings. Finally, the application produces detailed, on demand reports tracking placed orders.


Please note, Babel is a custom tool for BookOps which supposed to work with the particular systems and workflows used by BookOps (Sierra ILS, etc.). At the moment we do not plan to create a universal application that could be used by other libraries. It would not be too difficult to adapt our source code for your needs though, especially if you are Sierra or Millennium library.


## Database Localhost Installation
Babel is configured to work with MySQL database.
Follow [MySQL Installer instruction](https://dev.mysql.com/doc/refman/8.0/en/windows-installation.html) to install server on a localhost. Using MySQL Workbench create schema named as your db_name. Then use create_datastore method to setup database with all required tables.

localhost example:
```python
from babel.data.datastore import create_datastore
create_datastore(
    db_name='datastoredev'
    user='john',
    password='johns_password',
    host='127.0.0.1',
    port='3306')
```

## Stand-alone executable under Windows (initial & updates)
1. Update version (babel/babel.py and win_info.txt)
2. Change logging from development to production (babel.py) - make sure loggly token is added to `logging_settings.py`
3. Activate virtual environment
4. Make sure to change working directory to newly created main Babel directory
5. Encrypt credentials (`creds.json`) using `babel.credentials.enctrypt_file_data()` and copy to the distr directory as `creds.bin`. Note the encryption key, which will need to be provided to users to unlock the app
6. Package Babel by running `freeze-babel-debug.sh` shell script
7. Troubleshoot any import error or other issues. Test if the app launches
8. Rename generated `babel.exe` to `babel-debug.exe` and archive created distribution folder
9. Package app again using `freeze-babel.sh` shell script and copy to the archived directory the `babel.exe` file (actual executable file used by users).
10. Test if `babel.exe` launches correctly.
11. Zip the entire app folder (top level babel) and name it using version (example `babel-4.0.0.zip`)
12. Send the zipped app to ITG for packaging and distribution
13. Test ITG distribution
14. Remove loggly token from `logging_settings` and change logging back to `DEV_LOGGING`
14. Assist users with unlocking Babel (if creds changed)

## New Feature Requests
In addition to [GitHub Issues](https://github.com/BookOps-CAT/babel/issues) users can utilize [this google document](https://docs.google.com/document/d/18w87cPrZvU-DUNDGZl1_W-PIUVWcaS3cTW5nfNK_EZs/edit?usp=sharing) to suggest new features or report bugs.

## Icon Credits
Icons by
* Babel2 icon by our colleague Kimberly H. (thanks!)
* [Everaldo / Yellowicon](http://www.everaldo.com) used under [GNU Lesser General Public License](https://en.wikipedia.org/wiki/GNU_Lesser_General_Public_License).
* [Daniele De Santis](https://www.danieledesantis.net/) used under [CC Attribution 4.0](https://creativecommons.org/licenses/by/4.0/)
* [Icon Archive](http://www.iconarchive.com) used under [CC Attribution 4.0](https://creativecommons.org/licenses/by/4.0/)
* [Christopher Downer](http://christopherdowner.com/) used under [CC0 - Public Domain](https://creativecommons.org/publicdomain/zero/1.0/)
* [Simiographics](https://www.iconarchive.com/artist/simiographics.html) used under [CC0 - Public Domain](https://creativecommons.org/publicdomain/zero/1.0/)

## Changelog
### 4.0.1 (2024-10-09)
#### Fixed
+ escaped `system` table name to comply with the new MySQL 8 server and this word being reserved in its SQL syntax
### 4.0.0 (2022-07-27)
#### Added
+ ability to query NYPL Platform and BPL Solr to retrieve matches in the catalog
+ functionality to mark branches as temporarily closed which prompts warnings when distribution with such branch is applied to a cart
+ functionality to filter the cart for orders with temp branch locations, for orders identified as duplicates in the catalog, or duplicates in Babel
+ functionality to globally remove temp branch locations from orders
+ functionality to globally delete orders from cart that were identified as duplicates
+ new selector's reports and ability to download them as `csv` files
+ 910 tags with `BL` or `RL` for NYPL records
+ adds Poetry as dependencies management tool

#### Changed
+ alters `Branch` and `Resource` database tables to include data about temporarily closed location, branch-research identifiers for NYPL and catalog duplicates.
+ migrates database to a new server (v5.6)
+ improves process of saving to MARC and spreadsheet
+ button label "load" changed to "open" in the spreadsheet ingest module
+ cart name lenght extended to 120 characters

#### Fixed
+ Errors when importing BPL Sierra IDs with changed headers after Sierra update

#### Security
+ Dependencies updates (Pillow, urllib3, numpy, cryptography)

#### Deprecated
+ functionality to web scrape BPL and NYPL Webpacs in search for duplicates
+ updating from a shared drive

### 3.0.0 (2020-12-10)
#### Added
+ new installation splash window that provides means to unlock the credentials

#### Security
+ dependencies update (altgraph, attrs, beautifulsoup4, cryptography, loggly-python-handler, openpyxl, Pillow, psutils, py, pycryptodome, pywin, requests, urllib3)

### 2.3.2 (2020-10-14)
#### Security
+ dependencies update (Pillow, pytest, psutil)

### 2.3.1 (2020-01-28)
#### Fixed
+ report layouts
+ removed obsolete keyring.backends hook

### 2.3.0 (2020-01-27)
#### Added
+ report module
+ ability to add manually a new resource to a cart
+ functionality to add selectively grids to orders in a list
+ functionality to search order within a cart
+ total quantity tally in the cart
+ Matplotlib 3.1.2 dependency added

#### Fixed
+ disabled accidental switching between libraries when in the cart window
+ blocked application of funds when NYPL library is not specified
+ navigating resources in the cart with buttons
+ catalog duplicate web scraper timeout extended to 15 seconds
+ logging messages fixes

#### Security
+ Pyinstaller bump to 3.6

### 2.2.1 (2019-11-14)
#### Changed
+ removed hyphens from blanketPO, new format: {vendor code}{YYYYMMDD}{sequence}, example: chbks201911130 (BPL), 3433201909060 (NYPL)
+ list of carts sorted by default by date in descending order

#### Fixed
+ display of correct grids when two users name the distribution exactly the same
+ error when search retrieves results from carts without assigned library
+ linking Sierra IDs updates the display immediately
+ reseting of cart summary when another cart is selected

#### Security
+ Pillow update to 6.2.0

### 2.2.0 (2019-09-24)
#### Added
+ cart button in the CartView that tabulates orders by branch showing number of titles, copies and money per branch
+ extra column `comment` added to spreadsheet mapping
+ cart owner displayed in search results

#### Fixed
+ slow traversing between cart pages, saves and validation (optimization)
+ forces values in a spreadsheet to strings
+ anchors Babel window to the top left corner of the screen

### 2.1.0 (2019-09-12)
#### Changed
+ 30 resources per page displayed in a cart
+ cart name extended to 75 characters
+ speed up of FundView (optimization)

#### Fixed
+ a bug in the search functionality
+ deletion of user deletes related data
+ typo in order id range in CartsView summary
+ corrected display of linked carts
+ corrected display of cart's assigned library

## Presentations

[BookOps Babel : Filling Order Metadata Gaps in the ILS (ALA 2019, Washington, D.C.)](https://docs.google.com/presentation/d/1U4ZmFQBFp134S6qnglxZ32YuHRPz-UMrgCtwbG2KdMw/edit?usp=sharing)
