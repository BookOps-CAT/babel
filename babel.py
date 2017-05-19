import Tkinter as tk
import ttk
import tkMessageBox
import datetime
import tkFileDialog
import shelve
import os
# from os import startfile, getcwd
import logging  # more work needed to use this module for error reports, etc.
import logging.handlers

import babelstore as db
import validator as validation
import sheet_processing as sh
import wlo_generator
import celldata_parser as input_parser
from fund_applicator import *
from marc_generator import MARCGenerator
from ids_parser import *
from convert_price import dollars2cents, cents2dollars


LOG_FILENAME = './logs/babellog.out'

BTN_FONT = ('Helvetica', 10)
HDG_FONT = ('Helvetica', 12, 'bold')
LBL_FONT = ('Helvetica', 10, 'italic')
REG_FONT = ('Helvetica', 10)
LRG_FONT = ('Helvetica', 12)
REG_BOLD = ('Helvetica', 10, 'bold')


class DBSetup(tk.Frame):
    """database setup form recording connection details"""

    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.db_dialect = tk.StringVar()
        self.db_driver = tk.StringVar()
        self.db_host = tk.StringVar()
        self.db_port = tk.StringVar()
        self.db_user = tk.StringVar()
        self.db_password = tk.StringVar()
        self.db_name = tk.StringVar()
        self.db_charset = tk.StringVar()
        self.db_form()

    def db_form(self):
        self.columnconfigure(1, minsize=250)
        tk.Label(self, text='database dialect:').grid(
            row=0, column=0, sticky='snw', padx=5, pady=2)
        self.schemaCbx = ttk.Combobox(self, values=db.DB_DIALECTS,
                                      textvariable=self.db_dialect,
                                      state='readonly')
        self.schemaCbx.grid(
            row=0, column=1, sticky='snew', padx=5, pady=2)
        tk.Label(self, text='connection driver:').grid(
            row=1, column=0, sticky='snw', padx=5, pady=2)
        self.dialectCbx = ttk.Combobox(self, value=db.DB_DRIVERS,
                                       textvariable=self.db_driver,
                                       state='readonly')
        self.dialectCbx.grid(
            row=1, column=1, sticky='snew', padx=5, pady=2)
        tk.Label(self, text='host:').grid(
            row=2, column=0, sticky='snw', padx=5, pady=2)
        self.hostEnt = ttk.Entry(self, textvariable=self.db_host)
        self.hostEnt.grid(
            row=2, column=1, sticky='snew', padx=5, pady=2)
        tk.Label(self, text='port:').grid(
            row=3, column=0, sticky='snw', padx=5, pady=2)
        self.portEnt = ttk.Entry(self, textvariable=self.db_port)
        self.portEnt.grid(
            row=3, column=1, sticky='snew', padx=5, pady=2)
        tk.Label(self, text='database name').grid(
            row=4, column=0, sticky='snw', padx=5, pady=2)
        self.dbEnt = ttk.Entry(self, textvariable=self.db_name)
        self.dbEnt.grid(
            row=4, column=1, sticky='snew', padx=5, pady=2)
        tk.Label(self, text='user:').grid(
            row=5, column=0, sticky='snw', padx=5, pady=2)
        self.userEnt = ttk.Entry(self, textvariable=self.db_user)
        self.userEnt.grid(
            row=5, column=1, sticky='snew', padx=5, pady=2)
        tk.Label(self, text='password:').grid(
            row=6, column=0, sticky='snw', padx=5, pady=2)
        self.passEnt = ttk.Entry(self, textvariable=self.db_password,
                                 show='*')
        self.passEnt.grid(
            row=6, column=1, sticky='snew', padx=5, pady=2)
        tk.Label(self, text='character encoding:').grid(
            row=7, column=0, sticky='snw', padx=5, pady=2)
        self.charCbx = ttk.Combobox(self, value=db.DB_CHARSET,
                                    textvariable=self.db_charset)
        self.charCbx.grid(
            row=7, column=1, sticky='snew', padx=5, pady=2)
        self.grid(padx=10, pady=10)

        # info
        mysql_info = 'MYSQL\n' \
               'database dialect: mysql\n' \
               'connection driver: pymysql\n' \
               'character encoding: uft8\n'
        sqlite_info = 'SQLite (not supported at this momement)\n' \
                      'database dialect: sqlite\n' \
                      'connection driver: empty\n' \
                      'database host: enter path to db folder\n' \
                      'characer encoding: empty'
        tk.Label(self, text=mysql_info, justify=tk.LEFT).grid(
            row=0, column=2, rowspan=4, sticky='snw', padx=5)
        tk.Label(self, text=sqlite_info, justify=tk.LEFT).grid(
            row=3, column=2, rowspan=4, sticky='snw', padx=5)

        tk.Button(self, text='existing DB', command=self.link_to_existing,
                  width=10).grid(
            row=9, column=0, sticky='snw', padx=5, pady=2)
        tk.Button(self, text='new DB', command=self.create_new,
                  width=10).grid(
            row=9, column=1, sticky='snw', padx=5, pady=2)
        tk.Button(self, text='test', command=self.test,
                  width=10, state=tk.DISABLED).grid(
            row=9, column=2, sticky='snw', padx=5, pady=2)
        tk.Button(self, text='close', command=self.quit,
                  width=10).grid(
            row=9, column=2, sticky='sne', padx=5, pady=2)

    def validate_form(self):
        correct_input = True
        if self.db_dialect.get() == '':
            tkMessageBox.showwarning(
                'Input error',
                'please select database dialect')
            correct_input = False
        if self.db_dialect.get() == 'mysql' and \
                self.db_driver.get() != 'pymysql':
            tkMessageBox.showwarning(
                'Input error',
                'with MYSQL database please select "pymysql"'
                ' connection dialect')
            correct_input = False
        if self.db_host.get() == '':
            tkMessageBox.showwarning(
                'Input error',
                'please select database host/folder')
            correct_input = False

        # add more validation here

        return correct_input

    def link_to_existing(self):
        # save if correct
        correct_input = self.validate_form()
        if correct_input:
            user_data = shelve.open('user_data')
            user_data['db_config'] = {
                'dialect': self.db_dialect.get(),
                'driver': self.db_driver.get(),
                'db_name': self.db_name.get(),
                'host': self.db_host.get(),
                'port': self.db_port.get(),
                'user': self.db_user.get(),
                'password': self.db_password.get(),
                'charset': self.db_charset.get()
            }
            user_data.close()
            tkMessageBox.showinfo(
                'Input message',
                'Database details have been saved.\n'
                'Please close this window and restart Babel')

    def create_new(self):
        correct_input = self.validate_form()
        if correct_input:
            user_data = shelve.open('user_data')
            user_data['db_config'] = {
                'dialect': self.db_dialect.get(),
                'driver': self.db_driver.get(),
                'db_name': self.db_name.get(),
                'host': self.db_host.get(),
                'port': self.db_port.get(),
                'user': self.db_user.get(),
                'password': self.db_password.get(),
                'charset': self.db_charset.get()
            }
            user_data.close()
            tkMessageBox.showinfo(
                'Input message',
                'Database details have been saved.\n'
                'Please close this window and restart Babel'
            )
            try:
                db.initiateDB()
            except Exception as e:
                m = 'Encountered unexpected error.\n %s' % str(e)
                tkMessageBox.showerror('Database error', m)

    def test(self):
        pass


class BusyManager:
    """cursor manager"""

    def __init__(self, widget):
        self.toplevel = widget.winfo_toplevel()
        self.widgets = {}

    def busy(self, widget=None):
        if widget is None:
            w = self.toplevel
        else:
            w = widget

        if str(w) not in self.widgets:
            try:
                # attach cursor to this widget
                cursor = w.cget("cursor")
                if cursor != "watch":
                    self.widgets[str(w)] = (w, cursor)
                    w.config(cursor="watch")
            except tk.TclError:
                pass

        for w in w.children.values():
            self.busy(w)

    def notbusy(self):
        # restore cursors
        for w, cursor in self.widgets.values():
            try:
                w.config(cursor=cursor)
            except tk.TclError:
                pass
        self.widgets = {}


class MainApplication(tk.Tk):

    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        # container where frames are stacked
        container = tk.Frame(self)
        container.grid()

        # bind shared data betweeen windows
        self.tier = tk.StringVar()
        self.action = tk.StringVar()
        self.selectedItem_1 = tk.StringVar()
        self.selectedItem_2 = tk.StringVar()
        self.selectedItem_3 = tk.IntVar()
        self.selectedItem_4 = tk.IntVar()
        self.sharedData = {'tier': self.tier,
                           'action': self.action,
                           'selectedItem_1': self.selectedItem_1,
                           'selectedItem_2': self.selectedItem_2,
                           'selectedItem_3': self.selectedItem_3,
                           'selectedItem_4': self.selectedItem_4}

        # spawn Babel frames
        self.frames = {}
        for F in (
                CartSheet,
                CollaboratorBrowse,
                CollaboratorSingle,
                DefaultDirectories,
                DistributionBrowse,
                DistributionSingle,
                FundBrowse,
                FundSingle,
                ImportCartSheet,
                LocationBrowse,
                LocationSingle,
                Main,
                OrderBrowse,
                OrderEdit,
                Search,
                Settings,
                ShelfCodes,
                VendorBrowse,
                VendorSheetBrowse,
                VendorSheetSingle,
                VendorSingle,
                Z3950Settings):
            page_name = F.__name__
            frame = F(parent=container, controller=self,
                      **self.sharedData)
            self.frames[page_name] = frame

            # put all windows in the same location
            frame.grid(row=0, column=0, sticky='snew', padx=10, pady=10)

        # set up menu bar
        menubar = tk.Menu(self, font=REG_FONT)
        navig_menu = tk.Menu(menubar, font=REG_FONT, tearoff=0)
        navig_menu.add_command(label='new cart sheet',
                               command=lambda: self.show_frame('CartSheet'))
        navig_menu.add_command(label='import cart sheet',
                               command=lambda: self.show_frame(
                                   'ImportCartSheet'))
        navig_menu.add_command(label='orders & MARC records',
                               command=lambda: self.show_frame(
                                   'OrderBrowse'))
        navig_menu.add_command(label='settings',
                               command=lambda: self.show_frame('Settings'))
        navig_menu.add_separator()
        navig_menu.add_command(label='exit', command=self.quit)
        menubar.add_cascade(label='Menu', menu=navig_menu)
        search_menu = tk.Menu(menubar, font=REG_FONT, tearoff=0)
        menubar.add_checkbutton(label='Search', command=lambda: self.show_frame('Search'))
        report_menu = tk.Menu(menubar, font=REG_FONT, tearoff=0)
        report_menu.add_command(label='reports', command=None)
        menubar.add_cascade(label='Reports', menu=report_menu)
        help_menu = tk.Menu(menubar, font=REG_FONT, tearoff=0)
        help_menu.add_command(label='help index', command=None)
        help_menu.add_command(label='updates', command=self.updates)
        help_menu.add_command(label='about...', command=None)
        menubar.add_cascade(label='Help', menu=help_menu)
        self.config(menu=menubar)

        # lift to the top main window
        self.show_frame('Main')

    def updates(self):
        user_data = shelve.open('user_data')
        if 'version' in user_data:
            app_version = user_data['version']
        else:
            app_version = None

        if 'update_dir' in user_data:
            update_dir = user_data['update_dir']
            if os.path.isfile(update_dir + 'version.txt'):
                print 'trigger'
                fh = update_dir + 'version.txt'
                f = open(fh, 'r')
                update_version = f.read()
                if app_version != update_version:
                    m = 'A new version ({}) of Babel has been found.\n' \
                        'Would you like to run the update?.'.format(update_version)
                    if tkMessageBox.askyesno('update info', m):
                        # launch updater & quit main app
                        user_data.close()
                        args = '{} {} {}'.format('updater.exe', update_dir, update_version)
                        os.system(args)
                else:
                    m = 'Babel is up-to-date'
                    tkMessageBox.showinfo('info', m)
            else:
                m = 'Update files not found.\n' \
                    'Please provide update directory\n' \
                    'Go to:\n' \
                    'settings>default directories>update folder'
                tkMessageBox.showwarning('missing files', m)          

        else:
            m = 'please provide update directory\n' \
                'Go to:\n' \
                'settings>default directories>update folder'
            tkMessageBox.showwarning('missing directory', m)
        user_data.close()    

    def show_frame(self, page_name):
        """show frame for the given page name"""
        frame = self.frames[page_name]
        # set tier for behavioral control
        self.tier.set(page_name)
        frame.tkraise()


class Main(tk.Frame):

    def __init__(self, parent, controller, **sharedData):
        self.parent = parent
        tk.Frame.__init__(self, parent)
        self.controller = controller


class Settings(tk.Frame):

    def __init__(self, parent, controller, **sharedData):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.tier = sharedData['tier']

        # configure layout
        self.columnconfigure(0, minsize=72)
        self.columnconfigure(1, minsize=72)
        self.columnconfigure(2, minsize=72)
        self.rowconfigure(0, minsize=35)
        self.rowconfigure(1, minsize=35)
        self.rowconfigure(2, minsize=35)
        self.rowconfigure(3, minsize=35)
        self.rowconfigure(4, minsize=20)

        tk.Button(self, text='locations', font=BTN_FONT,
                  height=2,
                  width=20,
                  command=lambda: controller.show_frame(
                      'LocationBrowse')).grid(
            row=0, column=0, padx=10, pady=10)
        tk.Button(self, text='funds', font=BTN_FONT,
                  height=2,
                  width=20,
                  command=lambda: controller.show_frame(
                      'FundBrowse')).grid(
            row=0, column=1, padx=10, pady=10)
        tk.Button(self, text='distributions', font=BTN_FONT,
                  height=2,
                  width=20,
                  command=lambda: controller.show_frame(
                      'DistributionBrowse')).grid(
            row=0, column=2, padx=10, pady=10)
        tk.Button(self, text='vendors', font=BTN_FONT,
                  height=2,
                  width=20,
                  command=lambda: controller.show_frame(
                      'VendorBrowse')).grid(
            row=1, column=0, padx=10, pady=10)
        tk.Button(self, text='vendor\nsheets', font=BTN_FONT,
                  height=2,
                  width=20,
                  command=lambda: controller.show_frame(
                      'VendorSheetBrowse')).grid(
            row=1, column=1, padx=10, pady=10)
        tk.Button(self, text='collaborators', font=BTN_FONT,
                  height=2,
                  width=20,
                  command=lambda: controller.show_frame(
                      'CollaboratorBrowse')).grid(
            row=1, column=2, padx=10, pady=10)
        tk.Button(self, text='default\ndirectories',
                  font=BTN_FONT,
                  height=2,
                  width=20,
                  command=lambda: controller.show_frame(
                      'DefaultDirectories')).grid(
            row=2, column=0, padx=10, pady=10)
        tk.Button(self, text='languages', font=BTN_FONT,
                  height=2,
                  width=20,
                  command=None,
                  state=tk.DISABLED).grid(
            row=2, column=1, padx=10, pady=10)
        tk.Button(self, text='item codes', font=BTN_FONT,
                  height=2,
                  width=20,
                  command=lambda: controller.show_frame(
                      'ShelfCodes')).grid(
            row=2, column=2, padx=10, pady=10)

        tk.Button(self, text='Z3950', font=BTN_FONT,
                  height=2,
                  width=20,
                  command=lambda: controller.show_frame(
                        'Z3950Settings')).grid(
            row=3, column=0, padx=10, pady=10)
        tk.Button(self, text='close', font=BTN_FONT,
                  # height=2,
                  width=15,
                  command=lambda: controller.show_frame('Main')).grid(
            row=5, column=0, columnspan=3, padx=10, pady=10)


class DefaultDirectories(tk.Frame):

    def __init__(self, parent, controller, **sharedData):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.tier = sharedData['tier']
        self.tier.trace('w', self.observer)

        # local variables
        self.db_details = tk.StringVar()

        # configure layout
        self.rowconfigure(0, minsize=20)
        self.rowconfigure(4, minsize=20)
        self.columnconfigure(1, minsize=20)

        # directories frame
        self.dirFrm = ttk.LabelFrame(self, text='default directories')
        self.dirFrm.grid(
            row=1, column=0, sticky='snew', padx=5, pady=5)

        # initiate widgets
        tk.Button(self.dirFrm, text='vendor sheets', font=BTN_FONT,
                  width=15,
                  command=self.vendor_sheets).grid(
            row=0, column=0, sticky='snw', padx=10, pady=10)
        tk.Button(self.dirFrm, text='cart sheets', font=BTN_FONT,
                  width=15,
                  command=self.cart_sheets).grid(
            row=1, column=0, sticky='snw', padx=10, pady=10)
        tk.Button(self.dirFrm, text='completed carts', font=BTN_FONT,
                  width=15,
                  command=self.completed_carts).grid(
            row=2, column=0, sticky='snw', padx=10, pady=10)
        tk.Button(self.dirFrm, text='sierra ids', font=BTN_FONT,
                  width=15,
                  command=self.sierra_ids).grid(
            row=3, column=0, sticky='snw', padx=10, pady=10)
        tk.Button(self.dirFrm, text='order sheets', font=BTN_FONT,
                  width=15,
                  command=self.order_sheets).grid(
            row=4, column=0, sticky='snw', padx=10, pady=10)
        tk.Button(self.dirFrm, text='marc records', font=BTN_FONT,
                  width=15,
                  command=self.marc_records).grid(
            row=5, column=0, sticky='snw', padx=10, pady=10)

        tk.Button(self.dirFrm, text='update folder', font=BTN_FONT,
                  width=15,
                  command=self.update_folder).grid(
            row=6, column=0, sticky='snw', padx=10, pady=10)

        tk.Button(self, text='close', font=BTN_FONT,
                  width=15,
                  command=lambda: controller.show_frame(
                      'Main')).grid(
            row=2, column=1, columnspan=3, sticky='snw', padx=10, pady=10)

        # database frame
        self.dbFrm = ttk.LabelFrame(self, text='database')
        self.dbFrm.grid(row=1, column=2, sticky='snew', padx=5, pady=5)
        self.dbFrm.rowconfigure(6, minsize=134)
        tk.Label(self.dbFrm, textvariable=self.db_details,
                 justify=tk.LEFT).grid(
            row=0, column=0, rowspan=5, sticky='snew', padx=5, pady=5)

        tk.Button(self.dbFrm, text='change database', font=BTN_FONT,
                  width=15,
                  command=self.local_db).grid(
            row=7, column=0, sticky='snw', padx=10, pady=10)

    def vendor_sheets(self):
        self.widget_title = 'New releases sheets folder'
        folder = self.directory()
        user_data = shelve.open('user_data')
        user_data['ven_sheet_dir'] = folder + '/'
        user_data.close()

    def cart_sheets(self):
        self.widget_title = 'Empty carts folder'
        folder = self.directory()
        user_data = shelve.open('user_data')
        user_data['cart_dir'] = folder + '/'
        user_data.close()

    def completed_carts(self):
        self.widget_title = 'Completed carts folder'
        folder = self.directory()
        user_data = shelve.open('user_data')
        user_data['cart_completed_dir'] = folder + '/'
        user_data.close()

    def sierra_ids(self):
        self.widget_title = 'Sierra IDs default folder'
        folder = self.directory()
        user_data = shelve.open('user_data')
        user_data['sierra_ids_dir'] = folder + '/'
        user_data.close()

    def order_sheets(self):
        self.widget_title = 'Order sheets default folder'
        folder = self.directory()
        user_data = shelve.open('user_data')
        user_data['order_dir'] = folder + '/'
        user_data.close()

    def marc_records(self):
        self.widget_title = 'MARC records default folder'
        folder = self.directory()
        user_data = shelve.open('user_data')
        user_data['marc_dir'] = folder + '/'
        user_data.close()

    def update_folder(self):
        self.widget_title = 'Folder to check for updates'
        folder = self.directory()
        user_data = shelve.open('user_data')
        user_data['update_dir'] = folder + '/'
        user_data.close()

    def local_db(self):
        self.dbFormFrm = ttk.LabelFrame(self, text='enter new db information')
        self.dbFormFrm.grid(
            row=1, column=3, sticky='snew', padx=5, pady=5)
        DBSetup(self.dbFormFrm)

    def directory(self):
        self.dir_opt = options = {}
        options['title'] = self.widget_title
        return tkFileDialog.askdirectory(**self.dir_opt)

    def show_db(self):
        # pull db details for display
        user_data = shelve.open('user_data')
        if 'db_config' in user_data:
            details = 'dialect: %s\n' \
                      'driver: %s\n' \
                      'host: %s\n' \
                      'db name: %s\n' \
                      'user: %s\n' \
                      'charset: %s' % (
                          user_data['db_config']['dialect'],
                          user_data['db_config']['driver'],
                          user_data['db_config']['host'],
                          user_data['db_config']['db_name'],
                          user_data['db_config']['user'],
                          user_data['db_config']['charset']
                      )
            self.db_details.set(details)
        user_data.close()

    def observer(self, *args):
        if self.tier.get() == 'DefaultDirectories':
            self.show_db()


class VendorBrowse(tk.Frame):

    def __init__(self, parent, controller, **sharedData):
        tk.Frame.__init__(self, parent)
        # set shared between widgets variables
        self.controller = controller
        self.tier = sharedData['tier']
        self.action = sharedData['action']
        self.selectedItem_1 = sharedData['selectedItem_1']
        self.tier.trace('w', self.observer)

        # configure layout
        self.columnconfigure(0, minsize=72)
        self.columnconfigure(1, minsize=72)
        self.columnconfigure(2, minsize=10)
        self.columnconfigure(3, minsize=50)
        self.columnconfigure(4, minsize=144)
        self.rowconfigure(9, minsize=50)

        # initiate widgets
        tk.Label(self, text='vendor name:', font=LBL_FONT).grid(
            row=0, column=0, sticky='snw')
        scrollbar = tk.Scrollbar(self, orient=tk.VERTICAL)
        scrollbar.grid(
            row=1, column=2, sticky='nsw', rowspan=10, padx=2, pady=10)
        self.vendorLst = tk.Listbox(self, font=REG_FONT,
                                    yscrollcommand=scrollbar.set)
        self.vendorLst.bind('<Double-Button-1>', self.edit_entry)
        self.vendorLst.grid(
            row=1, column=0, columnspan=2, sticky='snew', rowspan=10, pady=10)
        scrollbar['command'] = self.vendorLst.yview
        tk.Button(self, text='add', font=BTN_FONT,
                  command=self.add_entry,
                  width=15).grid(
            row=1, column=3, sticky='snew', padx=10, pady=10)
        tk.Button(self, text='edit', font=BTN_FONT,
                  command=self.edit_entry,
                  width=15).grid(
            row=2, column=3, sticky='snew', padx=10, pady=10)
        tk.Button(self, text='delete', font=BTN_FONT,
                  command=self.delete_entry,
                  width=15).grid(
            row=3, column=3, sticky='snew', padx=10, pady=10)
        tk.Button(self, text='close', font=BTN_FONT,
                  command=lambda: controller.show_frame('Settings'),
                  width=15).grid(
            row=10, column=3, sticky='snew', padx=10, pady=10)

    def add_entry(self):
        self.action.set('add')
        self.controller.show_frame('VendorSingle')

    def edit_entry(self, *args):
        if self.vendorLst.get(tk.ANCHOR) != '':
            self.selectedItem_1.set(self.vendorLst.get(tk.ANCHOR))
            self.action.set('update')
            self.controller.show_frame('VendorSingle')
        else:
            msg = 'Please select a vendor on the list'
            tkMessageBox.showwarning('Input Error', msg)

    def delete_entry(self):
        if self.vendorLst.get(tk.ANCHOR) != '':
            if tkMessageBox.askokcancel(
                    'deleting vendor',
                    'are you sure to you want to delete this vendor?'):
                delete_name = self.vendorLst.get(tk.ANCHOR)
                db.delete_record(db.Vendor, name=delete_name)
                self.vendorLst.delete(tk.ANCHOR)
        else:
            msg = 'Please select a vendor on the list'
            tkMessageBox.showwarning('Input Error', msg)

    def reloadLst(self):
        self.vendorLst.delete(0, tk.END)
        records = db.col_preview(db.Vendor, 'name')
        for row in records:
            self.vendorLst.insert(tk.END, row.name)

    def observer(self, *args):
        # refresh displayed vendor list when window is lifted to the top
        if self.tier.get() == 'VendorBrowse':
            self.reloadLst()


class VendorSingle(tk.Frame):

    def __init__(self, parent, controller, **sharedData):
        tk.Frame.__init__(self, parent)
        # set shared between widgets variables
        self.controller = controller
        self.tier = sharedData['tier']
        self.action = sharedData['action']
        self.selectedItem_1 = sharedData['selectedItem_1']
        self.tier.trace('w', self.observer)

        # configure layout
        self.columnconfigure(0, minsize=72)
        self.columnconfigure(1, minsize=72)
        self.columnconfigure(2, minsize=144)

        # define local variables
        self.id = tk.IntVar()
        self.nameFormal = tk.StringVar()
        self.bplcode = tk.StringVar()
        self.nyplcode = tk.StringVar()
        self.name = tk.StringVar()

        # initiate widgets
        tk.Label(self, text=' vendor full name:', font=REG_FONT).grid(
            row=0, column=0, columnspan=2, sticky='snw', padx=10)
        tk.Entry(self, textvariable=self.nameFormal, font=REG_FONT).grid(
            row=1, column=0, columnspan=2, sticky='snew', padx=10, pady=10)
        tk.Label(self, text='notes:', font=REG_FONT).grid(
            row=2, column=0, sticky='snw', padx=10)
        self.note = tk.Text(self, font=REG_FONT, height=5, width=44)
        self.note.grid(
            row=3, column=0, columnspan=2,
            padx=10, pady=10)
        tk.Label(self, text='BPL Sierra code:', font=REG_FONT).grid(
            row=4, column=0, sticky='snw', padx=10)
        tk.Entry(self, textvariable=self.bplcode, font=REG_FONT).grid(
            row=5, column=0, sticky='snw', padx=10)
        tk.Label(self, text='NYPL Sierra code:', font=REG_FONT).grid(
            row=6, column=0, sticky='snw', padx=10)
        tk.Entry(self, textvariable=self.nyplcode, font=REG_FONT).grid(
            row=7, column=0, sticky='snw', padx=10)
        tk.Label(self, text='save as:', font=REG_FONT).grid(
            row=8, column=0, sticky='snw', padx=10)
        tk.Entry(self, textvariable=self.name, font=REG_FONT).grid(
            row=9, column=0, columnspan=2, sticky='snew', padx=10)
        tk.Button(self, text='save', font=BTN_FONT,
                  command=self.new_vendor,
                  width=15).grid(
            row=10, column=0, pady=10, padx=10)
        tk.Button(self, text='close', font=BTN_FONT,
                  command=self.on_close,
                  width=15).grid(
            row=10, column=1, pady=10, padx=10)

    def new_vendor(self):
        new_ven = {'name': self.name.get().strip(),
                   'nameFormal': self.nameFormal.get().strip(),
                   'note': self.note.get('0.0', tk.END).strip(),
                   'bplCode': self.bplcode.get().strip(),
                   'nyplCode': self.nyplcode.get().strip()}

        # validate input / consider validation via tkinter
        msg = validation.vendor_form(new_ven)
        if msg is not None:
            tkMessageBox.showerror('Input Error', msg)
        else:
            if self.tier.get() == 'VendorSingle':
                if self.action.get() == 'add':
                    db.ignore_or_insert(db.Vendor,
                                        name=new_ven['name'],
                                        nameFormal=new_ven['nameFormal'],
                                        note=new_ven['note'],
                                        bplCode=new_ven['bplCode'],
                                        nyplCode=new_ven['nyplCode'])
                elif self.action.get() == 'update':
                    db.update_record(db.Vendor,
                                     id=self.id.get(),
                                     name=new_ven['name'],
                                     nameFormal=new_ven['nameFormal'],
                                     note=new_ven['note'],
                                     bplCode=new_ven['bplCode'],
                                     nyplCode=new_ven['nyplCode'])

            # clear the fields in the form
            tkMessageBox.showinfo('Vendor', 'vendor data saved')
            self.reset_values()

    def on_close(self):
        # clear the fields
        self.reset_values()
        # lift to the top VendorBrowse windot
        self.controller.show_frame('VendorBrowse')

    def reset_values(self):
        # reset variables
        self.action.set('add')
        self.id.set(0)
        self.name.set('')
        self.nameFormal.set('')
        self.note.delete('0.0', tk.END)
        self.bplcode.set('')
        self.nyplcode.set('')

    def observer(self, *args):
        if (self.tier.get() == 'VendorSingle') and (
                self.action.get() == 'update'):
            name = self.selectedItem_1.get()
            record = db.retrieve_record(db.Vendor, name=name)
            self.id.set(record.id)
            self.name.set(record.name)
            self.nameFormal.set(record.nameFormal)
            self.note.insert(tk.END, record.note)
            self.bplcode.set(record.bplCode)
            self.nyplcode.set(record.nyplCode)


class CollaboratorBrowse(tk.Frame):

    def __init__(self, parent, controller, **sharedData):
        tk.Frame.__init__(self, parent)
        # set shared between widgets variables
        self.controller = controller
        self.tier = sharedData['tier']
        self.action = sharedData['action']
        self.selectedItem_1 = sharedData['selectedItem_1']
        self.tier.trace('w', self.observer)

        # configure layout
        self.columnconfigure(0, minsize=72)
        self.columnconfigure(1, minsize=72)
        self.columnconfigure(2, minsize=10)
        self.columnconfigure(3, minsize=50)
        self.columnconfigure(4, minsize=144)
        self.rowconfigure(9, minsize=50)

        # initiate widgets
        tk.Label(self, text='selection committee template:',
                 font=LBL_FONT).grid(
            row=0, column=0, columnspan=2, sticky='snew')
        scrollbar = tk.Scrollbar(self, orient=tk.VERTICAL)
        scrollbar.grid(
            row=1, column=2, sticky='nsw', rowspan=10, padx=2, pady=10)
        self.collabLst = tk.Listbox(self, font=REG_FONT,
                                    yscrollcommand=scrollbar.set)
        self.collabLst.bind('<Double-Button-1>', self.edit_entry)
        self.collabLst.grid(
            row=1, column=0, columnspan=2, sticky='snew',
            rowspan=10, pady=10)
        scrollbar['command'] = self.collabLst.yview
        tk.Button(self, text='add', font=BTN_FONT,
                  command=self.add_entry,
                  width=15).grid(
            row=1, column=3, sticky='snew', padx=10, pady=10)
        tk.Button(self, text='edit', font=BTN_FONT,
                  command=self.edit_entry,
                  width=15).grid(
            row=2, column=3, sticky='snew', padx=10, pady=10)
        tk.Button(self, text='delete', font=BTN_FONT,
                  command=self.delete_entry,
                  width=15).grid(
            row=3, column=3, sticky='snew', padx=10, pady=10)
        tk.Button(self, text='close', font=BTN_FONT,
                  command=lambda: controller.show_frame('Settings'),
                  width=15).grid(
            row=10, column=3, sticky='snew', padx=10, pady=10)

    def add_entry(self):
        self.action.set('add')
        self.controller.show_frame('CollaboratorSingle')

    def edit_entry(self, *args):
        if self.collabLst.get(tk.ANCHOR) != '':
            self.selectedItem_1.set(self.collabLst.get(tk.ANCHOR))
            self.action.set('update')
            self.controller.show_frame('CollaboratorSingle')
        else:
            msg = 'Please select a template from the list'
            tkMessageBox.showwarning('Input Error', msg)

    def delete_entry(self):
        if self.collabLst.get(tk.ANCHOR) != '':
            if tkMessageBox.askokcancel(
                    'Collaborator',
                    'delete collaborator template?'):
                delete_name = self.collabLst.get(tk.ANCHOR)
                db.delete_record(db.Collaborator, templateName=delete_name)
                self.collabLst.delete(tk.ANCHOR)
        else:
            msg = 'Please select a template from the list'
            tkMessageBox.showwarning('Input Error', msg)

    def reloadLst(self):
        self.collabLst.delete(0, tk.END)
        records = db.col_preview(db.Collaborator, 'templateName')
        for row in records:
            self.collabLst.insert(tk.END, row.templateName)

    def observer(self, *args):
        # refresh displayed collaborator list on change in self.action
        if self.tier.get() == 'CollaboratorBrowse':
            self.reloadLst()


