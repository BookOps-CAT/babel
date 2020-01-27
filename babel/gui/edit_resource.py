import logging
from tkinter import *
from tkinter.ttk import *
from tkinter import messagebox


from data.datastore import Resource
from data.transactions_cart import (add_resource, update_resource,
                                    convert_price2datastore)
from errors import BabelError
from gui.data_retriever import (convert4display,
                                convert4datastore,
                                get_record)
from gui.fonts import RFONT
from gui.utils import BusyManager
from logging_settings import LogglyAdapter


mlogger = LogglyAdapter(logging.getLogger('babel'), None)


class EditResourceWidget:
    """
    Widget for editing Resource records
    """

    def __init__(self, parent, cart_id=None, resource_id=None, **app_data):
        self.parent = parent
        self.app_data = app_data
        self.cart_id = cart_id
        self.rec_id = resource_id
        self.rec = None

        top = self.top = Toplevel(master=self.parent)
        top.title('Editing resource')
        self.cur_manager = BusyManager(self.top)

        # icons
        saveImg = self.app_data['img']['save']
        closeImg = self.app_data['img']['delete']

        # variables
        self.title = StringVar()
        self.add_title = StringVar()
        self.author = StringVar()
        self.series = StringVar()
        self.publisher = StringVar()
        self.pub_date = StringVar()
        self.pub_place = StringVar()
        self.isbn = StringVar()
        self.upc = StringVar()
        self.other_no = StringVar()
        self.price_list = StringVar()
        self.price_disc = StringVar()
        self.misc = StringVar()

        # register entries validation
        self.vlam = (self.top.register(self.onValidatePrice),
                     '%i', '%d', '%P')
        self.vlis = (self.top.register(self.onValidateIsbn),
                     '%i', '%d', '%P')
        self.vldt = (self.top.register(self.onValidateDate),
                     '%i', '%d', '%P')
        self.vlup = (self.top.register(self.onValidateUpc),
                     '%i', '%d', '%P')

        # layout
        frm = Frame(top)
        frm.grid(row=0, column=0, sticky='snew', padx=10, pady=10)
        frm.columnconfigure(3, minsize=100)

        Label(frm, text='title:').grid(
            row=0, column=0, sticky='snw')
        titleEnt = Entry(
            frm,
            font=RFONT,
            textvariable=self.title)
        titleEnt.grid(
            row=0, column=1, columnspan=3, sticky='snew', padx=5, pady=5)

        Label(frm, text='extra title:').grid(
            row=1, column=0, sticky='snw')
        addtitleEnt = Entry(
            frm,
            font=RFONT,
            textvariable=self.add_title)
        addtitleEnt.grid(
            row=1, column=1, columnspan=3, sticky='snew', padx=5, pady=5)

        Label(frm, text='author:').grid(
            row=2, column=0, sticky='snw')
        authorEnt = Entry(
            frm,
            font=RFONT,
            textvariable=self.author)
        authorEnt.grid(
            row=2, column=1, columnspan=3, sticky='snew', padx=5, pady=5)

        Label(frm, text='series').grid(
            row=3, column=0, sticky='snw')
        seriesEnt = Entry(
            frm,
            font=RFONT,
            textvariable=self.series)
        seriesEnt.grid(
            row=3, column=1, columnspan=3, sticky='snew', padx=5, pady=5)

        Label(frm, text='publisher:').grid(
            row=4, column=0, sticky='snw')
        publisherEnt = Entry(
            frm,
            font=RFONT,
            textvariable=self.publisher)
        publisherEnt.grid(
            row=4, column=1, columnspan=3, sticky='snew', padx=5, pady=5)

        Label(frm, text='date:').grid(
            row=5, column=0, sticky='snw')
        pubdateEnt = Entry(
            frm,
            font=RFONT,
            textvariable=self.pub_date,
            validate="key", validatecommand=self.vldt)
        pubdateEnt.grid(
            row=5, column=1, sticky='snew', padx=5, pady=5)

        Label(frm, text='place:').grid(
            row=5, column=2, sticky='sne')
        pubplaceEnt = Entry(
            frm,
            font=RFONT,
            textvariable=self.pub_place)
        pubplaceEnt.grid(
            row=5, column=3, sticky='snew', padx=5, pady=5)

        Label(frm, text='ISBN').grid(
            row=6, column=0, sticky='snw')
        isbnEnt = Entry(
            frm,
            font=RFONT,
            textvariable=self.isbn,
            validate="key", validatecommand=self.vlis)
        isbnEnt.grid(
            row=6, column=1, sticky='snew', padx=5, pady=5)

        Label(frm, text='UPC:').grid(
            row=6, column=2, sticky='sne')
        upcEnt = Entry(
            frm,
            font=RFONT,
            textvariable=self.upc,
            validate="key", validatecommand=self.vlup)
        upcEnt.grid(
            row=6, column=3, sticky='snew', padx=5, pady=5)

        Label(frm, text='Other #:').grid(
            row=7, column=0, sticky='snw')
        othernoEnt = Entry(
            frm,
            font=RFONT,
            textvariable=self.other_no)
        othernoEnt.grid(
            row=7, column=1, sticky='snew', padx=5, pady=5)

        Label(frm, text='misc.:').grid(
            row=7, column=2, sticky='sne')
        miscEnt = Entry(
            frm,
            font=RFONT,
            textvariable=self.misc)
        miscEnt.grid(
            row=7, column=3, sticky='snew', padx=5, pady=5)

        Label(frm, text='list price ($):').grid(
            row=8, column=0, sticky='snw')
        pricelistEnt = Entry(
            frm,
            font=RFONT,
            textvariable=self.price_list,
            validate="key", validatecommand=self.vlam)
        pricelistEnt.grid(
            row=8, column=1, sticky='snew', padx=5, pady=5)

        Label(frm, text='discount price ($):').grid(
            row=8, column=2, sticky='sne')
        pricediscEnt = Entry(
            frm,
            font=RFONT,
            textvariable=self.price_disc,
            validate="key", validatecommand=self.vlam)
        pricediscEnt.grid(
            row=8, column=3, sticky='snew', padx=5, pady=5)

        Label(frm, text='summary:').grid(
            row=9, column=0, sticky='snw')
        self.summaryTxt = Text(
            frm,
            font=RFONT,
            wrap='word',
            width=50,
            height=5)
        self.summaryTxt.grid(
            row=9, column=1, rowspan=3, columnspan=3,
            sticky='snew', padx=5, pady=5)

        saveBtn = Button(
            frm,
            image=saveImg,
            command=self.save_resource)
        saveBtn.grid(
            row=12, column=1, sticky='sne', padx=5, pady=10)

        cancelBtn = Button(
            frm,
            image=closeImg,
            command=self.top.destroy)
        cancelBtn.grid(
            row=12, column=2, sticky='snw', padx=5, pady=10)

        if self.rec_id is not None:
            # populate for edit
            self.get_data()

    def get_data(self):
        self.rec = get_record(Resource, did=self.rec_id)
        rec = convert4display(self.rec)
        self.title.set(rec.title)
        self.add_title.set(rec.add_title)
        self.author.set(rec.author)
        self.series.set(rec.series)
        self.publisher.set(rec.publisher)
        self.pub_date.set(rec.pub_date)
        self.pub_place.set(rec.pub_place)
        self.isbn.set(rec.isbn)
        self.upc.set(rec.upc)
        self.other_no.set(rec.other_no)
        self.price_list.set(rec.price_list)
        self.price_disc.set(rec.price_disc)
        self.misc.set(rec.misc)

        self.summaryTxt.insert('1.0', rec.summary)

    def save_resource(self):
        if self.title.get():
            kwargs = dict(
                title=self.title.get(),
                add_title=self.add_title.get(),
                author=self.author.get(),
                series=self.series.get(),
                publisher=self.publisher.get(),
                pub_date=self.pub_date.get(),
                pub_place=self.pub_place.get(),
                summary=self.summaryTxt.get(
                    '1.0', END).replace('\n', ' ').replace('\t', ''),
                isbn=self.isbn.get(),
                upc=self.upc.get(),
                other_no=self.other_no.get(),
                price_list=convert_price2datastore(self.price_list.get()),
                price_disc=convert_price2datastore(self.price_disc.get()),
                misc=self.misc.get()
            )

            kwargs = convert4datastore(kwargs)

            try:
                if self.rec_id is not None:
                    update_resource(self.rec_id, **kwargs)
                    self.top.destroy()
                else:
                    add_resource(cart_id=self.cart_id, **kwargs)
                    self.top.destroy()
            except BabelError as e:
                messagebox.showerror(
                    'Datastore Error', e, parent=self.top)

        else:
            messagebox.showwarning(
                'Input Error',
                'Resource must have title.', parent=self.top)

    def onValidateIsbn(self, i, d, P):
        mlogger.debug(
            f'onValidateIsbn entered: {P}, index: {i}, action {d}')
        valid = True
        if i == '13':
            # ISBN no longer than 13 chr
            valid = False
        if int(i) < 13 and d == '1':
            if i == '9':
                # 10-digit ISBN case
                if not P[int(i)].isdigit() and P[(int(i))].lower() != 'x':
                    mlogger.debug('Invalid 10-digit ISBN')
                    valid = False
            else:
                # 13-digit ISBNs
                if not P.isdigit():
                    mlogger.debug('Invalid 13-digit ISBN')
                    valid = False

        return valid

    def onValidateDate(self, i, d, P):
        mlogger.debug(
            f'onValidateDate entered: {P}, index: {i}, action: {d}')
        valid = True
        if int(i) > 3:
            valid = False
        if d == '1' and not P.isdigit():
            valid = False
        return valid

    def onValidateUpc(self, i, d, P):
        mlogger.debug('onValidateUpc entered: {p}, index: {i}, action: {d}')
        valid = True
        if d == '1' and not P.isdigit():
            valid = False
        return valid

    def onValidatePrice(self, i, d, P):
        mlogger.debug(
            f'onValidatePrice entered: {P}, index: {i}, action {d}')
        valid = True
        # case 1
        if i == '0' and not P.isdigit() and d == '1':
            mlogger.debug('Price validation: Failed case 1')
            valid = False
        # case 2
        if d == '1' and int(i) > 0:
            e = P[int(i)]
            if not e.isdigit() and e != '.':
                mlogger.debug('Price validation: Failed case 2')
                valid = False
        return valid
