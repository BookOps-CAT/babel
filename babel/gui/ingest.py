from datetime import datetime
import logging
import shelve
from tkinter import *
from tkinter.ttk import *
from tkinter import messagebox, filedialog


from errors import BabelError
from data.datastore import Sheet
from gui.data_retriever import (get_names, save_data, get_record,
                                convert4display, delete_data,
                                create_resource_reader, create_cart)
from gui.fonts import RFONT, LFONT
from gui.utils import (ToolTip, get_id_from_index, disable_widgets,
                       enable_widgets, open_url)
from paths import USER_DATA, MY_DOCS
from ingest.xlsx import SheetReader
from logging_settings import format_traceback

mlogger = logging.getLogger('babel_logger')


class ImportView(Frame):
    """
    Sheet import window
    """

    def __init__(self, parent, controller, **app_data):
        self.parent = parent
        Frame.__init__(self, parent)
        self.controller = controller
        self.app_data = app_data
        self.activeW = app_data['activeW']
        self.activeW.trace('w', self.observer)
        self.system = app_data['system']
        self.profile = app_data['profile']
        self.profile.trace('w', self.profile_observer)
        self.profile_idx = app_data['profile_idx']
        # list_height = int((self.winfo_screenheight() - 100) / 25)

        # variables
        self.sheet_name = StringVar()
        self.sheet_name.trace('w', self.sheet_observer)
        self.record = None
        self.edit_mode = False
        self.header_row = StringVar()
        self.title_col = StringVar()
        self.add_title_col = StringVar()
        self.author_col = StringVar()
        self.series_col = StringVar()
        self.publisher_col = StringVar()
        self.pub_date_col = StringVar()
        self.pub_place_col = StringVar()
        self.summary_col = StringVar()
        self.isbn_col = StringVar()
        self.upc_col = StringVar()
        self.other_no_col = StringVar()
        self.price_list_col = StringVar()
        self.price_disc_col = StringVar()
        self.desc_url_col = StringVar()
        self.misc_col = StringVar()
        self.created = StringVar()
        self.updated = StringVar()
        self.fh = None

        # icons
        addImg = self.app_data['img']['add']
        editImg = self.app_data['img']['edit']
        deleteImg = self.app_data['img']['delete']
        saveImg = self.app_data['img']['save']
        helpImg = self.app_data['img']['help']
        loadImg = self.app_data['img']['load']
        importImg = self.app_data['img']['import']

        self.actionFrm = Frame(self)
        self.actionFrm.grid(
            row=0, column=0, sticky='snew', padx=10, pady=10)

        # action buttons
        self.addBtn = Button(
            self.actionFrm,
            image=addImg,
            command=self.add_data)
        # self.addBtn.image = addImg
        self.addBtn.grid(
            row=0, column=0, sticky='sw', padx=20, pady=10)
        self.createToolTip(self.addBtn, 'new sheet template')

        self.editBtn = Button(
            self.actionFrm,
            image=editImg,
            command=self.edit_data)
        # self.editBtn.image = editImg
        self.editBtn.grid(
            row=1, column=0, sticky='sw', padx=20, pady=5)
        self.createToolTip(self.editBtn, 'edit sheet template')

        self.deleteBtn = Button(
            self.actionFrm,
            image=deleteImg,
            command=self.delete_data)
        # self.deleteBtn.image = deleteImg
        self.deleteBtn.grid(
            row=2, column=0, sticky='sw', padx=20, pady=5)
        self.createToolTip(self.deleteBtn, 'delete sheet template')

        self.saveBtn = Button(
            self.actionFrm,
            image=saveImg,
            command=self.insert_or_update_data)
        # self.saveBtn.image = saveImg
        self.saveBtn.grid(
            row=3, column=0, sticky='sw', padx=20, pady=5)
        self.createToolTip(self.saveBtn, 'save sheet template')

        self.helpBtn = Button(
            self.actionFrm,
            image=helpImg,
            command=self.help)
        # self.helpBtn.image = helpImg
        self.helpBtn.grid(
            row=4, column=0, sticky='sw', padx=20, pady=5)
        self.createToolTip(self.helpBtn, 'help')

        # sheet template data frame
        self.templateFrm = LabelFrame(self, text='sheet template')
        self.templateFrm.grid(
            row=0, column=1, sticky='snew', padx=5, pady=10)

        # validation of column comboboxes
        self.vlcl = (self.register(self.onValidateCol),
                     '%d', '%i', '%P', '%W')
        self.vlen = (self.register(self.onValidateName),
                     '%P')

        self.sheetCbx = Combobox(
            self.templateFrm,
            font=RFONT,
            textvariable=self.sheet_name,
            validate="key", validatecommand=self.vlen)
        self.sheetCbx.grid(
            row=0, column=0, columnspan=2, sticky='snew', padx=5, pady=5)

        self.createdLbl = Label(
            self.templateFrm, textvariable=self.created, font=LFONT)
        self.createdLbl.grid(
            row=1, column=0, columnspan=2, sticky='snw', padx=5, pady=2)
        self.updatedLbl = Label(
            self.templateFrm, textvariable=self.updated, font=LFONT)
        self.updatedLbl.grid(
            row=2, column=0, columnspan=2, sticky='snw', padx=5, pady=2)

        Label(self.templateFrm, text='header row:').grid(
            row=3, column=0, sticky='snw', padx=5, pady=2)
        self.headerrowEnt = Entry(
            self.templateFrm,
            font=RFONT,
            width=5,
            textvariable=self.header_row,
            validate="key", validatecommand=self.vlcl)
        self.headerrowEnt.grid(
            row=3, column=1, sticky='snw', padx=5, pady=2)

        Label(self.templateFrm, text='title column:').grid(
            row=4, column=0, sticky='snw', padx=5, pady=2)
        self.titlecolEnt = Entry(
            self.templateFrm,
            font=RFONT,
            width=5,
            textvariable=self.title_col,
            validate="key", validatecommand=self.vlcl)
        self.titlecolEnt.grid(
            row=4, column=1, sticky='snw', padx=5, pady=2)

        Label(self.templateFrm, text='extra title col.:').grid(
            row=5, column=0, sticky='snw', padx=5, pady=2)
        self.addtitlecolEnt = Entry(
            self.templateFrm,
            font=RFONT,
            width=5,
            textvariable=self.add_title_col,
            validate="key", validatecommand=self.vlcl)
        self.addtitlecolEnt.grid(
            row=5, column=1, sticky='snw', padx=5, pady=2)

        Label(self.templateFrm, text='author column:').grid(
            row=6, column=0, sticky='snw', padx=5, pady=2)
        self.authorcolEnt = Entry(
            self.templateFrm,
            font=RFONT,
            width=5,
            textvariable=self.author_col,
            validate="key", validatecommand=self.vlcl)
        self.authorcolEnt.grid(
            row=6, column=1, sticky='snw', padx=5, pady=2)

        Label(self.templateFrm, text='series column:').grid(
            row=7, column=0, sticky='snw', padx=5, pady=2)
        self.seriescolEnt = Entry(
            self.templateFrm,
            font=RFONT,
            width=5,
            textvariable=self.series_col,
            validate="key", validatecommand=self.vlcl)
        self.seriescolEnt.grid(
            row=7, column=1, sticky='snw', padx=5, pady=2)

        Label(self.templateFrm, text='publisher column:').grid(
            row=8, column=0, sticky='snw', padx=5, pady=2)
        self.publishercolEnt = Entry(
            self.templateFrm,
            font=RFONT,
            width=5,
            textvariable=self.publisher_col,
            validate="key", validatecommand=self.vlcl)
        self.publishercolEnt.grid(
            row=8, column=1, sticky='snw', padx=5, pady=2)

        Label(self.templateFrm, text='pub. date column:').grid(
            row=9, column=0, sticky='snw', padx=5, pady=2)
        self.pubdatecolEnt = Entry(
            self.templateFrm,
            font=RFONT,
            width=5,
            textvariable=self.pub_date_col,
            validate="key", validatecommand=self.vlcl)
        self.pubdatecolEnt.grid(
            row=9, column=1, sticky='snw', padx=5, pady=2)

        Label(self.templateFrm, text='pub. place column:').grid(
            row=10, column=0, sticky='snw', padx=5, pady=2)
        self.pubplacecolEnt = Entry(
            self.templateFrm,
            font=RFONT,
            width=5,
            textvariable=self.pub_place_col,
            validate="key", validatecommand=self.vlcl)
        self.pubplacecolEnt.grid(
            row=10, column=1, sticky='snw', padx=5, pady=2)

        Label(self.templateFrm, text='summary column:').grid(
            row=11, column=0, sticky='snw', padx=5, pady=2)
        self.summarycolEnt = Entry(
            self.templateFrm,
            font=RFONT,
            width=5,
            textvariable=self.summary_col,
            validate="key", validatecommand=self.vlcl)
        self.summarycolEnt.grid(
            row=11, column=1, sticky='snw', padx=5, pady=2)

        Label(self.templateFrm, text='ISBN column:').grid(
            row=12, column=0, sticky='snw', padx=5, pady=2)
        self.isbncolEnt = Entry(
            self.templateFrm,
            font=RFONT,
            width=5,
            textvariable=self.isbn_col,
            validate="key", validatecommand=self.vlcl)
        self.isbncolEnt.grid(
            row=12, column=1, sticky='snw', padx=5, pady=2)

        Label(self.templateFrm, text='UPC column:').grid(
            row=13, column=0, sticky='snw', padx=5, pady=2)
        self.upccolEnt = Entry(
            self.templateFrm,
            font=RFONT,
            width=5,
            textvariable=self.upc_col,
            validate="key", validatecommand=self.vlcl)
        self.upccolEnt.grid(
            row=13, column=1, sticky='snw', padx=5, pady=2)

        Label(self.templateFrm, text='other no. column:').grid(
            row=14, column=0, sticky='snw', padx=5, pady=2)
        self.othernocolEnt = Entry(
            self.templateFrm,
            font=RFONT,
            width=5,
            textvariable=self.other_no_col,
            validate="key", validatecommand=self.vlcl)
        self.othernocolEnt.grid(
            row=14, column=1, sticky='snw', padx=5, pady=2)

        Label(self.templateFrm, text='list price column:').grid(
            row=15, column=0, sticky='snw', padx=5, pady=2)
        self.pricelistcolEnt = Entry(
            self.templateFrm,
            font=RFONT,
            width=5,
            textvariable=self.price_list_col,
            validate="key", validatecommand=self.vlcl)
        self.pricelistcolEnt.grid(
            row=15, column=1, sticky='snw', padx=5, pady=2)

        Label(self.templateFrm, text='discount price col.:').grid(
            row=16, column=0, sticky='snw', padx=5, pady=2)
        self.pricedisccolEnt = Entry(
            self.templateFrm,
            font=RFONT,
            width=5,
            textvariable=self.price_disc_col,
            validate="key", validatecommand=self.vlcl)
        self.pricedisccolEnt.grid(
            row=16, column=1, sticky='snw', padx=5, pady=2)

        Label(self.templateFrm, text='URL column:').grid(
            row=17, column=0, sticky='snw', padx=5, pady=2)
        self.urldesccolEnt = Entry(
            self.templateFrm,
            font=RFONT,
            width=5,
            textvariable=self.desc_url_col,
            validate="key", validatecommand=self.vlcl)
        self.urldesccolEnt.grid(
            row=17, column=1, sticky='snw', padx=5, pady=2)

        Label(self.templateFrm, text='misc column:').grid(
            row=18, column=0, sticky='snw', padx=5, pady=2)
        self.misccolEnt = Entry(
            self.templateFrm,
            font=RFONT,
            width=5,
            textvariable=self.misc_col,
            validate="key", validatecommand=self.vlcl)
        self.misccolEnt.grid(
            row=18, column=1, sticky='snw', padx=5, pady=2)

        # sheet frame
        self.sheetFrm = LabelFrame(self, text='sheet')
        self.sheetFrm.grid(
            row=0, column=2, sticky='snew', padx=5, pady=10)

        self.loadBtn = Button(
            self.sheetFrm,
            image=loadImg,
            text='load',
            compound=TOP,
            width=10,
            command=self.load_sheet)
        # self.loadBtn.image = loadImg
        self.loadBtn.grid(
            row=0, column=0, sticky='snw', padx=50, pady=20)

        self.importBtn = Button(
            self.sheetFrm,
            image=importImg,
            text='import',
            compound=TOP,
            width=10,
            command=self.name_cart_widget)
        # self.importBtn.image = importImg
        self.importBtn.grid(
            row=0, column=0, sticky='sne', padx=50, pady=20)

        # sheet display frame
        self.sheetPreviewFrm = Frame(self.sheetFrm)
        self.sheetPreviewFrm.grid(
            row=1, column=0, columnspan=3, sticky='snw')
        self.sheetPreviewFrm.columnconfigure(2, minsize=800)

        # sheet preview
        self.xscrollbar = Scrollbar(self.sheetPreviewFrm, orient=HORIZONTAL)
        self.xscrollbar.grid(
            row=10, column=1, columnspan=7, sticky='nwe', padx=10)
        self.yscrollbar = Scrollbar(self.sheetPreviewFrm, orient=VERTICAL)
        self.yscrollbar.grid(
            row=0, column=0, sticky='nse', padx=2)
        self.preview_base = Canvas(
            self.sheetPreviewFrm, bg='gray',
            height=450,  # find a way to adjust based on preview frm size
            # width=800,
            xscrollcommand=self.xscrollbar.set,
            yscrollcommand=self.yscrollbar.set)
        self.preview_base.grid(
            row=0, column=1, columnspan=7, sticky='nwe', padx=10)
        self.preview()

    def generate_preview(self):
        # clear and recreate frame
        self.reset_preview()
        if self.fh:
            # provide template layout
            if self.record:
                tmask = self.template_mask()
                mlogger.debug(
                    'Applying template mask: {}'.format(tmask))
            sheet_reader = SheetReader(self.fh)
            max_row = sheet_reader.max_row
            max_column = sheet_reader.max_column
            rowLst = Listbox(
                self.preview_frame, font=LFONT,
                width=3,
                height=max_row + 1)
            rowLst.grid(
                row=1, column=1, sticky='nsw')

            if self.record:
                rowLst.insert(END, '')

            for row in range(max_row + 1):
                rowLst.insert(END, row)
            if self.record:
                rowLst.itemconfig(
                    self.record.header_row + 1, {'bg': 'SteelBlue1'})
            c = 0
            r = 0
            for column in range(max_column):
                colLst = Listbox(
                    self.preview_frame, font=LFONT,
                    width=15,
                    height=max_row + 1)
                colLst.grid(
                    row=1, column=c + 2, sticky='nsw')
                if self.record:
                    if column in tmask:
                        colLst['bg'] = 'SlateGray1'
                        colLst.insert(END, tmask[column])
                    else:
                        colLst.insert(END, '')
                colLst.insert(END, str(c))
                for row in sheet_reader:
                    if row[r] is None:
                        colLst.insert(END, '')
                    else:
                        colLst.insert(END, row[r])
                if self.record:
                    colLst.itemconfig(
                        self.record.header_row + 1, {'bg': 'SteelBlue1'})
                r += 1
                c += 1

    def template_mask(self):
        tmask = {}

        if self.record.title_col is not None:
            tmask[self.record.title_col] = 'title'
        if self.record.add_title_col is not None:
            tmask[self.record.add_title_col] = 'extra title'
        if self.record.author_col is not None:
            tmask[self.record.author_col] = 'author'
        if self.record.series_col is not None:
            tmask[self.record.series_col] = 'series'
        if self.record.publisher_col is not None:
            tmask[self.record.publisher_col] = 'publisher'
        if self.record.pub_date_col is not None:
            tmask[self.record.pub_date_col] = 'pub.date'
        if self.record.pub_place_col is not None:
            tmask[self.record.pub_place_col] = 'pub.place'
        if self.record.summary_col is not None:
            tmask[self.record.summary_col] = 'summary'
        if self.record.isbn_col is not None:
            tmask[self.record.isbn_col] = 'ISBN'
        if self.record.upc_col is not None:
            tmask[self.record.upc_col] = 'UPC'
        if self.record.other_no_col is not None:
            tmask[self.record.other_no_col] = 'other no'
        if self.record.price_list_col is not None:
            tmask[self.record.price_list_col] = 'list price'
        if self.record.price_disc_col is not None:
            tmask[self.record.price_disc_col] = 'disc. price'
        if self.record.desc_url_col is not None:
            tmask[self.record.desc_url_col] = 'URL'
        if self.record.misc_col is not None:
            tmask[self.record.misc_col] = 'misc.'

        return tmask

    def preview(self):
        self.preview_frame = Frame(
            self.preview_base)
        self.xscrollbar.config(command=self.preview_base.xview)
        self.yscrollbar.config(command=self.preview_base.yview)
        self.preview_base.create_window(
            (0, 0), window=self.preview_frame, anchor="nw",
            tags="self.preview_frame")
        self.preview_frame.bind("<Configure>", self.onFrameConfigure)

    def onFrameConfigure(self, event):
        self.preview_base.config(scrollregion=self.preview_base.bbox('all'))

    def reset_preview(self):
        self.preview_frame.grid_forget()
        self.preview_frame.destroy()
        self.preview()

    def add_data(self, *args):
        self.reset_template()
        enable_widgets(self.templateFrm.winfo_children())
        self.sheetCbx['state'] = '!readonly'
        self.edit_mode = True

    def edit_data(self, *args):
        self.sheetCbx['state'] = '!readonly'
        self.edit_mode = True
        enable_widgets(self.templateFrm.winfo_children())

    def delete_data(self, *args):
        if self.record and self.sheet_name.get():
            msg = 'Are you sure you want to delete\n{}?'.format(
                str(self.record))
            if messagebox.askokcancel('Deletion', msg):
                mlogger.info('Data for deletion: {}'.format(
                    str(self.record)))
                delete_data(self.record)

                mlogger.debug('Data deleted.')
                self.reset_template()
                disable_widgets(self.templateFrm.winfo_children())
                enable_widgets([self.sheetCbx])
                self.sheetCbx['state'] = 'readonly'
            else:
                mlogger.debug('Delection cancelled by user.')

    def insert_or_update_data(self, *args):
        if self.sheet_name.get() and self.header_row.get() and \
                self.edit_mode:
            kwargs = {
                'header_row': self.header_row.get().strip(),
                'title_col': self.title_col.get().strip(),
                'add_title_col': self.add_title_col.get().strip(),
                'author_col': self.author_col.get().strip(),
                'series_col': self.series_col.get().strip(),
                'publisher_col': self.publisher_col.get().strip(),
                'pub_date_col': self.pub_date_col.get().strip(),
                'pub_place_col': self.pub_place_col.get().strip(),
                'summary_col': self.summary_col.get().strip(),
                'isbn_col': self.isbn_col.get().strip(),
                'upc_col': self.upc_col.get().strip(),
                'other_no_col': self.other_no_col.get().strip(),
                'price_list_col': self.price_list_col.get().strip(),
                'price_disc_col': self.price_disc_col.get().strip(),
                'desc_url_col': self.desc_url_col.get().strip(),
                'misc_col': self.misc_col.get().strip()
            }

            # store as int
            for key, value in kwargs.items():
                if value.isdigit():
                    kwargs[key] = int(value)

            kwargs['name'] = self.sheet_name.get().strip()
            kwargs['user_id'] = get_id_from_index(
                self.profile.get(), self.profile_idx)
            kwargs['updated'] = datetime.now()
            try:
                if self.record:
                    mlogger.debug(
                        'Updating sheet template for record.did: {} '
                        'with values {}'.format(
                            self.record.did, kwargs))
                    save_data(Sheet, did=self.record.did, **kwargs)
                else:
                    mlogger.debug(
                        'Saving new sheet template with values: {}'.format(
                            kwargs))
                    save_data(Sheet, **kwargs)
                    self.created.set(
                        f'created:{kwargs["updated"]:%y-%m-%d %H:%M}')

                self.updated.set(
                    f'updated:{kwargs["updated"]:%y-%m-%d %H:%M}')

                self.record = get_record(Sheet, name=self.sheet_name.get().strip())
                self.update_sheet_templates()
                disable_widgets(self.templateFrm.winfo_children())
                enable_widgets([self.sheetCbx])
                self.sheetCbx['state'] = 'readonly'
                self.edit_mode = False
            except BabelError as e:
                messagebox.showerror('Database Error', e)

    def help(self):
        open_url('https://github.com/BookOps-CAT/babel/wiki/Import')

    def load_sheet(self):
        # retrieve last used directory
        user_data = shelve.open(USER_DATA)
        if 'sheet_dir' in user_data:
            sheet_dir = user_data['sheet_dir']
        else:
            sheet_dir = MY_DOCS
        fh = filedialog.askopenfilename(initialdir=sheet_dir)
        if fh:
            # record directory
            n = fh.rfind('/')
            sheet_dir = fh[:n + 1]
            user_data['sheet_dir'] = sheet_dir
            # validate if correct file type
            if fh.rfind('.xlsx') == -1:
                msg = 'Wrong type of spreadsheet file.\n' \
                      'Only sheets with extention .xlsx are permitted'
                tkMessageBox.showwarning('File type error', msg)
            else:
                self.fh = fh
                self.generate_preview()

        user_data.close()

    def name_cart_widget(self):
        if self.fh and self.record:
            top = Toplevel()
            top.title('New cart')

            cart_name = StringVar()

            if self.system.get() == 1:
                system = 'system: BPL'
            elif self.system.get() == 2:
                system = 'system: NYPL'

            profile = f'profile: {self.profile.get()}'
            profile_id = get_id_from_index(
                self.profile.get(), self.profile_idx)

            # calculate number of resources
            c = 0
            data = create_resource_reader(
                self.record, self.fh)
            try:
                for d in data:
                    c += 1
            except Exception as exc:
                _, _, exc_traceback = sys.exc_info()
                tb = format_traceback(exc, exc_traceback)
                mlogger.error(
                    f'Unhandled error while using ResourceDataReader.'
                    'Traceback: {tb}')

            frm = Frame(top)
            frm.grid(
                row=0, column=0, sticky='snew', padx=20, pady=20)
            Label(frm, text='enter cart name:').grid(
                row=0, column=0, columnspan=2, sticky='snew')
            nameEnt = Entry(
                frm,
                font=RFONT,
                textvariable=cart_name,
                validate="key", validatecommand=self.vlen)
            nameEnt.grid(
                row=1, column=0, columnspan=2, sticky='snew')
            Label(frm, text=system).grid(
                row=2, column=0, sticky='snew', pady=5)
            Label(frm, text=profile).grid(
                row=3, column=0, sticky='snew', pady=5)

            progbar = Progressbar(
                frm,
                mode='determinate',
                orient=HORIZONTAL,)
            progbar.grid(
                row=3, column=0, columnspan=2, sticky='snew', pady=10)
            progbar['maximum'] = c + 1

            okBtn = Button(
                frm,
                text='create',
                command=lambda: self.import_sheet(
                    top, progbar, cart_name.get(),
                    self.system.get(), profile_id))
            okBtn.grid(
                row=4, column=0, sticky='snew', padx=25, pady=10)
            cancelBtn = Button(
                frm,
                text='cancel',
                command=top.destroy)
            cancelBtn.grid(
                row=4, column=1, sticky='snew', padx=25, pady=10)

            top.wait_window()

    def import_sheet(
            self, top_widget, progbar, cart_name,
            system_id, profile_id):
        if cart_name:
            data = create_resource_reader(
                self.record, self.fh)
            try:
                create_cart(
                    cart_name, system_id, profile_id, data,
                    progbar)
            except BabelError as e:
                messagebox.showerror('Database Error', e)
            finally:
                top_widget.destroy()

    def update_sheet_templates(self):
        if self.profile.get() == 'All users':
                kwargs = {}
        else:
            kwargs = {
                'user_id': get_id_from_index(
                    self.profile.get(), self.profile_idx)}
        templates = get_names(Sheet, **kwargs)
        self.sheetCbx['values'] = templates
        self.edit_mode = False
        self.sheetCbx['state'] = 'readonly'

    def reset_template(self):
        self.record = None
        self.sheet_name.set('')
        self.edit_mode = False
        self.created.set('')
        self.updated.set('')
        self.header_row.set('')
        self.title_col.set('')
        self.add_title_col.set('')
        self.author_col.set('')
        self.series_col.set('')
        self.publisher_col.set('')
        self.pub_date_col.set('')
        self.pub_place_col.set('')
        self.summary_col.set('')
        self.isbn_col.set('')
        self.upc_col.set('')
        self.other_no_col.set('')
        self.desc_url_col.set('')
        self.price_list_col.set('')
        self.price_disc_col.set('')
        self.misc_col.set('')
        self.update_sheet_templates()

    def onValidateCol(self, d, i, P, W):
        # %d = Type of action (1=insert, 0=delete, -1 for others)
        # %i = index of char string to be inserted/deleted, or -1
        # %P = value of the entry if the edit is allowed

        valid = True
        if d == '1' and not P.isdigit():
            valid = False
        if int(i) > 1:
            valid = False
        if P == '0' and W == str(self.header_row):
            valid = False
        return valid

    def onValidateName(self, P):
        valid = True
        if len(P) > 50:
            valid = False
        return valid

    def sheet_observer(self, *args):
        if not self.edit_mode:
            if self.profile.get() == 'All users':
                kwargs = {}
            else:
                kwargs = {
                    'user_id': get_id_from_index(
                        self.profile.get(), self.profile_idx)}
            kwargs['name'] = self.sheet_name.get()
            self.record = get_record(Sheet, **kwargs)
            if self.record:
                drec = convert4display(self.record)
                enable_widgets(self.templateFrm.winfo_children())
                self.sheet_name.set(drec.name)
                self.created.set(f'created:{drec.created:%y-%m-%d %H:%M}')
                self.updated.set(f'updated:{drec.updated:%y-%m-%d %H:%M}')
                self.header_row.set(drec.header_row)
                self.title_col.set(drec.title_col)
                self.add_title_col.set(drec.add_title_col)
                self.author_col.set(drec.author_col)
                self.series_col.set(drec.series_col)
                self.publisher_col.set(drec.publisher_col)
                self.pub_date_col.set(drec.pub_date_col)
                self.pub_place_col.set(drec.pub_place_col)
                self.summary_col.set(drec.summary_col)
                self.isbn_col.set(drec.isbn_col)
                self.upc_col.set(drec.upc_col)
                self.other_no_col.set(drec.other_no_col)
                self.price_list_col.set(drec.price_list_col)
                self.price_disc_col.set(drec.price_disc_col)
                self.desc_url_col.set(drec.desc_url_col)
                self.misc_col.set(drec.misc_col)

                disable_widgets(self.templateFrm.winfo_children())
                enable_widgets([self.sheetCbx])
                self.sheetCbx['state'] = 'readonly'
                self.generate_preview()

    def profile_observer(self, *args):
        if self.activeW.get() == "ImportView":
            self.update_sheet_templates()
            disable_widgets(self.templateFrm.winfo_children())
            enable_widgets([self.sheetCbx])
            self.sheetCbx['state'] = 'readonly'
            self.update_sheet_templates()
            self.reset_template()

    def observer(self, *args):
        if self.activeW.get() == 'ImportView':
            disable_widgets(self.templateFrm.winfo_children())
            enable_widgets([self.sheetCbx])
            self.update_sheet_templates()

    def createToolTip(self, widget, text):
        toolTip = ToolTip(widget)

        def enter(event):
            toolTip.showtip(text)

        def leave(event):
            toolTip.hidetip()

        widget.bind('<Enter>', enter)
        widget.bind('<Leave>', leave)