class CollaboratorSingle(tk.Frame):

    def __init__(self, parent, controller, **sharedData):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.tier = sharedData['tier']
        self.action = sharedData['action']
        self.selectedItem_1 = sharedData['selectedItem_1']
        self.tier.trace('w', self.observer)

        self.columnconfigure(0, minsize=72)
        self.columnconfigure(1, minsize=72)

        self.id = tk.IntVar()
        self.templateName = tk.StringVar()
        self.lang = tk.StringVar()
        self.lang_id = tk.IntVar()
        self.collab1 = tk.StringVar()
        self.collab2 = tk.StringVar()
        self.collab3 = tk.StringVar()
        self.collab4 = tk.StringVar()
        self.collab5 = tk.StringVar()

        choices = ()
        self.langs_by_name = {}
        self.langs_by_id = {}
        for row in db.col_preview(db.Lang, 'id', 'code', 'name'):
            choices = choices + (row.name, )
            self.langs_by_name[row.name] = (row.id, row.code)
            self.langs_by_id[row.id] = (row.name, row.code)

        tk.Label(self, text='language:', font=LBL_FONT).grid(
            row=2, column=0, sticky='snw')
        ttk.Combobox(self, textvariable=self.lang,
                     value=choices, state='readonly').grid(
            row=3, column=0, sticky='snew', padx=10, pady=10)
        self.lang.set('Undetermined')
        tk.Label(self, text='collaborator 1:', font=LBL_FONT).grid(
            row=4, column=0, sticky='snw')
        tk.Entry(self, textvariable=self.collab1, font=REG_FONT).grid(
            row=5, column=0, sticky='snew', padx=10)
        tk.Label(self, text='collaborator 2:', font=LBL_FONT).grid(
            row=6, column=0, sticky='snw')
        tk.Entry(self, textvariable=self.collab2, font=REG_FONT).grid(
            row=7, column=0, sticky='snew', padx=10)
        tk.Label(self, text='collaborator 3:', font=LBL_FONT).grid(
            row=8, column=0, sticky='snw')
        tk.Entry(self, textvariable=self.collab3, font=REG_FONT).grid(
            row=9, column=0, sticky='snew', padx=10)
        tk.Label(self, text='collaborator 4:', font=LBL_FONT).grid(
            row=10, column=0, sticky='snw')
        tk.Entry(self, textvariable=self.collab4, font=REG_FONT).grid(
            row=11, column=0, sticky='snew', padx=10)
        tk.Label(self, text='collaborator 5:', font=LBL_FONT).grid(
            row=12, column=0, sticky='snw')
        tk.Entry(self, textvariable=self.collab5, font=REG_FONT).grid(
            row=13, column=0, sticky='snew', padx=10)
        tk.Label(self, text='save as:', font=LBL_FONT).grid(
            row=14, column=0, sticky='snw')
        tk.Entry(self, textvariable=self.templateName,
                 font=REG_FONT).grid(
            row=15, column=0, columnspan=2, sticky='snew', padx=10)
        tk.Button(self, text='save', font=BTN_FONT,
                  command=self.on_save,
                  width=15).grid(
            row=16, column=0, padx=10, pady=10)
        tk.Button(self, text='close', font=BTN_FONT,
                  command=self.on_close,
                  width=15).grid(
            row=16, column=1, padx=10, pady=10)

    def on_save(self):
        new = {'templateName': self.templateName.get().strip(),
               'lang': self.lang.get(),
               'collab1': self.collab1.get().strip(),
               'collab2': self.collab2.get().strip(),
               'collab3': self.collab3.get().strip(),
               'collab4': self.collab4.get().strip(),
               'collab5': self.collab5.get().strip()}

        # validate input / consider validation via tkinter
        msg = validation.collaborator_form(new)
        if msg is not None:
            tkMessageBox.showerror('Input Error', msg)
        else:
            if self.tier.get() == 'CollaboratorSingle':
                if self.action.get() == 'add':
                    db.ignore_or_insert(
                        db.Collaborator,
                        templateName=new['templateName'],
                        lang_id=self.langs_by_name[new['lang']][0],
                        collab1=new['collab1'],
                        collab2=new['collab2'],
                        collab3=new['collab3'],
                        collab4=new['collab4'],
                        collab5=new['collab5'])
                elif self.action.get() == 'update':
                    db.update_record(
                        db.Collaborator,
                        id=self.id.get(),
                        templateName=new['templateName'],
                        lang_id=self.lang_id.get(),
                        collab1=new['collab1'],
                        collab2=new['collab2'],
                        collab3=new['collab3'],
                        collab4=new['collab4'],
                        collab5=new['collab5'])

            # clear the fields in the form
            self.reset_values()

    def on_close(self):
        # clear the fields
        self.reset_values()
        # switch top window
        self.controller.show_frame('CollaboratorBrowse')

    def reset_values(self):
        # reset form values
        self.action.set('add')
        self.id.set(0)
        self.templateName.set('')
        self.lang.set('Undetermined')
        self.lang_id.set(0)
        self.collab1.set('')
        self.collab2.set('')
        self.collab3.set('')
        self.collab4.set('')
        self.collab5.set('')

    def observer(self, *args):
        if (self.tier.get()):
            if (self.tier.get() == 'CollaboratorSingle') and \
               (self.action.get() == 'update'):
                edit_collab = self.selectedItem_1.get()
                record = db.retrieve_record(
                    db.Collaborator,
                    templateName=edit_collab)
                self.id.set(record.id)
                self.templateName.set(record.templateName)
                self.lang_id.set(record.lang_id)
                self.lang.set(self.langs_by_id[record.lang_id][0])
                self.collab1.set(record.collab1)
                self.collab2.set(record.collab2)
                self.collab3.set(record.collab3)
                self.collab4.set(record.collab4)
                self.collab5.set(record.collab5)


class LocationBrowse(tk.Frame):

    def __init__(self, parent, controller, **sharedData):
        tk.Frame.__init__(self, parent)

        # shared variables
        self.tier = sharedData['tier']
        self.action = sharedData['action']
        self.selectedItem_1 = sharedData['selectedItem_1']
        self.selectedItem_2 = sharedData['selectedItem_2']
        self.selectedItem_3 = sharedData['selectedItem_3']
        self.selectedItem_4 = sharedData['selectedItem_4']
        self.tier.trace('w', self.observer)

        # local variables
        self.controller = controller
        self.library_id = tk.IntVar()
        # display list of location dynamically based on library
        self.library_id.trace('w', self.dynamic_library)
        self.matType = tk.StringVar()
        # display list of location dynamically based on matType
        self.matType.trace('w', self.dynamic_material)
        self.matType_id = tk.IntVar()

        self.matType_choices = ()
        self.matType_by_name = {}
        # self.matType_by_id = {}

        # layout configuration
        self.columnconfigure(0, minsize=72)
        self.columnconfigure(1, minsize=72)
        self.columnconfigure(2, minsize=10)
        self.columnconfigure(3, minsize=50)
        self.columnconfigure(4, minsize=144)
        self.rowconfigure(9, minsize=50)

        # initiate widgets
        ttk.Radiobutton(self, text='BPL',
                        variable=self.library_id, value=1).grid(
            row=0, column=0, sticky='snw')
        ttk.Radiobutton(self, text='NYPL',
                        variable=self.library_id, value=2).grid(
            row=1, column=0, sticky='snw')
        tk.Label(self, text='select material type:',
                 font=LBL_FONT).grid(
            row=2, column=0, sticky='snw')
        self.matCbx = ttk.Combobox(self, textvariable=self.matType,
                                   state='readonly')
        self.matCbx.grid(
            row=2, column=1, sticky='snw', pady=10)
        tk.Label(self, text='location shorthand:',
                 font=LBL_FONT).grid(
            row=3, column=0, columnspan=2, sticky='sw')
        scrollbar = tk.Scrollbar(self, orient=tk.VERTICAL)
        scrollbar.grid(
            row=4, column=2, sticky='nsw', rowspan=10, padx=2, pady=10)
        self.locationLst = tk.Listbox(self, font=REG_FONT,
                                      yscrollcommand=scrollbar.set)
        self.locationLst.bind('<Double-Button-1>', self.edit_entry)
        self.locationLst.grid(
            row=4, column=0, columnspan=2, sticky='snew', rowspan=10, pady=10)
        scrollbar['command'] = self.locationLst.yview

        # buttons on the right
        tk.Button(self, text='add', font=BTN_FONT,
                  command=self.add_entry,
                  width=15).grid(
            row=4, column=3, sticky='snew', padx=10, pady=10)
        tk.Button(self, text='edit', font=BTN_FONT,
                  command=self.edit_entry,
                  width=15).grid(
            row=5, column=3, sticky='snew', padx=10, pady=10)
        tk.Button(self, text='delete', font=BTN_FONT,
                  command=self.delete_entry,
                  width=15).grid(
            row=6, column=3, sticky='snew', padx=10, pady=10)
        tk.Button(self, text='close', font=BTN_FONT,
                  command=self.on_close,
                  width=15).grid(
            row=10, column=3, sticky='snew', padx=10, pady=10)

    def add_entry(self):
        self.selectedItem_3.set(self.library_id.get())
        self.selectedItem_4.set(self.matType_id.get())
        self.action.set('add')
        self.controller.show_frame('LocationSingle')

    def edit_entry(self):
        if self.locationLst.get(tk.ANCHOR) != '':
            # location name will uniqly identify record
            self.selectedItem_1.set(self.locationLst.get(tk.ANCHOR))
            self.action.set('update')
            self.controller.show_frame('LocationSingle')
        else:
            msg = 'Please select a location from the list'
            tkMessageBox.showwarning('Input Error', msg)

    def delete_entry(self):
        if self.locationLst.get(tk.ANCHOR) != '':
            if tkMessageBox.askokcancel(
                    'Locations',
                    'delete location?'):
                delete_name = self.locationLst.get(tk.ANCHOR)
                db.delete_record(db.Location, name=delete_name)
                self.locationLst.delete(tk.ANCHOR)
        else:
            msg = 'Please select a template from the list'
            tkMessageBox.showwarning('Input Error', msg)

    def on_close(self):
        self.controller.show_frame('Settings')

    def dynamic_library(self, *args):
        if self.tier.get() == 'LocationBrowse':
            if self.library_id.get() in (1, 2):
                self.selectedItem_2.set(self.library_id.get())
                if self.matType.get() == '':
                    records = db.col_preview(
                        db.Location,
                        'name',
                        library_id=self.library_id.get()
                    )
                else:
                    records = db.col_preview(
                        db.Location,
                        'name',
                        library_id=self.library_id.get(),
                        matType_id=self.matType_id.get())
                self.reloadLst(records)

    def dynamic_material(self, *args):
        if self.tier.get() == 'LocationBrowse':
            if self.matType.get() != '':
                self.matType_id.set(
                    self.matType_by_name[self.matType.get()][0])
                self.selectedItem_4.set(self.matType_id.get())
                if self.library_id.get() in (1, 2):
                    records = db.col_preview(
                        db.Location,
                        'name',
                        library_id=self.library_id.get(),
                        matType_id=self.matType_id.get())
                else:
                    records = db.col_preview(
                        db.Location,
                        'name',
                        matType_id=self.matType_id.get())
                self.reloadLst(records)

    def observer(self, *args):
        # refresh displayed collaborator list on change in self.action
        if self.tier.get() == 'LocationBrowse':
            self.reset_values()
            names = []
            self.reloadLst(names)
            self.matType_choices = ()
            # create indexes
            types = db.col_preview(
                db.MatType,
                'id', 'name')
            for row in types:
                self.matType_choices = self.matType_choices + (row.name, )
                self.matType_by_name[row.name] = (row.id, )
                # self.matType_by_id[row.id] = (row.name, )
            self.matCbx['values'] = self.matType_choices

    def reloadLst(self, records):
        self.locationLst.delete(0, tk.END)
        # filter by selected library and material type
        for row in records:
            self.locationLst.insert(tk.END, row.name)

    def reset_values(self):
        self.selectedItem_1.set('')
        self.selectedItem_3.set(0)
        self.selectedItem_4.set(0)
        self.library_id.set(0)
        self.matType.set('')
        self.matType_id.set(0)


class LocationSingle(tk.Frame):

    def __init__(self, parent, controller, **sharedData):
        tk.Frame.__init__(self, parent)
        # bind shared variables
        self.tier = sharedData['tier']
        self.action = sharedData['action']
        self.selectedItem_1 = sharedData['selectedItem_1']
        self.selectedItem_3 = sharedData['selectedItem_3']
        self.selectedItem_4 = sharedData['selectedItem_4']
        self.tier.trace('w', self.observer)

        # set local variables
        self.controller = controller
        self.id = tk.IntVar()
        self.name = tk.StringVar()
        self.library_id = tk.IntVar()
        self.library_id.trace('w', self.dynamic_branches)
        self.matType_id = tk.IntVar()
        self.matType = tk.StringVar()
        self.branch_id = tk.IntVar()
        self.branch_code = tk.StringVar()
        self.shelf = tk.StringVar()
        self.audnPresent = tk.StringVar()
        self.audnPresent.set('y')

        self.bpl_branches = ()
        self.nypl_branches = ()
        self.branch_choices = ()
        self.branch_by_code = {}
        self.branch_by_id = {}
        self.matType_choices = ()
        self.matType_by_name = {}
        self.matType_by_id = {}

        # configure layout
        self.columnconfigure(0, minsize=72)
        self.columnconfigure(1, minsize=72)
        self.columnconfigure(3, minsize=144)

        # initiate widgets
        ttk.Radiobutton(self, text='BPL',
                        variable=self.library_id, value=1).grid(
            row=0, column=0, sticky='snw')
        ttk.Radiobutton(self, text='NYPL',
                        variable=self.library_id, value=2).grid(
            row=1, column=0, sticky='snw')
        tk.Label(self, text='location shorthand:',
                 font=LBL_FONT).grid(
            row=2, column=0, sticky='snw')
        tk.Entry(self, textvariable=self.name,
                 font=REG_FONT).grid(
            row=3, column=0, columnspan=2, sticky='snew', padx=10)
        tk.Label(self, text='material format:', font=LBL_FONT).grid(
            row=4, column=0, sticky='sne')
        self.matCbx = ttk.Combobox(self, textvariable=self.matType,
                                   state='readonly')
        self.matCbx.grid(
            row=4, column=1, sticky='snew', padx=10, pady=10)
        tk.Label(self, text='branch code:', font=LBL_FONT).grid(
            row=5, column=0, sticky='sne')
        self.branchCbx = ttk.Combobox(self, textvariable=self.branch_code,
                                      state='readonly')
        self.branchCbx.grid(
            row=5, column=1, sticky='snew', padx=10, pady=10)
        tk.Label(self, text='item code:', font=LBL_FONT).grid(
            row=6, column=0, sticky='sne')
        self.shelfCbx = ttk.Combobox(self, textvariable=self.shelf,
                                     state='readonly')
        self.shelfCbx.grid(
            row=6, column=1, sticky='sne', padx=10, pady=10)
        audnChb = tk.Checkbutton(
            self, text='audience designation in Sierra '
            'location code?', variable=self.audnPresent,
            font=LBL_FONT,
            onvalue='y', offvalue='n')
        audnChb.grid(row=7, column=0, columnspan=2, sticky='sne')
        tk.Button(self, text='save', font=BTN_FONT,
                  command=self.on_save,
                  width=15).grid(
            row=8, column=0, padx=10, pady=10)
        tk.Button(self, text='close', font=BTN_FONT,
                  command=self.on_close,
                  width=15).grid(
            row=8, column=1, padx=10, pady=10)

    def on_save(self):
        if self.library_id.get() == 0:
            m = 'please select library to proceed'
            tkMessageBox.showwarning('Input error', m)
        elif self.name.get().strip() == '':
            m = 'please enter location shorthand'
            tkMessageBox.showwarning('Input error', m)
        elif self.matType.get() == '':
            m = 'please select material type to proceed'
            tkMessageBox.showwarning('Input error', m)
        elif self.branch_code.get() == '':
            m = 'please select branch code to proceed'
            tkMessageBox.showwarning('Input error', m)
        else:
            self.matType_id.set(self.matType_by_name[self.matType.get()][0])
            self.branch_id.set(self.branch_by_code[self.branch_code.get()][0])
            new = {'name': self.name.get().strip(),
                   'library_id': self.library_id.get(),
                   'matType_id': self.matType_id.get(),
                   'branch_id': self.branch_id.get(),
                   'shelf': self.shelf.get().strip(),
                   'audnPresent': self.audnPresent.get()}

            # validate input / consider validation via tkinter
            msg = validation.location_form(new)
            if msg is not None:
                tkMessageBox.showerror('Input Error', msg)
            else:
                if self.action.get() == 'add':
                    db.ignore_or_insert(db.Location,
                                        name=new['name'],
                                        library_id=new['library_id'],
                                        matType_id=new['matType_id'],
                                        branch_id=new['branch_id'],
                                        shelf=new['shelf'],
                                        audnPresent=new['audnPresent'])
                if self.action.get() == 'update':
                    db.update_record(db.Location,
                                     id=self.id.get(),
                                     name=new['name'],
                                     library_id=new['library_id'],
                                     matType_id=new['matType_id'],
                                     branch_id=new['branch_id'],
                                     shelf=new['shelf'],
                                     audnPresent=new['audnPresent'])
                self.reset_values()

    def on_close(self):
        self.reset_values()
        self.controller.show_frame('LocationBrowse')

    def dynamic_branches(self, *args):
        if self.library_id.get() == 1:
            self.branch_choices = self.bpl_branches
            self.shelf_choices = self.bpl_shelves
        if self.library_id.get() == 2:
            self.branch_choices = self.nypl_branches
            self.shelf_choices = self.nypl_shelves
        self.branchCbx['values'] = self.branch_choices
        self.shelfCbx['values'] = self.shelf_choices

    def reset_values(self):
        self.action.set('add')
        self.id.set(0)
        self.name.set('')
        self.branch_id.set(0)
        self.branch_code.set('')
        # self.shelf.set('')
        self.audnPresent.set('y')

    def observer(self, *args):
        if self.tier.get() == 'LocationSingle':
            # reset local var & indexes
            self.bpl_branches = ()
            self.nypl_branches = ()
            self.branch_choices = ()
            self.branch_by_code = {}
            self.branch_by_id = {}
            self.matType_choices = ()
            self.matType_by_name = {}
            self.matType_by_id = {}
            self.nypl_shelves = ()
            self.bpl_shelves = ()

            # re-create indexes
            matTypes = db.col_preview(
                db.MatType,
                'id', 'name')
            for row in matTypes:
                self.matType_choices = self.matType_choices + (row.name, )
                self.matType_by_name[row.name] = (row.id, )
                self.matType_by_id[row.id] = (row.name, )
            self.matCbx['values'] = self.matType_choices
            branches = db.col_preview(
                db.Branch,
                'code', 'id', 'library_id')
            for branch in branches:
                if branch.library_id == 1:
                    self.bpl_branches = self.bpl_branches + (branch.code, )
                if branch.library_id == 2:
                    self.nypl_branches = self.nypl_branches + (branch.code, )
                self.branch_by_code[branch.code] = (branch.id, )
                self.branch_by_id[branch.id] = (branch.code, )
            shelf_records = db.col_preview(
                db.ShelfCode,
                'code', 'library_id')
            for shelf_record in shelf_records:
                if shelf_record.library_id == 1:
                    self.bpl_shelves = self.bpl_shelves + (shelf_record.code, )
                if shelf_record.library_id == 2:
                    self.nypl_shelves = self.nypl_shelves + (shelf_record.code, )

            # prepopulate library and matType if selected in LocationBrowse    
            if self.selectedItem_3.get() in (1, 2):
                self.library_id.set(self.selectedItem_3.get())
            if self.selectedItem_4.get() != 0:
                self.matType.set(
                    self.matType_by_id[self.selectedItem_4.get()][0])
            if self.action.get() == 'update':
                name = self.selectedItem_1.get()
                record = db.retrieve_record(db.Location,
                                            name=name)
                self.id.set(record.id)
                self.name.set(record.name)
                self.library_id.set(record.library_id)
                self.matType_id.set(record.matType_id)
                self.branch_id.set(record.branch_id)
                self.shelf.set(record.shelf)
                self.audnPresent.set(record.audnPresent)
                self.matType.set(self.matType_by_id[record.matType_id][0])
                self.branch_code.set(self.branch_by_id[record.branch_id][0])


class ShelfCodes(tk.Frame):

    def __init__(self, parent, controller, **sharedData):
        tk.Frame.__init__(self, parent)

        # shared variables
        self.tier = sharedData['tier']
        self.action = sharedData['action']
        # self.tier.trace('w', self.observer)

        # local variables
        self.controller = controller
        self.library_id = tk.IntVar()
        self.library_id.trace('w', self.dynamic_codes)
        self.shelf_code = tk.StringVar()

        # configure main widget layout
        self.rowconfigure(0, minsize=10)

        # configure labeled frame layout
        self.group = tk.LabelFrame(self, text='item codes', font=LBL_FONT)
        self.group.columnconfigure(0, minsize=20)
        self.group.rowconfigure(0, minsize=20)
        self.group.rowconfigure(5, minsize=60)
        self.group.rowconfigure(7, minsize=20)
        self.group.grid(row=0, column=0, sticky='snew', padx=10, pady=10)

        # initiate widgets
        ttk.Radiobutton(self.group, text='BPL',
                        variable=self.library_id, value=1).grid(
            row=0, column=1, sticky='snw', padx=10)
        ttk.Radiobutton(self.group, text='NYPL',
                        variable=self.library_id, value=2).grid(
            row=1, column=1, sticky='snw', padx=10)
        scrollbar = tk.Scrollbar(self.group, orient=tk.VERTICAL)
        scrollbar.grid(
            row=3, column=3, sticky='nsw', rowspan=4, padx=2, pady=10)
        self.shelfLst = tk.Listbox(self.group, font=REG_FONT,
                                   yscrollcommand=scrollbar.set)
        self.shelfLst.grid(
            row=3, column=1, columnspan=2, sticky='snew', rowspan=4, pady=10)
        scrollbar['command'] = self.shelfLst.yview
        tk.Button(self.group, text='add', font=BTN_FONT,
                  width=15,
                  command=self.on_add).grid(
            row=3, column=4, sticky='snw', padx=10, pady=10)
        self.shelfEnt = tk.Entry(self.group, textvariable=self.shelf_code,
                                 font=REG_FONT)
        self.shelfEnt.grid(
            row=3, column=5, sticky='snw', padx=10, pady=10)
        tk.Button(self.group, text='delete', font=BTN_FONT,
                  width=15,
                  command=self.on_delete).grid(
            row=4, column=4, sticky='snw', padx=10, pady=10)
        tk.Button(self.group, text='close', font=BTN_FONT,
                  width=15,
                  command=self.on_close).grid(
            row=6, column=4, sticky='snw', padx=10, pady=10)

    def on_add(self):
        if self.shelf_code.get() == '':
            m = 'please enter a new code'
            tkMessageBox.showwarning('Input error', m)
        elif self.library_id.get() == 0:
            m = 'please select a library'
            tkMessageBox.showwarning('Input error', m)
        else:
            if len(self.shelf_code.get()) > 3:
                m = 'shelf code cannot be longer than 3 characters'
                tkMessageBox.showwarning('Input error', m)
            else:
                record = db.retrieve_record(
                    db.ShelfCode,
                    library_id=self.library_id.get(),
                    code=self.shelf_code.get().strip())
                if record is not None:
                    m = 'location already exists'
                    tkMessageBox.showerror('Database error', m)
                else:
                    db.ignore_or_insert(
                        db.ShelfCode,
                        library_id=self.library_id.get(),
                        code=self.shelf_code.get().strip())
                    self.shelf_code.set('')
                    self.refreshLst()

    def on_delete(self):
        if self.library_id.get() == 0:
            m = 'please select a library'
            tkMessageBox.showwarning('Input error', m)
        elif self.shelfLst.get(tk.ANCHOR) == '':
            m = 'please select code for deletion'
            tk.MessageBox.showwarning('Input error', m)
        else:
            code = self.shelfLst.get(tk.ANCHOR)
            db.delete_record(
                db.ShelfCode,
                library_id=self.library_id.get(),
                code=code)
            self.shelfLst.delete(tk.ANCHOR)

    def on_close(self):
        self.reset_form()
        self.controller.show_frame('Settings')

    def refreshLst(self):
        self.shelfLst.delete(0, tk.END)
        records = db.col_preview(
            db.ShelfCode,
            'code',
            library_id=self.library_id.get())
        for record in records:
            self.shelfLst.insert(tk.END, record.code)

    def dynamic_codes(self, *args):
        if self.tier.get() == 'ShelfCodes':
            self.refreshLst()

    def reset_form(self):
        self.library_id.set(0)
        self.shelf_code.set('')


class DistributionBrowse(tk.Frame):

    def __init__(self, parent, controller, **sharedData):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        # bind shared variables
        self.tier = sharedData['tier']
        self.tier.trace('w', self.observer)
        self.action = sharedData['action']
        self.selectedItem_1 = sharedData['selectedItem_1']
        self.selectedItem_3 = sharedData['selectedItem_3']

        # bind local variables
        self.library_id = tk.IntVar()
        # display lst dynamically based on radiobutton
        self.library_id.trace('w', self.dynamic_selection)
        self.name = tk.StringVar()
        self.lang_id = tk.IntVar()

        # configure layout
        self.browseFrm = ttk.LabelFrame(self, borderwidth=5,
                                        text='distribution templates',
                                        padding=5)
        self.browseFrm.grid(row=0, column=0, sticky='snew')

        self.browseFrm.columnconfigure(0, minsize=200)
        self.browseFrm.columnconfigure(1, minsize=72)
        self.browseFrm.columnconfigure(2, minsize=10)
        self.browseFrm.columnconfigure(3, minsize=50)
        # self.browseFrm.columnconfigure(4, minsize=144)
        self.browseFrm.rowconfigure(9, minsize=250)

        # initiate widgets
        ttk.Radiobutton(self.browseFrm, text='BPL',
                        variable=self.library_id, value=1).grid(
            row=0, column=0, sticky='snew')
        ttk.Radiobutton(self.browseFrm, text='NYPL',
                        variable=self.library_id, value=2).grid(
            row=1, column=0, sticky='snew')
        tk.Label(self.browseFrm, text='name:', font=LBL_FONT).grid(
            row=2, column=0, columnspan=2, sticky='snw')
        scrollbar = tk.Scrollbar(self.browseFrm, orient=tk.VERTICAL)
        scrollbar.grid(
            row=3, column=2, sticky='nsw', rowspan=10, padx=2, pady=10)
        self.distrLst = tk.Listbox(self.browseFrm, font=REG_FONT,
                                   yscrollcommand=scrollbar.set)
        self.distrLst.bind('<Double-Button-1>', self.edit_entry)
        self.distrLst.grid(
            row=3, column=0, columnspan=2, sticky='snew', rowspan=10,
            pady=10)
        scrollbar['command'] = self.distrLst.yview

        # buttons of the left panel
        tk.Button(self.browseFrm, text='add', font=BTN_FONT,
                  command=self.add_entry,
                  width=15).grid(
            row=3, column=3, sticky='snew', padx=10, pady=10)
        tk.Button(self.browseFrm, text='edit', font=BTN_FONT,
                  command=self.edit_entry,
                  width=15).grid(
            row=4, column=3, sticky='snew', padx=10, pady=10)
        tk.Button(self.browseFrm, text='delete', font=BTN_FONT,
                  command=self.delete_entry,
                  width=15).grid(
            row=5, column=3, sticky='snew', padx=10, pady=10)
        tk.Button(self.browseFrm, text='close', font=BTN_FONT,
                  width=15,
                  command=lambda: controller.show_frame(
                      'Settings')).grid(
            row=10, column=3, sticky='snew', padx=10, pady=10)

    def add_entry(self):
        if self.library_id.get() == 0:
            msg = 'Please select library'
            tkMessageBox.showwarning('Input Error', msg)
        else:
            self.selectedItem_3.set(self.library_id.get())
            self.action.set('add')
            self.controller.show_frame('DistributionSingle')

    def delete_entry(self):
        if self.distrLst.get(tk.ANCHOR) != '':
            delete_name = self.distrLst.get(tk.ANCHOR)
            db.delete_record(db.DistrTemplate, name=delete_name)
            self.distrLst.delete(tk.ANCHOR)
        else:
            msg = 'Please select a template from the list'
            tkMessageBox.showwarning('Input Error', msg)

    def edit_entry(self, *args):
        if self.distrLst.get(tk.ANCHOR) != '':
            self.selectedItem_1.set(self.distrLst.get(tk.ANCHOR))
            self.selectedItem_3.set(self.library_id.get())
            self.action.set('update')
            self.controller.show_frame('DistributionSingle')
        else:
            msg = 'Please select a template from the list'
            tkMessageBox.showwarning('Input Error', msg)

    def reloadLst(self, records):
        self.distrLst.delete(0, tk.END)
        for row in records:
            self.distrLst.insert(tk.END, row.name)

    def observer(self, *args):
        if (self.tier.get()):
            if self.tier.get() == 'DistributionBrowse':
                self.library_id.set(0)
                records = []
                self.reloadLst(records)

    def dynamic_selection(self, *args):
        if self.library_id.get() == 1 or self.library_id.get() == 2:
            records = db.col_preview(
                db.DistrTemplate,
                'name',
                library_id=self.library_id.get())
            self.reloadLst(records)


