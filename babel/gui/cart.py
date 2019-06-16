from collections import OrderedDict
from datetime import datetime
import logging
from tkinter import *
from tkinter.ttk import *
from tkinter import messagebox


from errors import BabelError
from data.datastore import (Cart, Order, Resource, Lang, Audn, DistSet,
                            DistGrid, ShelfCode, Vendor, MatType, Fund,
                            Branch, Status)
from gui.data_retriever import (get_names, save_data, get_record,
                                get_records, convert4display,
                                delete_data, delete_data_by_did,
                                create_resource_reader, create_cart,
                                get_carts_data, get_codes, get_orders_by_id,
                                get_order_ids, create_code_index,
                                create_name_index, save_displayed_order_data,
                                update_orders, apply_globals_to_cart,
                                apply_fund_to_cart, save_new_dist_and_grid)
from gui.fonts import RFONT, RBFONT, LFONT, HBFONT
from gui.utils import (ToolTip, get_id_from_index, disable_widgets,
                       enable_widgets, open_url)


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
        self.profile_idx = app_data['profile_idx']
        self.profile.trace('w', self.profile_observer)
        max_height = int((self.winfo_screenheight() - 200))

        # local variables
        self.cart_name = StringVar()
        self.order_ids = []
        self.dist_set = StringVar()
        self.dist_set.trace('w', self.distribution_observer)
        self.dist_id = IntVar()
        self.dist_template = StringVar()
        self.dist_template.trace('w', self.template_observer)
        self.new_dist = StringVar()
        self.grid_template = StringVar()
        self.grid_template.trace('w', self.template_observer)
        self.new_grid = StringVar()
        self.library = StringVar()
        self.status = StringVar()
        self.status.trace('w', self.status_observer)
        self.lang = StringVar()
        self.vendor = StringVar()
        self.mattype = StringVar()
        self.price = StringVar()
        self.discount = StringVar()
        self.audn = StringVar()
        self.poperline = StringVar()
        self.note = StringVar()

        # icons
        copyImg = self.app_data['img']['copy']
        editImg = self.app_data['img']['edit']
        deleteImg = self.app_data['img']['delete']
        helpImg = self.app_data['img']['help']
        saveImg = self.app_data['img']['save']
        previousImg = self.app_data['img']['previous']
        nextImg = self.app_data['img']['next']
        startImg = self.app_data['img']['start']
        endImg = self.app_data['img']['end']
        sierraImg = self.app_data['img']['sierra']
        validationImg = self.app_data['img']['valid']
        fundImgM = self.app_data['img']['fundM']
        self.editImgS = self.app_data['img']['editS']
        self.removeImgS = self.app_data['img']['removeS']
        self.deleteImgS = self.app_data['img']['deleteS']
        self.addImgS = self.app_data['img']['addS']
        self.foundImg = self.app_data['img']['found']
        self.notfoundImg = self.app_data['img']['notfound']
        self.copyImgS = self.app_data['img']['copyS']
        self.saveImgS = self.app_data['img']['saveS']

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

        self.saveBtn = Button(
            self.actionFrm,
            image=saveImg,
            command=self.save_cart)
        self.saveBtn.image = saveImg
        self.saveBtn.grid(
            row=1, column=0, sticky='sw', padx=10, pady=5)
        self.createToolTip(self.saveBtn, 'save cart')

        self.fundBtn = Button(
            self.actionFrm,
            image=fundImgM,
            command=self.show_fund_widget)
        self.fundBtn.image = fundImgM
        self.fundBtn.grid(
            row=2, column=0, sticky='sw', padx=10, pady=5)
        self.createToolTip(self.fundBtn, 'apply funds')

        self.validBtn = Button(
            self.actionFrm,
            image=validationImg,
            command=self.validate_cart)
        # self.validBtn.image = saveImg
        self.validBtn.grid(
            row=3, column=0, sticky='sw', padx=10, pady=5)
        self.createToolTip(self.validBtn, 'validate cart')

        self.copyBtn = Button(
            self.actionFrm,
            image=copyImg,
            command=self.copy_cart)
        self.copyBtn.image = copyImg
        self.copyBtn.grid(
            row=4, column=0, sticky='sw', padx=10, pady=5)
        self.createToolTip(self.copyBtn, 'copy entire cart')

        self.deleteBtn = Button(
            self.actionFrm,
            image=deleteImg,
            command=self.delete_cart)
        self.deleteBtn.image = deleteImg
        self.deleteBtn.grid(
            row=5, column=0, sticky='sw', padx=10, pady=5)
        self.createToolTip(self.deleteBtn, 'delete cart')

        self.sierraBtn = Button(
            self.actionFrm,
            image=sierraImg,
            command=self.search_sierra)
        self.sierraBtn.image = sierraImg
        self.sierraBtn.grid(
            row=6, column=0, sticky='sw', padx=10, pady=5)
        self.createToolTip(self.sierraBtn, 'search Sierra')

        self.helpBtn = Button(
            self.actionFrm,
            image=helpImg,
            command=self.help)
        self.helpBtn.image = helpImg
        self.helpBtn.grid(
            row=7, column=0, sticky='sw', padx=10, pady=5)
        self.createToolTip(self.helpBtn, 'help')

        self.globdataFrm = Frame(self, relief='groove')
        self.globdataFrm.grid(
            row=0, column=1, sticky='snew', padx=20, pady=10)

        # register cart name validation
        self.vlen = (self.register(self.onValidateName),
                     '%i', '%W')
        self.vlqt = (self.register(self.onValidateQty),
                     '%i', '%d', '%P')

        Label(self.globdataFrm, text='cart name:').grid(
            row=0, column=0, columnspan=2, sticky='nsw', padx=5, pady=2)
        self.cartEnt = Entry(
            self.globdataFrm,
            textvariable=self.cart_name,
            font=RFONT,
            width=27,
            validate="key", validatecommand=self.vlen)
        self.cartEnt.grid(
            row=1, column=0, columnspan=2, sticky='snw', padx=6, pady=2)

        Label(self.globdataFrm, text='library:').grid(
            row=2, column=0, sticky='snw', padx=5, pady=2)
        self.libCbx = Combobox(
            self.globdataFrm,
            width=16,
            textvariable=self.library,
            font=RFONT,
            state='readonly',
            values=['branches', 'research'])
        self.libCbx.grid(
            row=2, column=1, sticky='snw', padx=5, pady=2)

        Label(self.globdataFrm, text='status:').grid(
            row=3, column=0, sticky='snw', padx=5, pady=2)
        self.statusCbx = Combobox(
            self.globdataFrm,
            width=16,
            font=RFONT,
            textvariable=self.status,
            state='readonly')
        self.statusCbx.grid(
            row=3, column=1, sticky='snw', padx=5, pady=2)

        Separator(self.globdataFrm, orient=HORIZONTAL).grid(
            row=4, columnspan=2, sticky='snew', padx=5, pady=4)

        Label(self.globdataFrm, text='use distribution:').grid(
            row=5, column=0, columnspan=2, sticky='nsw', padx=5, pady=2)
        self.distCbx = Combobox(
            self.globdataFrm,
            font=RFONT,
            width=25,
            textvariable=self.dist_set,
            state='readonly')
        self.distCbx.grid(
            row=6, column=0, columnspan=2, sticky='snw', padx=5, pady=2)

        Label(self.globdataFrm, text='language:').grid(
            row=7, column=0, sticky='snw', padx=5, pady=2)
        self.langCbx = Combobox(
            self.globdataFrm,
            width=24,
            textvariable=self.lang)
        self.langCbx.grid(
            row=7, column=1, sticky='snw', padx=5, pady=2)
        self.langCbx['state'] = 'readonly'

        Label(self.globdataFrm, text='vendor:').grid(
            row=8, column=0, sticky='snw', padx=5, pady=2)
        self.vendorCbx = Combobox(
            self.globdataFrm,
            width=24,
            textvariable=self.vendor)
        self.vendorCbx.grid(
            row=8, column=1, sticky='snw', padx=5, pady=2)
        self.vendorCbx['state'] = 'readonly'

        Label(self.globdataFrm, text='mat.type').grid(
            row=9, column=0, sticky='nsw', padx=5, pady=2)
        self.mattypeCbx = Combobox(
            self.globdataFrm,
            width=24,
            textvariable=self.mattype)
        self.mattypeCbx.grid(
            row=9, column=1, sticky='snw', padx=5, pady=2)
        self.mattypeCbx['state'] = 'readonly'

        Label(self.globdataFrm, text='audience:').grid(
            row=10, column=0, sticky='snw', padx=5, pady=2)
        self.audnCbx = Combobox(
            self.globdataFrm,
            width=24,
            textvariable=self.audn)
        self.audnCbx.grid(
            row=10, column=1, sticky='snw', padx=5, pady=2)
        self.audnCbx['state'] = 'readonly'

        Label(self.globdataFrm, text='PO:').grid(
            row=11, column=0, sticky='snw', padx=5, pady=2)
        self.poEnt = Entry(
            self.globdataFrm,
            width=24,
            textvariable=self.poperline)
        self.poEnt.grid(
            row=11, column=1, sticky='snw', padx=5, pady=2)

        Label(self.globdataFrm, text='ord. note:').grid(
            row=12, column=0, sticky='snw', padx=5, pady=2)
        self.noteEnt = Entry(
            self.globdataFrm,
            width=24,
            textvariable=self.note)
        self.noteEnt.grid(
            row=12, column=1, sticky='snw', padx=5, pady=2)

        Label(self.globdataFrm, text='def.price:').grid(
            row=13, column=0, sticky='snw', padx=5, pady=2)
        self.priceEnt = Entry(
            self.globdataFrm,
            width=24,
            textvariable=self.price,
            validate="key", validatecommand=self.vlen)
        self.priceEnt.grid(
            row=13, column=1, sticky='snw', padx=5, pady=2)

        Label(self.globdataFrm, text='discount').grid(
            row=14, column=0, sticky='snw', padx=5, pady=2)
        self.discEnt = Entry(
            self.globdataFrm,
            width=24,
            textvariable=self.discount,
            validate="key", validatecommand=self.vlen)
        self.discEnt.grid(
            row=14, column=1, sticky='snw', padx=5, pady=2)

        self.applyBtn = Button(
            self.globdataFrm,
            text='apply',
            command=self.apply_globals)
        self.applyBtn.grid(
            row=15, column=0, columnspan=2, sticky='snew', padx=70, pady=10)

        self.navFrm = Label(self.globdataFrm)
        self.navFrm.grid(
            row=16, column=0, columnspan=2, sticky='snew', padx=10, pady=10)

        self.dispLbl = Label(self.navFrm, text='1 ouf 100 displayed')
        self.dispLbl.grid(
            row=0, column=0, columnspan=4, sticky='snw', padx=5, pady=5)

        Label(self.navFrm, text='24 titles / 62 copies', font=LFONT).grid(
            row=1, column=0, columnspan=4, sticky='snew', padx=5, pady=5)
        Label(self.navFrm, text='206wl: $1,234.23 | 106wl: $923.00', font=LFONT).grid(
            row=2, column=0, columnspan=4, sticky='snw', padx=5, pady=5)

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
            row=0, column=1, columnspan=7, sticky='nwe')
        self.yscrollbar = Scrollbar(self.ordsFrm, orient=VERTICAL)
        self.yscrollbar.grid(
            row=0, column=0, rowspan=41, sticky='nse', pady=5)
        self.preview_base = Canvas(
            self.ordsFrm, bg='gray',
            height=max_height,
            width=830,
            xscrollcommand=self.xscrollbar.set,
            yscrollcommand=self.yscrollbar.set)
        self.preview_base.grid(
            row=1, column=1, rowspan=40, columnspan=7, sticky='nwe')
        self.preview_base.bind_all("<MouseWheel>", self.on_mousewheel)
        self.preview()

    def rename_cart(self):
        if self.cart_name.get():
            self.cartEnt['state'] = '!disable'
            self.statusCbx['state'] = 'readonly'
            print(self.statusCbx['state'])
            if self.system.get() == 2:
                self.libCbx['state'] = 'readonly'

    def save_cart(self):
        try:
            save_displayed_order_data(self.tracker.values())

            # save cart data
            if self.cartEnt['state'] != 'disable':
                kwargs = {}
                kwargs['name'] = self.cartEnt.get().strip()
                if self.system.get() == 2 and self.library.get() != '':
                    if self.library.get() == 'branches':
                        library_id = 1
                    elif self.library.get() == 'research':
                        library_id = 2
                    kwargs['library_id'] = library_id
                rec = get_record(Status, name=self.status.get())
                kwargs['status_id'] = rec.did
                kwargs['updated'] = datetime.now()

                save_data(
                    Cart, self.cart_id.get(), **kwargs)

                # disable cart widgets
                self.cartEnt['state'] = 'disable'
                self.libCbx['state'] = 'disable'
                self.statusCbx['state'] = 'disable'

            messagebox.showinfo('Saving', 'Data has been saved.')
        except BabelError:
            messagebox.showerror('Database error', e)

    def show_fund_widget(self):
        self.fundTop = Toplevel(self)
        self.fundTop.title('Funds')
        # add funds icon here

        frm = Frame(self.fundTop)
        frm.grid(
            row=0, column=0, sticky='snew', padx=10, pady=10)
        frm.columnconfigure(0, minsize=40)

        Label(frm, text='select funds:').grid(
            row=0, column=0, sticky='snw', pady=5)
        applyBtn = Button(
            frm,
            image=self.saveImgS,
            command=lambda: self.apply_funds(listbox, listbox.curselection()))
        applyBtn.grid(
            row=0, column=1, sticky='se', padx=5, pady=10)
        self.createToolTip(applyBtn, 'apply selected funds')

        scrollbar = Scrollbar(frm, orient=VERTICAL)
        scrollbar.grid(
            row=1, column=2, sticky='sne', pady=5)
        listbox = Listbox(
            frm,
            font=RFONT,
            selectmode=EXTENDED,
            yscrollcommand=scrollbar.set)
        listbox.grid(
            row=1, column=0, columnspan=2, sticky='snew', pady=5)
        scrollbar.config(command=listbox.yview)

        for code in sorted(self.fund_idx.values()):
            listbox.insert(END, code)

    def apply_funds(self, listbox, selected):
        values = listbox.get(0, END)
        selected_funds = [values[s] for s in selected]
        apply_fund_to_cart(self.system.get(), self.cart_id.get(), selected_funds)

        # update display
        # maybe it would be better to simply insert
        # new values into appropriate fundCbxes?
        self.preview_frame.destroy()
        self.preview()
        self.display_selected_orders(self.selected_order_ids)

        self.fundTop.destroy()

    def validate_cart(self):
        pass

    def copy_cart(self):
        pass

    def delete_cart(self):
        msg = 'Are you sure you want to delete entire cart?'
        if messagebox.askokcancel('Deletion', msg):
            delete_data_by_did(Cart, self.cart_id.get())
            self.controller.show_frame('CartsView')

    def search_sierra(self):
        pass

    def help(self):
        pass

    def apply_globals(self):
        # updates all order records even ones not displayed
        widgets = {
            'langCbx': self.langCbx,
            'vendorCbx': self.vendorCbx,
            'mattypeCbx': self.mattypeCbx,
            'audnCbx': self.audnCbx,
            'poEnt': self.poEnt,
            'noteEnt': self.noteEnt,
            'priceEnt': self.priceEnt,
            'discEnt': self.discEnt
        }

        apply_globals_to_cart(self.cart_id.get(), widgets)

        self.preview_frame.destroy()
        self.preview()
        self.display_selected_orders(self.selected_order_ids)

    def nav_start(self):
        pass

    def nav_end(self):
        pass

    def nav_previous(self):
        pass

    def nav_next(self):
        pass

    def display_selected_orders(self, order_ids):
        recs = get_orders_by_id(order_ids)
        row = 0
        for orec in recs:
            ntb = self.order_widget(self.preview_frame, row + 1, orec)
            ntb.grid(
                row=row, column=0, sticky='snew', padx=2, pady=2)
            row += 1

    def order_widget(self, parent, no, orec):
        # displays individual notebook for resource & order data

        ntb = Notebook(
            parent,
            width=830)

        # main tab
        mainTab = Frame(ntb)

        res_tracker = self.create_resource_frame(mainTab, orec.resource)
        ord_tracker = self.create_order_frame(mainTab, orec)

        gridFrm = LabelFrame(mainTab, text='grid')
        gridFrm.grid(
            row=1, column=1, sticky='snew', padx=10)
        mlogger.debug('New gridFrm ({}, child of mainTab {})'.format(
            gridFrm.winfo_id(), mainTab.winfo_id()))

        gridCbx = Combobox(
            gridFrm,
            values=sorted(self.grid_idx.values()),
            state='readonly')
        gridCbx.grid(
            row=0, column=0, columnspan=4, sticky='snew', padx=5, pady=2)

        applyBtn = Button(
            gridFrm,
            image=self.saveImgS,
            command=lambda: self.apply_grid_template(ntb.winfo_id()))
        applyBtn.grid(
            row=0, column=5, sticky='snw', padx=5, pady=2)
        applyBtn.image = self.saveImgS

        copyBtn = Button(
            gridFrm,
            image=self.copyImgS,
            command=lambda: self.copy_grid_to_template(ntb.winfo_id()))
        copyBtn.grid(
            row=0, column=6, sticky='snw', padx=5, pady=2)
        copyBtn.image = self.copyImgS

        # grid labels
        Label(gridFrm, text=' branch', font=LFONT).grid(
            row=1, column=0, sticky='se', padx=7)
        Label(gridFrm, text='shelf', font=LFONT).grid(
            row=1, column=1, sticky='sew', padx=10)
        Label(gridFrm, text='qty', font=LFONT).grid(
            row=1, column=2, sticky='sw')
        Label(gridFrm, text='fund', font=LFONT).grid(
            row=1, column=3, sticky='sew', padx=2)

        locsFrm = Frame(gridFrm)
        locsFrm.grid(
            row=2, column=0, columnspan=4, sticky='snew')
        mlogger.debug('New locsFrm ({}, child of gridfrm {})'.format(
            locsFrm.winfo_id(), gridFrm.winfo_id()))

        grids = []
        if orec.locations:
            r = 0
            for loc in orec.locations:
                r += 1

                try:
                    branch = self.branch_idx[loc.branch_id]
                except KeyError:
                    branch = ''
                try:
                    shelf = self.shelf_idx[loc.shelfcode_id]
                except KeyError:
                    shelf = ''
                if loc.qty is None:
                    qty = ''
                else:
                    qty = str(loc.qty)
                try:
                    fund = self.fund_idx[loc.fund_id]
                except KeyError:
                    fund = ''

                grid_tracker = self.create_grid(
                    locsFrm,
                    r,
                    (loc.did, branch, shelf, qty, fund))
                grids.append(grid_tracker)

        else:
            grid_tracker = self.create_grid(locsFrm, 1)
            grids.append(grid_tracker)

        self.create_add_locationBtn(gridFrm)

        # miscellaneous tab
        moreTab = Frame(ntb)
        more_tracker = self.populate_more_tab(
            moreTab, orec)

        ntb.add(mainTab, text=f'title {no}')
        ntb.add(moreTab, text='more')

        self.tracker[ntb.winfo_id()] = {
            'resource': res_tracker,
            'more': more_tracker,
            'order': ord_tracker,
            'grid': {
                'gridCbx': gridCbx,
                'locsFrm': locsFrm,
                'locs': grids
            },
        }

        return ntb

    def populate_more_tab(self, tab, orec):
        title = f'{orec.resource.title} / {orec.resource.author}.'
        Label(tab, text=title, font=RBFONT).grid(
            row=0, column=0, sticky='snw', padx=5, pady=5)
        urlBtn = Button(
            tab, text='link',
            width=10,
            command=lambda aurl=orec.resource.desc_url: open_url(aurl))
        urlBtn.grid(
            row=0, column=0, sticky='sne', padx=20, pady=20)

        scrollbar = Scrollbar(tab, orient=VERTICAL)
        scrollbar.grid(row=1, column=1, rowspan=5, sticky='snw')

        summaryTxt = Text(
            tab,
            font=RFONT,
            wrap='word',
            height=12,
            yscrollcommand=scrollbar.set)
        summaryTxt.grid(
            row=1, column=0, rowspan=5, sticky="snew", padx=10)
        scrollbar['command'] = summaryTxt.yview


        summaryTxt.insert(END, f'Misc:\n{orec.resource.misc}\n\n')
        summaryTxt.insert(END, f'Summary:\n{orec.resource.summary}\n')
        summaryTxt['state'] = 'disable'

        tracker = {}

        return tracker

    def create_resource_frame(self, parent, resource):
        resourceFrm = Frame(parent)
        resourceFrm.grid(
            row=0, column=0, columnspan=2, sticky='snew', padx=5, pady=5)
        mlogger.debug('New resourceFrm ({}, child of mainTab {})'.format(
            resourceFrm.winfo_id(), parent.winfo_id()))

        # provide description data
        sierraBtn = Button(
            resourceFrm,
            image=self.notfoundImg,
            command=lambda: self.sierra_check(parent))
        sierraBtn.image = self.notfoundImg
        sierraBtn.grid(
            row=0, column=0, sticky='nw', padx=2, pady=2)

        line1 = f'{resource.title} / {resource.author}.'
        Label(resourceFrm, text=line1, font=RBFONT).grid(
            row=0, column=1, sticky='snw', padx=5, pady=5)

        if resource.add_title:
            line2 = f'{resource.add_title}'
            Label(resourceFrm, text=line2, font=RBFONT).grid(
                row=1, column=1, sticky='snw', padx=5, pady=5)

        line3 = f'\t{resource.pub_place} : {resource.publisher}, {resource.pub_date}. -- ({resource.series}).'
        Label(resourceFrm, text=line3, font=LFONT).grid(
            row=2, column=1, sticky='snw', padx=5, pady=2)

        line4 = f'\tISBN: {resource.isbn} | UPC: {resource.upc} | other no.: {resource.other_no}'
        Label(resourceFrm, text=line4, font=LFONT).grid(
            row=3, column=1, sticky='snw', padx=5, pady=2)

        line5 = f'\tlist price: ${resource.price_list} | discount price: ${resource.price_disc}'
        pricesLbl = Label(resourceFrm, text=line5, font=LFONT)
        pricesLbl.grid(
            row=4, column=1, sticky='snw', padx=5, pady=2)

        editBtn = Button(
            resourceFrm,
            image=self.editImgS,
            command=lambda: self.edit_resource(parent.master))
        editBtn.image = self.editImgS
        editBtn.grid(
            row=0, column=4, sticky='se', padx=2, pady=2)

        deleteBtn = Button(
            resourceFrm,
            image=self.deleteImgS,
            command=lambda: self.delete_resource(parent.master))
        # deleteBtn.imgage = self.deleteImgS
        deleteBtn.grid(
            row=0, column=5, sticky='se', padx=2, pady=2)

        tracker = {
            'resource_id': resource.did,
            'resourcefrm': resourceFrm,
            'sierraBtn': sierraBtn,
            'pricesLbl': pricesLbl
        }

        return tracker

    def create_order_frame(self, parent, order):
        # Comboboxes and entries
        orderFrm = Frame(parent)
        orderFrm.grid(
            row=1, column=0, sticky='snew', padx=5, pady=5)
        mlogger.debug('New orderFrm ({}, child of mainTab {})'.format(
            orderFrm.winfo_id(), parent.winfo_id()))

        Label(orderFrm, text='lang:').grid(
            row=0, column=0, sticky='snw', padx=2, pady=2)
        langCbx = Combobox(
            orderFrm,
            values=sorted(self.lang_idx.values()),
            state='readonly')
        langCbx.grid(
            row=0, column=1, sticky='snew', padx=5, pady=2)
        if order.lang_id:
            langCbx.set(self.lang_idx[order.lang_id])

        Label(orderFrm, text='ven:').grid(
            row=1, column=0, sticky='snw', padx=2, pady=2)
        vendorCbx = Combobox(
            orderFrm,
            values=sorted(self.vendor_idx.values()),
            state='readonly')
        vendorCbx.grid(
            row=1, column=1, sticky='snew', padx=5, pady=2)
        if order.vendor_id:
            vendorCbx.set(self.vendor_idx[order.vendor_id])

        Label(orderFrm, text='audn:').grid(
            row=2, column=0, sticky='snw', padx=2, pady=2)
        audnCbx = Combobox(
            orderFrm,
            values=sorted(self.audn_idx.values()),
            state='readonly')
        audnCbx.grid(
            row=2, column=1, sticky='snew', padx=5, pady=2)
        if order.audn_id:
            audnCbx.set(self.audn_idx[order.audn_id])

        Label(orderFrm, text='mat.:').grid(
            row=3, column=0, sticky='snw', padx=2, pady=2)
        mattypeCbx = Combobox(
            orderFrm,
            values=sorted(self.mattype_idx.values()),
            state='readonly')
        mattypeCbx.grid(
            row=3, column=1, sticky='snew', padx=5, pady=2)
        if order.matType_id:
            mattypeCbx.set(self.mattype_idx[order.matType_id])

        Label(orderFrm, text='PO').grid(
            row=4, column=0, sticky='snw', padx=2, pady=2)
        poEnt = Entry(orderFrm)
        poEnt.grid(
            row=4, column=1, sticky='snew', padx=5, pady=2)
        if order.poPerLine:
            poEnt.insert(END, order.poPerLine)

        Label(orderFrm, text='order note').grid(
            row=5, column=0, sticky='snw', padx=2, pady=2)
        noteEnt = Entry(orderFrm)
        noteEnt.grid(
            row=5, column=1, sticky='snew', padx=5, pady=2)
        if order.note:
            noteEnt.insert(END, order.note)

        Label(orderFrm, text='comment').grid(
            row=6, column=0, sticky='snw', padx=2, pady=2)
        commentEnt = Entry(orderFrm)
        commentEnt.grid(
            row=6, column=1, columnspan=3, sticky='snew', padx=5, pady=2)
        if order.comment:
            commentEnt.insert(END, order.comment)

        # ids
        Label(orderFrm, text='order #: ').grid(
            row=0, column=2, sticky='snw', padx=2, pady=2)
        oidEnt = Entry(
            orderFrm,
            state='disable')
        oidEnt.grid(
            row=0, column=3, sticky='snew', padx=5, pady=2)
        if order.oid:
            oidEnt.insert(END, order.oid)

        Label(orderFrm, text='bib #: ').grid(
            row=1, column=2, sticky='snw', padx=2, pady=2)
        bidEnt = Entry(
            orderFrm,
            state='disable')
        bidEnt.grid(
            row=1, column=3, sticky='snew', padx=5, pady=2)
        if order.bid:
            bidEnt.insert(END, order.bid)

        Label(orderFrm, text='wlo #: ').grid(
            row=2, column=2, sticky='snw', padx=2, pady=2)
        wloEnt = Entry(
            orderFrm,
            state='disable')
        wloEnt.grid(
            row=2, column=3, sticky='snew', padx=5, pady=2)
        if order.wlo:
            wloEnt.insert(END, order.wlo)

        tracker = {
            'order_id': order.did,
            'langCbx': langCbx,
            'vendorCbx': vendorCbx,
            'audnCbx': audnCbx,
            'mattypeCbx': mattypeCbx,
            'poEnt': poEnt,
            'noteEnt': noteEnt,
            'commentEnt': commentEnt,
            'oidEnt': oidEnt,
            'bidEnt': bidEnt,
            'wloEnt': wloEnt
        }

        return tracker

    def create_grid(self, parent, row, loc=(None, '', '', '', '')):
        unitFrm = Frame(parent)
        unitFrm.grid(
            row=row, column=0, sticky='snew')
        mlogger.debug(
            'New grid unitFrm ({}): row: {}, parent locsFrm: {}'.format(
                unitFrm.winfo_id(), row, parent.winfo_id()))
        removeBtn = Button(
            unitFrm,
            image=self.removeImgS,)
        removeBtn.image = self.removeImgS
        removeBtn.grid(row=0, column=0, sticky='ne', padx=5, pady=2)
        removeBtn['command'] = lambda: self.remove_location(removeBtn)

        branchCbx = Combobox(
            unitFrm, font=RFONT, width=3,
            state='readonly',
            values=sorted(self.branch_idx.values()))
        branchCbx.grid(
            row=0, column=1, sticky='snew', padx=2, pady=4)
        branchCbx.set(loc[1])

        shelfCbx = Combobox(
            unitFrm, font=RFONT, width=3,
            state='readonly',
            values=sorted(self.shelf_idx.values()))
        shelfCbx.grid(
            row=0, column=2, sticky='snew', padx=2, pady=4)
        shelfCbx.set(loc[2])

        qtyEnt = Entry(
            unitFrm, font=RFONT, width=3,
            validate="key", validatecommand=self.vlqt)
        qtyEnt.grid(
            row=0, column=3, sticky='snew', padx=2, pady=4)
        qtyEnt.insert(END, loc[3])

        fundCbx = Combobox(
            unitFrm, font=RFONT, width=10,
            values=sorted(self.fund_idx.values()),
            state='readonly')
        fundCbx.grid(
            row=0, column=4, columnspan=2, sticky='snew', padx=2, pady=4)
        fundCbx.set(loc[4])

        tracker = {
            'loc_id': loc[0],
            'unitFrm': unitFrm,
            'unitFrm_row': row,
            'removeBtn': removeBtn,
            'branchCbx': branchCbx,
            'shelfCbx': shelfCbx,
            'qtyEnt': qtyEnt,
            'fundCbx': fundCbx,
        }

        return tracker

    def create_add_locationBtn(self, parent):
        # recreate in new row
        add_locationBtn = Button(
            parent,
            image=self.addImgS,
            command=lambda: self.add_location(parent))
        add_locationBtn.image = self.addImgS
        add_locationBtn.grid(
            row=3, column=0, sticky='nw', padx=5, pady=2)
        mlogger.debug('Created addlocBtn ({}, child of gridFrm {})'.format(
            add_locationBtn.winfo_id(), parent.winfo_id()))

    def add_location(self, parent):
        ntb_id = parent.master.master.winfo_id()
        locs = self.tracker[ntb_id]['grid']['locs']

        try:
            row = locs[-1]['unitFrm_row'] + 1
        except IndexError:
            row = 0
        mlogger.debug('adding new loc in row {}'.format(
            row))

        loc = self.create_grid(
            self.tracker[ntb_id]['grid']['locsFrm'], row)
        locs.append(loc)
        self.tracker[ntb_id]['grid']['locs'] = locs
        mlogger.debug('tracker after new loc appended: {}'.format(
            [l['loc_id'] for l in self.tracker[ntb_id]['grid']['locs']]))

    def apply_grid_template(self, ntb_id):
        grid_template_name = self.tracker[ntb_id]['grid']['gridCbx'].get()

        if grid_template_name != '':

            # destroy current grid widgets
            locsFrm = self.tracker[ntb_id]['grid']['locsFrm']
            for w in locsFrm.winfo_children():
                w.destroy()

            # get grid record
            grid_record = get_record(
                DistGrid,
                distset_id=self.dist_id.get(),
                name=grid_template_name)
            r = 0
            locs = []
            for l in grid_record.gridlocations:
                branch = self.branch_idx[l.branch_id]
                shelf = self.shelf_idx[l.shelfcode_id]
                qty = l.qty
                loc = self.create_grid(
                    locsFrm, r, (l.did, branch, shelf, qty, ''))
                locs.append(loc)
                r += 1
            self.tracker[ntb_id]['grid']['locs'] = locs

    def copy_grid_to_template(self, ntb_id):

        # reset any previous variables
        self.new_dist.set('')
        self.new_grid.set('')
        self.dist_template.set('')
        self.grid_template.set('')

        self.gridTop = Toplevel(self)
        self.gridTop.title('Copying grid to template')

        frm = Frame(self.gridTop)
        frm.grid(
            row=0, column=0, sticky='snew', padx=10, pady=10)

        Label(frm, text='new name:').grid(
            row=0, column=2, sticky='snew', padx=5)

        Label(frm, text='distribution:').grid(
            row=1, column=0, sticky='snw', padx=5, pady=5)
        distCbx = Combobox(
            frm,
            font=RFONT,
            textvariable=self.dist_template,
            state='readonly')
        distCbx.grid(
            row=1, column=1, sticky='snew', padx=5, pady=5)
        values = ['new distribution']
        if self.dist_set.get() != '':
            values.append(self.dist_set.get())
        distCbx['values'] = values

        self.newdistEnt = Entry(
            frm,
            font=RFONT,
            textvariable=self.new_dist,
            state='disabled')
        self.newdistEnt.grid(
            row=1, column=2, sticky='snew', padx=5, pady=5)

        Label(frm, text='grid:').grid(
            row=2, column=0, sticky='snw', padx=5, pady=5)
        self.gridCbx = Combobox(
            frm,
            font=RFONT,
            textvariable=self.grid_template,
            state='readonly')
        self.gridCbx.grid(
            row=2, column=1, sticky='snew', padx=5, pady=5)
        values = sorted(self.grid_idx.values())
        values.insert(0, 'new grid')
        self.gridCbx['values'] = values
        self.newgridEnt = Entry(
            frm,
            font=RFONT,
            textvariable=self.new_grid,
            state='disabled')
        self.newgridEnt.grid(
            row=2, column=2, sticky='snew', padx=5, pady=5)

        btnFrm = Frame(frm)
        btnFrm.grid(
            row=3, column=0, columnspan=2, sticky='snew', padx=10, pady=10)
        btnFrm.columnconfigure(0, minsize=200)

        okBtn = Button(
            btnFrm,
            image=self.saveImgS,
            command=lambda: self.save_new_template(ntb_id))
        okBtn.grid(
            row=0, column=1, sticky='snw', padx=5, pady=10)
        cancelBtn = Button(
            btnFrm,
            image=self.deleteImgS,
            command=self.gridTop.destroy)
        cancelBtn.grid(
            row=0, column=2, sticky='snw', padx=5, pady=10)

    def save_new_template(self, ntb_id):
        try:
            grids = self.tracker[ntb_id]['grid']
            profile_id = get_id_from_index(
                self.profile.get(), self.profile_idx)
            if self.new_dist.get() != '':
                # save under new distribution
                if self.new_grid.get() != '':
                    # as new grid
                    save_new_dist_and_grid(
                        self.system.get(),
                        profile_id,
                        grids,
                        self.branch_idx,
                        self.shelf_idx,
                        self.new_dist.get(),
                        self.new_grid.get())
                else:
                    messagebox.showerror(
                        'Input error',
                        'Please provide name for the new grid.')
            else:
                if self.dist_template == 'new distribution':
                    messagebox.showerror(
                        'Input error',
                        'Please provide name for the new distribution.')
                else:
                    # existing distribution
                    if self.new_grid.get() != '':
                        save_new_dist_and_grid(
                            self.system.get(),
                            profile_id,
                            grids,
                            self.branch_idx,
                            self.shelf_idx,
                            self.dist_template.get(),
                            self.new_grid.get())
                    else:
                        # existing grid
                        save_new_dist_and_grid(
                            self.system.get(),
                            profile_id,
                            grids,
                            self.branch_idx,
                            self.shelf_idx,
                            self.dist_template.get(),
                            self.grid_template.get())

            # update dist/grid indexes
            self.profile_observer()
            self.distribution_observer()
            self.gridTop.destroy()

        except BabelError as e:
            self.gridTop.destroy()
            messagebox.showerror('Input Error', e)


    def remove_location(self, removeBtn):
        ntb_id = removeBtn.master.master.master.master.master.winfo_id()
        locs = self.tracker[ntb_id]['grid']['locs']
        mlogger.debug('Locs before removal: {}'.format(
            [l['loc_id'] for l in locs]))
        n = 0
        for l in locs:
            if l['removeBtn'] == removeBtn:
                parent = l['unitFrm']
                break
            n += 1
        locs.pop(n)
        self.tracker[ntb_id]['grid']['locs'] = locs
        parent.destroy()
        mlogger.debug('locs after removal: {}'.format(
            [l['loc_id'] for l in self.tracker[ntb_id]['grid']['locs']]))

    def sierra_check(self, ntb):
        pass

    def edit_resource(self, ntb):
        pass

    def delete_resource(self, ntb):
        msg = 'Are you sure you want to delete order?'
        if messagebox.askokcancel('Deletion', msg):
            order_id = self.tracker[ntb.winfo_id()]['order']['order_id']

            delete_data_by_did(Order, order_id)
            self.tracker.pop(ntb.winfo_id(), None)
            ntb.destroy()

    def reset(self):
        self.order_ids = []
        self.dist_set.set('')
        self.lang.set('')
        self.vendor.set('')
        self.mattype.set('')
        self.price.set('')
        self.discount.set('')
        self.audn.set('')
        self.poperline.set('')
        self.note.set('')
        self.dist_template.set('')
        self.new_dist.set('')
        self.grid_template.set('')
        self.new_grid.set('')

    def template_observer(self, *args):
        try:
            if self.dist_template.get() == 'new distribution':
                self.newdistEnt['state'] = '!disabled'
                self.gridCbx['values'] = ['new grid']
            else:
                self.newdistEnt['state'] = 'disabled'
                if self.dist_template.get() != '':
                    values = sorted(self.grid_idx.values())
                    values.insert(0, 'new grid')
                    self.gridCbx['values'] = values
            if self.grid_template.get() == 'new grid':
                self.newgridEnt['state'] = '!disabled'
            else:
                self.newgridEnt['state'] = 'disabled'
        except AttributeError:
            pass
        except TclError:
            pass

    def status_observer(self, *args):
        if self.status.get() == 'finalized':
            # run validation
            pass

    def profile_observer(self, *args):
        if self.activeW.get() == 'CartView':
            if self.profile.get() != 'All users':
                profile_id = get_id_from_index(
                    self.profile.get(), self.profile_idx)

                # distribution
                self.distr = get_names(
                    DistSet,
                    system_id=self.system.get(),
                    user_id=profile_id)
                self.distCbx['values'] = self.distr

            else:
                msg = 'Cart must have an owner.\nPlease select ' \
                      'one in profile'
                messagebox.showwarning('Cart Problem', msg)

    def distribution_observer(self, *args):
        if self.activeW.get() == 'CartView':
            if self.profile.get() != 'All users':

                profile_id = get_id_from_index(
                    self.profile.get(), self.profile_idx)

                if self.dist_set.get():
                    dist_rec = get_record(
                        DistSet,
                        name=self.dist_set.get(),
                        system_id=self.system.get(),
                        user_id=profile_id)
                    self.dist_id.set(dist_rec.did)

                    self.grid_idx = create_name_index(
                        DistGrid,
                        distset_id=dist_rec.did)

                    # populate gridCbx values
                    for values in self.tracker.values():
                        gridCbx = values['grid']['gridCbx']
                        gridCbx['values'] = sorted(self.grid_idx.values())

    def observer(self, *args):
        if self.activeW.get() == 'CartView':
            if self.profile.get() != 'All users':

                self.reset()

                # trigger profile observer when Window active
                self.profile_observer()

                # create new data tracker
                self.tracker = OrderedDict()
                self.grid_idx = {}

                cart = get_record(Cart, did=self.cart_id.get())
                self.cart_name.set(cart.name)
                self.cartEnt['state'] = 'disable'
                self.status_idx = create_name_index(Status)
                self.statusCbx['values'] = sorted(self.status_idx.values())
                self.statusCbx.set(self.status_idx[cart.status_id])
                self.statusCbx['state'] = 'disable'

                # populate values in global checkboxes

                if self.system.get() == 1:
                    self.library.set('')
                    self.libCbx['state'] = 'disable'
                elif self.system.get() == 2:
                    self.libCbx['state'] = '!disable'

                # langs
                self.lang_idx = create_name_index(Lang)
                values = (sorted(self.lang_idx.values()))
                values.insert(0, 'keep current')
                self.langCbx['values'] = values

                # vendors
                self.vendor_idx = create_name_index(Vendor)
                values = sorted(self.vendor_idx.values())
                values.insert(0, 'keep current')
                self.vendorCbx['values'] = values

                # mattype
                self.mattype_idx = create_name_index(MatType)
                values = sorted(self.mattype_idx.values())
                values.insert(0, 'keep current')
                self.mattypeCbx['values'] = values

                # audience
                self.audn_idx = create_name_index(Audn)
                values = sorted(self.audn_idx.values())
                values.insert(0, 'keep current')
                self.audnCbx['values'] = values

                # funds
                self.fund_idx = create_code_index(
                    Fund,
                    system_id=self.system.get())

                # branches
                self.branch_idx = create_code_index(
                    Branch,
                    system_id=self.system.get())

                # shelf codes
                self.shelf_idx = create_code_index(
                    ShelfCode,
                    system_id=self.system.get())

                self.order_ids = get_order_ids(self.cart_id.get())
                self.selected_order_ids = self.order_ids[:5]
                self.display_selected_orders(self.selected_order_ids)

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

    def on_mousewheel(self, event):
        self.preview_base.yview_scroll(
            int(-1 * (event.delta / 120)), "units")

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

    def onValidateQty(self, i, d, P):
        valid = True
        if d == '1' and not P.isdigit():
            valid = False
        if int(i) > 2:
            valid = False
        if i == '0' and P == '0':
            valid = False
        return valid

    def createToolTip(self, widget, text):
        toolTip = ToolTip(widget)

        def enter(event):
            toolTip.showtip(text)

        def leave(event):
            toolTip.hidetip()

        widget.bind('<Enter>', enter)
        widget.bind('<Leave>', leave)
