import logging
import shelve
from tkinter import *
from tkinter.ttk import *
from tkinter import messagebox

from PIL import Image, ImageTk


from data.datastore import (Audn, Branch, Lang, MatType, ShelfCode,
                            User, Vendor)
from errors import BabelError
from gui.data_retriever import (get_names, get_record, save_data,
                                delete_data)
from gui.fonts import RFONT
from gui.utils import disable_widgets, enable_widgets
from paths import USER_DATA


mlogger = logging.getLogger('babel_logger')


class TableView(Frame):
    """
    Shared among settings widgets frame
    """

    def __init__(self, parent, controller, **app_data):
        self.parent = parent
        Frame.__init__(self, parent)
        self.controller = controller
        self.app_data = app_data
        self.activeW = app_data['activeW']
        self.activeW.trace('w', self.observer)
        self.profile = app_data['profile']
        self.system = app_data['system']
        self.system.trace('w', self.system_observer)
        self.gen_list_select = StringVar()
        self.det_list_select = StringVar()
        self.det_list_select.trace('w', self.recreate_details_frame)
        self.record = None
        list_height = int((self.winfo_screenheight() - 100) / 25)

        # layout
        self.columnconfigure(0, minsize=200)  # genLst col
        self.columnconfigure(2, minsize=5)
        self.columnconfigure(3, minsize=300)  # detLst col

        # tables list
        Label(self, text='Tables:').grid(
            row=0, column=0, sticky='nw')
        scrollbarA = Scrollbar(self, orient=VERTICAL)
        scrollbarA.grid(
            row=1, column=1, rowspan=40, sticky='nsw')
        self.genLst = Listbox(
            self,
            font=RFONT,
            height=list_height,
            selectmode=SINGLE,
            yscrollcommand=scrollbarA.set)
        self.genLst.bind('<Double-Button-1>', self.set_general_variable)
        self.genLst.grid(
            row=1, column=0, rowspan=40, sticky='snew')
        scrollbarA['command'] = self.genLst.yview
        # populate tables list
        tables = [
            'Audiences',
            'Branches',
            'Languages',
            'Material Types',
            'Users',
            'Shelf Codes',
            'Vendors']
        for t in tables:
            self.genLst.insert(END, t)

        # table values list
        self.detLbl = Label(self, textvariable=self.gen_list_select)
        self.detLbl.grid(
            row=0, column=3, sticky='nw')
        scrollbarB = Scrollbar(self, orient=VERTICAL)
        scrollbarB.grid(
            row=1, column=4, rowspan=40, sticky='nsw')
        self.detLst = Listbox(
            self,
            font=RFONT,
            height=list_height,
            yscrollcommand=scrollbarB.set)
        self.detLst.bind('<Double-Button-1>', self.set_detail_variable)
        self.detLst.grid(
            row=1, column=3, rowspan=40, sticky='snew')
        scrollbarB['command'] = self.detLst.yview

        # action buttons
        img = Image.open('./icons/Action-edit-add-iconM.png')
        addImg = ImageTk.PhotoImage(img)
        self.addBtn = Button(
            self,
            image=addImg,
            command=self.add_data)
        self.addBtn.image = addImg
        self.addBtn.grid(
            row=1, column=5, sticky='sw', padx=20, pady=10)

        img = Image.open('./icons/Action-reload-iconM.png')
        editImg = ImageTk.PhotoImage(img)
        self.editBtn = Button(
            self,
            image=editImg,
            command=self.edit_data)
        self.editBtn.image = editImg
        self.editBtn.grid(
            row=2, column=5, sticky='sw', padx=20, pady=5)

        img = Image.open('./icons/Action-cancel-iconM.png')
        deleteImg = ImageTk.PhotoImage(img)
        self.deleteBtn = Button(
            self,
            image=deleteImg,
            command=self.delete_data)
        self.deleteBtn.image = deleteImg
        self.deleteBtn.grid(
            row=3, column=5, sticky='sw', padx=20, pady=5)

        img = Image.open('./icons/Action-ok-iconM.png')
        saveImg = ImageTk.PhotoImage(img)
        self.saveBtn = Button(
            self,
            image=saveImg,
            command=self.insert_or_update_data)
        self.saveBtn.image = saveImg
        self.saveBtn.grid(
            row=4, column=5, sticky='sw', padx=20, pady=5)

        img = Image.open('./icons/Action-button-info-iconM.png')
        helpImg = ImageTk.PhotoImage(img)
        self.helpBtn = Button(
            self,
            image=helpImg,
            command=self.help)
        self.helpBtn.image = helpImg
        self.helpBtn.grid(
            row=5, column=5, sticky='sw', padx=20, pady=5)

        self.initiate_details_frame()

    def add_data(self):
        mlogger.debug('Add btn clicked.')
        self.record = None
        self.det_list_select.set('')
        if self.gen_list_select.get():
            if self.gen_list_select.get() in (
                    'Branches', 'Shelf Codes'):
                if self.system.get():
                    self.populate_detail_frame()
                    enable_widgets(self.detFrm.winfo_children())
                    mlogger.debug('Detail frame ready for new data.')
            else:
                self.populate_detail_frame()
                enable_widgets(self.detFrm.winfo_children())
                mlogger.debug('Detail frame ready for new data.')

    def edit_data(self):
        mlogger.debug('Edit btn clicked.')
        self.recreate_details_frame()
        if self.gen_list_select.get() and self.det_list_select.get():
            self.populate_detail_frame()
            enable_widgets(self.detFrm.winfo_children())
            mlogger.debug('Detail frame ready for data edit.')

    def delete_data(self):
        mlogger.debug('Delete btn clicked.')
        # ask before deletion
        if self.record:
            msg = 'Are you sure you want to delete\n{}?'.format(
                str(self.record))
            if messagebox.askokcancel('Deletion', msg):
                mlogger.info('Data for deletion: {}'.format(
                    str(self.record)))
                delete_data(self.record)
                if type(self.record).__name__ == 'User':
                    messagebox.showwarning(
                        'Restart',
                        'For changes to Users to take effect\n'
                        'Babel needs to be restarted.\n'
                        'Please close and reopen Babel.')
                self.populate_detail_list()
                self.detFrm.destroy()
                self.initiate_details_frame()
                mlogger.debug('Data deleted.')

            else:
                mlogger.debug('Delection cancelled by user.')

    def insert_or_update_data(self):
        # check what table it is
        mlogger.debug('Save btn clicked.')
        kwargs = {}
        error_msg = False
        if self.record:
            mlogger.debug('Saving existing data.')
            if self.gen_list_select.get() in (
                    'Audiences', 'Branches', 'Languages',
                    'Shelf Codes'):
                name = self.nameEnt.get().strip()
                code = self.codeEnt.get().strip()
                kwargs = {
                    'name': name,
                    'code': code}

            elif self.gen_list_select.get() in (
                    'Users', 'Vendors'):
                name = self.nameEnt.get().strip()
                bpl_code = self.bplcodeEnt.get().strip()
                nyp_code = self.nypcodeEnt.get().strip()
                kwargs = {
                    'name': name,
                    'bpl_code': bpl_code,
                    'nyp_code': nyp_code}
                if self.gen_list_select.get() == 'Vendors':
                    kwargs['note'] = self.noteEnt.get().strip()

            for k, v in kwargs.items():
                if v == '':
                    kwargs[k] = None
            model, kwargs = self.get_corresponding_model(**kwargs)
            try:
                save_data(
                    model, did=record.did, **kwargs)
                if model.__name__ == 'User':
                    messagebox.showwarning(
                        'Restart',
                        'For changes to Users to take effect\n'
                        'Babel needs to be restarted.\n'
                        'Please close and reopen Babel.')
            except BabelError as e:
                error_msg = True
                messagebox.showerror('Database error', e)

        else:
            mlogger.debug('Saving new data.')
            if self.gen_list_select.get() in (
                    'Audiences', 'Branches', 'Languages',
                    'Shelf Codes'):
                try:
                    name = self.nameEnt.get()
                    code = self.codeEnt.get()
                    # validate
                    kwargs = {
                        'name': name,
                        'code': code}
                except TclError:
                    pass

            elif self.gen_list_select.get() in (
                    'Users', 'Vendors'):
                try:
                    name = self.nameEnt.get().strip()
                    bpl_code = self.bplcodeEnt.get().strip()
                    nyp_code = self.nypcodeEnt.get().strip()
                    kwargs = {
                        'name': name,
                        'bpl_code': bpl_code,
                        'nyp_code': nyp_code}

                    if self.gen_list_select.get() == 'Vendors':
                        kwargs['note'] = self.noteEnt.get().strip()
                except TclError:
                    pass

            for k, v in kwargs.items():
                if v == '':
                    kwargs[k] = None

            model, kwargs = self.get_corresponding_model(**kwargs)
            try:
                if model is not None:
                    save_data(
                        model, **kwargs)
                    if model.__name__ == 'User':
                        messagebox.showwarning(
                            'Restart',
                            'For changes to Users to take effect\n'
                            'Babel needs to be restarted.\n'
                            'Please close and reopen Babel.')
            except BabelError as e:
                error_msg = True
                messagebox.showerror('Database error', e)

        self.populate_detail_list(redo_detail_frame=False)
        if not error_msg:
            disable_widgets(self.detFrm.winfo_children())

    def help(self):
        pass

    def get_corresponding_model(self, **kwargs):
        mlogger.debug('Getting db model for {}'.format(
            self.gen_list_select.get()))

        if not kwargs:
            kwargs = {}

        if self.gen_list_select.get() == 'Audiences':
            model = Audn
        elif self.gen_list_select.get() == 'Users':
            model = User
        elif self.gen_list_select.get() == 'Material Types':
            model = MatType
        elif self.gen_list_select.get() == 'Languages':
            model = Lang
        elif self.gen_list_select.get() == 'Vendors':
            model = Vendor
        elif self.system.get():
            kwargs['system_id'] = self.system.get()
            if self.gen_list_select.get() == 'Branches':
                model = Branch
            elif self.gen_list_select.get() == 'Shelf Codes':
                model = ShelfCode
        else:
            model = None

        if model:
            mlogger.debug(
                'Identified corresponding db model: {}, kwargs:{}'.format(
                    model.__name__, kwargs))
        else:
            mlogger.debug('Failed to identify corresponding db model.')

        return (model, kwargs)

    def set_general_variable(self, *args):
        self.gen_list_select.set(self.genLst.get(ACTIVE))
        self.populate_detail_list()

    def set_detail_variable(self, *args):
        self.det_list_select.set(self.detLst.get(ACTIVE))
        self.populate_detail_frame(self.det_list_select.get())

    def populate_detail_frame(self, *args):
        mlogger.debug('Populating details frame for {}/{}.'.format(
            self.gen_list_select.get(), self.det_list_select.get()))
        model = self.get_corresponding_model()[0]
        if self.gen_list_select.get() in (
                'Audiences', 'Branches', 'Languages',
                'Shelf Codes'):
            if self.det_list_select.get():
                self.record = get_record(
                    model, name=self.det_list_select.get())
                self.simpleDetailFrame(
                    self.record.name, self.record.code)
            else:
                mlogger.debug('Creating empty details frame.')
                self.simpleDetailFrame()
        elif self.gen_list_select.get() == 'Users':
            if self.det_list_select.get():
                self.record = get_record(
                    model, name=self.det_list_select.get())
                self.userDetailFrame(
                    self.record.name, self.record.bpl_code,
                    self.record.nyp_code)
            else:
                mlogger.debug('Creating empty details frame.')
                self.userDetailFrame()
        elif self.gen_list_select.get() == 'Vendors':
            if self.det_list_select.get():
                self.record = get_record(
                    model, name=self.det_list_select.get())
                self.vendorDetailFrame(
                    self.record.name, self.record.note,
                    self.record.bpl_code, self.record.nyp_code)
            else:
                mlogger.debug('Creating empty details frame.')
                self.vendorDetailFrame()
        elif self.gen_list_select.get() == 'Material Types':
            if self.det_list_select.get():
                self.record = get_record(model, name=self.det_list_select.get())
                self.mattypeDetailFrame(
                    self.record.name, self.record.bpl_bib_code,
                    self.record.bpl_ord_code,
                    self.record.nyp_bib_code, self.record.nyp_ord_code)
            else:
                mlogger.debug('Creating empty details frame.')
                self.mattypeDetailFrame()

    def userDetailFrame(self, name='', bpl_code='', nyp_code=''):
        mlogger.debug('userDetailFrame activated.')
        if bpl_code is None:
            bpl_code = ''
        if nyp_code is None:
            nyp_code = ''

        Label(self.detFrm, text='user').grid(
            row=0, column=0, sticky='snw', padx=5, pady=5)
        Label(self.detFrm, text='BPL code').grid(
            row=1, column=0, sticky='snw', padx=5, pady=5)
        Label(self.detFrm, text='NYPL code').grid(
            row=2, column=0, sticky='snw', padx=5, pady=5)
        self.nameEnt = Entry(
            self.detFrm,
            font=RFONT)
        self.nameEnt.grid(
            row=0, column=1, columnspan=3, padx=5, pady=5)
        self.bplcodeEnt = Entry(
            self.detFrm,
            font=RFONT)
        self.bplcodeEnt.grid(
            row=1, column=1, columnspan=3, padx=5, pady=5)
        self.nypcodeEnt = Entry(
            self.detFrm,
            font=RFONT)
        self.nypcodeEnt.grid(
            row=2, column=1, columnspan=3, padx=5, pady=5)
        self.nameEnt.insert(0, name)
        self.bplcodeEnt.insert(0, bpl_code)
        self.nypcodeEnt.insert(0, nyp_code)
        disable_widgets(
            [self.nameEnt, self.bplcodeEnt, self.nypcodeEnt])

    def simpleDetailFrame(self, name='', code=''):
        mlogger.debug('simpleDetailFrame activated.')
        if code is None:
            code = ''

        Label(self.detFrm, text='name').grid(
            row=0, column=0, sticky='snw', padx=5, pady=5)
        Label(self.detFrm, text='code').grid(
            row=1, column=0, sticky='snw', padx=5, pady=5)
        self.nameEnt = Entry(
            self.detFrm,
            font=RFONT)
        self.nameEnt.grid(
            row=0, column=1, columnspan=3, padx=5, pady=5)
        self.codeEnt = Entry(
            self.detFrm,
            font=RFONT,)
        self.codeEnt.grid(
            row=1, column=1, columnspan=3, padx=5, pady=5)
        self.nameEnt.insert(0, name)
        self.codeEnt.insert(0, code)
        disable_widgets([self.nameEnt, self.codeEnt])

    def vendorDetailFrame(self, name='', note='', bpl_code='', nyp_code=''):
        mlogger.debug('vendorDetailFrame activated.')

        if note is None:
            note = ''
        if bpl_code is None:
            bpl_code = ''
        if nyp_code is None:
            nyp_code = ''

        Label(self.detFrm, text='name').grid(
            row=0, column=0, sticky='snw', padx=5, pady=5)
        Label(self.detFrm, text='note').grid(
            row=1, column=0, sticky='snw', padx=5, pady=5)
        Label(self.detFrm, text='BPL code').grid(
            row=2, column=0, sticky='snw', padx=5, pady=5)
        Label(self.detFrm, text='NYPL code').grid(
            row=3, column=0, sticky='snw', padx=5, pady=5)
        self.nameEnt = Entry(
            self.detFrm,
            font=RFONT)
        self.nameEnt.grid(
            row=0, column=1, columnspan=3, padx=5, pady=5)
        self.noteEnt = Entry(
            self.detFrm,
            font=RFONT,)
        self.noteEnt.grid(
            row=1, column=1, columnspan=3, padx=5, pady=5)
        self.bplcodeEnt = Entry(
            self.detFrm,
            font=RFONT,)
        self.bplcodeEnt.grid(
            row=2, column=1, columnspan=3, padx=5, pady=5)
        self.nypcodeEnt = Entry(
            self.detFrm,
            font=RFONT,)
        self.nypcodeEnt.grid(
            row=3, column=1, columnspan=3, padx=5, pady=5)
        self.nameEnt.insert(0, name)
        self.noteEnt.insert(0, note)
        self.bplcodeEnt.insert(0, bpl_code)
        self.nypcodeEnt.insert(0, nyp_code)
        disable_widgets([
            self.nameEnt, self.noteEnt,
            self.bplcodeEnt, self.nypcodeEnt])

    def mattypeDetailFrame(
            self, name='', bpl_bib_code='', bpl_ord_code='',
            nyp_bib_code='', nyp_ord_code=''):

        mlogger.debug('mattypeDetailFrame activated.')

        if bpl_bib_code is None:
            bpl_bib_code = ''
        if bpl_ord_code is None:
            bpl_ord_code = ''
        if nyp_bib_code is None:
            nyp_bib_code = ''
        if nyp_ord_code is None:
            nyp_ord_code = ''

        Label(self.detFrm, text='name').grid(
            row=0, column=0, sticky='snw', padx=5, pady=5)
        Label(self.detFrm, text='BPL bib code').grid(
            row=1, column=0, sticky='snw', padx=5, pady=5)
        Label(self.detFrm, text='BPL ord code').grid(
            row=2, column=0, sticky='snw', padx=5, pady=5)
        Label(self.detFrm, text='NYP bib code').grid(
            row=3, column=0, sticky='snw', padx=5, pady=5)
        Label(self.detFrm, text='NYP ord code').grid(
            row=4, column=0, sticky='snw', padx=5, pady=5)
        self.nameEnt = Entry(
            self.detFrm,
            font=RFONT)
        self.nameEnt.grid(
            row=0, column=1, columnspan=3, padx=5, pady=5)
        self.bplbibcodeEnt = Entry(
            self.detFrm,
            font=RFONT,)
        self.bplbibcodeEnt.grid(
            row=1, column=1, columnspan=3, padx=5, pady=5)
        self.bplordcodeEnt = Entry(
            self.detFrm,
            font=RFONT,)
        self.bplordcodeEnt.grid(
            row=2, column=1, columnspan=3, padx=5, pady=5)
        self.nypbibcodeEnt = Entry(
            self.detFrm,
            font=RFONT,)
        self.nypbibcodeEnt.grid(
            row=3, column=1, columnspan=3, padx=5, pady=5)
        self.nypordcodeEnt = Entry(
            self.detFrm,
            font=RFONT,)
        self.nypordcodeEnt.grid(
            row=4, column=1, columnspan=3, padx=5, pady=5)
        self.nameEnt.insert(0, name)
        self.bplbibcodeEnt.insert(0, bpl_bib_code)
        self.bplordcodeEnt.insert(0, bpl_ord_code)
        self.nypbibcodeEnt.insert(0, nyp_bib_code)
        self.nypordcodeEnt.insert(0, nyp_ord_code)
        disable_widgets([
            self.nameEnt, self.bplbibcodeEnt, self.bplordcodeEnt,
            self.nypbibcodeEnt, self.nypordcodeEnt])

    def initiate_details_frame(self):
        mlogger.debug('Initiating details frame.')
        # Details frame
        self.detFrm = LabelFrame(self, text='Values')
        self.detFrm.grid(row=1, column=7, rowspan=40, sticky='snew', padx=5)

    def recreate_details_frame(self, *args):
        mlogger.debug('Recreating details frame.')
        self.detFrm.destroy()
        self.record = None
        self.initiate_details_frame()

    def populate_detail_list(self, redo_detail_frame=True, *args):
        mlogger.debug('Populating detail list.')
        # destroy any detail frame that may display
        # previous data
        if redo_detail_frame:
            self.recreate_details_frame()
        else:
            mlogger.debug('Details frame preserved.')

        # detelet current detail list
        self.detLst.delete(0, END)

        # # retrieve data
        # self.gen_list_select.set(self.genLst.get(ACTIVE))

        # repopulate
        model, kwargs = self.get_corresponding_model()
        if model is not None:
            values = get_names(model, **kwargs)
            for v in values:
                self.detLst.insert(END, v)

    def system_observer(self, *args):
        mlogger.debug('System_observer triggered.')
        if self.gen_list_select.get():
            mlogger.debug('Table {} active'.format(
                self.gen_list_select.get()))
            self.populate_detail_list()

            # persist current system
            user_data = shelve.open(USER_DATA)
            user_data['system'] = self.system.get()
            user_data.close()

    def observer(self, *args):
        if self.activeW.get() == 'TableView':
            self.profile.set('All users')