class DistributionSingle(tk.Frame):
    # this window needs to be redone to improve interface
    # see OrderSingle interface as an example what should be done here

    def __init__(self, parent, controller, **sharedData):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        # bind shared variables
        self.tier = sharedData['tier']
        self.tier.trace('w', self.observer)
        self.action = sharedData['action']
        self.selectedItem_1 = sharedData['selectedItem_1']
        self.library_id = sharedData['selectedItem_3']

        # bind local variables
        self.library = tk.StringVar()
        self.distrTemplate_id = tk.IntVar()
        self.distrCode_id = tk.IntVar()
        self.name = tk.StringVar()
        self.code = tk.StringVar()
        self.code.trace('w', self.activate_code)
        self.location = tk.StringVar()
        self.quantity = tk.IntVar()
        self.quantity.set(1)
        self.lang = tk.StringVar()
        self.last_row = 0
        self.format_filter = tk.StringVar()
        self.format_filter.set('all')
        self.format_filter.trace('w', self.dynamic_locations)
        self.itemcode_filter = tk.StringVar()
        self.itemcode_filter.set('all')
        self.itemcode_filter.trace('w', self.dynamic_locations)

        self.lang_by_name = {}
        self.lang_by_id = {}
        self.lang_choices = ()

        self.location_by_name = {}

        # bind variables for preview
        self.active_code_id = tk.StringVar()

        # configure layout
        self.mainFrm = ttk.LabelFrame(self,
                                      text='Recording distribution template',
                                      padding=5)
        self.mainFrm.grid(
            row=0, column=0, sticky='snew')
        self.mainFrm.columnconfigure(0, minsize=20)
        self.mainFrm.columnconfigure(1, minsize=20)
        self.mainFrm.columnconfigure(2, minsize=30)
        self.mainFrm.columnconfigure(3, minsize=30)
        self.mainFrm.columnconfigure(4, minsize=30)
        self.mainFrm.columnconfigure(5, minsize=30)
        self.mainFrm.columnconfigure(6, minsize=30)
        # self.mainFrm.columnconfigure(10, weight=3, minsize=350)

        # initilize widgets
        tk.Label(self.mainFrm, text='library:', font=LBL_FONT).grid(
            row=0, column=0, columnspan=2, sticky='snw', pady=5, padx=5)
        self.libraryLbl = tk.Label(
            self.mainFrm, textvariable=self.library, font=HDG_FONT)
        self.libraryLbl.grid(
            row=0, column=2, columnspan=2, sticky='snw', pady=5, padx=5)
        tk.Label(self.mainFrm, text='language:', font=LBL_FONT).grid(
            row=0, column=3, columnspan=2, sticky='snw', pady=5, padx=5)
        self.langCbx = ttk.Combobox(self.mainFrm, textvariable=self.lang,
                                    state='readonly')
        self.langCbx.grid(
            row=0, column=5, columnspan=3, sticky='snw', pady=5, padx=5)

        tk.Label(self.mainFrm, text='enter distribution template name:',
                 font=LBL_FONT).grid(
            row=1, column=0, columnspan=3, sticky='snw', pady=5)
        tk.Entry(self.mainFrm, textvariable=self.name, font=REG_FONT).grid(
            row=1, column=3, columnspan=4, sticky='snew', pady=5, padx=5)
        tk.Label(self.mainFrm, text='code', font=HDG_FONT).grid(
            row=2, column=1, sticky='snew', padx=5)
        tk.Label(self.mainFrm, text='distribution', font=HDG_FONT).grid(
            row=2, column=2, sticky='snw', padx=5)

        # scrollable canvas
        self.xscrollbar = tk.Scrollbar(self.mainFrm, orient=tk.HORIZONTAL)
        self.xscrollbar.grid(
            row=18, column=1, columnspan=10, sticky='nwe', padx=10)
        self.yscrollbar = tk.Scrollbar(self.mainFrm, orient=tk.VERTICAL)
        self.yscrollbar.grid(
            row=3, column=0, rowspan=15, sticky='nsw')
        self.preview_base = tk.Canvas(
            self.mainFrm,
            width=830,
            height=490,  # find a way to adjust based on preview frm size
            xscrollcommand=self.xscrollbar.set,
            yscrollcommand=self.yscrollbar.set)
        self.preview_base.grid(
            row=3, column=1, columnspan=10, sticky='nsw', rowspan=15, padx=10)

        # right panel filters frame
        self.filterFrm = ttk.LabelFrame(self.mainFrm, text='location filters',
                                        padding=5)
        self.filterFrm.grid(
            row=0, column=11, rowspan=3, columnspan=2, sticky='snew', padx=2)
        self.formatCbx = ttk.Combobox(self.filterFrm,
                                      textvariable=self.format_filter,
                                      state='readonly',
                                      width=15)
        self.formatCbx.grid(
            row=0, column=0, sticky='snw', padx=2, pady=2)
        tk.Label(self.filterFrm, text='format', font=LBL_FONT).grid(
            row=0, column=12, sticky='snw', padx=2, pady=2)
        self.itemcodeCbx = ttk.Combobox(self.filterFrm,
                                        textvariable=self.itemcode_filter,
                                        state='readonly',
                                        width=15)
        self.itemcodeCbx.grid(
            row=1, column=0, sticky='snw', padx=2, pady=2)
        tk.Label(self.filterFrm, text='item code', font=LBL_FONT).grid(
            row=1, column=12, sticky='snw', padx=2, pady=2)

        # right panel add new code frame
        self.codeFrm = ttk.LabelFrame(self.mainFrm, text='code', padding=5)
        self.codeFrm.grid(
            row=3, column=11, columnspan=2, sticky='snew', padx=2)
        self.codeCbx = ttk.Combobox(self.codeFrm, textvariable=self.code,
                                    postcommand=self.dynamic_codes,
                                    width=5)
        self.codeCbx.grid(
            row=0, column=0, sticky='snw', padx=2, pady=2)
        tk.Button(self.codeFrm, text='add',
                  font=REG_FONT,
                  command=self.new_code,
                  width=10).grid(
            row=0, column=1, sticky='snw', padx=2, pady=2)
        tk.Button(self.codeFrm, text='delete',
                  font=REG_FONT,
                  command=self.delete_code,
                  width=10).grid(
            row=0, column=2, sticky='snw', padx=2, pady=2)

        # right panel add distribution frame
        self.addFrm = ttk.LabelFrame(self.mainFrm, text="code's distribution",
                                     padding=5)
        self.addFrm.grid(
            row=4, column=11, columnspan=2, sticky='snew', padx=2)
        self.addFrm.rowconfigure(3, minsize=20)

        tk.Label(self.addFrm, text='code', font=LBL_FONT, width=5).grid(
            row=0, column=1, sticky='snw', padx=5, pady=2)
        self.active_codeLbl = tk.Label(self.addFrm,
                                       textvariable=self.code,
                                       font=HDG_FONT)
        self.active_codeLbl.grid(
            row=0, column=2, sticky='snew', padx=2, pady=2)

        tk.Label(self.addFrm, text='location', font=LBL_FONT, width=10).grid(
            row=1, column=0, columnspan=2, sticky='snw', padx=5, pady=2)
        tk.Label(self.addFrm, text='qty', font=LBL_FONT, width=5).grid(
            row=1, column=2, sticky='snw', padx=5, pady=2)

        self.locationCbx = ttk.Combobox(self.addFrm,
                                        textvariable=self.location,
                                        state='readonly',
                                        width=15)
        self.locationCbx.grid(
            row=2, column=0, columnspan=2, sticky='snw', padx=2, pady=2)
        ttk.Combobox(self.addFrm, textvariable=self.quantity,
                     values=tuple(range(1, 51)),
                     state='readonly',
                     width=5).grid(
            row=2, column=2, sticky='snw', padx=2, pady=2)

        tk.Button(self.addFrm, text='add', font=BTN_FONT,
                  width=10,
                  command=self.add_distr).grid(
            row=2, column=4, padx=5, pady=2)

        # list of locations for particular code that can be used for removal
        distrLst_scrollbar = tk.Scrollbar(self.addFrm, orient=tk.VERTICAL)
        distrLst_scrollbar.grid(
            row=4, column=3, sticky='nsw', rowspan=15, padx=2, pady=2)
        self.distrLst = tk.Listbox(self.addFrm, font=REG_FONT,
                                   height=14,
                                   yscrollcommand=distrLst_scrollbar.set)
        self.distrLst.bind('<Double-Button-1>', self.remove_distr)
        self.distrLst.grid(
            row=4, column=0, columnspan=3, sticky='snew', rowspan=15,
            padx=2, pady=2)
        distrLst_scrollbar['command'] = self.distrLst.yview
        tk.Button(self.addFrm, text='remove',
                  font=REG_FONT,
                  width=10,
                  command=self.remove_distr).grid(
            row=4, column=4, sticky='nw', padx=5, pady=2)

        tk.Button(self.mainFrm, text='save', font=BTN_FONT,
                  width=10,
                  anchor=tk.CENTER,
                  command=self.on_save).grid(
            row=17, column=11, padx=10, pady=10)
        tk.Button(self.mainFrm, text='close', font=BTN_FONT,
                  width=10,
                  anchor=tk.CENTER,
                  command=self.on_close).grid(
            row=17, column=12, padx=10, pady=10)

    def preview(self):
        self.preview_frame = tk.Frame(
            self.preview_base)
        self.xscrollbar.config(command=self.preview_base.xview)
        self.yscrollbar.config(command=self.preview_base.yview)
        self.preview_base.create_window(
            (0, 0), window=self.preview_frame, anchor="nw",
            tags="self.preview_frame")
        self.preview_frame.bind("<Configure>", self.onFrameConfigure)

    def onFrameConfigure(self, event):
        self.preview_base.config(scrollregion=self.preview_base.bbox('all'))

    def display_code(self, code_data, r):
        # generates single frame where distribtion code and it's details
        # are displayed
        distrFrm = tk.Frame(self.preview_frame)
        distrFrm.grid(
            row=r, column=0, sticky='snew', padx=5)
        selectBtn = ttk.Radiobutton(distrFrm, variable=self.active_code_id,
                                    command=self.edit_code)
        selectBtn.grid(
            row=0, column=0, rowspan=3, sticky='snw', padx=5, pady=5)
        selectBtn['value'] = selectBtn.winfo_parent()
        code = tk.Label(distrFrm,
                        font=REG_FONT)
        code.grid(
            row=0, column=1, sticky='snw', pady=5, padx=5)
        code['text'] = code_data[0].code

        # distribution location string
        distr = tk.Label(distrFrm,
                         font=REG_FONT)
        distr.grid(
            row=0, column=2, sticky='snw', pady=5, padx=5)
        items = []
        for item in code_data[1]:
            if item[2]:
                items.append(item[0] + '(' + str(item[1].quantity) + ')')

        distr['text'] = ','.join(items)

        # add to widget index
        self.distr_data[
            str(selectBtn.winfo_parent())] = {'code_data': code_data,
                                              'distr_str': distr['text'],
                                              'delete_code': False,
                                              'selectBtn_widget': selectBtn,
                                              'code_widget': code,
                                              'distr_widget': distr,
                                              'frame_widget': distrFrm}
        # keep track of last row
        self.last_row = r
        return str(selectBtn.winfo_parent())

    def on_save(self):
        # validate if requried elements are present
        correct = True
        if self.name.get() == '':
            m = 'Please enter template name'
            tkMessageBox.showerror('Input error', m)
            correct = False
        if self.lang.get() == '':
            m = 'Please select language'
            tkMessageBox.showerror('Input error', m)
            correct = False
        # add validation for codes and distributions

        if correct:
            if self.distrTemplate_id.get() == 0:
                new_record = db.ignore_or_insert(
                    db.DistrTemplate,
                    library_id=self.library_id.get(),
                    name=self.name.get().strip(),
                    lang_id=self.lang_by_name[self.lang.get()][0])

                # update id or DistrCode records stored in mememory
                new_template = db.retrieve_last(
                    db.DistrTemplate)
                for item in self.distr_data.itervalues():
                    item['code_data'][0].distrTemplate_id = new_template.id
                if not new_record:
                    tkMessageBox.showerror('Database error', new_record)
            else:
                db.update_record(
                    db.DistrTemplate,
                    id=self.distrTemplate_id.get(),
                    library_id=self.library_id.get(),
                    name=self.name.get().strip(),
                    lang_id=self.lang_by_name[self.lang.get()][0])

            codes_for_removal = []
            distr_for_removal = []

            for key, item in self.distr_data.iteritems():
                if item['delete_code']:
                    # delete any disribution codes and its locations
                    # if marked for del
                    if item['code_data'][0].id is not None:
                        db.delete_record(
                            db.DistrCode,
                            id=item['code_data'][0].id)
                    codes_for_removal.append(key)
                else:
                    # delete any location marked for removal
                    new_distr = []
                    for distr in item['code_data'][1]:
                        if distr[2]:
                            new_distr.append(distr[1])
                        else:
                            distr_for_removal.append(distr)

                    item['code_data'][0].distrLocQtys = new_distr
                    db.merge_object(item['code_data'][0])

            for key in codes_for_removal:
                self.distr_data.pop(key)

            self.action.set('update')
            self.observer()
            tkMessageBox.showinfo('Saving', 'distribution has been saved')

    def new_code(self):
        # remove whitespaces and change to uppercase
        self.distrLst.delete(0, tk.END)
        self.code.set(self.code.get().strip())
        code_chars = []
        for character in self.code.get():
            try:
                character = character.upper()
                code_chars.append(character)
            except:
                code_char.append(character)
        self.code.set(''.join(code_chars))

        # check if already displayed
        if self.code.get() == '':
            m = 'please provide code'
            tkMessageBox.showwarning('Input error', m)
        elif self.code.get() in self.codeCbx['values']:
            m = 'code already created'
            tkMessageBox.showwarning('Input error', m)
        else:
            if self.codeCbx['values'] == '':
                self.codeCbx['values'] = (self.code.get(), )
            else:
                self.codeCbx['values'] = self.codeCbx['values'] + \
                    (self.code.get(), )
            code_record = db.create_db_object(
                db.DistrCode,
                code=self.code.get(),
                distrTemplate_id=self.distrTemplate_id.get())
            data = (code_record, [])
            active_widget = self.display_code(data, self.last_row + 1)
            self.active_code_id.set(active_widget)

    def activate_code(self, *args):
        code_chars = []
        for character in self.code.get():
            try:
                character = character.upper()
                code_chars.append(character)
            except:
                code_char.append(character)
        self.code.set(''.join(code_chars))

        if self.code.get() != '' and \
                self.code.get() in self.codeCbx['values']:

            for key, value in self.distr_data.iteritems():
                if value['code_data'][0].code == self.code.get():
                    self.active_code_id.set(key)
            self.edit_code()

    def edit_code(self):
        # dynamically updates code & location list on the right panel
        active_code = self.distr_data[self.active_code_id.get()]
        # update code
        self.code.set(active_code['code_data'][0].code)
        # update distr list
        self.distrLst.delete(0, tk.END)
        for distr in active_code['distr_str'].split(','):
            self.distrLst.insert(tk.END, distr)

    def delete_code(self):
        if self.active_code_id.get() == '':
            m = 'please select first code to be deleted'
            tkMessageBox.showinfo('deletion', m)
        else:
            m = 'Are you sure to delete the code?\n' \
                'This removes distribution code from being displayed only.\n' \
                'Please save the template to make it permanent.'
            if tkMessageBox.askokcancel('deletion', m):
                self.distr_data[
                    self.active_code_id.get()]['delete_code'] = True
                self.distrLst.delete(0, tk.END)
                self.code.set('')
                self.distr_data[
                    self.active_code_id.get()]['frame_widget'].destroy()

    def remove_distr(self, *args):
        active_data = self.distr_data[self.active_code_id.get()]
        for distr in active_data['code_data'][1]:
            if distr[0] == self.distrLst.get(
                    tk.ANCHOR)[:self.distrLst.get(tk.ANCHOR).find('(')]:
                distr[2] = False
                distr_old = active_data['distr_str'].split(',')
                distr_new = []
                for item in distr_old:
                    if item != self.distrLst.get(tk.ANCHOR):
                        distr_new.append(item)
                active_data['distr_str'] = ','.join(distr_new)
                active_data['distr_widget']['text'] = active_data['distr_str']
                self.edit_code()

    def on_close(self):
        self.reset_form()
        self.controller.show_frame('DistributionBrowse')

    def add_distr(self):
        # add validation for duplicate locations
        # find appropriate place
        if self.location.get() == '':
            m = 'please add location'
            tkMessageBox.showwarning('Input error', m)
        elif self.location.get() in self.distr_data[
                self.active_code_id.get()]['distr_str']:
            m = 'location already added to the distribution'
            tkMessageBox.showwarning('Input error', m)
        else:
            distr_records = self.distr_data[
                self.active_code_id.get()]['code_data'][1]
            location_id = self.location_by_name[self.location.get()]
            distr_record = db.create_db_object(
                db.DistrLocQuantity,
                location_id=location_id,
                quantity=self.quantity.get())
            distr_records.append([self.location.get(), distr_record, True])

            # update display
            items = []
            for item in distr_records:
                if item[2]:
                    items.append(item[0] + '(' + str(item[1].quantity) + ')')

            self.distr_data[
                self.active_code_id.get()][
                'distr_widget']['text'] = ','.join(items)
            self.distr_data[
                self.active_code_id.get()]['distr_str'] = ','.join(items)
            self.edit_code()

    def dynamic_codes(self, *args):
        # display dinamically distribution codes on the right panel
        codes = []
        for key, value in self.distr_data.iteritems():
            if value['delete_code'] is False:
                codes.append(value['code_data'][0].code)
        self.codeCbx['values'] = sorted(codes)

    def dynamic_locations(self, *args):

        if self.format_filter.get() != 'all':
            format_id = self.matTypes_by_name[
                self.format_filter.get()][0]
        else:
            format_id = None

        if self.itemcode_filter.get() != 'all':
            itemcode = self.itemcode_filter.get()
        else:
            itemcode = None

        filters = {'library_id': self.library_id.get(),
                   'matType_id': format_id ,
                   'shelf': itemcode}
        kwargs = {}
        for key, value in filters.iteritems():
            if value is not None:
                kwargs[key] = value
        records = db.col_preview(
            db.Location,
            'name',
            **kwargs)

        locations_filtered = ()
        for row in records:
            locations_filtered += (row.name, )
        self.locationCbx['values'] = locations_filtered

    def observer(self, *args):
        if self.tier.get() == 'DistributionSingle':
            try:
                self.preview_frame.destroy()
            except:
                pass

            # reset indexes
            self.distr_data = {}
            self.lang_by_name = {}
            self.lang_by_id = {}
            self.lang_choices = ()
            self.location_by_name = {}
            self.codeCbx['values'] = ()
            self.format_filter.set('all')
            self.itemcode_filter.set('all')

            # library
            if self.library_id.get() == 1:
                self.library.set('BPL')
            if self.library_id.get() == 2:
                self.library.set('NYPL')

            # create language index
            langs = db.col_preview(db.Lang, 'id',
                                   'code', 'name')
            for row in langs:
                self.lang_by_name[row.name] = (row.id, )
                self.lang_by_id[row.id] = (row.name, )
                self.lang_choices = self.lang_choices + (row.name, )

            self.langCbx['values'] = sorted(self.lang_choices)

            # available locations
            locations = ()
            records = db.col_preview(
                db.Location, 'name', library_id=self.library_id.get())
            for row in records:
                locations += (row.name, )
                self.location_by_name[row.name] = row.id
            self.locationCbx['values'] = sorted(locations)

            # itemcode filter options
            itemcodes = ()
            records = db.col_preview(
                db.ShelfCode,
                'code',
                library_id=self.library_id.get()
            )
            for row in records:
                itemcodes += (row.code, )
            self.itemcodeCbx['values'] = sorted(itemcodes + ('all', ))

            # matType filter options and index
            self.matTypes_by_name = {}
            matTypes = ()
            records = db.retrieve_all(
                db.MatType,
                'lib_joins')
            for record in records:
                for row in record.lib_joins:
                    if row.library_id == self.library_id.get():
                        self.matTypes_by_name[record.name] = (record.id, )
                        matTypes += (record.name, )
            self.formatCbx['values'] = sorted(matTypes + ('all', ))

            # initiate preview frame
            self.preview()

            if self.action.get() == 'update':
                # popluate form
                distr_code = []
                template = db.retrieve_record(
                    db.DistrTemplate,
                    name=self.selectedItem_1.get()
                )
                self.distrTemplate_id.set(template.id)
                self.lang.set(self.lang_by_id[template.lang_id][0])
                self.name.set(template.name)
                distr_codes_records = db.retrieve_all(
                    db.DistrCode,
                    'distrLocQtys',
                    distrTemplate_id=template.id)

                # retrieve locations for each code
                for code in distr_codes_records:
                    locs_qtys = []
                    for loc_qty_record in code.distrLocQtys:
                        location = db.retrieve_record(
                            db.Location,
                            id=loc_qty_record.location_id)
                        locs_qtys.append([location.name, loc_qty_record, True])
                    distr_code.append((code, locs_qtys))

                # sent to display generator
                r = 0
                for code in distr_code:
                    self.display_code(code, r)
                    r += 1
                # update codes in codeCbx list
                self.dynamic_codes()
            else:
                self.reset_form()
                self.preview()

    def reset_form(self):
        self.preview_frame.destroy()
        self.distrTemplate_id.set(0)
        self.distrCode_id.set(0)
        self.name.set('')
        self.code.set('')
        self.location.set('')
        self.quantity.set(1)
        self.lang.set('')
        self.distrLst.delete(0, tk.END)
        self.active_code_id.set('')
        # enter 'add new' mode on reset
        self.action.set('add')


class FundBrowse(tk.Frame):

    def __init__(self, parent, controller, **sharedData):
        tk.Frame.__init__(self, parent)
        # bind shared variables
        self.controller = controller
        self.tier = sharedData['tier']
        self.tier.trace('w', self.observer)
        self.action = sharedData['action']
        self.selectedItem_1 = sharedData['selectedItem_1']
        self.selectedItem_3 = sharedData['selectedItem_3']

        # bind local variables
        self.library_id = tk.IntVar()
        # display lst dynamically based on radiobutton
        self.library_id.trace('w', self.dynamic_selection)
        self.code = tk.StringVar()
        self.desc = tk.StringVar()

        # configure layout
        self.columnconfigure(0, minsize=72)
        self.columnconfigure(1, minsize=72)
        self.columnconfigure(2, minsize=10)
        self.columnconfigure(3, minsize=50)
        self.columnconfigure(4, minsize=144)
        self.rowconfigure(9, minsize=50)

        # initiate widgets
        ttk.Radiobutton(self, text='BPL',
                        variable=self.library_id, value=1).grid(
            row=0, column=0, sticky='snew')
        ttk.Radiobutton(self, text='NYPL',
                        variable=self.library_id, value=2).grid(
            row=1, column=0, sticky='snew')
        tk.Label(self, text='fund codes:', font=LBL_FONT).grid(
            row=2, column=0, columnspan=2, sticky='snw')
        scrollbar = tk.Scrollbar(self, orient=tk.VERTICAL)
        scrollbar.grid(
            row=3, column=2, sticky='nsw', rowspan=10, padx=2, pady=10)
        self.fundLst = tk.Listbox(self, font=REG_FONT,
                                  yscrollcommand=scrollbar.set)
        self.fundLst.bind('<Double-Button-1>', self.edit_entry)
        self.fundLst.grid(
            row=3, column=0, columnspan=2, sticky='snew', rowspan=10,
            pady=10)
        scrollbar['command'] = self.fundLst.yview
        # buttons of the left panel
        tk.Button(self, text='add', font=BTN_FONT,
                  command=self.add_entry,
                  width=15).grid(
            row=3, column=3, sticky='snew', padx=10, pady=10)
        tk.Button(self, text='edit', font=BTN_FONT,
                  command=self.edit_entry,
                  width=15).grid(
            row=4, column=3, sticky='snew', padx=10, pady=10)
        tk.Button(self, text='delete', font=BTN_FONT,
                  command=self.delete_entry,
                  width=15).grid(
            row=5, column=3, sticky='snew', padx=10, pady=10)
        tk.Button(self, text='close', font=BTN_FONT,
                  width=15,
                  command=lambda: controller.show_frame(
                      'Settings')).grid(
            row=10, column=3, sticky='snew', padx=10, pady=10)

    def add_entry(self):
        if self.library_id.get() not in (1, 2):
            msg = 'Please select library'
            tkMessageBox.showwarning('Input Error', msg)
        else:
            self.action.set('add')
            self.selectedItem_3.set(self.library_id.get())
            self.controller.show_frame('FundSingle')

    def edit_entry(self):
        if self.fundLst.get(tk.ANCHOR) != '':
            self.selectedItem_1.set(self.fundLst.get(tk.ANCHOR))
            self.selectedItem_3.set(self.library_id.get())
            self.action.set('update')
            self.controller.show_frame('FundSingle')
        else:
            msg = 'Please select library and fund code'
            tkMessageBox.showwarning('Input Error', msg)

    def delete_entry(self):
        if self.fundLst.get(tk.ANCHOR) != '':
            if tkMessageBox.askokcancel(
                    'Funds',
                    'delete fund?'):
                code = self.fundLst.get(tk.ANCHOR)
                db.delete_record(db.Fund, code=code)
                self.fundLst.delete(tk.ANCHOR)
        else:
            msg = 'Please select library and fund code from the list'
            tkMessageBox.showwarning('Input Error', msg)

    def reloadLst(self, records):
        self.fundLst.delete(0, tk.END)
        for row in records:
            self.fundLst.insert(tk.END, row.code)

    def dynamic_selection(self, *args):
        if self.library_id.get() == 1 or self.library_id.get() == 2:
            records = db.col_preview(
                db.Fund,
                'code',
                library_id=self.library_id.get())
            self.reloadLst(records)

    def observer(self, *args):
        if self.tier.get() == 'FundBrowse':
            self.library_id.set(0)
            records = []
            self.reloadLst(records)


class FundSingle(tk.Frame):

    def __init__(self, parent, controller, **sharedData):
        tk.Frame.__init__(self, parent)

        # bind shared variables
        self.tier = sharedData['tier']
        self.action = sharedData['action']
        self.selectedItem_1 = sharedData['selectedItem_1']
        self.selectedItem_3 = sharedData['selectedItem_3']
        self.tier.trace('w', self.observer)

        # set local variables
        self.controller = controller
        self.id = tk.IntVar()
        self.code = tk.StringVar()
        self.desc = tk.StringVar()
        self.select_all = tk.IntVar()
        self.select_all.trace('w', self.add_all)
        self.library_id = tk.IntVar()
        self.library = tk.StringVar()
        self.matType_id = tk.IntVar()
        self.matType = tk.StringVar()
        self.branch_code = tk.StringVar()

        # configure layout
        self.columnconfigure(0, minsize=30)
        self.columnconfigure(1, minsize=72)
        self.columnconfigure(2, minsize=10)
        self.columnconfigure(3, minsize=50)
        self.columnconfigure(4, minsize=144)
        self.rowconfigure(20, minsize=20)

        # initiate widgets
        tk.Label(self, textvariable=self.library, font=BTN_FONT).grid(
            row=0, column=0, columnspan=2, sticky='snw')
        tk.Label(self, text='Sierra fund code:', font=LBL_FONT).grid(
            row=1, column=0, columnspan=2, sticky='snw', padx=10)
        tk.Label(self, text='description:', font=LBL_FONT).grid(
            row=1, column=2, columnspan=2, sticky='snw', padx=10)
        tk.Entry(self, textvariable=self.code, font=REG_FONT).grid(
            row=2, column=0, columnspan=2, sticky='snew', padx=10)
        tk.Entry(self, textvariable=self.desc, font=REG_FONT).grid(
            row=2, column=2, columnspan=4, sticky='snew', padx=10)
        ttk.Radiobutton(self, text='apply to all locations',
                        variable=self.select_all, value=1).grid(
            row=3, column=0, columnspan=3, sticky='snw', padx=10, pady=2)
        ttk.Radiobutton(self, text='apply to specific locations',
                        variable=self.select_all, value=2).grid(
            row=4, column=0, columnspan=3, sticky='snw', padx=10, pady=2)
        tk.Label(self, text='available', font=REG_FONT).grid(
            row=5, column=1, sticky='nwe', padx=10)
        tk.Label(self, text='selected', font=REG_FONT).grid(
            row=5, column=4, sticky='new', padx=10)
        # branches
        scrollbar1 = tk.Scrollbar(self, orient=tk.VERTICAL)
        scrollbar1.grid(
            row=6, column=2, rowspan=6, sticky='nsw', padx=2)
        self.branchLstLeft = tk.Listbox(self, font=REG_FONT,
                                        yscrollcommand=scrollbar1.set)
        self.branchLstLeft.bind('<Double-Button-1>', self.add_branch)
        self.branchLstLeft.grid(
            row=6, column=1, sticky='snew', rowspan=6)
        scrollbar1['command'] = self.branchLstLeft.yview
        tk.Button(self, text='==>', font=BTN_FONT, width=10,
                  command=self.add_branch).grid(
            row=7, column=3, padx=5)
        tk.Button(self, text='<==', font=BTN_FONT, width=10,
                  command=self.remove_branch).grid(
            row=8, column=3, padx=5)
        scrollbar2 = tk.Scrollbar(self, orient=tk.VERTICAL)
        scrollbar2.grid(
            row=6, column=5, sticky='nsw', rowspan=6, padx=2)
        self.branchLstRight = tk.Listbox(self, font=REG_FONT,
                                         yscrollcommand=scrollbar2.set)
        self.branchLstRight.bind('<Double-Button-1>', self.remove_branch)
        self.branchLstRight.grid(
            row=6, column=4, rowspan=6, sticky='snew')
        scrollbar2['command'] = self.branchLstRight.yview
        # material type
        scrollbar3 = tk.Scrollbar(self, orient=tk.VERTICAL)
        scrollbar3.grid(
            row=13, column=2, sticky='nsw', rowspan=3, padx=2)
        self.matTypeLstLeft = tk.Listbox(self, font=REG_FONT,
                                         height=4,
                                         yscrollcommand=scrollbar3.set)
        self.matTypeLstLeft.bind('<Double-Button-1>', self.add_matType)
        self.matTypeLstLeft.grid(
            row=13, column=1, rowspan=3, sticky='snew')
        scrollbar3['command'] = self.matTypeLstLeft.yview
        tk.Button(self, text='==>', font=BTN_FONT, width=10,
                  command=self.add_matType).grid(
            row=13, column=3, padx=5)
        tk.Button(self, text='<==', font=BTN_FONT, width=10,
                  command=self.remove_matType).grid(
            row=14, column=3, padx=5)
        scrollbar4 = tk.Scrollbar(self, orient=tk.VERTICAL)
        scrollbar4.grid(
            row=13, column=5, sticky='nsw', rowspan=3, padx=2)
        self.matTypeLstRight = tk.Listbox(self, font=REG_FONT,
                                          height=4,
                                          yscrollcommand=scrollbar4.set)
        self.matTypeLstRight.bind('<Double-Button-1>', self.remove_matType)
        self.matTypeLstRight.grid(
            row=13, column=4, rowspan=3, sticky='snew')
        scrollbar4['command'] = self.matTypeLstRight.yview
        # audience
        scrollbar5 = tk.Scrollbar(self, orient=tk.VERTICAL)
        scrollbar5.grid(
            row=17, column=2, sticky='nsw', rowspan=3, padx=2)
        self.audnLstLeft = tk.Listbox(self, font=REG_FONT,
                                      height=4,
                                      yscrollcommand=scrollbar5.set)
        self.audnLstLeft.bind('<Double-Button-1>', self.add_audn)
        self.audnLstLeft.grid(
            row=17, column=1, rowspan=3, sticky='snew')
        scrollbar5['command'] = self.matTypeLstLeft.yview
        tk.Button(self, text='==>', font=BTN_FONT, width=10,
                  command=self.add_audn).grid(
            row=17, column=3, padx=5)
        tk.Button(self, text='<==', font=BTN_FONT, width=10,
                  command=self.remove_audn).grid(
            row=18, column=3, padx=5)
        scrollbar6 = tk.Scrollbar(self, orient=tk.VERTICAL)
        scrollbar6.grid(
            row=17, column=5, sticky='nsw', rowspan=3, padx=2)
        self.audnLstRight = tk.Listbox(self, font=REG_FONT,
                                       height=4,
                                       yscrollcommand=scrollbar6.set)
        self.audnLstRight.bind('<Double-Button-1>', self.remove_audn)
        self.audnLstRight.grid(
            row=17, column=4, rowspan=3, sticky='snew')
        scrollbar6['command'] = self.audnLstRight.yview

        tk.Button(self, text='save', font=BTN_FONT, width=15,
                  command=self.on_save).grid(
            row=21, column=1, columnspan=2, padx=10, pady=10)
        tk.Button(self, text='close', font=BTN_FONT, width=15,
                  command=self.on_close).grid(
            row=21, column=4, columnspan=2, padx=10, pady=10)

    def add_all(self, *args):
        if self.select_all.get() == 1:
            # delete on right list any choices that have been already
            # added and populate from start
            self.branchLstRight.delete(0, tk.END)
            # add complete list of choices to right list
            for branch in self.branch_choices:
                self.branchLstRight.insert(tk.END, branch)
            self.branchLstLeft.delete(0, tk.END)
            self.matTypeLstRight.delete(0, tk.END)
            for matType in self.matType_choices:
                self.matTypeLstRight.insert(tk.END, matType)
            self.matTypeLstLeft.delete(0, tk.END)
            self.audnLstRight.delete(0, tk.END)
            for audn in self.audn_choices:
                self.audnLstRight.insert(tk.END, audn)
            self.audnLstLeft.delete(0, tk.END)

    def add_branch(self, *args):
        if self.branchLstLeft.get(tk.ANCHOR) != '':
            if self.select_all.get() != 2:
                self.select_all.set(2)
            self.branchLstRight.insert(
                tk.END, self.branchLstLeft.get(tk.ANCHOR)
            )
            self.branchLstLeft.delete(tk.ANCHOR)
            lst = self.branchLstRight.get(0, tk.END)
            sortedLst = sorted(lst)
            self.branchLstRight.delete(0, tk.END)
            for item in sortedLst:
                self.branchLstRight.insert(tk.END, item)

    def remove_branch(self, *args):
        if self.branchLstRight.get(tk.ANCHOR) != '':
            if self.select_all.get() != 2:
                self.select_all.set(2)
            self.branchLstLeft.insert(
                tk.END, self.branchLstRight.get(tk.ANCHOR)
            )
            self.branchLstRight.delete(tk.ANCHOR)
            lst = self.branchLstLeft.get(0, tk.END)
            sortedLst = sorted(lst)
            self.branchLstLeft.delete(0, tk.END)
            for item in sortedLst:
                self.branchLstLeft.insert(tk.END, item)

    def add_matType(self, *args):
        if self.matTypeLstLeft.get(tk.ANCHOR) != '':
            if self.select_all.get() != 2:
                self.select_all.set(2)
            self.matTypeLstRight.insert(
                tk.END, self.matTypeLstLeft.get(tk.ANCHOR)
            )
            self.matTypeLstLeft.delete(tk.ANCHOR)
            lst = self.matTypeLstRight.get(0, tk.END)
            sortedLst = sorted(lst)
            self.matTypeLstRight.delete(0, tk.END)
            for item in sortedLst:
                self.matTypeLstRight.insert(tk.END, item)

    def remove_matType(self, *args):
        if self.matTypeLstRight.get(tk.ANCHOR) != '':
            if self.select_all.get() != 2:
                self.select_all.set(2)
            self.matTypeLstLeft.insert(
                tk.END, self.matTypeLstRight.get(tk.ANCHOR)
            )
            self.matTypeLstRight.delete(tk.ANCHOR)
            lst = self.matTypeLstLeft.get(0, tk.END)
            sortedLst = sorted(lst)
            self.matTypeLstLeft.delete(0, tk.END)
            for item in sortedLst:
                self.matTypeLstLeft.insert(tk.END, item)

    def add_audn(self, *args):
        if self.audnLstLeft.get(tk.ANCHOR) != '':
            if self.select_all.get() != 2:
                self.select_all.set(2)
            self.audnLstRight.insert(
                tk.END, self.audnLstLeft.get(tk.ANCHOR)
            )
            self.audnLstLeft.delete(tk.ANCHOR)
            lst = self.audnLstRight.get(0, tk.END)
            sortedLst = sorted(lst)
            self.audnLstRight.delete(0, tk.END)
            for item in sortedLst:
                self.audnLstRight.insert(tk.END, item)

    def remove_audn(self, *args):
        if self.audnLstRight.get(tk.ANCHOR) != '':
            if self.select_all.get() != 2:
                self.select_all.set(2)
            self.audnLstLeft.insert(
                tk.END, self.audnLstRight.get(tk.ANCHOR)
            )
            self.audnLstRight.delete(tk.ANCHOR)
            lst = self.audnLstLeft.get(0, tk.END)
            sortedLst = sorted(lst)
            self.audnLstLeft.delete(0, tk.END)
            for item in sortedLst:
                self.audnLstLeft.insert(tk.END, item)

    def on_save(self):
        # validate data entry
        new = {
            'code': self.code.get(),
            'desc': self.desc.get(),
            'branches': self.branchLstRight.get(0, tk.END),
            'matTypes': self.matTypeLstRight.get(0, tk.END),
            'audns': self.audnLstRight.get(0, tk.END)
        }
        error = validation.fund_form(new)
        if error is not None:
            tkMessageBox.showwarning('Input error', error)
        else:
            if self.action.get() == 'add':
                db.ignore_or_insert(
                    db.Fund,
                    code=self.code.get(),
                    desc=self.desc.get(),
                    library_id=self.library_id.get(),
                )
                inserted_fund = db.retrieve_record(
                    db.Fund,
                    code=self.code.get()
                )
                self.id.set(inserted_fund.id)
                # add records to joiner tables
                branches = []
                for branch in self.branchLstRight.get(0, tk.END):
                    inst = db.create_db_object(
                        db.FundBranchJoiner,
                        fund_id=self.id.get(),
                        branch_id=self.branch_by_code[branch][0])
                    branches.append(inst)
                db.update_record(
                    db.Fund,
                    id=self.id.get(),
                    code=self.code.get(),
                    desc=self.desc.get(),
                    branches=branches)
                audns = []
                for audn in self.audnLstRight.get(0, tk.END):
                    inst = db.create_db_object(
                        db.FundAudnJoiner,
                        fund_id=self.id.get(),
                        audn_id=self.audn_by_name[audn][0])
                    audns.append(inst)
                db.update_record(
                    db.Fund,
                    self.id.get(),
                    audns=audns)
                matTypes = []
                for matType in self.matTypeLstRight.get(0, tk.END):
                    inst = db.create_db_object(
                        db.FundMatTypeJoiner,
                        fund_id=self.id.get(),
                        matType_id=self.matType_by_name[matType][0])
                    matTypes.append(inst)
                db.update_record(
                    db.Fund,
                    self.id.get(),
                    matTypes=matTypes)
                self.reset_values()
                self.action.set('add')

            if self.action.get() == 'update':
                branches = []
                for branch in self.branchLstRight.get(0, tk.END):
                    inst = db.create_db_object(
                        db.FundBranchJoiner,
                        fund_id=self.id.get(),
                        branch_id=self.branch_by_code[branch][0])
                    branches.append(inst)
                db.update_record(
                    db.Fund,
                    self.id.get(),
                    code=self.code.get(),
                    desc=self.desc.get(),
                    library_id=self.library_id.get(),
                    branches=branches)
                matTypes = []
                for matType in self.matTypeLstRight.get(0, tk.END):
                    inst = db.create_db_object(
                        db.FundMatTypeJoiner,
                        fund_id=self.id.get(),
                        matType_id=self.matType_by_name[matType][0])
                    matTypes.append(inst)
                db.update_record(
                    db.Fund,
                    self.id.get(),
                    matTypes=matTypes)
                audns = []
                for audn in self.audnLstRight.get(0, tk.END):
                    inst = db.create_db_object(
                        db.FundAudnJoiner,
                        fund_id=self.id.get(),
                        audn_id=self.audn_by_name[audn][0])
                    audns.append(inst)
                db.update_record(
                    db.Fund,
                    self.id.get(),
                    audns=audns)
                self.reset_values()
                self.action.set('add')

    def on_close(self):
        self.reset_values()
        self.delete_panels()
        self.action.set('add')
        self.selectedItem_3.set(0)
        self.controller.show_frame('FundBrowse')

    def reset_values(self):
        self.id.set(0)
        self.code.set('')
        self.desc.set('')
        self.select_all.set(0)
        self.delete_panels()
        self.repopulate_panels()

    def delete_panels(self):
        # clear left and right panels with choices and re-populate left
        self.branchLstRight.delete(0, tk.END)
        self.branchLstLeft.delete(0, tk.END)
        self.matTypeLstRight.delete(0, tk.END)
        self.matTypeLstLeft.delete(0, tk.END)
        self.audnLstRight.delete(0, tk.END)
        self.audnLstLeft.delete(0, tk.END)

    def repopulate_panels(self):
        for branch in self.branch_choices:
            self.branchLstLeft.insert(tk.END, branch)
        for matType in self.matType_choices:
            self.matTypeLstLeft.insert(tk.END, matType)
        for audn in self.audn_choices:
            self.audnLstLeft.insert(tk.END, audn)

    def create_indexes(self):
        # reset vars and indexes
        self.branch_choices = ()
        self.branch_by_code = {}
        self.branch_by_id = {}
        self.audn_choices = ()
        self.audn_by_name = {}
        self.audn_by_id = {}
        self.matType_choices = ()
        self.matType_by_name = {}
        self.matType_by_id = {}

        records = db.col_preview(
            db.Branch, 'id', 'code', library_id=self.library_id.get())
        for record in records:
            self.branch_choices = self.branch_choices + (record.code, )
            self.branch_by_code[record.code] = (record.id, )
            self.branch_by_id[record.id] = (record.code, )
        records = db.col_preview(
            db.Audn, 'id', 'code', 'name')
        for record in records:
            self.audn_choices = self.audn_choices + (record.name, )
            self.audn_by_name[record.name] = (record.id, )
            self.audn_by_id[record.id] = (record.name, )
        records = db.col_preview(
            db.MatType, 'id', 'name')
        for record in records:
            self.matType_choices = self.matType_choices + (record.name, )
            self.matType_by_name[record.name] = (record.id, )
            self.matType_by_id[record.id] = (record.name, )

    def observer(self, *args):
        if self.tier.get() == 'FundSingle':
            self.library_id.set(self.selectedItem_3.get())
            if self.library_id.get() == 1:
                self.library.set('BPL')
            if self.library_id.get() == 2:
                self.library.set('NYPL')

            self.create_indexes()

            self.delete_panels()
            self.repopulate_panels()

            if self.action.get() == 'update':
                edited_fund = db.retrieve_record(
                    db.Fund,
                    code=self.selectedItem_1.get(),
                    library_id=self.library_id.get()
                )
                self.id.set(edited_fund.id)
                self.code.set(edited_fund.code)
                self.desc.set(edited_fund.desc)
                # populate right panel
                choices = self.branchLstLeft.get(0, tk.END)
                sortedLst = sorted(choices)
                branches = db.col_preview(
                    db.FundBranchJoiner,
                    'branch_id',
                    fund_id=self.id.get())
                for branch in branches:
                    id = branch.branch_id
                    code = self.branch_by_id[id][0]
                    self.branchLstRight.insert(
                        tk.END, code)
                    sortedLst.remove(code)

                # delete and repopulate left panel
                self.branchLstLeft.delete(0, tk.END)
                for item in sortedLst:
                    self.branchLstLeft.insert(tk.END, item)

                # populate right matType panel
                choices = self.matTypeLstLeft.get(0, tk.END)
                sortedLst = sorted(choices)
                matTypes = db.col_preview(
                    db.FundMatTypeJoiner,
                    'matType_id',
                    fund_id=self.id.get())
                for matType in matTypes:
                    id = matType.matType_id
                    name = self.matType_by_id[id][0]
                    self.matTypeLstRight.insert(
                        tk.END, name)
                    sortedLst.remove(name)

                # delete all and repopulate left matType panel
                self.matTypeLstLeft.delete(0, tk.END)
                for item in sortedLst:
                    self.matTypeLstLeft.insert(tk.END, item)

                # populate right audn panel
                choices = self.audnLstLeft.get(0, tk.END)
                sortedLst = sorted(choices)
                audns = db.col_preview(
                    db.FundAudnJoiner,
                    'audn_id',
                    fund_id=self.id.get())
                for audn in audns:
                    id = audn.audn_id
                    name = self.audn_by_id[id][0]
                    self.audnLstRight.insert(
                        tk.END, name)
                    sortedLst.remove(name)

                # delete all and repopulate left audn panel
                self.audnLstLeft.delete(0, tk.END)
                for item in sortedLst:
                    self.audnLstLeft.insert(tk.END, item)


