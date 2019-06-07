import logging
import shelve
from tkinter import *
from tkinter.ttk import *
from tkinter import messagebox, filedialog

from PIL import Image, ImageTk


from errors import BabelError
from data.datastore import Resource, Sheet
from gui.fonts import RFONT
from gui.utils import ToolTip
from paths import USER_DATA, MY_DOCS


from ingest.xlsx import OrderDataReader

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
        self.profile = app_data['profile']
        self.profile.trace('w', self.profile_observer)
        self.profile_idx = app_data['profile_idx']
        list_height = int((self.winfo_screenheight() - 100) / 25)

        # variables
        self.sheet_name = StringVar()
        self.header_row = StringVar()
        self.title_col = StringVar()
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

        self.actionFrm = Frame(self)
        self.actionFrm.grid(
            row=0, column=0, sticky='snew', padx=10, pady=10)

        # action buttons
        img = Image.open('./icons/Action-edit-add-iconM.png')
        addImg = ImageTk.PhotoImage(img)
        self.addBtn = Button(
            self.actionFrm,
            image=addImg,
            command=self.add_data)
        self.addBtn.image = addImg
        self.addBtn.grid(
            row=0, column=0, sticky='sw', padx=20, pady=10)
        self.createToolTip(self.addBtn, 'new sheet template')

        img = Image.open('./icons/Action-reload-iconM.png')
        editImg = ImageTk.PhotoImage(img)
        self.editBtn = Button(
            self.actionFrm,
            image=editImg,
            command=self.edit_data)
        self.editBtn.image = editImg
        self.editBtn.grid(
            row=1, column=0, sticky='sw', padx=20, pady=5)
        self.createToolTip(self.editBtn, 'edit sheet template')

        img = Image.open('./icons/Action-cancel-iconM.png')
        deleteImg = ImageTk.PhotoImage(img)
        self.deleteBtn = Button(
            self.actionFrm,
            image=deleteImg,
            command=self.delete_data)
        self.deleteBtn.image = deleteImg
        self.deleteBtn.grid(
            row=2, column=0, sticky='sw', padx=20, pady=5)
        self.createToolTip(self.deleteBtn, 'delete sheet template')

        img = Image.open('./icons/Action-ok-iconM.png')
        saveImg = ImageTk.PhotoImage(img)
        self.saveBtn = Button(
            self.actionFrm,
            image=saveImg,
            command=self.insert_or_update_data)
        self.saveBtn.image = saveImg
        self.saveBtn.grid(
            row=3, column=0, sticky='sw', padx=20, pady=5)
        self.createToolTip(self.saveBtn, 'save sheet template')

        img = Image.open('./icons/Action-button-info-iconM.png')
        helpImg = ImageTk.PhotoImage(img)
        self.helpBtn = Button(
            self.actionFrm,
            image=helpImg,
            command=self.help)
        self.helpBtn.image = helpImg
        self.helpBtn.grid(
            row=4, column=0, sticky='sw', padx=20, pady=5)
        self.createToolTip(self.helpBtn, 'help')

        # sheet template data frame
        self.templateFrm = LabelFrame(self, text='sheet template')
        self.templateFrm.grid(
            row=0, column=1, sticky='snew', padx=5, pady=10)

        self.sheetCbx = Combobox(
            self.templateFrm,
            font=RFONT,
            textvariable=self.sheet_name)
        self.sheetCbx.grid(
            row=0, column=0, columnspan=2, sticky='snew', padx=5, pady=5)

        Label(self.templateFrm, text='header row:').grid(
            row=1, column=0, sticky='snw', padx=5, pady=2)
        self.headerrowEnt = Entry(
            self.templateFrm,
            font=RFONT,
            width=5,
            textvariable=self.header_row)
        self.headerrowEnt.grid(
            row=1, column=1, sticky='snw', padx=5, pady=2)

        Label(self.templateFrm, text='title column:').grid(
            row=2, column=0, sticky='snw', padx=5, pady=2)
        self.titlecolEnt = Entry(
            self.templateFrm,
            font=RFONT,
            width=5,
            textvariable=self.title_col)
        self.titlecolEnt.grid(
            row=2, column=1, sticky='snw', padx=5, pady=2)

        Label(self.templateFrm, text='author column:').grid(
            row=3, column=0, sticky='snw', padx=5, pady=2)
        self.authorcolEnt = Entry(
            self.templateFrm,
            font=RFONT,
            width=5,
            textvariable=self.author_col)
        self.authorcolEnt.grid(
            row=3, column=1, sticky='snw', padx=5, pady=2)

        Label(self.templateFrm, text='series column:').grid(
            row=4, column=0, sticky='snw', padx=5, pady=2)
        self.seriescolEnt = Entry(
            self.templateFrm,
            font=RFONT,
            width=5,
            textvariable=self.series_col)
        self.seriescolEnt.grid(
            row=4, column=1, sticky='snw', padx=5, pady=2)

        Label(self.templateFrm, text='publisher column:').grid(
            row=5, column=0, sticky='snw', padx=5, pady=2)
        self.publishercolEnt = Entry(
            self.templateFrm,
            font=RFONT,
            width=5,
            textvariable=self.publisher_col)
        self.publishercolEnt.grid(
            row=5, column=1, sticky='snw', padx=5, pady=2)

        Label(self.templateFrm, text='pub. date column:').grid(
            row=6, column=0, sticky='snw', padx=5, pady=2)
        self.pubdatecolEnt = Entry(
            self.templateFrm,
            font=RFONT,
            width=5,
            textvariable=self.pub_date_col)
        self.pubdatecolEnt.grid(
            row=6, column=1, sticky='snw', padx=5, pady=2)

        Label(self.templateFrm, text='pub. place column:').grid(
            row=7, column=0, sticky='snw', padx=5, pady=2)
        self.pubplacecolEnt = Entry(
            self.templateFrm,
            font=RFONT,
            width=5,
            textvariable=self.pub_place_col)
        self.pubplacecolEnt.grid(
            row=7, column=1, sticky='snw', padx=5, pady=2)

        Label(self.templateFrm, text='summary column:').grid(
            row=8, column=0, sticky='snw', padx=5, pady=2)
        self.summarycolEnt = Entry(
            self.templateFrm,
            font=RFONT,
            width=5,
            textvariable=self.summary_col)
        self.summarycolEnt.grid(
            row=8, column=1, sticky='snw', padx=5, pady=2)

        Label(self.templateFrm, text='ISBN column:').grid(
            row=9, column=0, sticky='snw', padx=5, pady=2)
        self.isbncolEnt = Entry(
            self.templateFrm,
            font=RFONT,
            width=5,
            textvariable=self.isbn_col)
        self.isbncolEnt.grid(
            row=9, column=1, sticky='snw', padx=5, pady=2)

        Label(self.templateFrm, text='UPC column:').grid(
            row=10, column=0, sticky='snw', padx=5, pady=2)
        self.upccolEnt = Entry(
            self.templateFrm,
            font=RFONT,
            width=5,
            textvariable=self.upc_col)
        self.upccolEnt.grid(
            row=10, column=1, sticky='snw', padx=5, pady=2)

        Label(self.templateFrm, text='other no. column:').grid(
            row=11, column=0, sticky='snw', padx=5, pady=2)
        self.othernocolEnt = Entry(
            self.templateFrm,
            font=RFONT,
            width=5,
            textvariable=self.other_no_col)
        self.othernocolEnt.grid(
            row=11, column=1, sticky='snw', padx=5, pady=2)

        Label(self.templateFrm, text='list price column:').grid(
            row=12, column=0, sticky='snw', padx=5, pady=2)
        self.pricelistcolEnt = Entry(
            self.templateFrm,
            font=RFONT,
            width=5,
            textvariable=self.price_list_col)
        self.pricelistcolEnt.grid(
            row=12, column=1, sticky='snw', padx=5, pady=2)

        Label(self.templateFrm, text='discount price col.:').grid(
            row=13, column=0, sticky='snw', padx=5, pady=2)
        self.pricedisccolEnt = Entry(
            self.templateFrm,
            font=RFONT,
            width=5,
            textvariable=self.price_disc_col)
        self.pricedisccolEnt.grid(
            row=13, column=1, sticky='snw', padx=5, pady=2)

        Label(self.templateFrm, text='URL column:').grid(
            row=14, column=0, sticky='snw', padx=5, pady=2)
        self.urldesccolEnt = Entry(
            self.templateFrm,
            font=RFONT,
            width=5,
            textvariable=self.desc_url_col)
        self.urldesccolEnt.grid(
            row=14, column=1, sticky='snw', padx=5, pady=2)

        Label(self.templateFrm, text='misc column:').grid(
            row=15, column=0, sticky='snw', padx=5, pady=2)
        self.misccolEnt = Entry(
            self.templateFrm,
            font=RFONT,
            width=5,
            textvariable=self.misc_col)
        self.misccolEnt.grid(
            row=15, column=1, sticky='snw', padx=5, pady=2)

        # sheet frame
        self.sheetFrm = LabelFrame(self, text='sheet')
        self.sheetFrm.grid(
            row=0, column=2, sticky='snew', padx=5, pady=10)

        img = Image.open('./icons/Action-viewmag-iconM.png')
        loadImg = ImageTk.PhotoImage(img)
        self.loadBtn = Button(
            self.sheetFrm,
            image=loadImg,
            text='load',
            compound=TOP,
            width=10,
            command=self.load_sheet)
        self.loadBtn.image = loadImg
        self.loadBtn.grid(
            row=0, column=0, sticky='snw', padx=50, pady=20)

        img = Image.open('./icons/App-ark-iconM.png')
        importImg = ImageTk.PhotoImage(img)
        self.importBtn = Button(
            self.sheetFrm,
            image=importImg,
            text='import',
            compound=TOP,
            width=10,
            command=self.import_sheet)
        self.importBtn.image = importImg
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

    def generate_preview(self, data):
        # clear and recreate frame
        self.reset_preview()
        # self.rowLst = tk.Listbox(
        #     self.preview_frame, font=RF,
        #     width=3,
        #     height=self.row_qnt + 1)
        # self.rowLst.grid(
        #     row=1, column=1, sticky='nsw')

        # for number in range(0, self.row_qnt + 1):
        #     self.rowLst.insert(tk.END, number)
        # c = 0
        # r = 0
        # for column in range(0, self.col_qnt):
        #     self.col_name = tk.Listbox(
        #         self.preview_frame, font=RF,
        #         width=15,
        #         height=self.row_qnt + 1)
        #     self.col_name.grid(
        #         row=1, column=c + 2, sticky='nsw')
        #     self.col_name.insert(tk.END, self.column_letters[c])
        #     for row in data:
        #         if row[r] is None:
        #             self.col_name.insert(tk.END, '')
        #         else:
        #             self.col_name.insert(tk.END, row[r])
        #     r += 1
        #     c += 1

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
        pass

    def edit_data(self, *args):
        pass

    def delete_data(self, *args):
        pass

    def insert_or_update_data(self, *args):
        pass

    def help(self):
        pass

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
                print(fh)

        user_data.close()

    def import_sheet(self):
        pass

    def profile_observer(self, *args):
        pass

    def observer(self, *args):
        if self.activeW.get() == 'ImportView':
            pass

    def createToolTip(self, widget, text):
        toolTip = ToolTip(widget)

        def enter(event):
            toolTip.showtip(text)

        def leave(event):
            toolTip.hidetip()

        widget.bind('<Enter>', enter)
        widget.bind('<Leave>', leave)
