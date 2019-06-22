# Babel 2
Enhanced BookOps crosswalk from a spreadsheet to MARC21 format for Sierra ILS order records.
Babel 2 is a complete rewrite of the previous Babel app. It's written in Python 3, and is being actively developed.
Some of the features are missing even though the interface suggest their presence. In coming weeks we are planning to tackle them one by one.
In particular we will be focusing on developing following functionality:
* packaging and distribution of Babel (including a detail instruction how to, since these elements will not be part of Babel proper)
* extensive help hosted on Github wikis and accessible via Babel interface
* integration with ILS which includes holding reports and linking data between Sierra and Babel
* reporting tools (analysis, charts, etc. of carts data)
* creation of order sheets (which can be send to a vendor with order request, detailing the purchase)

Please note, Babel is a custom tool for BookOps which supposed to work with particular systems we use (Sierra ILS, etc.).
At the moment we do not plan to create a universal application that coulb be used by other libraries. It would not be too difficult to adapt our source code for your needs though, especially if you are Sierra or Millennium library.


## Database Localhost Installation
Babel is configured to work with MySQL database. 
Follow [MySQL Installer instruction](https://dev.mysql.com/doc/refman/8.0/en/windows-installation.html) to install server on a localhost. Then use create_datastore method to setup database with all required tables. 

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


## Icon Credits
Icons by [Everaldo / Yellowicon](http://www.everaldo.com) used under [GNU Lesser General Public License](https://en.wikipedia.org/wiki/GNU_Lesser_General_Public_License).