class VendorSheetBrowse(tk.Frame):

    def __init__(self, parent, controller, **sharedData):
        tk.Frame.__init__(self, parent)

        # bind shared variables
        self.controller = controller
        self.tier = sharedData['tier']
        self.tier.trace('w', self.observer)
        self.action = sharedData['action']
        self.selectedItem_1 = sharedData['selectedItem_1']

        # configure layout
        self.rowconfigure(0, minsize=10)
        self.columnconfigure(0, minsize=72)
        self.columnconfigure(1, minsize=72)
        self.columnconfigure(2, minsize=10)
        self.columnconfigure(3, minsize=50)
        self.columnconfigure(4, minsize=144)
        self.rowconfigure(9, minsize=50)

        # initiate widgets
        tk.Label(self, text='vendor sheet name:', font=LBL_FONT).grid(
            row=1, column=0, columnspan=2, sticky='snw')
        scrollbar = tk.Scrollbar(self, orient=tk.VERTICAL)
        scrollbar.grid(
            row=2, column=2, sticky='nsw', rowspan=10, padx=2, pady=10)
        self.vendorSheetLst = tk.Listbox(
            self, font=REG_FONT,
            yscrollcommand=scrollbar.set)
        self.vendorSheetLst.bind('<Double-Button-1>', self.edit_entry)
        self.vendorSheetLst.grid(
            row=2, column=0, columnspan=2, sticky='snew', rowspan=10,
            pady=10)
        scrollbar['command'] = self.vendorSheetLst.yview

        # buttons of the left panel
        tk.Button(self, text='add', font=BTN_FONT,
                  command=self.add_entry,
                  width=15).grid(
            row=2, column=3, sticky='snew', padx=10, pady=10)
        tk.Button(self, text='edit', font=BTN_FONT,
                  command=self.edit_entry,
                  width=15).grid(
            row=3, column=3, sticky='snew', padx=10, pady=10)
        tk.Button(self, text='delete', font=BTN_FONT,
                  command=self.delete_entry,
                  width=15).grid(
            row=4, column=3, sticky='snew', padx=10, pady=10)
        tk.Button(self, text='close', font=BTN_FONT,
                  width=15,
                  command=lambda: controller.show_frame(
                      'Settings')).grid(
            row=10, column=3, sticky='snew', padx=10, pady=10)

    def add_entry(self):
        self.selectedItem_1.set(self.vendorSheetLst.get(tk.ANCHOR))
        self.action.set('add')
        self.controller.show_frame('VendorSheetSingle')

    def edit_entry(self):
        if self.vendorSheetLst.get(tk.ANCHOR) == '':
            msg = 'Please select sheet template from the list'
            tkMessageBox.showwarning('Input error', msg)
        else:
            self.selectedItem_1.set(self.vendorSheetLst.get(tk.ANCHOR))
            self.action.set('update')
            self.controller.show_frame('VendorSheetSingle')

    def delete_entry(self):
        if self.vendorSheetLst.get(tk.ANCHOR) == '':
            msg = 'Please select sheet template from the list'
            tkMessageBox.showwarning('Input error', msg)
        else:
            if tkMessageBox.askokcancel(
                    'Orders',
                    'delete order?'):
                name = self.vendorSheetLst.get(tk.ANCHOR)
                db.delete_record(db.VendorSheetTemplate, name=name)
                self.vendorSheetLst.delete(tk.ANCHOR)

    def reloadLst(self):
        self.vendorSheetLst.delete(0, tk.END)
        records = db.col_preview(
            db.VendorSheetTemplate,
            'name')
        for row in records:
            self.vendorSheetLst.insert(tk.END, row.name)

    def observer(self, *args):
        if self.tier.get() == 'VendorSheetBrowse':
            self.reloadLst()


class VendorSheetSingle(tk.Frame):

    def __init__(self, parent, controller, **sharedData):
        tk.Frame.__init__(self, parent)

        # bind shared variables
        self.controller = controller
        self.tier = sharedData['tier']
        self.tier.trace('w', self.observer)
        self.action = sharedData['action']
        self.selectedItem_1 = sharedData['selectedItem_1']

        # bind local variables
        self.id = tk.IntVar()
        self.name = tk.StringVar()
        self.lastMod = tk.StringVar()
        self.vendor = tk.StringVar()
        self.lang = tk.StringVar()
        self.matType = tk.StringVar()
        self.head_row = tk.StringVar()
        self.title_col = tk.StringVar()
        self.isbn_col = tk.StringVar()
        self.priceReg_col = tk.StringVar()
        self.priceDisc_col = tk.StringVar()
        self.author_col = tk.StringVar()
        self.publisher_col = tk.StringVar()
        self.pubDate_col = tk.StringVar()
        self.pubPlace_col = tk.StringVar()
        self.venNum_col = tk.StringVar()
        self.vendor_choices = ()
        self.vendor_by_name = {}
        self.vendor_by_id = {}
        self.lang_choices = ()
        self.lang_by_name = {}
        self.lang_by_id = {}
        self.matType_choices = ()
        self.matType_by_name = {}
        self.matType_by_id = {}

        # configure layout
        self.columnconfigure(0, minsize=10)
        self.columnconfigure(2, minsize=72)
        self.columnconfigure(3, minsize=72)
        self.columnconfigure(4, minsize=72)
        self.columnconfigure(5, minsize=72)
        self.columnconfigure(6, minsize=72)
        self.columnconfigure(7, minsize=72)

        # initilize widgets
        # sheet preview
        self.xscrollbar = tk.Scrollbar(self, orient=tk.HORIZONTAL)
        self.xscrollbar.grid(
            row=10, column=1, columnspan=7, sticky='nwe', padx=10)
        self.yscrollbar = tk.Scrollbar(self, orient=tk.VERTICAL)
        self.yscrollbar.grid(
            row=0, column=0, rowspan=10, sticky='nse', padx=2)
        self.preview_base = tk.Canvas(
            self, bg='gray',
            height=250,  # find a way to adjust based on preview frm size
            xscrollcommand=self.xscrollbar.set,
            yscrollcommand=self.yscrollbar.set)
        self.preview_base.grid(
            row=0, column=1, columnspan=7, sticky='nwe', rowspan=10, padx=10)
        self.preview()

        # lower panel metadata
        tk.Button(self, text='load sheet',
                  font=BTN_FONT, width=10,
                  command=self.load_sheet).grid(
            row=11, column=1, padx=10, pady=10)

        tk.Label(self, text='save structure template as:',
                 font=LBL_FONT).grid(
            row=12, column=1, columnspan=4, sticky='snw', padx=10, pady=5)
        tk.Label(self, text='last modified:', font=LBL_FONT).grid(
            row=12, column=4, columnspan=2, sticky='snw', padx=5, pady=5)
        tk.Entry(self, textvariable=self.name, font=REG_FONT).grid(
            row=13, column=1, columnspan=3, sticky='snew', padx=10, pady=5)
        tk.Label(self, textvariable=self.lastMod, font=LBL_FONT).grid(
            row=13, column=4, columnspan=2, sticky='snw', padx=5, pady=5)
        tk.Label(self, text='vendor:', font=LBL_FONT).grid(
            row=14, column=1, sticky='snw', padx=10, pady=5)
        self.vendorCbx = ttk.Combobox(self, textvariable=self.vendor,
                                      state='readonly')
        self.vendorCbx.grid(
            row=14, column=2, sticky='snew', padx=10, pady=5)
        tk.Label(self, text='description:', font=LBL_FONT).grid(
            row=14, column=3, columnspan=2, sticky='snw', padx=10, pady=5)
        tk.Label(self, text='language:', font=LBL_FONT).grid(
            row=15, column=1, sticky='snw', padx=10, pady=5)
        self.langCbx = ttk.Combobox(self, textvariable=self.lang,
                                    state='readonly')
        self.langCbx.grid(
            row=15, column=2, sticky='snew', padx=10, pady=5)
        self.desc = tk.Text(self, font=REG_FONT, height=3, width=68)
        self.desc.grid(
            row=15, column=3, columnspan=3, rowspan=2, padx=10, pady=5)
        tk.Label(self, text='mat type:', font=LBL_FONT).grid(
            row=16, column=1, sticky='snw', padx=10, pady=5)
        self.matTypeCbx = ttk.Combobox(self, textvariable=self.matType,
                                       state='readonly')
        self.matTypeCbx.grid(
            row=16, column=2, sticky='snew', padx=10, pady=5)

        # structure entries
        self.str_frame = ttk.LabelFrame(self, borderwidth=10,
                                        text='sheet structure')
        self.str_frame.grid(
            row=17, column=1, columnspan=7, sticky='snew')
        tk.Label(self.str_frame, text='headings row:', font=LBL_FONT).grid(
            row=0, column=0, columnspan=2, sticky='sne', padx=5, pady=2)
        tk.Entry(self.str_frame, textvariable=self.head_row,
                 font=REG_BOLD,
                 width=5).grid(
            row=0, column=2, sticky='snw', padx=5, pady=2)
        tk.Label(self.str_frame, text='title column:', font=LBL_FONT).grid(
            row=0, column=3, columnspan=2, sticky='sne', padx=5, pady=2)
        tk.Entry(self.str_frame, textvariable=self.title_col,
                 font=REG_BOLD,
                 width=5).grid(
            row=0, column=5, sticky='snw', padx=5, pady=2)
        tk.Label(self.str_frame, text='ISBN column:',
                 font=LBL_FONT).grid(
            row=0, column=6, columnspan=2, sticky='sne', padx=5, pady=2)
        tk.Entry(self.str_frame, textvariable=self.isbn_col,
                 font=REG_BOLD,
                 width=5).grid(
            row=0, column=8, sticky='snw', padx=5, pady=2)
        tk.Label(self.str_frame, text='vendor number column:',
                 font=LBL_FONT).grid(
            row=0, column=9, columnspan=2, sticky='sne', padx=5, pady=2)
        tk.Entry(self.str_frame, textvariable=self.venNum_col,
                 font=REG_BOLD,
                 width=5).grid(
            row=0, column=11, sticky='snw', padx=5, pady=2)
        tk.Label(self.str_frame, text='author column:',
                 font=LBL_FONT).grid(
            row=1, column=0, columnspan=2, sticky='sne', padx=5, pady=2)
        tk.Entry(self.str_frame, textvariable=self.author_col,
                 font=REG_BOLD,
                 width=5).grid(
            row=1, column=2, sticky='snw', padx=5, pady=2)
        tk.Label(self.str_frame, text='publisher column:',
                 font=LBL_FONT).grid(
            row=1, column=3, columnspan=2, sticky='sne', padx=5, pady=2)
        tk.Entry(self.str_frame, textvariable=self.publisher_col,
                 font=REG_BOLD,
                 width=5).grid(
            row=1, column=5, sticky='snw', padx=5, pady=2)
        tk.Label(self.str_frame, text='publishing date column:',
                 font=LBL_FONT).grid(
            row=1, column=6, columnspan=2, sticky='sne', padx=5, pady=2)
        tk.Entry(self.str_frame, textvariable=self.pubDate_col,
                 font=REG_BOLD,
                 width=5).grid(
            row=1, column=8, sticky='snw', padx=5, pady=2)
        tk.Label(self.str_frame, text='publishing place column:',
                 font=LBL_FONT).grid(
            row=1, column=9, columnspan=2, sticky='sne', padx=5, pady=2)
        tk.Entry(self.str_frame, textvariable=self.pubPlace_col,
                 font=REG_BOLD,
                 width=5).grid(
            row=1, column=11, sticky='snw', padx=5, pady=2)
        tk.Label(self.str_frame, text='disc. price column:',
                 font=LBL_FONT).grid(
            row=2, column=0, columnspan=2, sticky='sne', padx=5, pady=2)
        tk.Entry(self.str_frame, textvariable=self.priceDisc_col,
                 font=REG_BOLD,
                 width=5).grid(
            row=2, column=2, sticky='snw', padx=5, pady=2)
        tk.Label(self.str_frame, text='list price column:',
                 font=LBL_FONT).grid(
            row=2, column=3, columnspan=2, sticky='sne', padx=5, pady=2)
        tk.Entry(self.str_frame, textvariable=self.priceReg_col,
                 font=REG_BOLD,
                 width=5).grid(
            row=2, column=5, sticky='snw', padx=5, pady=2)

        # bottom main buttons
        tk.Button(self, text='save', font=BTN_FONT,
                  width=15,
                  command=self.on_save).grid(
            row=20, column=1, padx=10, pady=10)
        tk.Button(self, text='close', font=BTN_FONT,
                  width=15,
                  command=self.on_close).grid(
            row=20, column=2, padx=10, pady=10)

    def preview(self):
        self.preview_frame = tk.Frame(
            self.preview_base)
        self.xscrollbar.config(command=self.preview_base.xview)
        self.yscrollbar.config(command=self.preview_base.yview)
        self.preview_base.create_window(
            (0, 0), window=self.preview_frame, anchor="nw",
            tags="self.preview_frame")
        self.preview_frame.bind("<Configure>", self.onFrameConfigure)

    def reset_preview(self):
        self.preview_frame.grid_forget()
        self.preview_frame.destroy()
        self.preview()

    def generate_preview(self, data):
        # clear and recreate frame
        self.preview_frame.grid_forget()
        self.preview_frame.destroy()
        self.preview()
        self.rowLst = tk.Listbox(
            self.preview_frame, font=REG_FONT,
            width=3,
            height=self.row_qnt + 1)
        self.rowLst.grid(
            row=1, column=1, sticky='nsw')

        for number in range(0, self.row_qnt + 1):
            self.rowLst.insert(tk.END, number)
        c = 0
        r = 0
        for column in range(0, self.col_qnt):
            self.col_name = tk.Listbox(
                self.preview_frame, font=REG_FONT,
                width=15,
                height=self.row_qnt + 1)
            self.col_name.grid(
                row=1, column=c + 2, sticky='nsw')
            self.col_name.insert(tk.END, self.column_letters[c])
            for row in data:
                if row[r] is None:
                    self.col_name.insert(tk.END, '')
                else:
                    self.col_name.insert(tk.END, row[r])
            r += 1
            c += 1

    def onFrameConfigure(self, event):
        self.preview_base.config(scrollregion=self.preview_base.bbox('all'))

    def load_sheet(self):
        # retrieve last used directory
        user_data = shelve.open('user_data')
        if 'ven_sheet_dir' in user_data:
            ven_sheet_dir = user_data['ven_sheet_dir']
        else:
            ven_sheet_dir = ''
        fh = tkFileDialog.askopenfilename(initialdir=ven_sheet_dir)
        if fh:
            # record directory
            n = fh.rfind('/')
            ven_sheet_dir = fh[:n + 1]
            user_data['ven_sheet_dir'] = ven_sheet_dir
            # validate if correct file type
            if fh.rfind('.xlsx') == -1:
                msg = 'Wrong type of spreadsheet file.\n' \
                      'Only sheets with extention .xlsx are permitted'
                tkMessageBox.showwarning('File type error', msg)
            else:
                s = sh.SheetManipulator(fh)
                self.column_letters = s.get_column_letters()
                data = s.extract_data()
                self.row_qnt = len(data)
                self.col_qnt = len(self.column_letters)
                self.generate_preview(data)
        user_data.close()

    def on_save(self):
        new = {
            'name': self.name.get().strip(),
            'vendor': self.vendor.get(),
            'lang': self.lang.get(),
            'matType': self.matType.get(),
            'desc': self.desc.get(0.0, tk.END),
            'head_row': self.head_row.get().strip(),
            'title_col': self.title_col.get().strip().upper(),
            'priceDisc_col': self.priceDisc_col.get().upper(),
            'author_col': self.author_col.get().strip().upper(),
            'isbn_col': self.isbn_col.get().strip().upper(),
            'publisher_col': self.publisher_col.get().strip().upper(),
            'pubDate_col': self.pubDate_col.get().strip().upper(),
            'pubPlace_col': self.pubPlace_col.get().strip().upper(),
            'priceReg_col': self.priceReg_col.get().strip().upper(),
            'venNum_col': self.venNum_col.get().strip().upper()
        }
        errors = validation.vendorSheet_form(new)
        if errors is not None:
            for e in errors:
                tkMessageBox.showwarning('Input error', e)
        else:
            new['matType_id'] = self.matType_by_name[self.matType.get()][0]
            new['lang_id'] = self.lang_by_name[self.lang.get()][0]
            new['vendor_id'] = self.vendor_by_name[self.vendor.get()][0]
            new['lastMod'] = str(datetime.datetime.now())
            if self.action.get() == 'add':
                r = db.ignore_or_insert(
                    db.VendorSheetTemplate,
                    name=new['name'],
                    desc=new['desc'],
                    lastMod=new['lastMod'],
                    vendor_id=new['vendor_id'],
                    lang_id=new['lang_id'],
                    matType_id=new['matType_id'],
                    headRow=new['head_row'],
                    titleCol=new['title_col'],
                    authorCol=new['author_col'],
                    isbnCol=new['isbn_col'],
                    priceDiscCol=new['priceDisc_col'],
                    priceRegCol=new['priceReg_col'],
                    venNoCol=new['venNum_col'],
                    publisherCol=new['publisher_col'],
                    pubDateCol=new['pubDate_col'],
                    pubPlaceCol=new['pubPlace_col'])
                if r is not True:
                    tkMessageBox.showerror('Database error', r)
                else:
                    self.reset_values()
            if self.action.get() == 'update':
                db.update_record(
                    db.VendorSheetTemplate,
                    id=self.id.get(),
                    name=new['name'],
                    desc=new['desc'],
                    lastMod=new['lastMod'],
                    vendor_id=new['vendor_id'],
                    lang_id=new['lang_id'],
                    matType_id=new['matType_id'],
                    headRow=new['head_row'],
                    titleCol=new['title_col'],
                    authorCol=new['author_col'],
                    isbnCol=new['isbn_col'],
                    priceDiscCol=new['priceDisc_col'],
                    priceRegCol=new['priceReg_col'],
                    venNoCol=new['venNum_col'],
                    publisherCol=new['publisher_col'],
                    pubDateCol=new['pubDate_col'],
                    pubPlaceCol=new['pubPlace_col'])
                self.reset_values()
                self.action.set('add')

    def on_close(self):
        self.reset_values()
        self.tier.set('VendorSheetBrowse')
        self.controller.show_frame('VendorSheetBrowse')

    def reset_values(self):
        self.name.set('')
        self.desc.delete(0.0, tk.END)
        self.lang.set('')
        self.matType.set('')
        self.vendor.set('')
        self.head_row.set('')
        self.title_col.set('')
        self.isbn_col.set('')
        self.venNum_col.set('')
        self.priceDisc_col.set('')
        self.priceReg_col.set('')
        self.author_col.set('')
        self.publisher_col.set('')
        self.pubDate_col.set('')
        self.pubPlace_col.set('')
        self.lastMod.set('')
        self.reset_preview()

    def bind_variables(self):
        self.vendor_choices = ()
        for row in db.col_preview(db.Vendor, 'name', 'id'):
            self.vendor_choices = self.vendor_choices + (row.name, )
            self.vendor_by_name[row.name] = (row.id, )
            self.vendor_by_id[row.id] = (row.name, )
        self.vendorCbx['values'] = self.vendor_choices
        self.lang_choices = ()
        for row in db.col_preview(db.Lang, 'name', 'id'):
            self.lang_choices = self.lang_choices + (row.name, )
            self.lang_by_name[row.name] = (row.id, )
            self.lang_by_id[row.id] = (row.name, )
        self.langCbx['values'] = self.lang_choices
        self.matType_choices = ()
        for row in db.col_preview(db.MatType, 'name', 'id'):
            self.matType_choices = self.matType_choices + (row.name, )
            self.matType_by_name[row.name] = (row.id, )
            self.matType_by_id[row.id] = (row.name, )
        self.matTypeCbx['values'] = self.matType_choices

    def observer(self, *args):
        if self.tier.get() == 'VendorSheetSingle':
            self.bind_variables()
            if self.action.get() == 'update':
                self.name.set(self.selectedItem_1.get())
                record = db.retrieve_record(
                    db.VendorSheetTemplate,
                    name=self.name.get())
                self.id.set(record.id)
                self.lastMod.set(record.lastMod)
                self.lang.set(self.lang_by_id[record.lang_id][0])
                self.vendor.set(self.vendor_by_id[record.vendor_id][0])
                self.matType.set(self.matType_by_id[record.matType_id][0])
                self.desc.insert(tk.END, record.desc)
                self.head_row.set(record.headRow)
                self.title_col.set(record.titleCol)
                self.author_col.set(record.authorCol)
                self.isbn_col.set(record.isbnCol)
                self.venNum_col.set(record.venNoCol)
                self.publisher_col.set(record.publisherCol)
                self.pubDate_col.set(record.pubDateCol)
                self.pubPlace_col.set(record.pubPlaceCol)
                self.priceDisc_col.set(record.priceDiscCol)
                self.priceReg_col.set(record.priceRegCol)


