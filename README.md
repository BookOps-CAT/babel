# babel2
Enhanced BookOps crosswalk from a spreadsheet to MARC21 format

==============
Warning!!!
Work-in-progress
==============

## Database Localhost Installation
Babel is configured to work with MySQL database. 
Follow [MySQL Installer instruction](https://dev.mysql.com/doc/refman/8.0/en/windows-installation.html) to install server on a localhost. Then use create_datastore method to setup database with all required tables. 

localhost example:
>>>from babel.data.datastore import create_datastore
>>>create_datastore(
    db_name='datastoredev'
    user='john',
    password='johns_password',
    host='127.0.0.1',
    port='3306')


## Icon Credits
Icons by [Everaldo / Yellowicon](http://www.everaldo.com) used under [GNU Lesser General Public License](https://en.wikipedia.org/wiki/GNU_Lesser_General_Public_License).


