# Babel
Is an Enhanced crosswalk to map data from a vendor spreadsheet to MARC21 format for Sierra ILS order records for the BookOps-NYPL and BPL technical services organization.
Babel 2 is a complete rewrite of the previous Babel app. It is written in Python 3, and is still being actively developed.
Some of the features are missing even though the interface suggest their presence. In coming weeks we are planning to tackle them one by one.
In particular we will be focusing on developing following functionality:
* Packaging and distribution of Babel (including a detail instruction how to, since these elements will not be part of Babel proper)
* Integration with ILS which includes holding reports and linking data between Sierra and Babel
* Reporting tools (analysis, charts, etc. of carts data)


Please note, Babel is a custom tool for BookOps which supposed to work with the particular systems and workflows used by BookOps (Sierra ILS, etc.).
At the moment we do not plan to create a universal application that could be used by other libraries. It would not be too difficult to adapt our source code for your needs though, especially if you are Sierra or Millennium library.


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
1. Copy content of Babel, Babel-updater (if changed) and Babel-windows-installer directories into a new space
2. Update version (version.txt)
3. Change logging from development to production (babel.py) - make sure loggly token is added
4. Activate virtual environment
5. Run freeze-babel-debug.cmd shell script from the main babel folder (repeat for updater and installer if changed)
6. Test if executable file launches correctly
7. Run freeze-babel.cmd shell scripts from the main babel folder
8. Copy created updater.exe to distr directory of babel proper
9. Encrypt MySQL creds using `credentials.enctrypt_file_data` and copy to distr directory
11. Run Babel Windows installer
12. Decrypt MySQL creds during installation
13. Create desktop shortcut for babel.exe
14. Launch babel to verify all is fine

## Icon Credits
Icons by
* Babel2 icon by our colleague Kimberly H. (thanks!)
* [Everaldo / Yellowicon](http://www.everaldo.com) used under [GNU Lesser General Public License](https://en.wikipedia.org/wiki/GNU_Lesser_General_Public_License).
* [Daniele De Santis](https://www.danieledesantis.net/) used under [CC Attribution 4.0](https://creativecommons.org/licenses/by/4.0/)
* [Icon Archive](http://www.iconarchive.com) used under [CC Attribution 4.0](https://creativecommons.org/licenses/by/4.0/)
* [Christopher Downer](http://christopherdowner.com/) used under [CC0 - Public Domain](https://creativecommons.org/publicdomain/zero/1.0/)
* [Simiographics](https://www.iconarchive.com/artist/simiographics.html) used under [CC0 - Public Domain](https://creativecommons.org/publicdomain/zero/1.0/)

## Presentations

[BookOps Babel : Filling Order Metadata Gaps in the ILS (ALA 2019, Washington, D.C.)](https://docs.google.com/presentation/d/1U4ZmFQBFp134S6qnglxZ32YuHRPz-UMrgCtwbG2KdMw/edit?usp=sharing)