class Z3950Settings(tk.Frame):
    """widget recording Z3950 targets"""

    def __init__(self, parent, controller, **sharedData):
        tk.Frame.__init__(self, parent)

        # bind shared variables
        self.controller = controller
        self.tier = sharedData['tier']
        self.tier.trace('w', self.observer)

        # initiate local variables
        self.target_id = tk.IntVar()
        self.name = tk.StringVar()
        self.host = tk.StringVar()
        self.database = tk.StringVar()
        self.port = tk.IntVar()
        self.user = tk.StringVar()
        self.password = tk.StringVar()
        self.syntax = tk.StringVar()
        self.isbn_url = tk.StringVar()

        # setup layout
        # set browsing frame

        tk.Button(self, text='back', font=BTN_FONT,
                  width=15,
                  command=lambda: controller.show_frame('Settings')).grid(
            row=1, column=0, sticky='sw', padx=5, pady=10)

        self.zBrowseFrm = ttk.LabelFrame(
            self, text='Z3950 targets',
            borderwidth=5,
            padding=5)
        self.zBrowseFrm.grid(
            row=0, column=0, sticky='snew', padx=10, pady=10)
        self.zBrowseFrm.columnconfigure(0, minsize=10)
        self.zBrowseFrm.columnconfigure(3, minsize=10)

        # browsing area
        scrollbar = tk.Scrollbar(self.zBrowseFrm, orient=tk.VERTICAL)
        scrollbar.grid(
            row=0, column=2, sticky='nsw', rowspan=10, padx=2, pady=10)
        self.targetLst = tk.Listbox(self.zBrowseFrm, font=REG_FONT,
                                    width=35,
                                    height=20,
                                    yscrollcommand=scrollbar.set)
        self.targetLst.bind('<Double-Button-1>', self.edit_target)
        self.targetLst.grid(
            row=0, column=1, rowspan=10, pady=10)
        scrollbar['command'] = self.targetLst.yview

        # menu buttons
        tk.Button(self.zBrowseFrm, text='new', font=BTN_FONT,
                  width=10,
                  command=self.new_target).grid(
            row=0, column=4, sticky='nw', padx=5, pady=5)
        tk.Button(self.zBrowseFrm, text='edit', font=BTN_FONT,
                  width=10,
                  command=self.edit_target).grid(
            row=1, column=4, sticky='nw', padx=5, pady=5)
        tk.Button(self.zBrowseFrm, text='delete', font=BTN_FONT,
                  width=10,
                  command=self.delete_target).grid(
            row=2, column=4, sticky='nw', padx=5, pady=5)

        # editing area
        self.zEditFrm = ttk.LabelFrame(
            self, text='Z3950 parameters',
            borderwidth=5,
            padding=5)
        self.zEditFrm.grid(
            row=0, column=1, sticky='snew', padx=10, pady=10)
        # self.zEditFrm.state(['disabled', 'readonly'])
        self.zEditFrm.columnconfigure(0, minsize=10)
        self.zEditFrm.rowconfigure(8, minsize=100)

        tk.Entry(self.zEditFrm, textvariable=self.name).grid(
            row=0, column=1, sticky='snwe', padx=5, pady=5)
        tk.Label(self.zEditFrm, text='target name', font=LBL_FONT).grid(
            row=0, column=2, sticky='nw', padx=5, pady=5)
        tk.Entry(self.zEditFrm, textvariable=self.host).grid(
            row=1, column=1, sticky='snwe', padx=5, pady=5)
        tk.Label(self.zEditFrm, text='host', font=LBL_FONT).grid(
            row=1, column=2, sticky='nw', padx=5, pady=5)
        tk.Entry(self.zEditFrm, textvariable=self.database).grid(
            row=2, column=1, sticky='snew', padx=5, pady=5)
        tk.Label(self.zEditFrm, text='database', font=LBL_FONT).grid(
            row=2, column=2, sticky='nw', padx=5, pady=5)
        tk.Entry(self.zEditFrm, textvariable=self.port).grid(
            row=3, column=1, sticky='snew', padx=5, pady=5)
        tk.Label(self.zEditFrm, text='port', font=LBL_FONT).grid(
            row=3, column=2, sticky='nw', padx=5, pady=5)
        tk.Entry(self.zEditFrm, textvariable=self.user).grid(
            row=4, column=1, sticky='snew', padx=5, pady=5)
        tk.Label(self.zEditFrm, text='user', font=LBL_FONT).grid(
            row=4, column=2, sticky='nw', padx=5, pady=5)
        tk.Entry(self.zEditFrm, textvariable=self.password).grid(
            row=5, column=1, sticky='snew', padx=5, pady=5)
        tk.Label(self.zEditFrm, text='password', font=LBL_FONT).grid(
            row=5, column=2, sticky='nw', padx=5, pady=5)
        self.syntaxCbx = ttk.Combobox(self.zEditFrm, textvariable=self.syntax,
                                      values=['MARC21', 'USMARC', 'XML'],
                                      state='readonly')
        self.syntaxCbx.grid(
            row=6, column=1, sticky='snew', padx=5, pady=5)
        tk.Label(self.zEditFrm, text='syntax', font=LBL_FONT).grid(
            row=6, column=2, sticky='nw', padx=5, pady=5)
        tk.Entry(self.zEditFrm, textvariable=self.isbn_url).grid(
            row=7, column=1, sticky='snew', padx=5, pady=5)
        tk.Label(self.zEditFrm, text='ISBN search URL', font=LBL_FONT).grid(
            row=7, column=2, sticky='nw', padx=5, pady=5)

        # buttons
        tk.Button(self.zEditFrm, text='save', font=BTN_FONT,
                  width=10,
                  command=self.save).grid(
            row=9, column=1, sticky='nw', padx=5, pady=5)
        tk.Button(self.zEditFrm, text='cancel', font=BTN_FONT,
                  width=10,
                  command=self.cancel).grid(
            row=9, column=2, sticky='nw', padx=5, pady=5)

        # disable widgets
        for child in self.zEditFrm.children.values():
            if child.winfo_class() in ('Entry', 'Button'):
                child['state'] = tk.DISABLED

    def activate_widgets(self, parent_widget):
        parent_widget.state(['!disabled'])
        select_widgets = (
            'Entry', 'Button', 'TCombobox')
        for child in parent_widget.children.values():

            if child.winfo_class() in select_widgets:
                child['state'] = tk.NORMAL

    def deactivate_widgets(self, parent_widget):
        parent_widget.state(['disabled'])
        select_widgets = (
            'Entry', 'Button', 'TCombobox')
        for child in parent_widget.children.values():
            if child.winfo_class() in select_widgets:
                child['state'] = tk.DISABLED

    def new_target(self):
        self.reset_values()
        self.activate_widgets(self.zEditFrm)

    def edit_target(self, *args):
        if self.targetLst.get(tk.ANCHOR) == '':
            m = 'please select target first'
            tkMessageBox.showinfo('Info', m)
        else:
            record = db.retrieve_record(
                db.Z3950params,
                name=self.targetLst.get(tk.ANCHOR))
            self.activate_widgets(self.zEditFrm)
            self.name.set(record.name)
            self.host.set(record.host)
            self.database.set(record.database)
            self.port.set(record.port)
            self.user.set(record.user)
            self.password.set(record.password)
            self.syntax.set(record.syntax)
            self.isbn_url.set(record.isbn_url)

            self.target_id.set(record.id)

    def delete_target(self):
        if self.targetLst.get(tk.ANCHOR) == '':
            m = 'please select target for deletion'
            tkMessageBox.showerror('Input error', m)
        else:
            m = "are you sure to delete '%s' target" % self.targetLst.get(tk.ANCHOR)
            if tkMessageBox.askyesno('Warning', m):
                db.delete_record(
                    db.Z3950params,
                    name=self.targetLst.get(tk.ANCHOR))
                self.targetLst.delete(tk.ANCHOR)

    def save(self):
        # validate input
        correct = True
        if self.name.get() == '':
            correct = False
            m = 'name field cannot be empty'
            tkMessageBox.showerror('Input error', m)
        if self.host.get() == '':
            correct = False
            m = 'host field cannot be empty'
            tkMessageBox.showerror('Input error', m)
        if self.database.get() == '':
            correct = False
            m = 'database field cannot be empty'
            tkMessageBox.showerror('Input error', m)
        if self.port.get() == 0:
            correct = False
            m = 'port field cannot be 0'
            tkMessageBox.showerror('Input error', m)
        if type(self.port.get()) is not int:
            correct = False
            m = 'port value must be a number'
            tkMessageBox.showerror('Input error', m)

        if correct:
            if self.target_id.get() == 0:
                # save as new record
                result = db.insert_record(
                    db.Z3950params,
                    name=self.name.get().strip(),
                    host=self.host.get().strip(),
                    database=self.database.get().strip(),
                    port=self.port.get(),
                    user=self.user.get().strip(),
                    password=self.password.get().strip(),
                    syntax=self.syntax.get().strip(),
                    isbn_url=self.isbn_url.get().strip())

                if result[0]:
                    m = 'target saved'
                    self.reset_values()
                    self.deactivate_widgets(self.zEditFrm)
                    tkMessageBox.showinfo('Info', m)
                    self.observer()
                elif result[0] is False:
                    # duplicate
                    m = "target '%s' already exists" % self.name.get()
                    tkMessageBox.showerror('Database error', m)
                elif result[0] is None:
                    m = result[1]
                    tkMessageBox.showerror('Database error', m)

            else:
                # update existing
                try:
                    db.update_record(
                        db.Z3950params,
                        id=self.target_id.get(),
                        name=self.name.get().strip(),
                        host=self.host.get().strip(),
                        database=self.database.get().strip(),
                        port=self.port.get(),
                        user=self.user.get().strip(),
                        password=self.password.get().strip(),
                        syntax=self.syntax.get().strip(),
                        isbn_url=self.isbn_url.get().strip())
                    m = 'target has been updated'
                    tkMessageBox.showinfo('Info', m)
                except Exception as e:
                    m = 'Database error: %s' % e
                    tkMessageBox.showerror('Database error', m)
            self.observer()

    def cancel(self):
        self.reset_values()
        self.deactivate_widgets(self.zEditFrm)

    def reset_values(self):
        self.target_id.set(0)
        self.name.set('')
        self.host.set('')
        self.database.set('')
        self.port.set(0)
        self.user.set('')
        self.password.set('')
        self.syntax.set('MARC21')
        self.isbn_url.set('')
        self.deactivate_widgets(self.zEditFrm)

    def observer(self, *args):
        if self.tier.get() == 'Z3950Settings':
            # reset form
            self.reset_values()
            # wipe target list
            self.targetLst.delete(0, tk.END)

            # retrieved stored targets & display them
            target_records = db.col_preview(
                db.Z3950params,
                'name')
            for target in target_records:
                self.targetLst.insert(tk.END, target.name)


class CartSheet(tk.Frame):
    """
    Produces an empty cart sheet which is used for selection and records
    distribution
    Module 
    """

    def __init__(self, parent, controller, **sharedData):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        # bind shared variables
        self.tier = sharedData['tier']
        self.tier.trace('w', self.observer)
        self.action = sharedData['action']

        # bind local variables

        self.library_id = tk.IntVar()
        self.fh_name = tk.StringVar()
        self.z3950target = tk.StringVar()
        self.sheet_template = tk.StringVar()
        self.sheet_template.trace('w', self.dynamic_sheetDetails)
        self.sheetDetails = tk.StringVar()
        self.collaborator = tk.StringVar()
        self.collaborator.trace('w', self.dynamic_collabDetails)
        self.collabDetails = tk.StringVar()
        self.distribution = tk.StringVar()
        self.distribution.trace('w', self.dynamic_distribDetails)
        self.distrDetails = tk.StringVar()
        self.distrDetailsShorten = tk.StringVar()
        self.price = tk.DoubleVar()
        self.priceDefault = False
        self.priceDefaultLbl = tk.StringVar()
        self.priceDefaultLbl.set('NOT APPLIED')
        self.discount_value = tk.IntVar()
        self.discount = False
        self.discountLbl = tk.StringVar()
        self.discountLbl.set('NOT APPLIED')
        self.verified = False

        # configure layout
        self.baseFrm = ttk.LabelFrame(self, text='create cart sheet')
        self.baseFrm.grid(
            row=0, column=0, sticky='snew', padx=5, pady=5)
        self.baseFrm.columnconfigure(0, minsize=10)
        self.baseFrm.columnconfigure(1, minsize=100)
        self.baseFrm.columnconfigure(2, minsize=72)
        self.baseFrm.columnconfigure(3, minsize=72)
        self.baseFrm.columnconfigure(4, minsize=72)
        self.baseFrm.columnconfigure(5, minsize=72)
        # self.baseFrm.columnconfigure(6, minsize=220)
        self.baseFrm.columnconfigure(7, minsize=100)
        self.baseFrm.columnconfigure(8, minsize=10)
        self.baseFrm.columnconfigure(9, minsize=72)
        self.baseFrm.columnconfigure(10, minsize=200)
        self.baseFrm.rowconfigure(4, minsize=200)
        self.baseFrm.rowconfigure(9, minsize=200)

        # initialize widgets

        # sheet preview
        self.xscrollbar = tk.Scrollbar(self.baseFrm, orient=tk.HORIZONTAL)
        self.xscrollbar.grid(
            row=5, column=1, columnspan=7, sticky='nwe', padx=10)
        self.yscrollbar = tk.Scrollbar(self.baseFrm, orient=tk.VERTICAL)
        self.yscrollbar.grid(
            row=0, column=0, rowspan=5, sticky='sne', padx=2)
        self.preview_base = tk.Canvas(
            self.baseFrm,
            xscrollcommand=self.xscrollbar.set,
            yscrollcommand=self.yscrollbar.set)
        self.preview_base.grid(
            row=0, column=1, columnspan=7, rowspan=5, sticky='snew', padx=10)
        self.preview()

        # right panel
        tk.Button(self.baseFrm, text='new sheet template', font=REG_FONT,
                  command=self.new_template,
                  width=15).grid(
            row=0, column=9, columnspan=2, sticky='snew', padx=10, pady=5)
        tk.Label(self.baseFrm, text='OR', font=LBL_FONT).grid(
            row=1, column=9, columnspan=2, sticky='snew', padx=10)
        tk.Label(self.baseFrm, text='apply stored sheet template:',
                 font=LBL_FONT).grid(
            row=2, column=9, columnspan=2, sticky='snw', padx=10)
        self.sheetTempCbx = ttk.Combobox(
            self.baseFrm, textvariable=self.sheet_template,
            state='readonly')
        self.sheetTempCbx.grid(
            row=3, column=9, columnspan=2, sticky='new', padx=10, pady=5)
        tk.Label(self.baseFrm, textvariable=self.sheetDetails, font=REG_FONT,
                 justify=tk.LEFT).grid(
            row=4, column=9, columnspan=2, rowspan=4, sticky='nw', padx=10)

        self.priceFrm = ttk.LabelFrame(self.baseFrm, text='price data')
        self.priceFrm.grid(
            row=7, column=9, rowspan=3, columnspan=2, sticky='snew', padx=10)
        # self.priceFrm.columnconfigure(1, minsize=80)
        tk.Label(self.priceFrm, text='average price?',
                 font=LBL_FONT).grid(
            row=0, column=0, columnspan=2, sticky='snw', padx=10, pady=5)
        tk.Label(self.priceFrm, text='discount?',
                 font=LBL_FONT).grid(
            row=3, column=0, sticky='snw', padx=10, pady=5)
        tk.Label(self.priceFrm, textvariable=self.priceDefaultLbl,
                 justify=tk.LEFT,
                 font=LBL_FONT).grid(
            row=1, column=0, columnspan=2, rowspan=2, sticky='nw', padx=10)
        tk.Label(self.priceFrm, textvariable=self.discountLbl,
                 justify=tk.LEFT,
                 font=LBL_FONT).grid(
            row=4, column=0, columnspan=2, rowspan=2, sticky='nw', padx=10)

        # bottom panel
        tk.Button(self.baseFrm, text='load vendor sheet', font=BTN_FONT,
                  width=15,
                  command=self.load_sheet).grid(
            row=6, column=1, sticky='snw', padx=10, pady=5)
        tk.Label(self.baseFrm, text='sheet name:', font=LBL_FONT).grid(
            row=6, column=2, sticky='snw', padx=10, pady=5)
        tk.Label(self.baseFrm, textvariable=self.fh_name, font=LBL_FONT).grid(
            row=6, column=1, columnspan=4, sticky='sne', pady=5)
        tk.Label(self.baseFrm, text='target:').grid(
            row=6, column=6, sticky='ne', pady=5)
        self.z3950targetCbx = ttk.Combobox(
            self.baseFrm,
            textvariable=self.z3950target,
            state='readonly',
            width=20)
        self.z3950targetCbx.grid(
            row=6, column=7, sticky='ne', padx=10, pady=5)

        tk.Label(self.baseFrm, text='collaborator template:',
                 font=LBL_FONT).grid(
            row=7, column=1, sticky='snw', padx=10, pady=5)
        tk.Label(self.baseFrm, text='distribution template:',
                 font=LBL_FONT).grid(
            row=7, column=2, sticky='snw', padx=10, pady=5)
        self.collabCbx = ttk.Combobox(
            self.baseFrm, textvariable=self.collaborator,
            state='readonly',
            font=REG_FONT)
        self.collabCbx.grid(
            row=8, column=1, sticky='nwe', padx=10)
        self.distrCbx = ttk.Combobox(
            self.baseFrm, textvariable=self.distribution,
            state='readonly',
            font=REG_FONT)
        self.distrCbx.grid(
            row=8, column=2, columnspan=3, sticky='nwe', padx=10)

        tk.Button(self.baseFrm, text='create sheet', font=BTN_FONT,
                  width=15,
                  command=self.create_sheet).grid(
            row=8, column=5, sticky='nw', padx=10)
        tk.Button(self.baseFrm, text='close', font=BTN_FONT,
                  width=15,
                  command=self.on_close).grid(
            row=8, column=6, sticky='nw', padx=10)

        tk.Label(self.baseFrm, textvariable=self.collabDetails, font=REG_FONT,
                 justify=tk.LEFT).grid(
            row=9, column=1, sticky='nw', padx=10)
        tk.Label(self.baseFrm, textvariable=self.distrDetailsShorten,
                 font=REG_FONT,
                 justify=tk.LEFT).grid(
            row=9, column=2, columnspan=20, sticky='nw', padx=10)

    def preview(self):
        self.preview_frame = tk.Frame(
            self.preview_base)
        self.xscrollbar.config(command=self.preview_base.xview)
        self.yscrollbar.config(command=self.preview_base.yview)
        self.preview_base.create_window(
            (0, 0), window=self.preview_frame, anchor="nw",
            tags="self.preview_frame")
        self.preview_frame.bind("<Configure>", self.onFrameConfigure)

    def generate_preview(self, data):
        # clear and recreate frame
        self.reset_preview()
        self.rowLst = tk.Listbox(
            self.preview_frame, font=REG_FONT,
            width=3,
            height=self.row_qnt + 1)
        self.rowLst.grid(
            row=1, column=1, sticky='nsw', pady=10)

        for number in range(0, self.row_qnt + 1):
            self.rowLst.insert(tk.END, number)
        c = 0
        r = 0
        for column in range(0, self.col_qnt):
            self.col_name = tk.Listbox(
                self.preview_frame, font=REG_FONT,
                width=15,
                height=self.row_qnt + 1)
            self.col_name.grid(
                row=1, column=c + 2, sticky='nsw', pady=10)
            self.col_name.insert(tk.END, self.column_letters[c])
            for row in data:
                if row[r] is None:
                    self.col_name.insert(tk.END, '')
                else:
                    self.col_name.insert(tk.END, row[r])
            r += 1
            c += 1

    def reset_preview(self):
        self.preview_frame.grid_forget()
        self.preview_frame.destroy()
        self.preview()

    def onFrameConfigure(self, event):
        self.preview_base.config(scrollregion=self.preview_base.bbox('all'))

    def load_sheet(self):
        # retrieve last used directory
        user_data = shelve.open('user_data')
        if 'ven_sheet_dir' in user_data:
            ven_sheet_dir = user_data['ven_sheet_dir']
        else:
            ven_sheet_dir = ''
        fh = tkFileDialog.askopenfilename(initialdir=ven_sheet_dir)
        if fh:
            # record directory
            n = fh.rfind('/')
            ven_sheet_dir = fh[:n + 1]
            fh_name = fh[n + 1:]
            # user_data['cart_dir'] = cart_dir
            # validate if correct file type
            if fh_name.rfind('.xlsx') == -1:
                msg = 'Wrong type of spreadsheet file.\n' \
                      'Only sheets with extention .xlsx are permitted'
                tkMessageBox.showwarning('File type error', msg)
            else:
                self.fh_name.set(fh_name)
                self.sheet = sh.SheetManipulator(fh)
                self.column_letters = self.sheet.get_column_letters()
                data = self.sheet.extract_data()
                self.row_qnt = len(data)
                self.col_qnt = len(self.column_letters)
                self.generate_preview(data)
        user_data.close()

    def dynamic_collabDetails(self, *args):
        if self.collabCbx.get() != '':
            collab_id = self.collab_by_name[self.collaborator.get()][0]
            record = db.retrieve_record(
                db.Collaborator,
                id=collab_id)
            d = 'coll 1: %s\ncoll 2: %s\ncoll 3: %s\n' \
                'coll 4: %s\ncoll 5: %s' % (
                    record.collab1, record.collab2,
                    record.collab3, record.collab4,
                    record.collab5)
            self.collabDetails.set(d)

    def dynamic_distribDetails(self, *args):
        if self.distrCbx.get() != '':
            distr_id = self.distr_by_name[self.distribution.get()][0]
            distr = db.retrieve_record(
                db.DistrTemplate,
                id=distr_id)
            library = db.retrieve_record(
                db.Library,
                id=distr.library_id)
            lang = self.lang_by_id[distr.lang_id][0]
            distrCodes = db.col_preview(
                db.DistrCode,
                'id', 'code',
                distrTemplate_id=distr_id)
            c = []
            self.codeTotalQntBranch = {}
            for code in distrCodes:
                locQnts = db.col_preview(
                    db.DistrLocQuantity,
                    'id', 'location_id', 'quantity',
                    distrCode_id=code.id
                )

                # define elements of distrDetails
                locs = []
                qnt = 0
                branches = ''
                for locQnt in locQnts:
                    loc = db.retrieve_record(
                        db.Location,
                        id=locQnt.location_id)
                    locs.append('%s(%s)' % (loc.name, locQnt.quantity))
                    qnt += locQnt.quantity
                    # define elements of distribution-branch relationship
                    branch = db.retrieve_record(
                        db.Branch,
                        id=loc.branch_id)
                    branches = branches + branch.code + ','

                c.append((code.code, locs))
                self.codeTotalQntBranch[code.code] = (qnt, branches)

            codes_cart = []
            codes_app = []
            for distr in c:
                # format codes for cart sheet legend
                code = '%s: %s' % (distr[0], ','.join(distr[1]))
                codes_cart.append(code)

                # format codes for babel display
                short_locs = []
                if len(distr[1]) > 5:
                    last_loc = distr[1][-1]
                    short_locs = distr[1][:6]
                    short_locs.append('...')
                    short_locs.append(last_loc)
                    code = '%s: %s' % (distr[0], ','.join(short_locs))
                else:
                    code = '%s: %s' % (distr[0], ','.join(distr[1]))
                codes_app.append(code)

            if len(codes_app) > 6:
                last_code = codes_app[-1]
                codes_app = codes_app[:6]
                codes_app.append('...')
                codes_app.append(last_code)

            c_str = '\n'.join(codes_cart)
            a_str = '\n'.join(codes_app)
            d_cart = ('library: %s\tlanguage: %s\n' + c_str) % (
                library.code, lang)
            d_app = ('library: %s\tlanguage: %s\n' + a_str) % (
                library.code, lang)
            self.distrDetails.set(d_cart)
            self.distrDetailsShorten.set(d_app)
            self.distr_record = distr

    def dynamic_sheetDetails(self, *args):
        if self.sheetTempCbx.get() != '':
            record = db.retrieve_record(
                db.VendorSheetTemplate,
                id=self.sheet_template_by_name[self.sheet_template.get()][0])
            self.vendor = str(self.vendor_by_id[record.vendor_id][0])
            self.lang = str(self.lang_by_id[record.lang_id][0])
            self.matType = str(self.matType_by_id[record.matType_id][0])
            self.head_row = record.headRow
            self.title_col = record.titleCol
            self.author_col = record.authorCol
            self.isbn_col = record.isbnCol
            self.venNum_col = record.venNoCol
            self.publisher_col = record.publisherCol
            self.pubDate_col = record.pubDateCol
            self.pubPlace_col = record.pubPlaceCol
            self.priceDisc_col = record.priceDiscCol
            self.priceReg_col = record.priceRegCol

            d = 'sheet template details:\n' \
                'vendor: %s\n' \
                'language: %s\n' \
                'material type: %s\n' \
                'heading row: %s\n' \
                'title column: %s\n' \
                'author column: %s\n' \
                'isbn column: %s\n' \
                'vendor # column: %s\n' \
                'disc.price column: %s\n' \
                'list price column: %s\n' \
                'publisher column: %s\n' \
                'pub date column: %s\n' \
                'pub place column: %s\n' % (
                    self.vendor,
                    self.lang,
                    self.matType,
                    self.head_row,
                    self.title_col,
                    self.author_col,
                    self.isbn_col,
                    self.venNum_col,
                    self.priceDisc_col,
                    self.priceReg_col,
                    self.publisher_col,
                    self.pubDate_col,
                    self.pubPlace_col)
            self.sheetDetails.set(d)

    def new_template(self):
        self.action.set('add')
        self.tier.set('VendorSheetSingle')
        self.controller.show_frame('VendorSheetSingle')

    def ask_for_price(self):
        self.top = tk.Toplevel()
        self.top.title('default price')
        self.top.columnconfigure(1, minsize=10)
        tk.Label(
            self.top,
            text='Discounted price column not specified.\n'
                 'Please provide average price that can\n'
                 'be applied to all titles').grid(
            row=0, column=0, columnspan=3, sticky='snew', padx=10, pady=10)
        self.priceEnt = tk.Entry(
            self.top, font=REG_FONT, textvariable=self.price,
            width=5)
        self.priceEnt.grid(
            row=1, column=1, sticky='snw', padx=15, pady=15)
        tk.Button(self.top, text='OK', font=REG_FONT,
                  width=15,
                  command=self.on_price_OK).grid(
            row=2, column=0, sticky='snw', padx=10, pady=10)
        tk.Button(self.top, text='cancel', font=REG_FONT,
                  width=15,
                  command=self.top.destroy).grid(
            row=2, column=2, sticky='sne', padx=10, pady=10)

    def ask_for_discount(self):
        self.top = tk.Toplevel()
        self.top.title('discount')
        self.top.columnconfigure(1, minsize=10)
        tk.Label(
            self.top,
            text='Discounted price column not specified.\n'
                 'Please provide discount % that will be\n'
                 'applied to all titles').grid(
            row=0, column=0, columnspan=3, sticky='snew', padx=10, pady=10)
        self.discountEnt = tk.Entry(
            self.top, font=REG_FONT, textvariable=self.discount_value,
            width=5)
        self.discountEnt.grid(
            row=1, column=1, sticky='snw', padx=15, pady=15)
        tk.Button(self.top, text='OK', font=REG_FONT,
                  width=15,
                  command=self.on_discount_OK).grid(
            row=2, column=0, sticky='snw', padx=10, pady=10)
        tk.Button(self.top, text='cancel', font=REG_FONT,
                  width=15,
                  command=self.top.destroy).grid(
            row=2, column=2, sticky='sne', padx=10, pady=10)

    def on_price_OK(self):
        if self.price.get() == 0.0:
            m = 'price must be bigger than $0.0'
            tkMessageBox.showwarning('Input error', m)
        else:
            self.verified = True
            m = 'Yes. Price $%s will be applied\n' \
                'to all titles' % self.price.get()
            self.priceDefaultLbl.set(m)
            self.top.destroy()

    def on_discount_OK(self):
        self.verified = True
        m = 'Discount %s percent will be applied\n' \
            'to all titles' % self.discount_value.get()
        self.discountLbl.set(m)
        self.top.destroy()

    def create_sheet(self):
        if self.sheet_template.get() != '':
            priceDisc_col = self.sheet_template_by_name[
                self.sheet_template.get()][1]
            priceReg_col = self.sheet_template_by_name[
                self.sheet_template.get()][2]
            if priceDisc_col == '' \
                    and self.discount is False \
                    and self.priceDefault is False \
                    and self.verified is False:
                if priceReg_col == '':
                    self.priceDefault = True
                else:
                    self.discount = True

        if self.fh_name.get() == '':
            m = 'please load a vendor sheet'
            tkMessageBox.showwarning('Input error', m)
        elif self.sheet_template.get() == '':
            m = 'please select a vendor sheet template'
            tkMessageBox.showwarning('Input error', m)
        elif self.distribution.get() == '':
            m = 'please select a distribution template'
            tkMessageBox.showwarning('Input error', m)
        elif self.priceDefault is True and self.verified is False:
            self.ask_for_price()
        elif self.discount is True and self.verified is False:
            self.ask_for_discount()
        else:
            # retrieve collaborators names
            # this could be improved by recording collabs in related table
            # insted of Collaborator table
            if self.collaborator.get() != '':
                collab_id = self.collab_by_name[self.collaborator.get()][0]
                record = db.retrieve_record(
                    db.Collaborator,
                    id=collab_id)
                collabs = ()
                if record.collab1 != '':
                    collabs = collabs + (record.collab1, )
                if record.collab2 != '':
                    collabs = collabs + (record.collab2, )
                if record.collab3 != '':
                    collabs = collabs + (record.collab3, )
                if record.collab4 != '':
                    collabs = collabs + (record.collab4, )
                if record.collab5 != '':
                    collabs = collabs + (record.collab5, )
            else:
                collabs = ()

            # add default price if needed:
            sheetTemp_id = self.sheet_template_by_name[
                self.sheet_template.get()][0]
            distr_id = self.distr_by_name[self.distribution.get()][0]
            if self.z3950target.get() == '':
                target = None
            else:
                target = self.targets_by_name[self.z3950target.get()]
            kwargs = {
                'collabs': collabs,
                'head_row': self.head_row,
                'distr_id': distr_id,
                'distrDetails': self.distrDetails.get(),
                'codeTotalQntBranch': self.codeTotalQntBranch,
                'priceDefault': self.price.get(),
                'sheetTemp_id': sheetTemp_id,
                'title_col': self.title_col,
                'author_col': self.author_col,
                'isbn_col': self.isbn_col,
                'venNum_col': self.venNum_col,
                'priceDisc_col': self.priceDisc_col,
                'priceReg_col': self.priceReg_col,
                'publisher_col': self.publisher_col,
                'pubDate_col': self.pubDate_col,
                'pubPlace_col': self.pubPlace_col,
                'discount': self.discount_value.get(),
                'z3950target': target
            }
            # print kwargs['z3950target']
            user_data = shelve.open('user_data')
            if 'cart_dir' in user_data:
                cart_dir = user_data['cart_dir']
            else:
                cart_dir = os.getcwd() + '\\'
            user_data.close()
            file_date = datetime.datetime.strftime(
                datetime.date.today(), '%y%m%d')
            fname = cart_dir + self.vendor + '-' + file_date

            # create cart sheet
            cur_manager.busy()
            try:
                cart_file = self.sheet.cart_sheet(fname, **kwargs)
                cur_manager.notbusy()
                m = 'Cart sheet:\n %s \nhas been created\n\n' \
                    'Open created sheet?' % cart_file
                if tkMessageBox.askyesno(
                        'Output message', m):
                    os.startfile(cart_file)

            except:
                main_logger.exception('Cart sheet error:')
                cur_manager.notbusy()

            self.reset_values()

    def on_close(self):
        # reset choices
        self.reset_preview()
        self.reset_values()
        self.tier.set('Main')
        self.controller.show_frame('Main')

    def reset_values(self):
        self.price.set(0.0)
        self.z3950target.set('')
        self.priceDefault = False
        self.priceDefaultLbl.set('NOT APPLIED')
        self.discountLbl.set('NOT APPLIED')
        self.discount_value.set(0)
        self.discount = False
        self.verified = False
        self.fh_name.set('')
        self.distrCbx.set('')
        self.distrDetails.set('')
        self.distrDetailsShorten.set('')
        self.collabCbx.set('')
        self.collabDetails.set('')
        self.sheetTempCbx.set('')
        self.sheetDetails.set('')
        self.sheet_template.set('')
        self.sheetDetails.set('')
        self.collabDetails.set('')
        self.collaborator.set('')
        self.distribution.set('')
        self.reset_preview()

    def observer(self, *args):
        if self.tier.get() == 'CartSheet':
            # reset values
            self.reset_values()
            # create & bind indexes:
            self.sheet_template_choices = ()
            self.sheet_template_by_name = {}
            self.vendor_choices = ()
            self.vendor_by_id = {}
            self.lang_by_id = {}
            self.matType_by_id = {}
            self.collab_choices = ()
            self.collab_by_name = {}
            self.distr_choices = ()
            self.distr_by_name = {}
            records = db.col_preview(
                db.Vendor,
                'name', 'id')
            for record in records:
                self.vendor_by_id[record.id] = (record.name, )
            records = db.col_preview(
                db.Lang,
                'name', 'id')
            for record in records:
                self.lang_by_id[record.id] = (record.name, )
            records = db.col_preview(
                db.MatType,
                'name', 'id')
            for record in records:
                self.matType_by_id[record.id] = (record.name, )
            records = db.col_preview(
                db.Collaborator,
                'templateName', 'id')
            for record in records:
                self.collab_choices = self.collab_choices + \
                    (record.templateName, )
                self.collab_by_name[record.templateName] = (record.id, )
            records = db.col_preview(
                db.DistrTemplate,
                'name', 'id')
            for record in records:
                self.distr_choices = self.distr_choices + (record.name, )
                self.distr_by_name[record.name] = (record.id, )
            records = db.col_preview(
                db.VendorSheetTemplate,
                'name', 'id', 'priceDiscCol', 'priceRegCol')
            for record in records:
                self.sheet_template_choices = self.sheet_template_choices + \
                    (record.name, )
                self.sheet_template_by_name[record.name] = (
                    record.id, record.priceDiscCol, record.priceRegCol)
            self.sheetTempCbx['values'] = self.sheet_template_choices
            self.collabCbx['values'] = self.collab_choices
            self.distrCbx['values'] = self.distr_choices

            # z3950 targets index
            targets = []
            self.targets_by_name = {}

            records = db.col_preview(
                db.Z3950params,
                'id',
                'name',
                'host',
                'database',
                'port',
                'user',
                'password',
                'syntax',
                'isbn_url')

            for record in records:
                targets.append(record.name)
                self.targets_by_name[record.name] = {
                    'name': record.name,
                    'host': record.host,
                    'database': record.database,
                    'port': record.port,
                    'user': record.user,
                    'password': record.password,
                    'syntax': record.syntax,
                    'isbn_url': record.isbn_url
                }

            self.z3950targetCbx['values'] = targets


