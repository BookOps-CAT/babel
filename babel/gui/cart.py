import logging
from tkinter import *
from tkinter.ttk import *
from tkinter import messagebox


from errors import BabelError
from data.datastore import Cart, Order, Resource
from gui.data_retriever import (get_names, save_data, get_record,
                                convert4display, delete_data,
                                create_resource_reader, create_cart,
                                get_carts_data)
from gui.fonts import RFONT
from gui.utils import (ToolTip, get_id_from_index, disable_widgets,
                       enable_widgets)


mlogger = logging.getLogger('babel_logger')


class CartView(Frame):
    """
    Gui for creating and managing order cart
    """

    def __init__(self, parent, controller, **app_data):
        self.parent = parent
        Frame.__init__(self, parent)
        self.controller = controller
        self.app_data = app_data
        self.cart_id = app_data['active_id']
        self.activeW = app_data['activeW']
        self.activeW.trace('w', self.observer)
        self.system = app_data['system']
        self.system.trace('w', self.observer)
        self.profile = app_data['profile']
        self.profile.trace('w', self.observer)
        max_height = int((self.winfo_screenheight() - 200))

        # local variables
        self.cart_name = StringVar()
        self.dist_set = StringVar()
        self.lang = StringVar()
        self.vendor = StringVar()
        self.fund = StringVar()
        self.mattype = StringVar()
        self.price = StringVar()
        self.discount = StringVar()
        self.audn = StringVar()

        # icons
        copyImg = self.app_data['img']['copy']
        editImg = self.app_data['img']['edit']
        deleteImg = self.app_data['img']['delete']
        helpImg = self.app_data['img']['help']
        viewImg = self.app_data['img']['view']
        saveImg = self.app_data['img']['save']
        previousImg = self.app_data['img']['previous']
        nextImg = self.app_data['img']['next']
        startImg = self.app_data['img']['start']
        endImg = self.app_data['img']['end']

        # action buttons frame
        self.actionFrm = Frame(self)
        self.actionFrm.grid(
            row=0, column=0, sticky='snew', padx=5, pady=10)

        self.editBtn = Button(
            self.actionFrm,
            image=editImg,
            command=self.rename_cart)
        self.editBtn.image = editImg
        self.editBtn.grid(
            row=0, column=0, sticky='sw', padx=10, pady=5)
        self.createToolTip(self.editBtn, 'edit cart name')

        self.copyBtn = Button(
            self.actionFrm,
            image=copyImg,
            command=self.copy_cart)
        self.copyBtn.image = copyImg
        self.copyBtn.grid(
            row=1, column=0, sticky='sw', padx=10, pady=5)
        self.createToolTip(self.copyBtn, 'copy entire cart')

        self.deleteBtn = Button(
            self.actionFrm,
            image=deleteImg,
            command=self.delete_cart)
        self.deleteBtn.image = deleteImg
        self.deleteBtn.grid(
            row=2, column=0, sticky='sw', padx=10, pady=5)
        self.createToolTip(self.deleteBtn, 'delete cart')

        self.helpBtn = Button(
            self.actionFrm,
            image=helpImg,
            command=self.help)
        self.helpBtn.image = helpImg
        self.helpBtn.grid(
            row=3, column=0, sticky='sw', padx=10, pady=5)
        self.createToolTip(self.helpBtn, 'help')

        self.globdataFrm = Frame(self, relief='groove')
        self.globdataFrm.grid(
            row=0, column=1, sticky='snew', padx=5, pady=10)

        # register cart name validation
        self.vlen = (self.register(self.onValidateName),
                     '%i', '%W')

        Label(self.globdataFrm, text='cart name:').grid(
            row=0, column=0, columnspan=2, sticky='nsw', padx=5, pady=2)
        self.cartEnt = Entry(
            self.globdataFrm,
            textvariable=self.cart_name,
            font=RFONT,
            width=27,
            validate="key", validatecommand=self.vlen)
        self.cartEnt.grid(
            row=1, column=0, columnspan=2, sticky='snw', padx=5, pady=2)

        Label(self.globdataFrm, text='use distribution:').grid(
            row=2, column=0, columnspan=2, sticky='nsw', padx=5, pady=2)
        self.distCbx = Combobox(
            self.globdataFrm,
            font=RFONT,
            width=25,
            textvariable=self.dist_set)
        self.distCbx.grid(
            row=3, column=0, columnspan=2, sticky='snw', padx=5, pady=2)
        self.distCbx['state'] = 'readonly'

        Label(self.globdataFrm, text='language:').grid(
            row=4, column=0, sticky='snw', padx=5, pady=2)
        self.langCbx = Combobox(
            self.globdataFrm,
            font=RFONT,
            width=10,
            textvariable=self.lang)
        self.langCbx.grid(
            row=4, column=1, sticky='snw', padx=5, pady=2)
        self.langCbx['state'] = 'readonly'

        Label(self.globdataFrm, text='vendor:').grid(
            row=5, column=0, sticky='snw', padx=5, pady=2)
        self.vendorCbx = Combobox(
            self.globdataFrm,
            font=RFONT,
            width=10,
            textvariable=self.vendor)
        self.vendorCbx.grid(
            row=5, column=1, sticky='snw', padx=5, pady=2)
        self.vendorCbx['state'] = 'readonly'

        Label(self.globdataFrm, text='mat.type').grid(
            row=6, column=0, sticky='nsw', padx=5, pady=2)
        self.mattypeCbx = Combobox(
            self.globdataFrm,
            font=RFONT,
            width=10,
            textvariable=self.mattype)
        self.mattypeCbx.grid(
            row=6, column=1, sticky='snw', padx=5, pady=2)
        self.mattypeCbx['state'] = 'readonly'

        Label(self.globdataFrm, text='fund:').grid(
            row=7, column=0, sticky='snw', padx=5, pady=2)
        self.fundCbx = Combobox(
            self.globdataFrm,
            font=RFONT,
            width=10,
            textvariable=self.fund)
        self.fundCbx.grid(
            row=7, column=1, sticky='snw', padx=5, pady=2)
        self.fundCbx['state'] = 'readonly'

        Label(self.globdataFrm, text='audience:').grid(
            row=8, column=0, sticky='snw', padx=5, pady=2)
        self.audnCbx = Combobox(
            self.globdataFrm,
            font=RFONT,
            width=10,
            textvariable=self.audn)
        self.audnCbx.grid(
            row=8, column=1, sticky='snw', padx=5, pady=2)
        self.audnCbx['state'] = 'readonly'

        Label(self.globdataFrm, text='def.price:').grid(
            row=9, column=0, sticky='snw', padx=5, pady=2)
        self.priceEnt = Entry(
            self.globdataFrm,
            font=RFONT,
            width=10,
            textvariable=self.price,
            validate="key", validatecommand=self.vlen)
        self.priceEnt.grid(
            row=9, column=1, sticky='snw', padx=5, pady=2)

        Label(self.globdataFrm, text='discount').grid(
            row=10, column=0, sticky='snw', padx=5, pady=2)
        self.discEnt = Entry(
            self.globdataFrm,
            font=RFONT,
            width=10,
            textvariable=self.discount,
            validate="key", validatecommand=self.vlen)
        self.discEnt.grid(
            row=10, column=1, sticky='snw', padx=5, pady=2)

        self.applyBtn = Button(
            self.globdataFrm,
            text='apply',
            command=self.apply_globals)
        self.applyBtn.grid(
            row=11, column=0, columnspan=2, sticky='snew', padx=70, pady=10)

        self.navFrm = Label(self.globdataFrm)
        self.navFrm.grid(
            row=15, column=0, columnspan=2, sticky='snew', padx=10, pady=10)

        self.dispLbl = Label(self.navFrm, text='1 ouf 100 displayed')
        self.dispLbl.grid(
            row=0, column=0, columnspan=4, sticky='snew', padx=5, pady=5)

        Label(self.navFrm, text='24 titles').grid(
            row=1, column=0, columnspan=4, sticky='snew', padx=5, pady=5)
        Label(self.navFrm, text='62 copies').grid(
            row=2, column=0, columnspan=4, sticky='snew', padx=5, pady=5)
        Label(self.navFrm, text='total $: 1,234').grid(
            row=3, column=0, columnspan=4, sticky='snew', padx=5, pady=5)

        self.startBtn = Button(
            self.navFrm,
            image=startImg,
            command=self.nav_start)
        self.startBtn.image = startImg
        self.startBtn.grid(
            row=4, column=0, sticky='sw', padx=2, pady=5)

        self.previousBtn = Button(
            self.navFrm,
            image=previousImg,
            command=self.nav_previous)
        self.previousBtn.image = previousImg
        self.previousBtn.grid(
            row=4, column=1, sticky='sw', padx=2, pady=5)

        self.nextBtn = Button(
            self.navFrm,
            image=nextImg,
            command=self.nav_next)
        self.nextBtn.image = nextImg
        self.nextBtn.grid(
            row=4, column=2, sticky='sw', padx=2, pady=5)

        self.endBtn = Button(
            self.navFrm,
            image=endImg,
            command=self.nav_end)
        self.endBtn.image = endImg
        self.endBtn.grid(
            row=4, column=3, sticky='sw', padx=2, pady=5)

        # individual order data
        self.ordsFrm = LabelFrame(self.globdataFrm, text='orders')
        self.ordsFrm.grid(
            row=0, column=2, rowspan=40, sticky='snew', padx=10, pady=5)

        self.xscrollbar = Scrollbar(self.ordsFrm, orient=HORIZONTAL)
        self.xscrollbar.grid(
            row=0, column=0, columnspan=7, sticky='nwe')
        self.yscrollbar = Scrollbar(self.ordsFrm, orient=VERTICAL)
        self.yscrollbar.grid(
            row=0, column=0, rowspan=40, sticky='nse', pady=5)
        self.preview_base = Canvas(
            self.ordsFrm, bg='gray',
            height=max_height,
            width=800,
            xscrollcommand=self.xscrollbar.set,
            yscrollcommand=self.yscrollbar.set)
        self.preview_base.grid(
            row=1, column=1, rowspan=40, columnspan=7, sticky='nwe')
        self.preview()

    def rename_cart(self):
        pass

    def copy_cart(self):
        pass

    def delete_cart(self):
        pass

    def help(self):
        pass

    def apply_globals(self):
        pass

    def nav_start(self):
        pass

    def nav_end(self):
        pass

    def nav_previous(self):
        pass

    def nav_next(self):
        pass

    def observer(self, *args):
        if self.activeW.get() == 'CartView':
            cart = get_record(Cart, did=self.cart_id.get())
            self.cart_name.set(cart.name)

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

    def onValidateName(self, i, W):
        valid = True
        if W == str(self.cartEnt):
            if int(i) >= 49:
                valid = False
        if W == str(self.priceEnt):
            pass
        if W == str(self.discEnt):
            pass
        return valid

    def createToolTip(self, widget, text):
        toolTip = ToolTip(widget)

        def enter(event):
            toolTip.showtip(text)

        def leave(event):
            toolTip.hidetip()

        widget.bind('<Enter>', enter)
        widget.bind('<Leave>', leave)
