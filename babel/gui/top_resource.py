import logging
from tkinter import *
from tkinter.ttk import *
from tkinter import messagebox


from data.datastore import Resource
from errors import BabelError
from gui.data_retriever import convert4display, get_record
from gui.fonts import RFONT
from gui.utils import BusyManager


mlogger = logging.getLogger('babel_logger')


class EditResourceWidget:
    """
    Widget for editing Resource records
    """

    def __init__(self, parent, resource_id, **app_data):
        self.parent = parent
        self.app_data = app_data
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
        self.summary = StringVar()
        self.isbn = StringVar()
        self.upc = StringVar()
        self.other_no = StringVar()
        self.price_list = StringVar()
        self.price_disc = StringVar()
        self.misc = StringVar()

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
            textvariable=self.pub_date)
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
            textvariable=self.isbn)
        isbnEnt.grid(
            row=6, column=1, sticky='snew', padx=5, pady=5)

        Label(frm, text='UPC:').grid(
            row=6, column=2, sticky='sne')
        upcEnt = Entry(
            frm,
            font=RFONT,
            textvariable=self.upc)
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
            textvariable=self.price_list)
        pricelistEnt.grid(
            row=8, column=1, sticky='snew', padx=5, pady=5)

        Label(frm, text='discount price ($):').grid(
            row=8, column=2, sticky='sne')
        pricediscEnt = Entry(
            frm,
            font=RFONT,
            textvariable=self.price_disc)
        pricediscEnt.grid(
            row=8, column=3, sticky='snew', padx=5, pady=5)

        Label(frm, text='summary:').grid(
            row=9, column=0, sticky='snw')
        summaryTxt = Text(
            frm,
            font=RFONT,
            wrap='word',
            width=50,
            height=5)
        summaryTxt.grid(
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
        self.summary.set(rec.summary)
        self.isbn.set(rec.isbn)
        self.upc.set(rec.upc)
        self.other_no.set(rec.other_no)
        self.price_list.set(rec.price_list)
        self.price_disc.set(rec.price_disc)
        self.misc.set(rec.misc)

    def save_resource(self):
        pass