class ImportCartSheet(tk.Frame):

    def __init__(self, parent, controller, **sharedData):
        tk.Frame.__init__(self, parent)

        # bind shared variables
        self.controller = controller
        self.tier = sharedData['tier']
        self.tier.trace('w', self.observer)
        self.action = sharedData['action']

        # bind local variables
        self.fh_name = tk.StringVar()
        self.sheet_meta = tk.StringVar()
        self.fund = tk.StringVar()
        self.funds = tk.StringVar()
        self.selector = tk.StringVar()

        # configure layout
        self.baseFrm = ttk.LabelFrame(self, text='sheet import')
        self.baseFrm.grid(
            row=0, column=0, sticky='snew', padx=5, pady=5)
        self.baseFrm.columnconfigure(0, minsize=10)
        self.baseFrm.columnconfigure(3, minsize=74)
        self.baseFrm.columnconfigure(6, minsize=400)
        self.baseFrm.columnconfigure(7, minsize=240)
        self.baseFrm.rowconfigure(4, minsize=350)
        self.baseFrm.rowconfigure(7, minsize=20)
        self.baseFrm.rowconfigure(11, minsize=10)

        # initiate widgets

        # sheet file info
        tk.Label(self.baseFrm, text='cart sheet preview:', font=LBL_FONT).grid(
            row=0, column=1, columnspan=2, sticky='snw', padx=10)
        tk.Label(self.baseFrm, textvariable=self.fh_name, font=LBL_FONT).grid(
            row=0, column=2, columnspan=5, sticky='snw', padx=10)

        # preview area
        self.xscrollbar = tk.Scrollbar(self.baseFrm, orient=tk.HORIZONTAL)
        self.xscrollbar.grid(
            row=6, column=1, columnspan=6, sticky='nwe', padx=10)
        self.yscrollbar = tk.Scrollbar(self.baseFrm, orient=tk.VERTICAL)
        self.yscrollbar.grid(
            row=1, column=0, rowspan=5, sticky='nse', padx=2)
        self.preview_base = tk.Canvas(
            self.baseFrm,
            xscrollcommand=self.xscrollbar.set,
            yscrollcommand=self.yscrollbar.set)
        self.preview_base.grid(
            row=1, column=1, columnspan=6, rowspan=5, sticky='snew', padx=5)
        self.preview_area()

        # sheet structure info
        tk.Label(self.baseFrm, text='cart sheet info:', font=LBL_FONT).grid(
            row=1, column=7, columnspan=2, sticky='snw', padx=10)
        tk.Label(self.baseFrm, textvariable=self.sheet_meta, font=REG_FONT,
                 justify=tk.LEFT).grid(
            row=2, column=7, columnspan=2, rowspan=10, sticky='nw',
            padx=15, pady=2)

        # operation panel
        tk.Button(self.baseFrm, text='load cart sheet', font=BTN_FONT,
                  width=15,
                  command=self.on_load).grid(
            row=8, column=1, columnspan=2, sticky='snw', padx=10, pady=2)
        tk.Label(self.baseFrm, text='selector:', font=LBL_FONT).grid(
            row=8, column=3, sticky='sne', padx=5, pady=2)
        self.selectorCbx = ttk.Combobox(self.baseFrm,
                                        textvariable=self.selector,
                                        width=20,
                                        height=1)
        self.selectorCbx.grid(
            row=8, column=4, sticky='snw', pady=2)

        self.fundFrm = ttk.LabelFrame(self.baseFrm, text='funds')
        self.fundFrm.grid(
            row=9, column=1, rowspan=3, columnspan=4, sticky='snew',
            padx=5, pady=5)
        self.fundFrm.columnconfigure(3, minsize=74)
        tk.Label(self.fundFrm, text='applied funds:', font=LBL_FONT).grid(
            row=0, column=1, sticky='sne', padx=10, pady=5)
        tk.Label(self.fundFrm, textvariable=self.funds, font=LBL_FONT).grid(
            row=0, column=2, columnspan=4, sticky='snw', padx=15, pady=5)
        tk.Button(self.fundFrm, text='reset', font=BTN_FONT,
                  width=10,
                  command=self.on_reset).grid(
            row=0, column=4, sticky='snw', padx=10, pady=5)

        tk.Label(self.fundFrm, text='fund:', font=LBL_FONT).grid(
            row=1, column=1, sticky='sne', padx=10, pady=5)
        self.fundCbx = ttk.Combobox(self.fundFrm, textvariable=self.fund,
                                    state='readonly',
                                    width=10,
                                    height=1,
                                    font=REG_FONT)
        self.fundCbx.grid(
            row=1, column=2, sticky='snw', padx=10, pady=5)
        tk.Button(self.fundFrm, text='apply', font=BTN_FONT,
                  width=10,
                  command=self.on_apply).grid(
            row=1, column=4, sticky='snw', padx=10, pady=5)

        # import & close buttons
        tk.Button(self.baseFrm, text='import', font=BTN_FONT,
                  width=15,
                  height=1,
                  command=self.on_process).grid(
            row=11, column=5, sticky='sw', padx=10, pady=20)
        tk.Button(self.baseFrm, text='close', font=BTN_FONT,
                  width=15,
                  height=1,
                  command=self.on_close).grid(
            row=11, column=6, sticky='sw', padx=10, pady=20)

    def preview_area(self):
        self.preview_frame = tk.Frame(
            self.preview_base)
        self.xscrollbar.config(command=self.preview_base.xview)
        self.yscrollbar.config(command=self.preview_base.yview)
        self.preview_base.create_window(
            (0, 0), window=self.preview_frame, anchor="nw",
            tags="self.preview_frame")
        self.preview_frame.bind("<Configure>", self.onFrameConfigure)

    def generate_preview(self, data):
        # clear and recreate frame
        self.reset_preview()
        self.rowLst = tk.Listbox(
            self.preview_frame, font=REG_FONT,
            width=3,
            height=self.row_qnt + 1)
        self.rowLst.grid(
            row=1, column=1, sticky='nsw', pady=10)

        for number in range(0, self.row_qnt + 1):
            self.rowLst.insert(tk.END, number)
        c = 0
        r = 0
        for column in range(0, self.col_qnt):
            self.col_name = tk.Listbox(
                self.preview_frame, font=REG_FONT,
                width=15,
                height=self.row_qnt + 1)
            self.col_name.grid(
                row=1, column=c + 2, sticky='nsw', pady=10)
            self.col_name.insert(tk.END, self.column_letters[c])
            for row in data:
                if row[r] is None:
                    self.col_name.insert(tk.END, '')
                else:
                    self.col_name.insert(tk.END, row[r])
            r += 1
            c += 1

    def reset_preview(self):
        self.preview_frame.grid_forget()
        self.preview_frame.destroy()
        self.preview_area()

    def onFrameConfigure(self, event):
        self.preview_base.config(scrollregion=self.preview_base.bbox('all'))

    def on_load(self):
        cur_manager.busy()
        self.reset_form()
        # retrieve last used directory
        user_data = shelve.open('user_data')
        if 'cart_completed_dir' in user_data:
            cart_completed_dir = user_data['cart_completed_dir']
        else:
            cart_completed_dir = ''
        fh = tkFileDialog.askopenfilename(initialdir=cart_completed_dir)
        if fh:
            # record directory
            n = fh.rfind('/')
            cart_completed_dir = fh[:n + 1]
            fh_name = fh[n + 1:]
            user_data['cart_completed_dir'] = cart_completed_dir
            # validate if correct file type
            if fh.rfind('.xlsx') == -1:
                msg = 'Wrong type of spreadsheet file.\n' \
                      'Only sheets with extention .xlsx are permitted'
                tkMessageBox.showwarning('File type error', msg)
            else:
                self.fh_name.set(fh_name)
                self.sheet = sh.SheetManipulator(fh)
                self.column_letters = self.sheet.get_column_letters()
                self.data = self.sheet.extract_data()
                try:
                    self.meta = self.sheet.extract_meta()
                    correct_sheet = True
                except KeyError:
                    m = 'It appears cart metadata is missing in the sheet.\n' \
                        'Please verify you try to process correct cart sheet'
                    tkMessageBox.showwarning('Sheet error', m)
                    correct_sheet = False
                if correct_sheet:
                    self.row_qnt = len(self.data)
                    self.col_qnt = len(self.column_letters)
                    self.generate_preview(self.data)
                    self.display_meta(self.meta)
        user_data.close()
        cur_manager.notbusy()

    def display_meta(self, meta):
        self.distr_record = db.retrieve_record(
            db.DistrTemplate,
            id=meta['distrTemplate_id'])
        if self.distr_record is None:
            metaDetails = 'Error...'
            m = 'Distribution template used in this cart sheet\n' \
                'has been deleted. Unable to proceed.'
            tkMessageBox.showerror('Error', m)
        else:
            self.distrTemplate_id = self.distr_record.id
            self.library_id = self.distr_record.library_id
            self.lang_id = self.distr_record.lang_id  # think if pulling lang from vendor would be more appropriate
            distr_name = self.distr_record.name

            lib_rec = db.retrieve_record(
                db.Library,
                id=self.distr_record.library_id)
            self.library = lib_rec.code
            if lib_rec.id == 1:
                self.fundCbx['values'] = self.bpl_fund_choices
            elif lib_rec.id == 2:
                self.fundCbx['values'] = self.nypl_fund_choices

            lang_rec = db.retrieve_record(
                db.Lang,
                id=self.distr_record.lang_id)
            lang = lang_rec.name

            venSheet_rec = db.retrieve_record(
                db.VendorSheetTemplate,
                id=meta['vendorSheetTemplate_id'])
            self.vendor_id = venSheet_rec.vendor_id
            self.matType_id = venSheet_rec.matType_id
            ven_rec = db.retrieve_record(
                db.Vendor,
                id=venSheet_rec.vendor_id)
            self.vendor = ven_rec.name

            matType_rec = db.retrieve_record(
                db.MatType,
                id=venSheet_rec.matType_id)
            matType = matType_rec.name
            metaDetails = 'library: %s\n' \
                          'vendor: %s\n' \
                          'language: %s\n' \
                          'material type: %s\n' \
                          'distribution template: \n  %s\n' \
                          '------------\n' \
                          'cart sheet structure:\n' \
                          'headings row: %s\n' \
                          'distribution column: %s\n' \
                          'audience column: %s\n' \
                          'PO per line: %s\n' \
                          'title column: %s\n' \
                          'author column: %s\n' \
                          'ISBN column: %s\n' \
                          'vendor number column: %s\n' \
                          'publisher column: %s\n' \
                          'pub. date column: %s\n' \
                          'pub. place column: %s\n' \
                          'list price column: %s\n' \
                          'discount price column: %s\n' % (
                              self.library, self.vendor, lang, matType,
                              distr_name,
                              meta['head_row'], meta['distr_col'],
                              meta['audn_col'], meta['po_per_line_col'],
                              meta['title_col'],
                              meta['author_col'],
                              meta['isbn_col'], meta['venNum_col'],
                              meta['publisher_col'], meta['pubDate_col'],
                              meta['pubPlace_col'],
                              meta['priceReg_col'], meta['priceDisc_col'])

            # find distr codes so they can be used for verification
            # that correct code has been used in the sheet
            records = db.col_preview(
                db.DistrCode,
                'code',
                distrTemplate_id=meta['distrTemplate_id'])
            self.distr_codes = ()
            for record in records:
                self.distr_codes = self.distr_codes + (record.code, )
        self.sheet_meta.set(metaDetails)

    def on_reset(self):
        self.funds.set('')

    def on_apply(self):
        if self.funds.get() == '':
            funds_str = self.fund.get()
        elif self.fund.get() in self.funds.get():
            funds_str = self.funds.get()
        else:
            funds_str = self.funds.get() + '+' + self.fund.get()
        self.funds.set(funds_str)

    def on_process(self):
        if self.funds.get() == '':
            m = 'at least one fund must be applied to proceed'
            tkMessageBox.showwarning('Input error', m)
        elif self.fh_name.get() == '':
            m = 'cart sheet must be loaded to proceed'
            tkMessageBox.showwarning('Input error', m)
        elif self.selector.get() == '':
            m = 'please pick a selector to proceed'
            tkMessageBox.showwarning('Input error', m)
        else:
            # error messages variable
            error_msg = set()
            # record selector
            user_data = shelve.open('user_data')
            user_data['last_selector'] = self.selector.get()
            user_data.close()
            self.selector_id = self.selector_by_name[self.selector.get()][0]

            # record date
            date = datetime.datetime.strftime(
                datetime.datetime.now(), '%Y%m%d%H%M%S')

            # record name of order
            name = self.library + '_' + self.vendor + '~' + \
                date[:4] + '-' + date[4:6] + '-' + date[6:8] + \
                '-' + date[8:10] + ':' + date[10:12] + ':' + date[12:]
            first_wlo = ''
            last_wlo = ''

            # insert order to babelstore
            cur_manager.busy()
            # assign blanketPO
            blanketPO_date = datetime.datetime.strftime(
                datetime.datetime.now(), '%Y%m%d')
            blanketPO_numbering = 0
            vendor_record = db.retrieve_record(
                db.Vendor,
                id=self.vendor_id)
            if vendor_record is not None:
                if self.library_id == 1:
                    blanketPO = vendor_record.bplCode + '-' + blanketPO_date
                elif self.library_id == 2:
                    blanketPO = vendor_record.nyplCode + '-' + blanketPO_date

                exist = False
                while exist is not None:
                    blanketPO_numbering += 1
                    test_blanketPO = blanketPO + '-' + str(blanketPO_numbering)
                    exist = db.retrieve_record(
                        db.Order,
                        library_id=self.library_id,
                        blanketPO=test_blanketPO)
                else:
                    blanketPO = test_blanketPO

            db.ignore_or_insert(
                db.Order,
                name=name,
                date=date,
                library_id=self.library_id,
                lang_id=self.lang_id,
                vendor_id=self.vendor_id,
                selector_id=self.selector_id,
                matType_id=self.matType_id,
                blanketPO=blanketPO)
            loaded_record = db.retrieve_last(
                db.Order)
            order_id = loaded_record.id

            # find selected rows
            # and determine if distr code in column mateches
            # applied distrTemplate
            results = self.sheet.find_orders(self.distr_codes)

            # insert new orderSingle record
            for order in results['orders']:
                # determine if add as new or attached as dup
                if order['isbn_col'] != '':
                    isbn = input_parser.parse_isbn(order['isbn_col'])
                else:
                    isbn = None

                # convert to cents for storing
                priceDisc = dollars2cents(order['priceDisc_col'])

                if order['priceReg_col'] is not None:
                    priceReg = dollars2cents(order['priceReg_col'])
                else:
                    priceReg = None

                # insert new bibRec
                title = order['title_col']
                author = order['author_col']
                publisher = order['publisher_col']
                # parse pubDate
                pubDate = input_parser.parse_year(order['pubDate_col'])
                pubPlace = order['pubPlace_col']
                venNo = order['venNum_col']
                audn = order['audn_col']
                po_per_line = order['po_per_line_col']
                distr_codes = str(order['distr_col'])

                # better be replaced by parsed id from db
                if audn == 'y' or audn == 'Y':
                    audn_id = 2
                elif audn == 'j' or audn == 'J':
                    audn_id = 1
                else:
                    audn_id = 3
                result = db.insert_record(
                    db.BibRec,
                    title=title,
                    author=author,
                    publisher=publisher,
                    pubDate=pubDate,
                    pubPlace=pubPlace,
                    audn_id=audn_id,
                    isbn=isbn,
                    venNo=venNo)

                if result[0] is False:
                    loaded_bib = result[1]
                elif result[0] is True:
                    loaded_bib = db.retrieve_last(
                        db.BibRec)
                else:
                    loaded_bib = None
                    m = result[1]
                    tkMessageBox.showerror('Database error', m)
                if loaded_bib is not None:
                    # insert OrderSingle record to localstore
                    db.ignore_or_insert(
                        db.OrderSingle,
                        wlo_id=wlo_generator.get_new_number(),
                        bibRec_id=loaded_bib.id,
                        order_id=order_id,
                        audn_id=audn_id,
                        po_per_line=po_per_line,
                        priceDisc=priceDisc,
                        priceReg=priceReg)

                    loaded_record = db.retrieve_last(
                        db.OrderSingle)
                    orderSingle_id = loaded_record.id

                    # find locations & funds that apply to them
                    # applied funds are parsed by find_fund()
                    distr_code_records = db.col_preview(
                        db.DistrCode,
                        'id', 'code',
                        distrTemplate_id=self.distrTemplate_id)
                    new_records = []
                    for record in distr_code_records:
                        if record.code in distr_codes:
                            location_records = db.col_preview(
                                db.DistrLocQuantity,
                                'id', 'location_id', 'quantity',
                                distrCode_id=record.id)
                            for distr_location in location_records:
                                # find correct fund
                                fund_search = find_fund(
                                    self.library_id, self.funds.get(),
                                    audn_id, self.matType_id,
                                    distr_location.location_id)
                                if fund_search[0]:
                                    fund_id = fund_search[1]
                                    new = db.create_db_object(
                                        db.OrderSingleLoc,
                                        orderSingle_id=orderSingle_id,
                                        location_id=distr_location.location_id,
                                        fund_id=fund_id,
                                        qty=distr_location.quantity)
                                    new_records.append(new)
                                else:
                                    # add message insted to be displayed
                                    error_msg.add(fund_search[1])

                    db.update_record(
                        db.OrderSingle,
                        id=orderSingle_id,
                        orderSingleLocations=new_records)

            # summarize order
            loaded_records = db.retrieve_all(
                db.OrderSingle,
                'orderSingleLocations',
                order_id=order_id)
            total_qty = 0
            total_titles = 0
            total_cost = 0
            first_wlo = None
            funds_used = {}
            for record in loaded_records:
                if first_wlo is None:
                    first_wlo = record.wlo_id
                total_titles += 1
                for related_record in record.orderSingleLocations:
                    total_qty = total_qty + \
                        related_record.qty
                    total_cost = total_cost + \
                        record.priceDisc * related_record.qty
                    fund_id = related_record.fund_id
                    if fund_id in funds_used:
                        funds_used[fund_id] = funds_used[fund_id] + (
                            related_record.qty * record.priceDisc)
                    else:
                        funds_used[fund_id] = related_record.qty * record.priceDisc
            total_cost = cents2dollars(total_cost)

            last_wlo = wlo_generator.get_last_number()

            # update order record
            db.update_record(
                db.Order,
                order_id,
                wlo_range=first_wlo + '-' + last_wlo)

            # display errors if any
            if len(error_msg) > 0:
                tkMessageBox.showerror('Import errors', '\n'.join(error_msg))

            m = 'order saved as %s\n' \
                'titles total=%s\n' \
                'quantity total=%s\n' \
                'cost total=$%s\n' \
                'wlo range: %s-%s\n' % (
                    name, total_titles, total_qty,
                    total_cost, first_wlo, last_wlo)

            f = '--------------\n'
            for fund_id in funds_used:
                fund_record = db.retrieve_record(
                    db.Fund,
                    id=fund_id)
                f = f + 'fund %s=$%s\n' % (fund_record.code,
                                           cents2dollars(funds_used[fund_id]))
            m = m + f

            # display summary message
            tkMessageBox.showinfo('Output message', m)

            self.reset_form()
            self.reset_preview()
            cur_manager.notbusy()

    def on_close(self):
        self.reset_preview()
        self.reset_form()
        self.controller.show_frame('Main')

    def reset_form(self):
        self.fh_name.set('')
        self.sheet_meta.set('')
        self.funds.set('')
        self.fund.set('')

    def observer(self, *args):
        if self.tier.get() == 'ImportCartSheet':
            self.reset_form()
            self.reset_preview()

            # create indexes
            self.bpl_fund_choices = ()
            self.nypl_fund_choices = ()
            self.fund_by_name = {}
            self.selector_choices = ()
            self.selector_by_name = {}
            records = db.col_preview(
                db.Fund,
                'code', 'library_id', 'id')
            for record in records:
                if record.library_id == 1:
                    self.bpl_fund_choices = self.bpl_fund_choices + (
                        record.code, )
                if record.library_id == 2:
                    self.nypl_fund_choices = self.nypl_fund_choices + (
                        record.code, )
                self.fund_by_name[record.code] = (record.id, )
            records = db.col_preview(
                db.Selector,
                'name', 'id')
            for record in records:
                self.selector_choices = self.selector_choices + (record.name, )
                self.selector_by_name[record.name] = (record.id, )
            self.selectorCbx['values'] = self.selector_choices
            user_data = shelve.open('user_data')
            if 'last_selector' in user_data:
                self.selector.set(user_data['last_selector'])
            user_data.close()


class OrderBrowse(tk.Frame):

    def __init__(self, parent, controller, **sharedData):
        tk.Frame.__init__(self, parent)

        # bind shared variables
        self.controller = controller
        self.tier = sharedData['tier']
        self.tier.trace('w', self.observer)
        self.action = sharedData['action']
        self.selectedOrder = sharedData['selectedItem_1']
        self.selectedLibrary_id = sharedData['selectedItem_3']

        # bind local variables
        self.library_id = tk.IntVar()
        self.orderName = tk.StringVar()
        self.orderId = 0
        self.selector_id = None
        self.vendor_id = None
        # self.orderDetails = tk.StringVar()
        self.date_sort = tk.StringVar()
        self.selector_filter = tk.StringVar()
        self.vendor_filter = tk.StringVar()
        self.lang_filter = tk.StringVar()
        self.matType_filter = tk.StringVar()

        # trace changes in filters to trigger dynamic display of orders
        self.library_id.trace('w', self.dynamic_orders)
        self.date_sort.trace('w', self.dynamic_orders)
        self.selector_filter.trace('w', self.dynamic_orders)
        self.vendor_filter.trace('w', self.dynamic_orders)
        self.lang_filter.trace('w', self.dynamic_orders)
        self.matType_filter.trace('w', self.dynamic_orders)

        # configure layout
        # self.columnconfigure(0, minsize=50)
        # self.columnconfigure(1, minsize=250)
        self.rowconfigure(4, minsize=5)
        self.rowconfigure(9, minsize=55)
        self.rowconfigure(13, minsize=145)

        # initiate widgets
        ttk.Radiobutton(self, text='BPL',
                        variable=self.library_id, value=1).grid(
            row=0, column=0, sticky='snew', padx=10)
        ttk.Radiobutton(self, text='NYPL',
                        variable=self.library_id, value=2).grid(
            row=1, column=0, sticky='snew', padx=10)
        tk.Label(self, text='sort by date:',
                 font=LBL_FONT).grid(
            row=0, column=1, sticky='snw', padx=5, pady=2)
        self.sortCbx = ttk.Combobox(self, textvariable=self.date_sort,
                                    width=10,
                                    state='readonly',
                                    value=(
                                        'ascending',
                                        'descending'))
        self.sortCbx.grid(
            row=0, column=2, sticky='sne', padx=5, pady=7)
        reset_filters = tk.Button(self, text='reset filters',
                                  command=self.reset_filters,
                                  width=10)
        reset_filters.grid(
            row=0, column=7, sticky='snw', padx=5, pady=2)
        tk.Label(self, text='filter by',
                 font=LBL_FONT).grid(
            row=0, column=3, sticky='snw', padx=5, pady=2)
        tk.Label(self, text='selector:').grid(
            row=0, column=4, columnspan=2, sticky='snw', padx=5, pady=2)
        self.selectorCbx = ttk.Combobox(
            self, textvariable=self.selector_filter,
            width=15,
            state='readonly')
        self.selectorCbx.grid(
            row=0, column=6, sticky='snw', padx=5, pady=7)
        tk.Label(self, text='vendor:').grid(
            row=1, column=4, columnspan=2, sticky='snw', padx=5, pady=2)
        self.vendorCbx = ttk.Combobox(
            self, textvariable=self.vendor_filter,
            width=15,
            state='readonly')
        self.vendorCbx.grid(
            row=1, column=6, sticky='snw', padx=5, pady=2)
        tk.Label(self, text='language:').grid(
            row=2, column=4, columnspan=2, sticky='snw', padx=5, pady=5)
        self.langCbx = ttk.Combobox(self, textvariable=self.lang_filter,
                                    width=15,
                                    state='readonly')
        self.langCbx.grid(
            row=2, column=6, sticky='snw', padx=5, pady=5)
        tk.Label(self, text='mat type').grid(
            row=3, column=4, columnspan=2, sticky='snw', padx=5, pady=5)
        self.matTypeCbx = ttk.Combobox(self, textvariable=self.matType_filter,
                                       width=15,
                                       state='readonly')
        self.matTypeCbx.grid(
            row=3, column=6, sticky='snw', padx=5, pady=5)

        tk.Label(self, text='order name', font=LBL_FONT).grid(
            row=5, column=0, sticky='snw', padx=10)
        scrollbar = tk.Scrollbar(self, orient=tk.VERTICAL)
        scrollbar.grid(
            row=6, column=5, sticky='nsw', rowspan=10, padx=2, pady=10)
        self.orderLst = tk.Listbox(self, font=REG_FONT,
                                   yscrollcommand=scrollbar.set)
        self.orderLst.bind('<Double-Button-1>', self.on_load)
        self.orderLst.bind('<Button-1>', self.dynamic_details)
        self.orderLst.grid(
            row=6, column=0, columnspan=5, sticky='snew', rowspan=10,
            pady=10)
        scrollbar['command'] = self.orderLst.yview

        # right panel
        tk.Button(self, text='load', font=BTN_FONT,
                  width=15,
                  command=self.on_load).grid(
            row=6, column=6, sticky='sne', padx=10, pady=5)
        self.orderDetailsTxt = tk.Text(
            self,
            font=REG_FONT,
            state=tk.DISABLED,
            background='SystemButtonFace',
            borderwidth=0)
        self.orderDetailsTxt.grid(
            row=6, column=7, rowspan=10, sticky='ne', padx=10, pady=5)
        tk.Button(self, text='edit', font=BTN_FONT,
                  width=15,
                  command=self.on_edit).grid(
            row=7, column=6, sticky='sne', padx=10, pady=5)
        tk.Button(self, text='delete', font=BTN_FONT,
                  width=15,
                  command=self.on_delete).grid(
            row=8, column=6, sticky='sne', padx=10, pady=5)
        tk.Button(self, text='create MARC', font=BTN_FONT,
                  width=15,
                  command=self.createMARC).grid(
            row=10, column=6, sticky='sne', padx=10, pady=5)
        tk.Button(self, text='add Sierra IDs', font=BTN_FONT,
                  width=15,
                  command=self.addIDs).grid(
            row=11, column=6, sticky='sne', padx=10, pady=5)
        tk.Button(self, text='create order', font=BTN_FONT,
                  width=15,
                  command=self.createOrder).grid(
            row=12, column=6, sticky='sne', padx=10, pady=5)
        tk.Button(self, text='cancel', font=BTN_FONT,
                  width=15,
                  command=self.on_cancel).grid(
            row=14, column=6, sticky='sne', padx=10, pady=5)

    def on_load(self, *args):
        try:
            cur_manager.busy()
            if self.library_id.get() == 0:
                m = 'please select library'
                tkMessageBox.showwarning('Input error', m)
            else:
                self.orderName.set(self.orderLst.get(tk.ANCHOR))
                order_record = db.retrieve_record(
                    db.Order,
                    library_id=self.library_id.get(),
                    name=self.orderName.get())
                self.orderId = order_record.id
                self.blanketPO = order_record.blanketPO
                date = order_record.date
                blanketPO = order_record.blanketPO

                # date = date[:4] + '-' + date[4:6] + '-' + date[6:8] + '-' + \
                #     date[8:10] + ':' + date[10:12] + '.' + date[12:]

                record = db.retrieve_record(
                    db.Lang,
                    id=order_record.lang_id)
                lang = record.name
                record = db.retrieve_record(
                    db.Vendor,
                    id=order_record.vendor_id)
                self.vendor = record.name
                record = db.retrieve_record(
                    db.MatType,
                    id=order_record.matType_id)
                matType = record.name
                wlo_range = order_record.wlo_range

                # find totals
                total_titles = db.count_all(
                    db.OrderSingle,
                    order_id=order_record.id)
                total_qty = 0
                self.records = db.retrieve_all(
                    db.OrderSingle,
                    'orderSingleLocations',
                    order_id=order_record.id)
                total_cost = 0.0
                linked_o = 0
                linked_b = 0
                funds_used = {}
                for singleOrder_record in self.records:
                    if singleOrder_record.oNumber is not None:
                        linked_o += 1
                    if singleOrder_record.bNumber is not None:
                        linked_b += 1
                    for related_record in singleOrder_record.orderSingleLocations:
                        total_cost = total_cost + (
                            related_record.qty * singleOrder_record.priceDisc)
                        total_qty = total_qty + related_record.qty

                        fund_id = related_record.fund_id
                        if fund_id in funds_used:
                            funds_used[fund_id] = funds_used[fund_id] + (
                                related_record.qty * singleOrder_record.priceDisc)
                        else:
                            funds_used[fund_id] = related_record.qty * singleOrder_record.priceDisc
                total_cost = cents2dollars(total_cost)

                if total_titles == linked_o and total_titles == linked_b:
                    linked_to_Sierra = 'Yes. All orders linked to Sierra records'
                else:
                    linked_to_Sierra = '\t%s o. numbers\n' \
                                       '\t%s b. numbers\n' \
                                       '\tare linked (out of %s total titles)' % (
                        linked_o, linked_b, total_titles)

                f = ''
                for fund_id in funds_used:
                    fund_record = db.retrieve_record(
                        db.Fund,
                        id=fund_id)
                    f = f + 'fund %s=$%s\n' % (fund_record.code,
                                               cents2dollars(funds_used[fund_id]))

                details = 'date loaded: %s\n' \
                          'language: %s\n' \
                          'vendor: %s\n' \
                          'material type: %s\n' \
                          'blanket PO: %s\n' \
                          'wlo number range: %s\n' \
                          '----------------\n' \
                          'total titles: %s\n' \
                          'total copies: %s\n' \
                          'total cost: %s\n' \
                          '---------------\n' % (
                              date, lang, self.vendor, matType, blanketPO,
                              wlo_range, total_titles, total_qty, total_cost)

                details = details + f + \
                          '---------------\n'
                linked = 'linked to Sierra numbers?:\n' \
                          '%s' % linked_to_Sierra
                details = details + linked

                # update display
                self.orderDetailsTxt['state'] = tk.NORMAL
                self.orderDetailsTxt.delete(1.0, tk.END)
                self.orderDetailsTxt.insert(tk.END, details)
                self.orderDetailsTxt['state'] = tk.DISABLED

                cur_manager.notbusy()
        except Exception as e:
            cur_manager.notbusy()
            m = 'not able to retrieve orders\n' \
                'from the database\nerror: %s' % e
            tkMessageBox.showerror('database error', m)

    def on_delete(self):
        try:
            cur_manager.busy()
            order_for_del = self.orderLst.get(tk.ANCHOR)
            if order_for_del != '':
                if tkMessageBox.askokcancel('Deletion', 'delete order?'):
                    self.orderLst.delete(tk.ANCHOR)
                    db.delete_record(
                        db.Order,
                        name=order_for_del)
            else:
                m = 'Please select order for deletion'
                tkMessageBox.showwarning('Deletion', m)
            self.orderDetailsTxt['state'] = tk.NORMAL
            self.orderDetailsTxt.delete(1.0, tk.END)
            self.orderDetailsTxt['state'] = tk.DISABLED
            cur_manager.notbusy()

        except:
            cur_manager.notbusy()
            m = 'not able to retrieve orders\n' \
                'from the database'
            tkMessageBox.showerror('database error', m)

    def on_edit(self):
        self.action.set('edit')
        self.selectedOrder.set(self.orderLst.get(tk.ANCHOR))
        self.selectedLibrary_id.set(self.library_id.get())
        self.controller.show_frame('OrderEdit')

    def createMARC(self):
        if self.orderId == 0:
            m = 'please select & load order'
            tkMessageBox.showwarning('Input error', m)
        else:
            try:
                cur_manager.busy()
                MARCGenerator(self.orderId)
                # add here file name & number of records
                tkMessageBox.showinfo(
                    'Output info', 'MARC file has been created')
                cur_manager.notbusy()
            except:
                cur_manager.notbusy()
                main_logger.exception('MARC file error:')
                tkMessageBox.showerror(
                    'Output error', 'not able to create MARC file')

    def addIDs(self):
        if self.orderId == 0:
            m = 'please select & load order'
            tkMessageBox.showwarning('Input error', m)
        else:
            # retrieve last used directory
            user_data = shelve.open('user_data')
            if 'sierra_ids_dir' in user_data:
                sierra_ids_dir = user_data['sierra_ids_dir']
            else:
                # ask instead to set default folder or in documents
                sierra_ids_dir = ''
            user_data.close()
            fh = tkFileDialog.askopenfilename(initialdir=sierra_ids_dir)
            if fh:
                try:
                    cur_manager.busy()
                    # record directory
                    n = fh.rfind('/')
                    sierra_ids_dir = fh[:n + 1]
                    # user_data['sierra_ids_dir'] = sierra_ids_dir
                    # validate if correct file type
                    if fh.rfind('.txt') == -1:
                        msg = 'Wrong type of file.\n' \
                              'Only text files with extention .txt are permitted'
                        tkMessageBox.showwarning('File type error', msg)
                    else:
                        # add some validation for correct results
                        ids = text_parser(fh)
                        for id in ids:
                            record = db.retrieve_record(
                                db.OrderSingle,
                                wlo_id=id[0])
                            if record is not None:
                                db.update_record(
                                    db.OrderSingle,
                                    id=record.id,
                                    oNumber=id[1],
                                    bNumber=id[2])
                        tkMessageBox.showinfo(
                            'Output message',
                            'numbers added to local database')
                    cur_manager.notbusy()
                except:
                    cur_manager.notbusy()
                    m = 'not able to match orders\n' \
                        'to Sierra IDs in the database'
                    tkMessageBox.showerror('database error', m)

    def createOrder(self):
        if self.orderId == 0:
            m = 'please select & load order'
            tkMessageBox.showwarning('Input error', m)
        else:
            if self.library_id.get() == 1:
                library = 'Brooklyn Public Library'
            elif self.library_id.get() == 2:
                library = 'New York Public Library'
            else:
                library = 'Library not identified'
            user_data = shelve.open('user_data')
            if 'order_dir' in user_data:
                order_dir = user_data['order_dir']
            else:
                # ask instead to set default folder or in documents
                order_dir = ''
            user_data.close()
            fname = self.vendor
            file_date = datetime.datetime.strftime(
                datetime.date.today(), '%y%m%d')
            fname = fname + '-' + file_date
            fh = order_dir + fname
            try:
                cur_manager.busy()
                data_set = []

                for singleOrder in self.records:
                    data = []
                    bib = db.retrieve_record(
                        db.BibRec,
                        id=singleOrder.bibRec_id)
                    data.append(bib.venNo)
                    data.append(bib.isbn)
                    data.append(bib.title)
                    data.append(bib.author)
                    total_cost = 0
                    total_qty = 0
                    for related_record in singleOrder.orderSingleLocations:
                        total_cost = total_cost + (
                            related_record.qty * singleOrder.priceDisc)
                        total_qty = total_qty + related_record.qty
                    total_cost = cents2dollars(total_cost)
                    data.append(cents2dollars(singleOrder.priceDisc))
                    data.append(total_qty)
                    data.append(total_cost)
                    data.append(singleOrder.oNumber)
                    data.append(self.blanketPO)
                    data_set.append(data)
                cur_manager.notbusy()
            except:
                cur_manager.notbusy()
                main_logger.exception('DB read error:')
                m = 'not able to retrieve orders\n' \
                    'from the database'
                tkMessageBox.showerror('database error', m)

            try:
                cur_manager.busy()
                res = sh.create_order(fh, library, data_set)
                cur_manager.notbusy()
            except:
                cur_manager.notbusy()
                res = None
                main_logger.exception('Order creation error:')

            if res is not None:
                # add here file name & number of records
                tkMessageBox.showinfo(
                    'Output info',
                    '%s \norder sheet has been created' % res)
            else:
                tkMessageBox.showerror(
                    'Output error',
                    'there was a problem in creating order sheet')

    def on_cancel(self):
        self.reset_values()
        self.controller.show_frame('Main')

    def dynamic_orders(self, *args):

        self.dynamic_details()
        self.orderLst.delete(0, tk.END)

        if self.selector_filter.get() not in ('all', ''):
            self.selector_id = self.selector_by_name[
                self.selector_filter.get()]
        else:
            self.selector_id = None
        if self.vendor_filter.get() not in ('all', ''):
            self.vendor_id = self.vendor_by_name[
                self.vendor_filter.get()]
        else:
            self.vendor_id = None
        if self.lang_filter.get() not in ('all', ''):
            self.lang_id = self.lang_by_name[
                self.lang_filter.get()]
        else:
            self.lang_id = None
        if self.matType_filter.get() not in ('all', ''):
            self.matType_id = self.matType_by_name[
                self.matType_filter.get()]
        else:
            self.matType_id = None

        filters = {
            'library_id': self.library_id.get(),
            'selector_id': self.selector_id,
            'vendor_id': self.vendor_id,
            'lang_id': self.lang_id,
            'matType_id': self.matType_id}

        kwargs = {}
        for key, value in filters.iteritems():
            if value is not None:
                kwargs[key] = value
        # print kwargs

        if self.date_sort.get() == 'descending':
            records = db.col_preview_date_desc(
                db.Order,
                'name',
                **kwargs)
        else:
            records = db.col_preview(
                db.Order,
                'date', 'name',
                **kwargs)

        for record in records:
            self.orderLst.insert(tk.END, record.name)

    def dynamic_details(self, *args):
        self.orderId = 0
        self.orderName.set('')
        self.orderDetailsTxt['state'] = tk.NORMAL
        self.orderDetailsTxt.delete(1.0, tk.END)
        self.orderDetailsTxt['state'] = tk.DISABLED

    def reset_values(self):
        # self.library_id.set(0)
        self.orderId = 0
        self.orderName.set('')
        self.orderDetailsTxt['state'] = tk.NORMAL
        self.orderDetailsTxt.delete(1.0, tk.END)
        self.orderDetailsTxt['state'] = tk.DISABLED
        self.selector_id = None
        self.vendor_id = None
        self.lang_id = None
        self.matType_id = None

    def reset_filters(self):
        self.vendor_filter.set('all')
        self.lang_filter.set('all')
        self.vendor_filter.set('all')
        self.matType_filter.set('all')
        self.date_sort.set('descending')
        user_data = shelve.open('user_data')
        if 'last_selector' in user_data:
            self.selector_filter.set(user_data['last_selector'])
            self.selector_id = self.selector_by_name[
                user_data['last_selector']]
        else:
            self.selector_filter.set('all')
        user_data.close()

    def observer(self, *args):
        if self.tier.get() == 'OrderBrowse':
            self.reset_values()

            # create list of selectors and id index
            self.selector_by_name = {}
            self.selector_choices = ()
            selector_records = db.col_preview(
                db.Selector,
                'id',
                'name')
            for selector in selector_records:
                self.selector_choices = self.selector_choices + (
                    selector.name, )
                self.selector_by_name[selector.name] = selector.id
            self.selector_choices += ('all', )
            self.selectorCbx['value'] = sorted(self.selector_choices)

            # create list of vendors and their id index
            self.vendor_by_name = {}
            self.vendor_choices = ()
            vendor_records = db.col_preview(
                db.Vendor,
                'id', 'name')
            for vendor in vendor_records:
                self.vendor_choices += (vendor.name, )
                self.vendor_by_name[vendor.name] = vendor.id
            self.vendor_choices += ('all', )
            self.vendorCbx['value'] = sorted(self.vendor_choices)

            # create list of languages and their ids
            self.lang_choices = ()
            self.lang_by_name = {}
            lang_records = db.col_preview(
                db.Lang,
                'name', 'id')
            for lang in lang_records:
                self.lang_choices += (lang.name, )
                self.lang_by_name[lang.name] = lang.id
            self.lang_choices += ('all', )
            self.langCbx['value'] = sorted(self.lang_choices)

            # create list of material types and their ids
            self.matType_choices = ()
            self.matType_by_name = {}
            matType_records = db.col_preview(
                db.MatType,
                'name', 'id')
            for matType in matType_records:
                self.matType_choices += (matType.name, )
                self.matType_by_name[matType.name] = matType.id
            self.matType_choices += ('all', )
            self.matTypeCbx['value'] = sorted(self.matType_choices)

            # set default values
            user_data = shelve.open('user_data')
            if 'last_selector' in user_data:
                self.selector_filter.set(user_data['last_selector'])
                self.selector_id = self.selector_by_name[
                    user_data['last_selector']]
            else:
                self.selector_filter.set('all')
            user_data.close()
            self.date_sort.set('descending')
            self.vendor_filter.set('all')
            self.matType_filter.set('all')
            self.lang_filter.set('all')


class OrderEdit(tk.Frame):

    def __init__(self, parent, controller, **sharedData):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        # bind shared variables
        self.tier = sharedData['tier']
        self.tier.trace('w', self.observer)
        self.action = sharedData['action']
        self.selectedOrder = sharedData['selectedItem_1']
        self.selectedLibrary_id = sharedData['selectedItem_3']

        # bind local variables
        self.orderName = tk.StringVar()
        self.orderDetails = tk.StringVar()
        self.orderSingle_id = tk.IntVar()
        self.library = tk.StringVar()
        self.titleQty = tk.StringVar()
        self.copiesQty = tk.StringVar()
        self.fundsDetails = tk.StringVar()
        self.lang = tk.StringVar()
        self.vendor = tk.StringVar()
        self.matType = tk.StringVar()
        self.entry_id = tk.StringVar()
        self.entry_id.trace('w', self.deactivate)
        self.previous_entry_id = ''
        # self.active_widget = ''
        self.snapshot = ''

        # configure layout
        self.columnconfigure(0, minsize=10)
        self.columnconfigure(4, minsize=380)
        self.columnconfigure(8, minsize=750)
        self.rowconfigure(1, weight=1, minsize=10)
        self.rowconfigure(10, weight=5, minsize=500)
        self.rowconfigure(13, weight=1, minsize=10)

        # initiate widgets

        # display order metadata
        self.metaFrm = ttk.LabelFrame(self, borderwidth=5)
        self.metaFrm.grid(
            row=0, column=0, columnspan=10, sticky='snw', padx=10)
        self.metaFrm.columnconfigure(2, minsize=50)
        tk.Label(self.metaFrm, textvariable=self.library, font=HDG_FONT).grid(
            row=0, column=0, columnspan=2, sticky='snw', padx=10, pady=2)
        tk.Label(self.metaFrm, textvariable=self.orderName,
                 font=LBL_FONT).grid(
            row=0, column=2, columnspan=4, sticky='snw', padx=10, pady=2)
        tk.Label(self.metaFrm, textvariable=self.titleQty, font=HDG_FONT).grid(
            row=0, column=6, sticky='snw', padx=10, pady=2)
        tk.Label(self.metaFrm, textvariable=self.copiesQty,
                 font=HDG_FONT).grid(
            row=0, column=7, sticky='snw', padx=10, pady=2)
        tk.Label(self.metaFrm, textvariable=self.fundsDetails,
                 font=HDG_FONT).grid(
            row=0, column=8, columnspan=2, sticky='snw', padx=10, pady=2)
        tk.Label(self.metaFrm, textvariable=self.vendor, font=HDG_FONT).grid(
            row=1, column=0, columnspan=4, sticky='snw', padx=10, pady=2)
        tk.Label(self.metaFrm, textvariable=self.lang, font=HDG_FONT).grid(
            row=1, column=4, sticky='snw', padx=10, pady=2)
        tk.Label(self.metaFrm, textvariable=self.matType, font=HDG_FONT).grid(
            row=1, column=5, columnspan=2, sticky='snw', padx=10, pady=2)

        self.yscrollbar = tk.Scrollbar(self, orient=tk.VERTICAL)
        self.yscrollbar.grid(
            row=2, column=0, rowspan=10, sticky='nse', padx=2)
        self.base = tk.Canvas(
            self, bg='gray',
            yscrollcommand=self.yscrollbar.set)
        self.base.grid(
            row=2, column=1, columnspan=10, rowspan=10, sticky='snew', padx=5)
        self.display_frame()

        # back button
        tk.Button(self, text='back', font=REG_FONT,
                  width=10,
                  command=self.go_back).grid(
            row=13, column=1, padx=10, pady=10)

    def display_frame(self):
        self.dispFrame = tk.Frame(
            self.base)
        # self.xscrollbar.config(command=self.base.xview)
        self.yscrollbar.config(command=self.base.yview)
        self.base.create_window(
            (0, 0), window=self.dispFrame, anchor="nw",
            tags="self.dispFrame")
        self.dispFrame.bind("<Configure>", self.onFrameConfigure)

    def onFrameConfigure(self, event):
        self.base.config(scrollregion=self.base.bbox('all'))

    def display_orders(self, data):
        self.entries = {}
        r = 0
        for item in data:
            # create frame for display of an entry
            entryFrm = ttk.LabelFrame(self.dispFrame)
            entryFrm.grid(
                row=r, column=0, columnspan=10, sticky='snew', padx=2)
            # configure column size
            entryFrm.columnconfigure(2, minsize=290)
            entryFrm.columnconfigure(3, minsize=200)
            entryFrm.rowconfigure(3, minsize=15)

            # create radiobutton that will activate entry for editing
            selectBtn = ttk.Radiobutton(entryFrm, variable=self.entry_id,
                                        value=None,
                                        command=self.edit_entry)
            selectBtn.grid(
                row=0, column=0, rowspan=3, sticky='snw', padx=10, pady=10)
            selectBtn['value'] = selectBtn.winfo_parent()

            # display data and record widgets ids
            tk.Label(entryFrm, text='title:', font=REG_FONT).grid(
                row=0, column=1, columnspan=2, sticky='sw', padx=2)
            tk.Label(entryFrm, text='author:', font=REG_FONT).grid(
                row=0, column=3, sticky='sw', padx=2)
            tk.Label(entryFrm, text='ISBN:', font=REG_FONT).grid(
                row=0, column=4, sticky='sw', padx=2)
            tk.Label(entryFrm, text='vendor #:', font=REG_FONT).grid(
                row=0, column=5, sticky='sw', padx=2)
            tk.Label(entryFrm, text='publisher:', font=REG_FONT).grid(
                row=0, column=6, sticky='sw', padx=2)
            tk.Label(entryFrm, text='date:', font=REG_FONT).grid(
                row=0, column=7, sticky='sw', padx=2)
            tk.Label(entryFrm, text='place:', font=REG_FONT).grid(
                row=0, column=8, sticky='sw', padx=2)
            tk.Label(entryFrm, text='est. price:', font=REG_FONT).grid(
                row=0, column=9, sticky='sw', padx=2)

            # register entry widgets
            title = ttk.Entry(entryFrm, font=REG_FONT)
            title.grid(
                row=1, column=1, columnspan=2, sticky='new', padx=5)
            if item['title'] is not None:
                title.insert(0, item['title'])
            title['state'] = tk.DISABLED

            author = ttk.Entry(entryFrm, font=REG_FONT)
            author.grid(
                row=1, column=3, sticky='new', padx=5)
            if item['author'] is not None:
                author.insert(0, item['author'])
            author['state'] = tk.DISABLED

            isbn = ttk.Entry(entryFrm, font=REG_FONT, width=15)
            isbn.grid(
                row=1, column=4, sticky='new', padx=2)
            if item['isbn'] is not None:
                isbn.insert(0, item['isbn'])
            isbn['state'] = tk.DISABLED

            venNo = ttk.Entry(entryFrm, font=REG_FONT, width=7)
            venNo.grid(
                row=1, column=5, sticky='new', padx=2)
            if item['venNo'] is not None:
                venNo.insert(0, item['venNo'])
            venNo['state'] = tk.DISABLED

            publisher = ttk.Entry(entryFrm, font=REG_FONT, width=15)
            publisher.grid(
                row=1, column=6, sticky='new', padx=5)
            if item['publisher'] is not None:
                publisher.insert(0, item['publisher'])
            publisher['state'] = tk.DISABLED

            date = ttk.Entry(entryFrm, font=REG_FONT, width=7)
            date.grid(
                row=1, column=7, sticky='new', padx=5)
            if item['date'] is not None:
                date.insert(0, item['date'])
            date['state'] = tk.DISABLED

            place = ttk.Entry(entryFrm, font=REG_FONT, width=15)
            place.grid(
                row=1, column=8, sticky='new', padx=5)
            if item['place'] is not None:
                place.insert(0, item['place'])
            place['state'] = tk.DISABLED

            price = ttk.Entry(entryFrm, font=REG_FONT, width=7)
            price.grid(
                row=1, column=9, sticky='new', padx=5)
            if item['price'] is not None:
                price.insert(0, cents2dollars(item['price']))
            price['state'] = tk.DISABLED

            # transliteration data
            tk.Label(entryFrm, text='=', font=REG_FONT).grid(
                row=2, column=1, sticky='new', padx=5)
            title_trans = ttk.Entry(entryFrm, font=REG_FONT)
            title_trans.grid(
                row=2, column=2, sticky='new', padx=5)
            if item['title_trans'] is not None:
                title_trans.insert(0, item['title_trans'])
            title_trans['state'] = tk.DISABLED

            author_trans = ttk.Entry(entryFrm, font=REG_FONT)
            author_trans.grid(
                row=2, column=3, sticky='new', padx=5)
            if item['author_trans'] is not None:
                author_trans.insert(0, item['author_trans'])
            author_trans['state'] = tk.DISABLED

            tk.Label(entryFrm, text='PO per line:', font=REG_FONT).grid(
                row=3, column=1, columnspan=2, sticky='nw', padx=5)
            po_per_line = ttk.Entry(entryFrm, font=REG_FONT,
                                    width=30)
            po_per_line.grid(
                row=3, column=2, sticky='ne', padx=5)
            if item['po_per_line'] is not None:
                po_per_line.insert(0, item['po_per_line'])
            po_per_line['state'] = tk.DISABLED

            tk.Label(entryFrm, text='audience:', font=REG_FONT).grid(
                row=3, column=3, sticky='nw', padx=5)
            audn = ttk.Combobox(entryFrm,
                                width=3,
                                values=self.audn_values,
                                state='readonly')
            audn.grid(
                row=3, column=3, sticky='ne', padx=5)
            if item['audn'] is not None:
                audn.set(item['audn'])
            audn['state'] = tk.DISABLED

            self.idsFrm = ttk.LabelFrame(entryFrm, text='Sierra IDs',
                                         padding=2)

            self.idsFrm.grid(
                row=2, column=4, columnspan=3, sticky='new', padx=5)
            oNumber = ttk.Entry(self.idsFrm, font=REG_FONT,
                                width=10)
            oNumber.grid(
                row=2, column=5, sticky='new', padx=5)
            if item['oNumber'] is not None:
                oNumber.insert(0, item['oNumber'])
            oNumber['state'] = tk.DISABLED

            bNumber = ttk.Entry(self.idsFrm, font=REG_FONT,
                                width=10)
            bNumber.grid(
                row=2, column=7, sticky='new', padx=5)
            if item['bNumber'] is not None:
                bNumber.insert(0, item['bNumber'])
            bNumber['state'] = tk.DISABLED

            wloNumber = ttk.Entry(self.idsFrm, font=REG_FONT,
                                  width=15)
            wloNumber.grid(
                row=2, column=8, sticky='new', padx=5)
            if item['wloNumber'] is not None:
                wloNumber.insert(0, item['wloNumber'])
            wloNumber['state'] = tk.DISABLED

            # distribution data
            self.distrFrm = ttk.LabelFrame(entryFrm,
                                           text='location/qty/fund',
                                           padding=4)
            self.distrFrm.grid(
                row=3, column=4, columnspan=4, rowspan=2,
                sticky='snew', padx=5)
            dr = 0
            distr = {}
            for code in item['distr']:
                location = ttk.Combobox(self.distrFrm, font=REG_FONT,
                                        width=10,
                                        values=self.location_values,
                                        state='readonly')
                location.grid(
                    row=dr, column=0, sticky='new', padx=5, pady=2)
                if code['location'] is not None:
                    location.set(code['location'])
                location['state'] = tk.DISABLED

                qty = ttk.Entry(self.distrFrm, font=REG_FONT,
                                width=5)
                qty.grid(
                    row=dr, column=1, sticky='new', padx=5, pady=2)
                if code['qty'] is not None:
                    qty.insert(0, code['qty'])
                qty['state'] = tk.DISABLED

                fund = ttk.Combobox(self.distrFrm, font=REG_FONT,
                                    width=10,
                                    values=self.fund_values,
                                    state='readonly')
                fund.grid(
                    row=dr, column=2, sticky='new', padx=5, pady=2)
                if code['fund'] is not None:
                    fund.set(code['fund'])
                fund['state'] = tk.DISABLED

                removeBtn = tk.Button(self.distrFrm, text='remove',
                                      font=REG_FONT,
                                      width=10,
                                      height=1)
                removeBtn.grid(row=dr, column=3, sticky='nw', padx=5, pady=2)
                removeBtn['command'] = lambda n=str(removeBtn): self.delete_distr(n)
                removeBtn['state'] = tk.DISABLED

                distr[str(removeBtn)] = {'distr_id': code['id'],
                                         'location': location,
                                         'qty': qty,
                                         'fund': fund,
                                         'removeBtn': removeBtn}

                dr += 1
            add_locationBtn = tk.Button(entryFrm, text='add location',
                                        font=REG_FONT,
                                        command=self.add_location)
            add_locationBtn.grid(row=3, column=8, sticky='nw', padx=10, pady=5)
            add_locationBtn['state'] = tk.DISABLED

            # display buttons and record their entry assigment
            saveBtn = tk.Button(entryFrm, text='save', font=REG_FONT,
                                width=10,
                                state=tk.DISABLED,
                                command=self.save_entry)
            saveBtn.grid(
                row=1, column=13, padx=5, pady=5)
            # saveBtn_pathname = saveBtn.winfo_id()
            deleteBtn = tk.Button(entryFrm, text='delete', font=REG_FONT,
                                  width=10,
                                  state=tk.DISABLED,
                                  command=self.delete_entry)
            deleteBtn.grid(
                row=2, column=13, padx=5, pady=5)

            self.entries[str(
                selectBtn.winfo_parent())] = {
                    'frame': entryFrm,
                    'title': title,
                    'title_trans': title_trans,
                    'author': author,
                    'author_trans': author_trans,
                    'isbn': isbn,
                    'venNo': venNo,
                    'publisher': publisher,
                    'place': place,
                    'date': date,
                    'price': price,
                    'audn': audn,
                    'po_per_line': po_per_line,
                    'oNumber': oNumber,
                    'bNumber': bNumber,
                    'wloNumber': wloNumber,
                    'distrFrm': self.distrFrm,
                    'distr': distr,
                    'addLocBtn': add_locationBtn,
                    'saveBtn': saveBtn,
                    'deleteBtn': deleteBtn,
                    'bib_id': item['bib_id'],
                    'ordSingle_id': item['ordSingle_id']}
            r += 1

    def take_snapshot(self, entry_id=None):
        snapshot = ''
        if entry_id is None:
            entry_id = self.entry_id.get()
        entry = self.entries[entry_id]

        # take a snapshot of distribution data
        for distr_widgets in entry['distr'].itervalues():
            # need to verify that disabled widgets can be read!
            snapshot += str(distr_widgets['location'].current())
            snapshot += distr_widgets['qty'].get()
            snapshot += str(distr_widgets['fund'].current())

        # tak a snapshot of bib and order data
        for key in entry:
            if key == 'bib_id' or key == 'ordSingle_id' or key == 'distr':
                pass
            elif key == 'frame' or key == 'distrFrm':
                pass
            elif key == 'audn':
                snapshot += str(entry[key].current())
            else:
                if entry[key].winfo_class() != 'Button':
                    snapshot += unicode(entry[key].get())
        return snapshot

    def edit_entry(self):
        # activate all widgets and take a snapshot their content
        self.snapshot = ''
        active_entry = self.entries[self.entry_id.get()]

        for key in active_entry:
            if key == 'distr':
                for widget_row in active_entry['distr'].itervalues():
                    for widget_key in widget_row:
                        if widget_key == 'distr_id':
                            pass
                        elif widget_key == 'location' or widget_key == 'fund':
                            widget_row[widget_key].state(
                                ['!disabled', 'readonly'])
                        else:
                            widget_row[widget_key]['state'] = tk.NORMAL
            elif key == 'bib_id' or key == 'ordSingle_id':
                pass
            elif key == 'frame' or key == 'distrFrm':
                pass
            elif key == 'audn':
                active_entry[key].state(['!disabled', 'readonly'])
            else:
                active_entry[key]['state'] = tk.NORMAL
        self.snapshot = self.take_snapshot()

    def save_entry(self, entry_id=None):
        errors = False
        if entry_id is None:
            entry_id = self.entry_id.get()
        active_entry = self.entries[entry_id]
        updated_bib = {
            'bib_id': active_entry['bib_id'],
            'title': active_entry['title'].get(),
            'title_trans': active_entry['title_trans'].get(),
            'author': active_entry['author'].get(),
            'author_trans': active_entry['author_trans'].get(),
            'isbn': active_entry['isbn'].get(),
            'venNo': active_entry['venNo'].get(),
            'publisher': active_entry['publisher'].get(),
            'place': active_entry['place'].get(),
            'date': active_entry['date'].get()
        }
        eval_result = validation.bib_validation(updated_bib)
        error = eval_result[0]
        updated_bib = eval_result[1]

        if error is None:
            # positive eval
            updated_bib = eval_result[1]
            db.update_record(
                db.BibRec,
                updated_bib['bib_id'],
                title=updated_bib['title'],
                title_trans=updated_bib['title_trans'],
                author=updated_bib['author'],
                author_trans=updated_bib['author_trans'],
                isbn=updated_bib['isbn'],
                venNo=updated_bib['venNo'],
                publisher=updated_bib['publisher'],
                pubPlace=updated_bib['place'],
                pubDate=updated_bib['date'])
        else:
            m = error
            tkMessageBox.showerror('Input error', m)
            errors = True

        price = dollars2cents(float(active_entry['price'].get().strip()))
        audn_rec = db.retrieve_record(
            db.Audn,
            code=active_entry['audn'].get())
        audn_id = audn_rec.id

        updated_ord = {
            'ordSingle_id': active_entry['ordSingle_id'],
            'oNumber': active_entry['oNumber'].get().strip(),
            'bNumber': active_entry['bNumber'].get().strip(),
            'price': price,
            'audn_id': audn_id,
            'po_per_line': active_entry['po_per_line'].get().strip()
        }

        db.update_record(
            db.OrderSingle,
            updated_ord['ordSingle_id'],
            oNumber=updated_ord['oNumber'],
            bNumber=updated_ord['bNumber'],
            priceDisc=updated_ord['price'],
            audn_id=updated_ord['audn_id'],
            po_per_line=updated_ord['po_per_line'])

        empty = []
        to_be_deleted = []
        complete = True
        for distr_key in active_entry['distr'].iterkeys():
            distr_unit = active_entry['distr'][distr_key]
            distr_unit_data = {'distr_id': distr_unit['distr_id'],
                               'location': distr_unit['location'].current(),
                               'fund': distr_unit['fund'].current(),
                               'qty': distr_unit['qty'].get()}
            eval_result = validation.eval_distr_unit(distr_unit_data)

            if eval_result[0] and eval_result[1] is None:
                # print 'empty'
                empty.append(distr_key)
            elif not eval_result[0] and eval_result[1] is None:
                # delete distr which values has been removed
                # print 'for deletion'
                to_be_deleted.append((distr_key, distr_unit_data['distr_id']))
            elif not eval_result[1] or not eval_result[2]:
                # stop saving if incomplete data
                # print 'incomplete'
                complete = False

        for empty_distr_id in empty:
            active_entry['distr'][empty_distr_id]['location'].destroy()
            active_entry['distr'][empty_distr_id]['fund'].destroy()
            active_entry['distr'][empty_distr_id]['qty'].destroy()
            active_entry['distr'][empty_distr_id]['removeBtn'].destroy()
            active_entry['distr'].pop(empty_distr_id, None)

        for empty_distr in to_be_deleted:
            db.delete_record(
                db.OrderSingleLoc,
                id=empty_distr[1])
            active_entry['distr'][empty_distr[0]]['location'].destroy()
            active_entry['distr'][empty_distr[0]]['fund'].destroy()
            active_entry['distr'][empty_distr[0]]['qty'].destroy()
            active_entry['distr'][empty_distr[0]]['removeBtn'].destroy()
            active_entry['distr'].pop(empty_distr[0], None)

        if complete:
            for distr_unit in active_entry['distr'].itervalues():
                location_rec = db.retrieve_record(
                    db.Location,
                    name=distr_unit['location'].get())
                location_id = location_rec.id
                fund_rec = db.retrieve_record(
                    db.Fund,
                    code=distr_unit['fund'].get())
                fund_id = fund_rec.id

                updated_distr = {
                    'id': distr_unit['distr_id'],
                    'location_id': location_id,
                    'qty': int(distr_unit['qty'].get().strip()),
                    'fund_id': fund_id
                }

                if distr_unit['distr_id'] is None:
                    # insert as new
                    result = db.insert_record(
                        db.OrderSingleLoc,
                        orderSingle_id=updated_ord['ordSingle_id'],
                        location_id=updated_distr['location_id'],
                        qty=updated_distr['qty'],
                        fund_id=updated_distr['fund_id'])
                    if result[0] is None:
                        m = 'Something went wrong.\n' \
                            'Not able to save to database.'
                        tkMessageBox.showerro('Database error', m)
                    elif result[0] is False:
                        m = 'Duplicate distribution.\n' \
                            'Plase modify existing if needed instead.\n' \
                            'Distribution ignored.'
                        tkMessageBox.showwarning('Input error', m)
                    elif result[0]:
                        loaded_distr = db.retrieve_last(
                            db.OrderSingleLoc)
                        distr_unit['distr_id'] = loaded_distr.id
                        self.snapshot = self.take_snapshot()

                else:
                    # update existing
                    db.update_record(
                        db.OrderSingleLoc,
                        updated_distr['id'],
                        location_id=updated_distr['location_id'],
                        fund_id=updated_distr['fund_id'],
                        qty=updated_distr['qty'])
                    self.snapshot = self.take_snapshot()
        else:
            m = 'One of the distributions seems incomplete.\n' \
                'Please correct it.'
            tkMessageBox.showwarning('Input error', m)
            errors = True
        if not errors:
            tkMessageBox.showinfo('Info', 'Saved')

    def delete_entry(self):
        confirmation = tkMessageBox.askokcancel('deletion', 'delete entry?')
        if confirmation:
            active_entry = self.entries[self.entry_id.get()]
            orderSingle_id = active_entry['ordSingle_id']
            db.delete_record(
                db.OrderSingle,
                id=orderSingle_id)
            bib_id = active_entry['bib_id']
            bibs_used = db.count_all(
                db.OrderSingle,
                bibRec_id=bib_id)
            if bibs_used == 0:
                db.delete_record(
                    db.BibRec,
                    id=bib_id)
            self.entries.pop(self.entry_id.get(), None)
            active_entry['frame'].destroy()
            self.previous_entry_id = ''
            self.entry_id.set('')

    def add_location(self):
        # rethink and rewrite to get rid of a bug:
        # if rows are removed, tkinter row index for distr widgets gets
        # messed up
        active_entry = self.entries[self.entry_id.get()]
        self.distrFrm = active_entry['distrFrm']
        distr = active_entry['distr']

        # collect used rows numbers in distrFrm to find later the last one
        distr_rows = []
        for item in distr.itervalues():
            distr_rows.append(int(item['removeBtn'].grid_info()['row']))

        location = ttk.Combobox(self.distrFrm, font=REG_FONT,
                                values=self.location_values,
                                width=10,
                                state='readonly')
        location.grid(
            row=max(distr_rows) + 1, column=0, sticky='new', padx=5, pady=2)

        qty = ttk.Entry(self.distrFrm, font=REG_FONT,
                        width=5)
        qty.grid(
            row=max(distr_rows) + 1, column=1, sticky='new', padx=5, pady=2)

        fund = ttk.Combobox(self.distrFrm, font=REG_FONT,
                            width=10,
                            values=self.fund_values,
                            state='readonly')
        fund.grid(
            row=max(distr_rows) + 1, column=2, sticky='new', padx=5, pady=2)

        removeBtn = tk.Button(self.distrFrm, text='remove',
                              font=REG_FONT,
                              width=10,
                              height=1)
        removeBtn.grid(row=max(distr_rows) + 1, column=3, sticky='nw',
                       padx=5, pady=2)
        removeBtn['command'] = lambda n=str(removeBtn): self.delete_distr(n)

        distr[str(removeBtn)] = {'distr_id': None,  # populate on save
                                 'location': location,
                                 'qty': qty,
                                 'fund': fund,
                                 'removeBtn': removeBtn}

    def delete_distr(self, button_id, entry_id=None):
        # includes a bug that needs to be addressed
        # removing location widgets in any other order that from last to first
        #  will mess up rows count and adding a new row may be displayed over
        # existing row
        if entry_id is None:
            entry_id = self.entry_id.get()
        active_entry = self.entries[entry_id]
        distr = active_entry['distr']
        related_widgets = distr[button_id]
        if related_widgets['distr_id'] is not None:
            m = 'delete location?'
            confirmation = tkMessageBox.askokcancel('Removing distribution', m)
            if confirmation:
                db.delete_record(
                    db.OrderSingleLoc,
                    id=related_widgets['distr_id'])
                for key in related_widgets:
                    if key == 'distr_id':
                        pass
                    else:
                        related_widgets[key].destroy()
                # remove from distribution dictionary
                distr.pop(button_id, None)
        else:
            for key in related_widgets:
                if key == 'distr_id':
                    pass
                else:
                    related_widgets[key].destroy()
            # remove from distribution dictionary
            distr.pop(button_id, None)
        # show message if no distribution was left attached
        if len(distr) == 0:
            m = 'last location has been deleted.\n' \
                'An order must have at least one location attached'
            tkMessageBox.showwarning('Input warning', m)
        # trigger new snapshot
        self.snapshot = self.take_snapshot()

    def rollback(self, entry_id):
        entry = self.entries[entry_id]

        # enable editing and delete current input
        for widget in entry.itervalues():
            try:
                if widget.winfo_class() in (
                   'TEntry', 'Button', 'TCombobox'):
                    widget['state'] = tk.NORMAL
                if widget.winfo_class() in ('TEntry', 'TCombobox'):
                    widget.delete(0, tk.END)
            except:
                pass
            if type(widget) is dict:
                for distr_widgets in entry['distr'].itervalues():
                    for widget in distr_widgets.itervalues():
                        if (type(widget) is not int) and (widget is not None):
                            widget['state'] = tk.NORMAL
                            if widget.winfo_class() != 'Button':
                                widget.delete(0, tk.END)

        # retreive bib & order original data from localstore
        bib_rec = db.retrieve_record(
            db.BibRec,
            id=entry['bib_id'])
        ord_rec = db.retrieve_record(
            db.OrderSingle,
            id=entry['ordSingle_id'])
        audn_rec = db.retrieve_record(
            db.Audn,
            id=ord_rec.audn_id)
        price = cents2dollars(ord_rec.priceDisc)

        # populate with database data
        entry['title'].insert(0, bib_rec.title)
        if bib_rec.title_trans is not None:
            entry['title_trans'].insert(0, bib_rec.title_trans)
        if bib_rec.author is not None:
            entry['author'].insert(0, bib_rec.author)
        if bib_rec.author_trans is not None:
            entry['author_trans'].insert(0, bib_rec.author_trans)
        if bib_rec.isbn is not None:
            entry['isbn'].insert(0, bib_rec.isbn)
        if bib_rec.venNo is not None:
            entry['venNo'].insert(0, bib_rec.venNo)
        if bib_rec.publisher is not None:
            entry['publisher'].insert(0, bib_rec.publisher)
        if bib_rec.pubPlace is not None:
            entry['place'].insert(0, bib_rec.pubPlace)
        if bib_rec.pubDate is not None:
            entry['date'].insert(0, bib_rec.pubDate)

        entry['audn'].insert(0, audn_rec.code)
        if entry['po_per_line'] is not None:
            entry['po_per_line'].insert(0, ord_rec.po_per_line)
        if ord_rec.oNumber is not None:
            entry['oNumber'].insert(0, ord_rec.oNumber)
        if ord_rec.bNumber is not None:
            entry['bNumber'].insert(0, ord_rec.bNumber)
        entry['wloNumber'].insert(0, ord_rec.wlo_id)
        entry['price'].insert(0, price)

        # retrieve distr original data from localstore
        # & re-populate distribution widgets
        # remove not committed distr
        for_deletion = []
        for widgets in entry['distr'].itervalues():
            if widgets['distr_id'] is None:
                for_deletion.append(str(widgets['removeBtn']))
        for del_widget in for_deletion:
                self.delete_distr(del_widget, entry_id)

        for widgets in entry['distr'].itervalues():
            distr_rec = db.retrieve_record(
                db.OrderSingleLoc,
                id=widgets['distr_id'])
            location_rec = db.retrieve_record(
                db.Location,
                id=distr_rec.location_id)
            fund_rec = db.retrieve_record(
                db.Fund,
                id=distr_rec.fund_id)
            widgets['location'].set(location_rec.name)
            widgets['location']['state'] = tk.DISABLED
            widgets['qty'].insert(0, distr_rec.qty)
            widgets['qty']['state'] = tk.DISABLED
            widgets['fund'].set(fund_rec.code)
            widgets['fund']['state'] = tk.DISABLED
            widgets['removeBtn']['state'] = tk.DISABLED

        # disable remaining widgets
        for widget in entry.itervalues():
            try:
                if widget.winfo_class() in (
                   'TEntry', 'Button', 'TCombobox'):
                    widget['state'] = tk.DISABLED
            except:
                pass

    def deactivate(self, *args):
        # disable widgets on previous entry and take a snapshot of user input
        self.snapshot_after = ''
        # deactivate widgets and distroy empty ones
        if self.previous_entry_id == '':
            self.previous_entry_id = self.entry_id.get()
        else:
            if self.entry_id.get() != '':
                # deactivate previous entry
                previous_entry = self.entries[self.previous_entry_id]
                # operates on single entry
                for key in previous_entry:
                    if key == 'distr':
                        # find if any empty distribution widgets exist
                        for_deletion = []
                        new_widget_row = []
                        for widget_row in previous_entry['distr'].itervalues():
                            if widget_row['distr_id'] is None:
                                for_deletion.append(
                                    str(widget_row['removeBtn']))
                                for widget_key in ('fund', 'qty', 'location'):
                                    entry_value = widget_row[
                                        widget_key].get().strip()
                                    if entry_value != '':
                                        new_widget_row.append(
                                            str(widget_row['removeBtn']))
                                        break

                        # destroy empty location widgets
                        for widget_id in for_deletion:
                            if widget_id not in new_widget_row:
                                self.delete_distr(
                                    widget_id, self.previous_entry_id)

                        # iterate again to disable widgets and
                        # take a snapshot of the content
                        for widget_row in previous_entry['distr'].itervalues():
                            for widget_key in widget_row:
                                if widget_key == 'distr_id':
                                    pass
                                elif widget_key == 'location' \
                                        or widget_key == 'fund':
                                    widget_row[widget_key].state(['disabled'])
                                else:
                                    widget_row[
                                        widget_key]['state'] = tk.DISABLED
                    elif key == 'bib_id' or key == 'ordSingle_id':
                        pass
                    elif key == 'frame' or key == 'distrFrm':
                        pass
                    elif key == 'audn':
                        previous_entry[key].state(['disabled'])
                    else:
                        previous_entry[key]['state'] = tk.DISABLED
                snapshot_after = self.take_snapshot(self.previous_entry_id)

                # compare snapshots
                if self.snapshot != snapshot_after:
                    m = 'would you like to save your changes?'
                    response = tkMessageBox.askokcancel('info', m)
                    if response:
                        self.save_entry(self.previous_entry_id)
                    else:
                        # rollback to original state
                        self.rollback(self.previous_entry_id)
                self.previous_entry_id = self.entry_id.get()

    def reset_values(self):
        self.entries = {}

    def go_back(self):
        self.reset_values()
        self.orderName.set('')
        self.orderDetails.set('')
        self.orderSingle_id.set(0)
        self.library.set('')
        self.titleQty.set('')
        self.copiesQty.set('')
        self.fundsDetails.set('')
        self.lang.set('')
        self.vendor.set('')
        self.matType.set('')
        self.entry_id.set('')
        self.previous_entry_id = ''
        self.selectedOrder.set('')
        self.order_data = []
        self.entries = {}

        # reset display frame
        self.dispFrame.destroy()
        self.display_frame()

        # reset shared variables
        self.selectedLibrary_id.set('')
        self.action.set('')
        self.tier.set('OrderBrowse')
        self.controller.show_frame('OrderBrowse')

    def observer(self, *args):
        if self.tier.get() == 'OrderEdit':
            self.reset_values()
            start_time = datetime.datetime.now()
            # create controlled list for audn, locations, & funds
            self.audn_values = ()
            self.location_values = ()
            self.fund_values = ()
            audn_codes = db.col_preview(
                db.Audn,
                'code')
            for record in audn_codes:
                self.audn_values = self.audn_values + (record.code, )

            locations = db.col_preview(
                db.Location,
                'name',
                library_id=self.selectedLibrary_id.get())
            for location_record in locations:
                self.location_values = self.location_values + (
                    location_record.name, )

            funds = db.col_preview(
                db.Fund,
                'code',
                library_id=self.selectedLibrary_id.get())
            for fund_record in funds:
                self.fund_values = self.fund_values + (
                    fund_record.code, )
            try:
                cur_manager.busy()
                if self.selectedLibrary_id.get() == 1:
                    self.library.set('BPL')
                elif self.selectedLibrary_id.get() == 2:
                    self.library.set('NYPL')
                self.orderName.set(self.selectedOrder.get())

                # retrieve records and pass to display generator
                # create index binding widget
                order = db.retrieve_record(
                    db.Order,
                    name=self.orderName.get())

                # parse order metadata for display
                lang_record = db.retrieve_record(
                    db.Lang,
                    id=order.lang_id)
                self.lang.set(lang_record.name)
                vendor_record = db.retrieve_record(
                    db.Vendor,
                    id=order.vendor_id)
                if self.selectedLibrary_id.get() == 1:
                    vendor_code = vendor_record.bplCode
                elif self.selectedLibrary_id.get() == 2:
                    vendor_code = vendor_record.nyplCode
                self.vendor.set(
                    vendor_record.name + ' (' + vendor_code + ')')
                matType_record = db.retrieve_record(
                    db.MatType,
                    id=order.matType_id)
                self.matType.set('material type: ' + matType_record.name)
                orderSingle_records = db.retrieve_all(
                    db.OrderSingle,
                    'orderSingleLocations',
                    order_id=order.id)

                # create  objects to be displayed
                self.order_data = []
                for ordSingle_rec in orderSingle_records:
                    audn_rec = db.retrieve_record(
                        db.Audn,
                        id=ordSingle_rec.audn_id)

                    distr = []
                    for distr_rec in ordSingle_rec.orderSingleLocations:
                        # find item code
                        location_rec = db.retrieve_record(
                            db.Location,
                            id=distr_rec.location_id)

                        # find fund code
                        fund_rec = db.retrieve_record(
                            db.Fund,
                            id=distr_rec.fund_id)
                        fund = fund_rec.code
                        # find quantity
                        qty = distr_rec.qty
                        distr_code = {'id': distr_rec.id,
                                      'location': location_rec.name,
                                      'qty': qty,
                                      'fund': fund}
                        distr.append(distr_code)

                    bib = db.retrieve_record(
                        db.BibRec,
                        id=ordSingle_rec.bibRec_id)

                    entry_data = {'bib_id': bib.id,
                                  'ordSingle_id': ordSingle_rec.id,
                                  'title': bib.title,
                                  'title_trans': bib.title_trans,
                                  'author': bib.author,
                                  'author_trans': bib.author_trans,
                                  'isbn': bib.isbn,
                                  'venNo': bib.venNo,
                                  'publisher': bib.publisher,
                                  'date': bib.pubDate,
                                  'place': bib.pubPlace,
                                  'price': ordSingle_rec.priceDisc,
                                  'oNumber': ordSingle_rec.oNumber,
                                  'bNumber': ordSingle_rec.bNumber,
                                  'wloNumber': ordSingle_rec.wlo_id,
                                  'audn': audn_rec.code,
                                  'po_per_line': ordSingle_rec.po_per_line,
                                  'distr': distr}

                    self.order_data.append(entry_data)

                self.display_orders(self.order_data)
                end_time = datetime.datetime.now()
                read_time = end_time - start_time
                read_time = read_time.total_seconds()
                main_logger.info('%s | loading %s order : %s seconds' % (
                    datetime.datetime.now(),
                    self.orderName.get(),
                    read_time))
                cur_manager.notbusy()
            except Exception as e:
                cur_manager.notbusy()
                main_logger.exception(
                    '%s |loading %s order: exception raised:' % (
                        datetime.datetime.now(),
                        self.orderName.get()))
                m = 'not able to retrieve records\n' \
                    'from database\n\n%s' % str(e)
                tkMessageBox.showerror('database error', m)


class Search(tk.Frame):

    """Search widget"""

    def __init__(self, parent, controller, **sharedData):
        tk.Frame.__init__(self, parent)

        # bind shared variables
        self.controller = controller
        self.tier = sharedData['tier']
        self.tier.trace('w', self.observer)

        # register entry validation
        vd = (self.register(self.validate_date), '%d', '%i', '%S')

        # bind local variables
        self.id_type = tk.StringVar()
        self.id_query = tk.StringVar()
        self.title_query = tk.StringVar()
        self.title_query_type = tk.StringVar()
        self.author_query = tk.StringVar()
        self.vendor = tk.StringVar()
        self.date1 = tk.StringVar()
        self.date2 = tk.StringVar()
        self.library = tk.StringVar()
        self.lang = tk.StringVar()
        self.matType = tk.StringVar()
        self.selector = tk.StringVar()

        # search results variables
        self.current_page = tk.IntVar()
        self.total_pages = 0
        self.hits = []
        self.total_hits = 0
        self.summary = tk.StringVar()

        # configure layout
        self.columnconfigure(0, minsize=50)
        self.columnconfigure(2, minsize=50)
        self.rowconfigure(0, minsize=10)
        self.rowconfigure(4, minsize=10)

        # initiate widgets

        # simple search
        self.simpleFrm = ttk.LabelFrame(self, text='simple search')
        self.simpleFrm.grid(
            row=1, column=1, sticky='snew', padx=5, pady=5)
        self.simpleFrm.columnconfigure(0, minsize=10)
        self.simpleFrm.columnconfigure(2, minsize=10)
        self.simpleFrm.columnconfigure(4, minsize=20)
        self.simpleFrm.columnconfigure(6, minsize=10)
        self.simpleFrm.rowconfigure(1, minsize=10)
        self.id_typeCbx = ttk.Combobox(self.simpleFrm,
                                       state='readonly',
                                       textvariable=self.id_type,
                                       width=15,
                                       height=6)
        self.id_typeCbx.grid(
            row=0, column=1, sticky='snw', pady=5)
        self.id_queryEnt = ttk.Entry(self.simpleFrm,
                                     textvariable=self.id_query,
                                     width=25)
        self.id_queryEnt.grid(
            row=0, column=3, sticky='snw', pady=5)
        tk.Button(self.simpleFrm, text='search', font=BTN_FONT,
                  width=15,
                  height=1,
                  command=self.simple_search).grid(
            row=0, column=5, sticky='sew', padx=5, pady=5)

        tk.Label(self, text='OR', font=LBL_FONT).grid(
            row=2, column=1, sticky='snw', padx=5, pady=5)

        # advanced search
        self.advFrm = ttk.LabelFrame(self, text='advanced search')
        self.advFrm.grid(
            row=3, column=1, sticky='snew', padx=5, pady=5)
        self.advFrm.columnconfigure(0, minsize=10)
        # self.advFrm.columnconfigure(5, minsize=10)
        self.advFrm.rowconfigure(3, minsize=10)
        self.advFrm.rowconfigure(10, minsize=10)
        self.advFrm.rowconfigure(11, minsize=10)

        self.title_queryEnt = ttk.Entry(self.advFrm,
                                        textvariable=self.title_query,
                                        width=50)
        self.title_queryEnt.grid(
            row=0, column=1, columnspan=3, sticky='snw', pady=2)
        self.titleTypeCbx = ttk.Combobox(self.advFrm,
                                         state='readonly',
                                         textvariable=self.title_query_type,
                                         values=[
                                             'title keyword',
                                             'title phrase'],
                                         width=12)
        self.titleTypeCbx.grid(
            row=0, column=4, columnspan=2, sticky='sne', pady=2)

        tk.Label(self.advFrm, text='AND', font=LBL_FONT).grid(
            row=0, column=7, columnspan=2, sticky='sne', padx=5, pady=5)
        self.authorEnt = ttk.Entry(self.advFrm,
                                   textvariable=self.author_query,
                                   width=28)
        self.authorEnt.grid(
            row=1, column=1, columnspan=3, sticky='snw', pady=2)
        tk.Label(self.advFrm, text='author', font=LBL_FONT).grid(
            row=1, column=2, sticky='sne', pady=5)
        tk.Label(self.advFrm, text='AND', font=LBL_FONT).grid(
            row=1, column=7, sticky='sne', pady=5)
        self.vendorCbx = ttk.Combobox(self.advFrm,
                                      state='readonly',
                                      textvariable=self.vendor,
                                      width=25)
        self.vendorCbx.grid(
            row=2, column=1, columnspan=3, sticky='snw', pady=2)
        tk.Label(self.advFrm, text='vendor', font=LBL_FONT).grid(
            row=2, column=2, sticky='sne', pady=5)
        tk.Label(self.advFrm, text='limit to:', font=LBL_FONT).grid(
            row=4, column=1, columnspan=4, sticky='snw', pady=5)
        tk.Label(self.advFrm, text='date created between',
                 font=LBL_FONT).grid(
            row=5, column=1, sticky='sne', padx=5, pady=5)
        self.date1Ent = ttk.Entry(self.advFrm,
                                  textvariable=self.date1,
                                  validate='key',
                                  validatecommand=vd,
                                  width=15)
        self.date1Ent.grid(
            row=5, column=2, sticky='snw', pady=2)
        tk.Label(self.advFrm, text='and', font=LBL_FONT).grid(
            row=5, column=3, sticky='snw', padx=5, pady=5)
        self.date2Ent = ttk.Entry(self.advFrm,
                                  validate='key',
                                  validatecommand=vd,
                                  textvariable=self.date2,
                                  width=15)
        self.date2Ent.grid(
            row=5, column=4, sticky='snw', pady=2)
        tk.Label(self.advFrm, text='MM/DD/YYYY', font=LBL_FONT).grid(
            row=6, column=2, sticky='snw', pady=2)
        tk.Label(self.advFrm, text='MM/DD/YYYY', font=LBL_FONT).grid(
            row=6, column=4, sticky='snw', pady=2)
        tk.Label(self.advFrm, text='library', font=LBL_FONT).grid(
            row=7, column=1, sticky='sne', padx=5, pady=5)
        self.libraryCbx = ttk.Combobox(self.advFrm,
                                       state='readonly',
                                       textvariable=self.library,
                                       width=12,
                                       height=2)
        self.libraryCbx.grid(
            row=7, column=2, sticky='snw', pady=2)

        tk.Label(self.advFrm, text='language', font=LBL_FONT).grid(
            row=8, column=1, sticky='sne', padx=5, pady=5)
        self.langCbx = ttk.Combobox(self.advFrm,
                                    state='readonly',
                                    textvariable=self.lang,
                                    width=12,
                                    height=15)
        self.langCbx.grid(
            row=8, column=2, sticky='snw', pady=2)

        tk.Label(self.advFrm, text='material type', font=LBL_FONT).grid(
            row=9, column=1, sticky='sne', padx=5, pady=5)
        self.matTypeCbx = ttk.Combobox(self.advFrm,
                                       state='readonly',
                                       textvariable=self.matType,
                                       width=12)
        self.matTypeCbx.grid(
            row=9, column=2, sticky='snw', pady=2)

        tk.Label(self.advFrm, text='selector', font=LBL_FONT).grid(
            row=10, column=1, sticky='sne', padx=5, pady=5)
        self.selectorCbx = ttk.Combobox(self.advFrm,
                                        state='readonly',
                                        textvariable=self.selector,
                                        width=12)
        self.selectorCbx.grid(
            row=10, column=2, sticky='snw', pady=2)

        tk.Button(self.advFrm, text='search', font=BTN_FONT,
                  command=self.adv_search,
                  width=15,
                  height=1).grid(
            row=12, column=1, sticky='snw', padx=5, pady=5)

        tk.Button(self.advFrm, text='reset', font=BTN_FONT,
                  command=self.reset,
                  width=15,
                  height=1).grid(
            row=12, column=2, sticky='sne', padx=5, pady=5)

    def simple_search(self):
        id_type = self.id_type.get()
        query = self.id_query.get().strip()
        if id_type != '' and query != '':
            cur_manager.busy()
            if id_type == '.o number':
                self.hits = db.id_search(db.OrderSingle.oNumber, query)
            elif id_type == '.b number':
                self.hits = db.id_search(db.OrderSingle.bNumber, query)
            elif id_type == 'wlo number':
                self.hits = db.id_search(db.OrderSingle.wlo_id, query)
            elif id_type == 'ISBN':
                self.hits = db.id_search(db.BibRec.isbn, query)
            elif id_type == 'vendor number':
                self.hits = db.id_search(db.BibRec.venNo, query)
            elif id_type == 'blanket PO':
                self.hits = db.id_search(db.Order.blanketPO, query)

            self.activate_display()
            cur_manager.notbusy()
        else:
            m = 'Please select type of search and enter your query'
            tk.MessageBox.showwarning('Input error', m)

    def adv_search(self):

        if (len(self.title_query.get().strip()) == 0 and
            len(self.author_query.get().strip()) == 0 and
                self.vendor.get() == 'any'):
            # empty search

            m = 'Please enter title or author or select specific vendor'
            tk.MessageBox.showwarning('Input error', m)
        else:
            cur_manager.busy()
            # find critieria babelstore id to be passed to query

            if self.title_query_type.get() == 'title keyword':
                if self.title_query.get().strip() == '':
                    title_query = None
                else:
                    title_query = self.title_query.get().strip().split(' ')
            else:
                if self.title_query.get().strip() == '':
                    title_query = None
                else:
                    title_query = self.title_query.get().strip()

            if self.author_query.get().strip() == '':
                author_query = None
            else:
                author_query = self.author_query.get().strip().split(' ')

            if self.vendor.get() == 'any':
                vendor_id = None
            else:
                vendor_id = self.vendor_by_name[self.vendor.get()]

            if self.library.get() == 'any':
                library_id = None
            else:
                library_id = self.library_by_name[self.library.get()]

            if self.matType.get() == 'any':
                matType_id = None
            else:
                matType_id = self.matType_by_name[self.matType.get()]

            if self.lang.get() == 'any':
                lang_id = None
            else:
                lang_id = self.lang_by_name[self.lang.get()]

            if self.selector.get() == 'any':
                selector_id = None
            else:
                selector_id = self.selector_by_name[self.selector.get()]

            # create datetime object to be passed to query
            if self.date1.get() == '':
                date1 = datetime.datetime.strptime('01/01/1900', '%m/%d/%Y')
            else:
                date1 = datetime.datetime.strptime(
                    self.date1.get(), '%m/%d/%Y')
            if self.date2.get() == '':
                date2 = datetime.datetime.strptime('12/31/3000', '%m/%d/%Y')
            else:
                date2 = datetime.datetime.strptime(
                    self.date2.get(), '%m/%d/%Y')

            self.hits = db.keyword_search(
                title_query,
                self.title_query_type.get(),
                author_query,
                vendor_id,
                date1,
                date2,
                library_id,
                lang_id,
                matType_id,
                selector_id)
            self.activate_display()
            cur_manager.notbusy()

    def result_pagination(self):
        self.total_hits = len(self.hits)
        self.pages = {}
        if self.total_hits <= 100:
            self.pages[1] = self.hits
            p = 1
        else:
            for p in range(1, self.total_hits // 100 + 1):
                self.pages[p] = self.hits[(p - 1) * 100:(p * 100)]
            if self.total_hits % 100 > 0:
                self.pages[p + 1] = self.hits[(p * 100):]
                p += 1
        self.total_pages = p
        self.current_page.set(1)

    def activate_display(self):
        self.result_pagination()

        self.top = tk.Toplevel(self)
        self.top.minsize(width=1000, height=500)
        self.top.title('Search results')
        self.top.columnconfigure(0, minsize=10)
        self.top.columnconfigure(2, minsize=800)
        self.top.rowconfigure(4, minsize=400)
        self.top.columnconfigure(13, minsize=10)
        self.top.rowconfigure(12, minsize=10)

        query = []
        filters = []
        if self.title_query.get() != '':
            query.append('{}("{}")'.format(
                self.title_query_type.get(), self.title_query.get()))
        if self.author_query.get() != '':
            query.append('author("{}")'.format(self.author_query.get()))
        if self.vendor.get() != 'any':
            query.append('vendor("{}")'.format(self.vendor.get()))
        if self.date1.get() != '':
            filters.append('from date("{}")'.format(self.date1.get()))
        if self.date2.get() != '':
            filters.append('to date("{}")'.format(self.date2.get()))
        if self.library.get() != 'any':
            filters.append('library("{}")'.format(self.library.get()))
        if self.lang.get() != 'any':
            filters.append('language("{}")'.format(self.lang.get()))
        if self.matType.get() != 'any':
            filters.append('mat type("{}")'.format(self.matType.get()))
        if self.selector.get() != 'any':
            filters.append('selector("{}")'.format(self.selector.get()))

        query = '&'.join(query)
        filters = '&'.join(filters)

        ttk.Label(self.top, textvariable=self.summary, font=LBL_FONT,
                  justify=tk.LEFT).grid(
            row=0, column=1, columnspan=10, sticky='snw', padx=5, pady=5)
        ttk.Label(self.top, text=(
            'query: ' + query + '\n' + 'filters: ' + filters), font=LBL_FONT,
                  justify=tk.LEFT).grid(
            row=1, column=1, columnspan=10, sticky='snw', padx=5, pady=5)

        self.nextBtn = tk.Button(self.top, text='next', font=BTN_FONT,
                                 width=15,
                                 height=1,
                                 command=self.next_page)
        self.nextBtn.grid(
            row=2, column=12, sticky='nw', padx=5, pady=5)

        self.previousBtn = tk.Button(self.top, text='previous', font=BTN_FONT,
                                     width=15,
                                     height=1,
                                     command=self.previous_page)
        self.previousBtn.grid(
            row=3, column=12, sticky='nw', padx=5, pady=5)

        tk.Button(self.top, text='export', font=BTN_FONT,
                  width=15,
                  height=1,
                  command=self.export).grid(
            row=5, column=12, sticky='nw', padx=5, pady=5)

        tk.Button(self.top, text='close', font=BTN_FONT,
                  width=15,
                  height=1,
                  command=self.top.destroy).grid(
            row=6, column=12, sticky='nw', padx=5, pady=5)

        self.yscrollbar = tk.Scrollbar(self.top, orient=tk.VERTICAL)
        self.yscrollbar.grid(
            row=2, column=1, rowspan=10, sticky='nse', padx=2)
        self.base = tk.Canvas(
            self.top,
            yscrollcommand=self.yscrollbar.set)
        self.base.grid(
            row=2, column=2, columnspan=10, rowspan=10, sticky='snew', padx=5)

        self.display_frame()
        self.display_hits()

    def display_frame(self):
        self.dispFrame = tk.Frame(
            self.base)
        # self.xscrollbar.config(command=self.base.xview)
        self.yscrollbar.config(command=self.base.yview)
        self.base.create_window(
            (0, 0), window=self.dispFrame, anchor="nw",
            tags="self.dispFrame")
        self.dispFrame.bind("<Configure>", self.onFrameConfigure)

    def onFrameConfigure(self, event):
        self.base.config(scrollregion=self.base.bbox('all'))

    def next_page(self):
        if self.current_page.get() < self.total_pages:
            self.dispFrame.destroy()
            self.display_frame()
            self.current_page.set(self.current_page.get() + 1)
            self.display_hits()

    def previous_page(self):
        if self.current_page.get() > 1:
            self.dispFrame.destroy()
            self.display_frame()
            self.current_page.set(self.current_page.get() - 1)
            self.display_hits()

    def display_hits(self):
        # disable next & previous buttons accordingly
        self.navigation()

        # display 100 results only
        n = (self.current_page.get() - 1) * 100
        sn = n + 1

        for hit in self.pages[self.current_page.get()]:
            unitFrm = ttk.LabelFrame(
                self.dispFrame, text=('hit ' + str(n + 1)))
            unitFrm.grid(
                row=n, column=0, sticky='snew', padx=5, pady=5)

            # calculate space for locations, each line has 5 locations
            loc_lines = []
            for i in range(0, len(hit['locations']), 5):
                loc_lines.append(','.join(hit['locations'][i:i + 5]))
            tr = 7 + len(loc_lines)

            title = tk.Text(
                unitFrm,
                font=LRG_FONT,
                state=tk.DISABLED,
                width=200,
                height=tr,
                background='SystemButtonFace',
                borderwidth=0)
            title.grid(
                row=0, column=0, sticky='nw', padx=5, pady=5)
            title['state'] = tk.NORMAL
            # title.delete(1.0, tk.END)
            unit = u'{title} / {author}. ' \
                   '{pubPlace} : {publisher}, {pubDate}.\n' \
                   'ISBN: {isbn}\n' \
                   '{lang}\t\t{matType}\n' \
                   'vendor: {vendor}\t\tvendor no: {venNo}\n' \
                   'order date: {date}\t\tlibrary: {library}' \
                   '\t\tselector: {selector}\n' \
                   'quantity: {qty}\t\tdisc. price: ${priceDisc}\n' \
                   'bNumber: {bNumber}\t\toNumber: {oNumber}\t\tBabel #: {wlo_id}' \
                   '\t\tblanket PO: {blanketPO}\n'.format(**hit)
            unit = unit.replace('None', '[ ]')

            title.insert(tk.END, unit)
            title.insert(tk.END, 'locations: ')
            title.insert(tk.END, '\n\t'.join(loc_lines))
            title.tag_add('heading', '1.0', '1.100')
            title.tag_config('heading', font=LRG_FONT)

            title['state'] = tk.DISABLED
            n += 1
        self.summary.set('displaying {}-{} out of {} hits'.format(sn, n, self.total_hits))

    def export(self):
        dir_opt = options = {}
        options['initialdir'] = os.path.expanduser('~/Documents')
        options['defaultextension'] = '.xlsx'
        options['initialfile'] = 'search_export.xlsx'
        filename = tkFileDialog.asksaveasfilename(**dir_opt)
        if filename:
            cur_manager.busy()
            file = sh.export_search(filename, self.hits)
            cur_manager.notbusy()
            if file is None:
                m = 'not able to save the file'
                tkMessageBox.showerror('error', m)
            else:
                tkMessageBox.showinfo('info', 'export saved')

    def reset(self):
        self.title_query.set('')
        self.title_query_type.set('title keyword')
        self.author_query.set('')
        self.vendor.set('any')
        self.date1.set('')
        self.date2.set('')
        self.library.set('any')
        self.lang.set('any')
        self.matType.set('any')
        self.selector.set('any')
        self.current_page.set(0)

    def validate_date(self, d, i, S):
        res = True
        if d == '1':
            for c in S:
                if i == '0':
                    if c not in '01':
                        res = False
                if i == '1':
                    if c not in '0123456789':
                        res = False
                if i in '25':
                    if c != '/':
                        res = False
                if i == '3':
                    if c not in '0123':
                        res = False
                if i in '6789':
                    if not c.isdigit():
                        res = False
                if int(i) > 9:
                    res = False
        return res

    def navigation(self, *args):
        if self.current_page.get() > 0:
            if self.current_page.get() >= self.total_pages:
                self.nextBtn['state'] = tk.DISABLED
            else:
                self.nextBtn['state'] = tk.NORMAL
                self.previousBtn['state'] = tk.NORMAL
            if self.current_page.get() == 1:
                self.previousBtn['state'] = tk.DISABLED

    def observer(self, *args):
        if self.tier.get() == 'Search':
            self.reset()

            # create indexes and populate drop-down comboboxes
            libraries = ()
            self.library_by_name = {}
            vendors = ()
            self.vendor_by_name = {}
            matTypes = ()
            self.matType_by_name = {}
            langs = ()
            self.lang_by_name = {}
            selectors = ()
            self.selector_by_name = {}

            self.title_query_type.set('title keyword')

            records = db.col_preview(
                db.Library,
                'id', 'code')
            for record in records:
                libraries = libraries + (record.code, )
                self.library_by_name[record.code] = record.id
            self.libraryCbx['values'] = libraries + ('any', )
            self.libraryCbx.set('any')

            records = db.col_preview(
                db.Vendor,
                'id', 'name')
            for record in records:
                vendors = vendors + (record.name, )
                self.vendor_by_name[record.name] = record.id
            self.vendorCbx['values'] = sorted(vendors + ('any', ))
            self.vendorCbx.set('any')

            records = db.col_preview(
                db.MatType,
                'id', 'name')
            for record in records:
                matTypes = matTypes + (record.name, )
                self.matType_by_name[record.name] = record.id
            self.matTypeCbx['values'] = matTypes + ('any', )
            self.matTypeCbx.set('any')

            records = db.col_preview(
                db.Selector,
                'id', 'name')
            for record in records:
                selectors = selectors + (record.name, )
                self.selector_by_name[record.name] = record.id
            self.selectorCbx['values'] = sorted(selectors + ('any', ))
            self.selectorCbx.set('any')

            records = db.col_preview(
                db.Lang,
                'id', 'name')
            for record in records:
                langs = langs + (record.name, )
                self.lang_by_name[record.name] = record.id
            self.langCbx['values'] = sorted(langs + ('any', ))
            self.langCbx.set('any')

            id_types = (
                '.o number',
                '.b number',
                'wlo number',
                'ISBN',
                'vendor number',
                'blanket PO'
            )

            self.id_typeCbx['values'] = id_types
            self.id_typeCbx.set('.o number')


if __name__ == '__main__':
    version = 'BABEL (beta v.0.8.1)'

    # setup log folder is does not exist
    if not os.path.isdir('./logs'):
        # create folder for logs
        os.mkdir('logs')

    # set up app logger
    main_logger = logging.getLogger('babel_logger')
    main_logger.setLevel(logging.DEBUG)
    handler = logging.handlers.RotatingFileHandler(
        LOG_FILENAME, maxBytes=1024 * 1024, backupCount=5)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    main_logger.addHandler(handler)

    # lounch application
    user_data = shelve.open('user_data')
    if 'version' in user_data:
        version = user_data['version']
    if 'db_config' in user_data:
        # pull db login details
        app = MainApplication()
        cur_manager = BusyManager(app)
        app.title(version)
        app.mainloop()
    else:
        # first time launch, show db details form
        setup_root = tk.Tk()
        setup_root.title("Database connection details")
        setup_app = DBSetup(setup_root)
        setup_root.mainloop()

    user_data.close()
