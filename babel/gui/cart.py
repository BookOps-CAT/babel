from collections import OrderedDict
from datetime import datetime
import logging
from tkinter import *
from tkinter.ttk import *
from tkinter import messagebox

from errors import BabelError
from data.transactions_cart import (apply_fund_to_cart,
                                    apply_grid_to_selected_orders,
                                    apply_globals_to_cart,
                                    assign_blanketPO_to_cart,
                                    assign_wlo_to_cart,
                                    delete_locations_from_selected_orders,
                                    find_matches,
                                    determine_needs_validation,
                                    get_cart_resources,
                                    get_last_cart,
                                    get_orders_by_id,
                                    has_library_assigned,
                                    save_displayed_order_data,
                                    save_new_dist_and_grid, validate_cart_data,
                                    tabulate_funds,
                                    create_order_snapshot,
                                    create_grids_snapshot,
                                    search_cart)
from data.datastore import (Cart, Order, Resource, Lang, Audn, DistSet,
                            DistGrid, ShelfCode, Vendor, MatType, Fund,
                            Branch, Status, Library)
from gui.carts import CopyCartWidget
from gui.data_retriever import (get_names, save_data, get_record,
                                delete_data_by_did,
                                get_order_ids, create_code_index,
                                create_name_index)
from gui.fonts import RFONT, RBFONT, LFONT
from gui.utils import ToolTip, BusyManager, get_id_from_index, open_url
from gui.edit_resource import EditResourceWidget
from logging_settings import LogglyAdapter
from reports.cart import tabulate_cart_data
from sierra_adapters.webpac_scraper import BPL_SEARCH_URL, NYPL_SEARCH_URL


mlogger = LogglyAdapter(logging.getLogger('babel'), None)


class CartSummary:
    """Displays a report on specific cart; invoked from CartView"""

    def __init__(self, parent, **app_data):

        self.parent = parent
        self.app_data = app_data

        mlogger.debug('CartSummary active.')

        self.top = Toplevel(master=self.parent)
        self.top.title('Cart summary')
        self.cur_manager = BusyManager(self.top)

        self.cart_id = app_data['active_id']

        frm = Frame(self.top)
        frm.grid(
            row=0, column=0, sticky='snew', padx=20, pady=20)

        scrollbar = Scrollbar(frm, orient=VERTICAL)
        scrollbar.grid(row=0, column=0, rowspan=5, sticky='snw')

        self.resultsTxt = Text(
            frm,
            wrap='word',
            height=30,
            width=40,
            background='SystemButtonFace',
            borderwidth=0,
            yscrollcommand=scrollbar.set)
        self.resultsTxt.grid(
            row=0, column=1, rowspan=5, sticky="snew", padx=10)
        scrollbar['command'] = self.resultsTxt.yview

        self.tabulate()

    def tabulate(self):
        self.resultsTxt['state'] = 'normal'
        self.resultsTxt.insert(
            '1.0', 'Cart summary:\n\n')
        self.resultsTxt.tag_add('header', '1.0', '1.end')

        data = tabulate_cart_data(self.cart_id.get())
        ln = 3
        for b, v in data.items():
            self.resultsTxt.insert(
                f'{ln}.0', f'{b}: titles={v["titles"]}, '
                f'copies={v["copies"]}, dollars={v["dollars"]}\n')
            ln += 1
            for l in range(3, ln):
                self.resultsTxt.tag_add('branch', f'{l}.0', f'{l}.3')
                self.resultsTxt.tag_add('data', f'{l}.4', f'{l}.end')

        self.resultsTxt.tag_config('header', font=RBFONT)
        self.resultsTxt.tag_config('branch', font=RFONT, foreground='tomato2')
        self.resultsTxt.tag_config('data', font=RFONT)
        self.resultsTxt['state'] = 'disabled'


class ApplyGridsWidget:
    """Widget for selective application of grids to resources in the cart"""

    def __init__(self, parent, system_id,
                 profile_id, distributions, **app_data):

        mlogger.debug('ApplyGridsWidget launched.')

        self.parent = parent
        self.app_data = app_data
        self.system_id = system_id
        self.profile_id = profile_id
        self.cart_id = app_data['active_id'].get()
        self.distr_names = distributions  # user specific
        self.append_grid = IntVar()
        self.selected_distr = StringVar()
        self.selected_distr.trace('w', self.distr_observer)
        self.selected_distr_id = None
        self.selected_grid = StringVar()
        self.grid_idx = dict()
        self.total_qty = StringVar()
        self.total_amount = StringVar()

        self.top = Toplevel(master=self.parent)
        self.top.title('Apply distributions')
        self.cur_manager = BusyManager(self.top)

        # icons
        applyImg = self.app_data['img']['save']
        removeImg = self.app_data['img']['delete']
        helpImg = self.app_data['img']['help']

        frm = Frame(self.top)
        frm.grid(
            row=0, column=0, sticky='snew', padx=10, pady=20)

        # list of resources

        # in the next release try to allow user pick columns to display
        columns = (
            'oid', '#', 'title', 'author', 'ISBN', 'price', 'comment',
            'qty', 'locations')

        self.resourcesTrv = Treeview(
            frm,
            columns=columns,
            displaycolumns=columns[1:],
            show='headings',
            height=40)

        for col in columns:
            self.resourcesTrv.heading(
                col,
                text=col,
                command=lambda _col=col: self._treeview_sort_column(
                    self.resourcesTrv, _col, False))

        self.resourcesTrv.column('#', width=50, anchor='center')
        self.resourcesTrv.column('title', width=200)
        self.resourcesTrv.column('author', width=150, anchor='center')
        self.resourcesTrv.column('ISBN', width=130, anchor='center')
        self.resourcesTrv.column('price', width=80, anchor='center')
        self.resourcesTrv.column('comment', width=80, anchor='center')
        self.resourcesTrv.column('qty', width=60, anchor='center')
        self.resourcesTrv.column('locations', width=200, anchor='center')

        self.resourcesTrv.grid(
            row=0, column=0, rowspan=20, sticky='snew')

        scrollbar = Scrollbar(
            frm, orient='vertical', command=self.resourcesTrv.yview)
        scrollbar.grid(row=0, column=1, rowspan=20, sticky='ns')
        self.resourcesTrv.configure(yscrollcommand=scrollbar.set)

        # buttons
        btnFrm = Frame(self.top)
        btnFrm.grid(
            row=0, column=1, rowspan=20, sticky='snew', pady=20)

        applyBtn = Button(
            btnFrm,
            image=applyImg,
            command=self.apply_distribution)
        applyBtn.grid(
            row=0, column=0, sticky='sw', padx=5, pady=5)
        self._createToolTip(applyBtn, 'apply grid')

        removeBtn = Button(
            btnFrm,
            image=removeImg,
            command=self.remove_distribution)
        removeBtn.grid(
            row=1, column=0, sticky='sw', padx=5, pady=5)
        self._createToolTip(removeBtn, 'remove grid')

        helpBtn = Button(
            btnFrm,
            image=helpImg,
            command=self.help)
        helpBtn.grid(
            row=2, column=0, sticky='sw', padx=5, pady=5)
        self._createToolTip(helpBtn, 'help')

        # grids frm
        gridFrm = Frame(self.top)
        gridFrm.grid(
            row=0, column=2, rowspan=20, sticky='snew', padx=5, pady=20)
        gridFrm.rowconfigure(4, minsize=30)
        gridFrm.rowconfigure(7, minsize=50)

        Label(gridFrm, text='distributions', font=RBFONT).grid(
            row=0, column=0, sticky='snw', padx=5, pady=10)

        self.distrCbx = Combobox(
            gridFrm,
            state='readonly',
            font=RFONT,
            values=self.distr_names,
            textvariable=self.selected_distr)
        self.distrCbx.grid(
            row=1, column=0, sticky='snew', padx=5, pady=5)

        self.gridCbx = Combobox(
            gridFrm,
            state='readonly',
            font=RFONT,
            textvariable=self.selected_grid)
        self.gridCbx.grid(
            row=2, column=0, sticky='snew', padx=5, pady=5)

        Checkbutton(
            gridFrm,
            text='add to existing',
            variable=self.append_grid).grid(
            row=3, column=0, sticky='snw', padx=5, pady=5)

        Label(
            gridFrm,
            textvariable=self.total_qty,
            font=RFONT).grid(
            row=5, column=0, sticky='snw', padx=5, pady=5)

        Label(
            gridFrm,
            textvariable=self.total_amount,
            font=RFONT).grid(
            row=6, column=0, sticky='snw', padx=5, pady=5)

        self.create_resources_list()

        closeBtn = Button(
            gridFrm,
            text='close',
            width=10,
            command=self.top.destroy)
        closeBtn.grid(
            row=8, column=0, sticky='snw', padx=20, pady=5)

    def apply_distribution(self):
        # verify distribution and grid is selected
        if not self.selected_distr.get() or \
                not self.selected_grid.get():
            messagebox.showwarning(
                'Missing data', 'Please select distribution.',
                parent=self.top)
        else:
            # determine datastore id of orders to be modified
            order_ids = self.map_selection_to_order_ids()
            grid_id = get_id_from_index(
                self.selected_grid.get(), self.grid_idx)

            if self.append_grid.get():
                append = True
            else:
                append = False

            mlogger.debug(
                f'Applying DistGrid.did={grid_id} to order dids={order_ids}, '
                f'append mode={append}')

            # apply distribution to datastore
            if order_ids:
                self.cur_manager.busy()
                apply_grid_to_selected_orders(
                    order_ids, grid_id, append=append)
                self.create_resources_list()
                self.cur_manager.notbusy()
            else:
                messagebox.showwarning(
                    'Missing data',
                    'Please select titles to apply distribution',
                    parent=self.top)

    def create_resources_list(self):
        mlogger.debug('Retrieving cart resources.')
        self.cur_manager.busy()

        # delete any previous data
        self.resourcesTrv.delete(*self.resourcesTrv.get_children())

        # repopulate
        total_qty = 0
        total_amount = 0
        resources = get_cart_resources(self.cart_id)
        for res in resources:
            self.resourcesTrv.insert('', END, values=res)
            total_amount += float(res[5]) * res[7]
            total_qty += res[7]

        # update running tally labels
        self.total_qty.set(f'Total qty: {total_qty} copie(s)')
        self.total_amount.set(f'Total amount: ${total_amount:,.2f}')
        self.cur_manager.notbusy()

    def distr_observer(self, *args):
        if self.selected_distr.get():
            dist_rec = get_record(
                DistSet,
                name=self.selected_distr.get(),
                system_id=self.system_id,
                user_id=self.profile_id)
            self.selected_distr_id = dist_rec.did
            mlogger.debug(
                'User seclected DistSet.did={dist_rec.did}')

            self.grid_idx = create_name_index(
                DistGrid,
                distset_id=dist_rec.did)

            # populate gridCbx values
            values = sorted(self.grid_idx.values())
            self.gridCbx['values'] = values

    def help(self):
        pass

    def map_selection_to_order_ids(self):
        sel = self.resourcesTrv.selection()
        order_dids = [self.resourcesTrv.item(i)['values'][0] for i in sel]
        return order_dids

    def remove_distribution(self):
        order_ids = self.map_selection_to_order_ids()
        if order_ids:
            self.cur_manager.busy()
            delete_locations_from_selected_orders(order_ids)
            self.cur_manager.notbusy()
            self.create_resources_list()
        else:
            messagebox.showwarning(
                'Missing data',
                'Please select titles to remove distribution',
                parent=self.top)

    def _createToolTip(self, widget, text):
        toolTip = ToolTip(widget)

        def enter(event):
            toolTip.showtip(text)

        def leave(event):
            toolTip.hidetip()

        widget.bind('<Enter>', enter)
        widget.bind('<Leave>', leave)

    def _treeview_sort_column(self, tv, col, reverse):
        tree_list = [(tv.set(k, col), k) for k in tv.get_children('')]
        tree_list.sort(reverse=reverse)

        # rearrange items in sorted positions
        for index, (val, k) in enumerate(tree_list):
            tv.move(k, '', index)

        # reverse sort next time
        tv.heading(
            col,
            command=lambda: self._treeview_sort_column(tv, col, not reverse))


class SearchCartWidget:
    """Top window allowing searching currently displayed cart"""

    def __init__(self, parent, **app_data):
        mlogger.debug('SearchCartWidget launched.')

        self.parent = parent
        self.app_data = app_data
        self.order_id = app_data['searched_order']
        self.cart_id = app_data['active_id'].get()
        self.keywords = StringVar()
        self.key_type = StringVar()

        self.search_top = Toplevel(master=self.parent)
        self.search_top.title('Search cart')
        self.cur_manager = BusyManager(self.search_top)

        # input frame
        inputFrm = Frame(self.search_top)
        inputFrm.grid(
            row=0, column=0, sticky='snew', padx=20, pady=20)

        self.keywordEnt = Entry(
            inputFrm,
            font=RFONT,
            textvariable=self.keywords,
            width=40)
        self.keywordEnt.grid(
            row=0, column=0, sticky='snew', padx=2, pady=5)

        self.key_types = [
            'isbn',
            'upc',
            'wlo #',
            'order #',
            'bib #',
            'other #',
            'title',
            'author'
        ]

        self.keytypeCbx = Combobox(
            inputFrm,
            font=RFONT,
            values=self.key_types,
            textvariable=self.key_type,
            state='readonly',
            width=10)
        self.keytypeCbx.grid(
            row=0, column=1, sticky='snew', padx=2, pady=5)
        self.keytypeCbx.set(self.key_types[0])

        self.search_types = [
            'phrase',
            'keyword'
        ]

        self.searchtypeCbx = Combobox(
            inputFrm,
            font=RFONT,
            values=self.search_types,
            state='readonly',
            width=10)
        self.searchtypeCbx.grid(
            row=0, column=2, sticky='snew', padx=2, pady=5)
        self.searchtypeCbx.set(self.search_types[0])

        # buttons frame
        btnFrm = Frame(self.search_top)
        btnFrm.grid(
            row=1, column=0, sticky='snew', padx=20)
        btnFrm.columnconfigure(0, minsize=160)

        self.searchBtn = Button(
            btnFrm,
            text='search',
            command=self.search,
            width=10)
        self.searchBtn.grid(
            row=0, column=1, sticky='snw', padx=5, pady=5)

        self.closeBtn = Button(
            btnFrm,
            text='close',
            command=self.search_top.destroy,
            width=10)
        self.closeBtn.grid(
            row=0, column=2, sticky='snw', padx=5, pady=5)

        # results frame
        resFrm = Frame(self.search_top)
        resFrm.grid(
            row=2, column=0, sticky='snew', padx=20, pady=20)

        columns = (
            'oid', '#', 'title', 'author', 'ISBN')

        self.resultsTrv = Treeview(
            resFrm,
            columns=columns,
            displaycolumns=columns[1:],
            show='headings',
            height=20)

        for col in columns:
            self.resultsTrv.heading(
                col,
                text=col,
                command=lambda _col=col: self._treeview_sort_column(
                    self.resultsTrv, _col, False))

        self.resultsTrv.column('#', width=50, anchor='center')
        self.resultsTrv.column('title', width=200)
        self.resultsTrv.column('author', width=150, anchor='center')
        self.resultsTrv.column('ISBN', width=130, anchor='center')

        self.resultsTrv.grid(
            row=0, column=0, sticky='snew')
        self.resultsTrv.bind('<Double-Button-1>', self.select_item)

        scrollbar = Scrollbar(
            resFrm, orient='vertical', command=self.resultsTrv.yview)
        scrollbar.grid(row=0, column=1, sticky='ns')
        self.resultsTrv.configure(yscrollcommand=scrollbar.set)

    def populate_result_list(self, results):
        for value in results:
            self.resultsTrv.insert('', END, values=value)

    def search(self):
        self.resultsTrv.delete(*self.resultsTrv.get_children())
        if not self.keywords.get().strip():
            messagebox.showwarning(
                'Missing data',
                'Please enter keywords to search.',
                parent=self.search_top)
        else:
            # force any id type keywords to be searched as phrases
            if self.key_type.get() in self.key_types[:6]:
                self.searchtypeCbx.set(self.search_types[0])

            keywords = self.keywords.get().strip()

            results = search_cart(
                self.cart_id,
                keywords,
                self.keytypeCbx.get(),
                self.searchtypeCbx.get())

            self.populate_result_list(results)

    def select_item(self, a):
        curItem = self.resultsTrv.focus()
        try:
            self.order_id.set(self.resultsTrv.item(curItem)['values'][0])
            mlogger.debug(
                f'Cart SearchWidget: selected Order.did={self.order_id.get()}')
        except IndexError:
            pass

    def _treeview_sort_column(self, tv, col, reverse):
        tree_list = [(tv.set(k, col), k) for k in tv.get_children('')]
        tree_list.sort(reverse=reverse)

        # rearrange items in sorted positions
        for index, (val, k) in enumerate(tree_list):
            tv.move(k, '', index)

        # reverse sort next time
        tv.heading(
            col,
            command=lambda: self._treeview_sort_column(tv, col, not reverse))


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
        self.searched_order = IntVar()
        self.app_data['searched_order'] = self.searched_order
        self.searched_order.trace('w', self.search_observer)
        self.profile.trace('w', self.profile_observer)
        max_height = int((self.winfo_screenheight() - 200))
        self.cur_manager = BusyManager(self)

        # local variables
        self.cart_name = StringVar()
        self.dist_set = StringVar()
        self.dist_set.trace('w', self.distribution_observer)
        self.dist_id = IntVar()
        self.dist_template = StringVar()
        self.dist_template.trace('w', self.template_observer)
        self.new_dist = StringVar()
        self.grid_template = StringVar()
        self.grid_template.trace('w', self.template_observer)
        self.glob_grid_template = StringVar()
        self.new_grid = StringVar()
        self.library = StringVar()
        self.status = StringVar()
        self.lang = StringVar()
        self.lang.set('keep current')
        self.vendor = StringVar()
        self.vendor.set('keep current')
        self.mattype = StringVar()
        self.mattype.set('keep current')
        self.price = StringVar()
        self.discount = StringVar()
        self.audn = StringVar()
        self.audn.set('keep current')
        self.poperline = StringVar()
        self.note = StringVar()
        self.poChb_var = IntVar()
        self.noteChb_var = IntVar()
        self.priceChb_var = IntVar()
        self.discountChb_var = IntVar()

        # navigation variables
        self.order_ids = []
        self.disp_start = 0
        self.disp_end = 0
        self.disp_number = 30
        self.orders_displayed = StringVar()
        self.funds_tally = StringVar()

        # icons
        addImg = self.app_data['img']['add']
        copyImg = self.app_data['img']['copy']
        editImg = self.app_data['img']['edit']
        self.deleteImg = self.app_data['img']['delete']
        helpImg = self.app_data['img']['help']
        self.saveImg = self.app_data['img']['save']
        searchImg = self.app_data['img']['view']
        previousImg = self.app_data['img']['previous']
        nextImg = self.app_data['img']['next']
        startImg = self.app_data['img']['start']
        endImg = self.app_data['img']['end']
        sierraImg = self.app_data['img']['sierra']
        validationImg = self.app_data['img']['valid']
        fundImgM = self.app_data['img']['fundM']
        calcImgM = self.app_data['img']['calcM']
        gridImg = self.app_data['img']['gridM']
        self.editImgS = self.app_data['img']['editS']
        self.removeImgS = self.app_data['img']['removeS']
        self.deleteImgS = self.app_data['img']['deleteS']
        self.addImgS = self.app_data['img']['addS']
        self.foundImg = self.app_data['img']['found']
        self.notfoundImg = self.app_data['img']['notfound']
        self.notcheckedImg = self.app_data['img']['notchecked']
        self.babeldupImg = self.app_data['img']['babeldup']
        self.copyImgS = self.app_data['img']['copyS']
        self.saveImgS = self.app_data['img']['saveS']

        # action buttons frame
        self.actionFrm = Frame(self)
        self.actionFrm.grid(
            row=0, column=0, sticky='snew', padx=5, pady=10)

        # register comboboxes and entries validation
        self.vlen = (self.register(self._onValidateName),
                     '%i', '%W')
        self.vlqt = (self.register(self._onValidateQty),
                     '%i', '%d', '%P')
        self.vlam = (self.register(self._onValidatePrice),
                     '%i', '%d', '%P')
        self.vlds = (self.register(self._onValidateDiscount),
                     '%i', '%d', '%P')

        self.addBtn = Button(
            self.actionFrm,
            image=addImg,
            command=self.add_resource)
        self.addBtn.grid(
            row=0, column=0, sticky='sw', padx=10, pady=5)
        self._createToolTip(self.addBtn, 'add title to cart')

        self.editBtn = Button(
            self.actionFrm,
            image=editImg,
            command=self.rename_cart)
        self.editBtn.grid(
            row=1, column=0, sticky='sw', padx=10, pady=5)
        self._createToolTip(self.editBtn, 'edit cart name')

        self.saveBtn = Button(
            self.actionFrm,
            image=self.saveImg,
            command=self.save_cart)
        self.saveBtn.grid(
            row=2, column=0, sticky='sw', padx=10, pady=5)
        self._createToolTip(self.saveBtn, 'save cart')

        self.gridBtn = Button(
            self.actionFrm,
            image=gridImg,
            command=self.selective_grids_widget)
        self.gridBtn.grid(
            row=3, column=0, sticky='sw', padx=10, pady=5)
        self._createToolTip(
            self.gridBtn, 'apply distribution to\nselected titles')

        self.fundBtn = Button(
            self.actionFrm,
            image=fundImgM,
            command=self.show_fund_widget)
        self.fundBtn.grid(
            row=4, column=0, sticky='sw', padx=10, pady=5)
        self._createToolTip(self.fundBtn, 'apply funds')

        self.validBtn = Button(
            self.actionFrm,
            image=validationImg,
            command=self.validation_report)
        self.validBtn.grid(
            row=5, column=0, sticky='sw', padx=10, pady=5)
        self._createToolTip(self.validBtn, 'validate cart')

        self.copyBtn = Button(
            self.actionFrm,
            image=copyImg,
            command=self.copy_cart)
        self.copyBtn.grid(
            row=6, column=0, sticky='sw', padx=10, pady=5)
        self._createToolTip(self.copyBtn, 'copy entire cart')

        self.searchBtn = Button(
            self.actionFrm,
            image=searchImg,
            command=self.search_widget)
        self.searchBtn.grid(
            row=7, column=0, sticky='sw', padx=10, pady=5)
        self._createToolTip(self.searchBtn, 'search cart')

        self.sierraBtn = Button(
            self.actionFrm,
            image=sierraImg,
            command=self.find_duplicates_widget)
        self.sierraBtn.grid(
            row=8, column=0, sticky='sw', padx=10, pady=5)
        self._createToolTip(self.sierraBtn, 'search Sierra')

        self.tabulateBtn = Button(
            self.actionFrm,
            image=calcImgM,
            command=self.tabulate_cart_widget)
        self.tabulateBtn.grid(
            row=9, column=0, sticky='sw', padx=10, pady=5)
        self._createToolTip(self.tabulateBtn, 'tabulate cart data')

        self.helpBtn = Button(
            self.actionFrm,
            image=helpImg,
            command=self.help)
        self.helpBtn.grid(
            row=10, column=0, sticky='sw', padx=10, pady=5)
        self._createToolTip(self.helpBtn, 'help')

        self.deleteBtn = Button(
            self.actionFrm,
            image=self.deleteImg,
            command=self.delete_cart)
        self.deleteBtn.grid(
            row=11, column=0, sticky='sw', padx=10, pady=5)
        self._createToolTip(self.deleteBtn, 'delete cart')

        self.globdataFrm = Frame(self, relief='groove')
        self.globdataFrm.grid(
            row=0, column=1, sticky='snew', padx=20, pady=10)

        Label(self.globdataFrm, text='cart name:').grid(
            row=0, column=0, columnspan=2, sticky='nsw', padx=5, pady=2)
        self.cartEnt = Entry(
            self.globdataFrm,
            textvariable=self.cart_name,
            font=RFONT,
            validate="key", validatecommand=self.vlen)
        self.cartEnt.grid(
            row=1, column=0, columnspan=3, sticky='snew', padx=6, pady=2)

        Label(self.globdataFrm, text='library:').grid(
            row=2, column=0, sticky='snw', padx=5, pady=2)
        self.libCbx = Combobox(
            self.globdataFrm,
            textvariable=self.library,
            font=RFONT,
            state='readonly')
        self.libCbx.grid(
            row=2, column=1, columnspan=2, sticky='snew', padx=5, pady=2)

        Label(self.globdataFrm, text='status:').grid(
            row=3, column=0, sticky='snw', padx=5, pady=2)
        self.statusCbx = Combobox(
            self.globdataFrm,
            font=RFONT,
            textvariable=self.status,
            state='readonly')
        self.statusCbx.grid(
            row=3, column=1, columnspan=2, sticky='snew', padx=5, pady=2)

        Separator(self.globdataFrm, orient=HORIZONTAL).grid(
            row=4, column=0, columnspan=3, sticky='snew', padx=5, pady=4)

        Label(self.globdataFrm, text='use distribution:').grid(
            row=5, column=0, columnspan=3, sticky='nsw', padx=5, pady=2)
        self.distCbx = Combobox(
            self.globdataFrm,
            font=RFONT,
            textvariable=self.dist_set,
            state='readonly')
        self.distCbx.grid(
            row=6, column=0, columnspan=3, sticky='snew', padx=5, pady=2)

        Separator(self.globdataFrm, orient=HORIZONTAL).grid(
            row=7, column=0, columnspan=3, sticky='snew', padx=5, pady=6)

        Label(self.globdataFrm, text='grid:').grid(
            row=8, column=0, sticky='snw', padx=5, pady=5)
        self.globgridCbx = Combobox(
            self.globdataFrm,
            font=RFONT,
            state='readonly',
            textvariable=self.glob_grid_template)
        self.globgridCbx.grid(
            row=8, column=1, columnspan=2, sticky='snew', padx=5, pady=2)

        Label(self.globdataFrm, text='language:').grid(
            row=9, column=0, sticky='snw', padx=5, pady=2)
        self.langCbx = Combobox(
            self.globdataFrm,
            font=RFONT,
            textvariable=self.lang)
        self.langCbx.grid(
            row=9, column=1, columnspan=2, sticky='snew', padx=5, pady=2)
        self.langCbx['state'] = 'readonly'

        Label(self.globdataFrm, text='vendor:').grid(
            row=10, column=0, sticky='snw', padx=5, pady=2)
        self.vendorCbx = Combobox(
            self.globdataFrm,
            font=RFONT,
            textvariable=self.vendor)
        self.vendorCbx.grid(
            row=10, column=1, columnspan=2, sticky='snew', padx=5, pady=2)
        self.vendorCbx['state'] = 'readonly'

        Label(self.globdataFrm, text='mat.type').grid(
            row=11, column=0, sticky='nsw', padx=5, pady=2)
        self.mattypeCbx = Combobox(
            self.globdataFrm,
            font=RFONT,
            textvariable=self.mattype)
        self.mattypeCbx.grid(
            row=11, column=1, columnspan=2, sticky='snew', padx=5, pady=2)
        self.mattypeCbx['state'] = 'readonly'

        Label(self.globdataFrm, text='audience:').grid(
            row=12, column=0, sticky='snw', padx=5, pady=2)
        self.audnCbx = Combobox(
            self.globdataFrm,
            font=RFONT,
            textvariable=self.audn)
        self.audnCbx.grid(
            row=12, column=1, columnspan=2, sticky='snew', padx=5, pady=2)
        self.audnCbx['state'] = 'readonly'

        Label(self.globdataFrm, text='PO:').grid(
            row=13, column=0, sticky='snw', padx=5, pady=2)
        self.poEnt = Entry(
            self.globdataFrm,
            font=RFONT,
            textvariable=self.poperline)
        self.poEnt.grid(
            row=13, column=1, sticky='snew', padx=5, pady=2)
        self.poChb = Checkbutton(self.globdataFrm, variable=self.poChb_var)
        self.poChb.grid(
            row=13, column=2, sticky='sne', padx=5, pady=2)

        Label(self.globdataFrm, text='ord. note:').grid(
            row=14, column=0, sticky='snw', padx=5, pady=2)
        self.noteEnt = Entry(
            self.globdataFrm,
            font=RFONT,
            textvariable=self.note)
        self.noteEnt.grid(
            row=14, column=1, sticky='snew', padx=5, pady=2)
        self.noteChb = Checkbutton(
            self.globdataFrm, variable=self.noteChb_var)
        self.noteChb.grid(
            row=14, column=2, sticky='sne', padx=5, pady=2)

        Label(self.globdataFrm, text='def.price:').grid(
            row=15, column=0, sticky='snw', padx=5, pady=2)
        self.priceEnt = Entry(
            self.globdataFrm,
            font=RFONT,
            textvariable=self.price,
            validate="key", validatecommand=self.vlam)
        self.priceEnt.grid(
            row=15, column=1, sticky='snew', padx=5, pady=2)
        self.priceChb = Checkbutton(
            self.globdataFrm, variable=self.priceChb_var)
        self.priceChb.grid(
            row=15, column=2, sticky='sne', padx=5, pady=2)

        Label(self.globdataFrm, text='discount').grid(
            row=16, column=0, sticky='snw', padx=5, pady=2)
        self.discEnt = Entry(
            self.globdataFrm,
            font=RFONT,
            textvariable=self.discount,
            validate="key", validatecommand=self.vlds)
        self.discEnt.grid(
            row=16, column=1, sticky='snew', padx=5, pady=2)
        self.discountChb = Checkbutton(
            self.globdataFrm, variable=self.discountChb_var)
        self.discountChb.grid(
            row=16, column=2, sticky='sne', padx=5, pady=2)

        self.applyBtn = Button(
            self.globdataFrm,
            text='apply',
            width=10,
            command=self.apply_globals)
        self.applyBtn.grid(
            row=17, column=1, sticky='snw', pady=10)

        self.fundLbl = Label(
            self.globdataFrm,
            textvariable=self.funds_tally,
            anchor=CENTER)
        self.fundLbl.grid(
            row=18, column=0, columnspan=3, sticky='snew', padx=5, pady=5)

        self.dispLbl = Label(
            self.globdataFrm, textvariable=self.orders_displayed,
            anchor=CENTER)
        self.dispLbl.grid(
            row=19, column=0, columnspan=3, sticky='snew', padx=5, pady=5)

        self.navFrm = Frame(self.globdataFrm)
        self.navFrm.grid(
            row=20, column=1, sticky='snew', padx=10, pady=10)

        self.startBtn = Button(
            self.navFrm,
            image=startImg,
            command=self.nav_start)
        self.startBtn.image = startImg
        self.startBtn.grid(
            row=0, column=0, sticky='sw', padx=2, pady=5)

        self.previousBtn = Button(
            self.navFrm,
            image=previousImg,
            command=self.nav_previous)
        self.previousBtn.image = previousImg
        self.previousBtn.grid(
            row=0, column=1, sticky='sw', padx=2, pady=5)

        self.nextBtn = Button(
            self.navFrm,
            image=nextImg,
            command=self.nav_next)
        self.nextBtn.image = nextImg
        self.nextBtn.grid(
            row=0, column=2, sticky='sw', padx=2, pady=5)

        self.endBtn = Button(
            self.navFrm,
            image=endImg,
            command=self.nav_end)
        self.endBtn.image = endImg
        self.endBtn.grid(
            row=0, column=3, sticky='sw', padx=2, pady=5)

        # individual order data
        self.ordsFrm = LabelFrame(self.globdataFrm, text='orders')
        self.ordsFrm.grid(
            row=0, column=3, rowspan=40, sticky='snew', padx=10, pady=5)

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
        # self.preview_base.bind_all("<MouseWheel>", self.on_mousewheel)
        self._preview()

    def add_location(self, parent):
        ntb_id = parent.master.master.winfo_id()
        locs = self.tracker[ntb_id]['grid']['locs']

        try:
            row = locs[-1]['unitFrm_row'] + 1
        except IndexError:
            row = 0
        # mlogger.debug('adding new loc in row {}'.format(
        #     row))

        loc = self.create_grid(
            self.tracker[ntb_id]['grid']['locsFrm'], row)
        locs.append(loc)
        self.tracker[ntb_id]['grid']['locs'] = locs
        # mlogger.debug('tracker after new loc appended: {}'.format(
        #     [l['loc_id'] for l in self.tracker[ntb_id]['grid']['locs']]))

    def add_resource(self):
        edit_widget = EditResourceWidget(
            self, cart_id=self.cart_id.get(), **self.app_data)
        self.wait_window(edit_widget.top)

        # redo display
        self.observer()

    def apply_funds(self, listbox, selected):
        self.cur_manager.busy()

        # save any changes to orders first
        save_displayed_order_data(self.tracker.values())

        values = listbox.get(0, END)
        selected_funds = [values[s] for s in selected]
        try:
            apply_fund_to_cart(
                self.system.get(), self.cart_id.get(), selected_funds)
        except BabelError as e:
            self.cur_manager.notbusy()
            messagebox.showerror(
                'Funds error',
                f'Unable to apply funds correctly. Error: {e}')
        else:
            self.update_funds_tally()
            self.cur_manager.notbusy()

        # update display
        # maybe it would be better to simply insert
        # new values into appropriate fundCbxes?
        self._redo_preview_frame()
        self.display_selected_orders(self.selected_order_ids)

        self.fundTop.destroy()

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
                    locsFrm, r, (None, branch, shelf, qty, ''))
                locs.append(loc)
                r += 1
            self.tracker[ntb_id]['grid']['locs'] = locs

    def apply_globals(self):
        # save any changes to records first
        save_displayed_order_data(self.tracker.values())

        # update all order records even ones not displayed
        widgets = {
            'globgrid': [self.dist_id.get(), self.glob_grid_template.get()],
            'langCbx': self.langCbx,
            'vendorCbx': self.vendorCbx,
            'mattypeCbx': self.mattypeCbx,
            'audnCbx': self.audnCbx}

        if self.poChb_var.get():
            widgets['poEnt'] = self.poEnt
        if self.noteChb_var.get():
            widgets['noteEnt'] = self.noteEnt
        if self.priceChb_var.get():
            widgets['priceEnt'] = self.priceEnt
        if self.discountChb_var.get():
            widgets['discEnt'] = self.discEnt

        self.cur_manager.busy()
        try:
            apply_globals_to_cart(self.cart_id.get(), widgets)
            self.cur_manager.notbusy()
        except BabelError as e:
            self.cur_manager.notbusy()
            messagebox.showerror(
                'Database error',
                'Something went wrong when applying global values.\n'
                f'Error: {e}')

        self._redo_preview_frame()
        self.display_selected_orders(self.selected_order_ids)
        self.update_funds_tally()

    def copy_cart(self):
        ccw = CopyCartWidget(
            self, self.cart_id.get(),
            self.cart_name.get(), **self.app_data)
        self.wait_window(ccw.top)

        # show new cart
        self.reset()
        cart_rec = get_last_cart()
        self.cart_id.set(cart_rec.did)
        self.system.set(cart_rec.system_id)
        self.profile.set(self.profile_idx[cart_rec.user_id])

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

    def create_add_locationBtn(self, parent):
        # recreate in new row
        add_locationBtn = Button(
            parent,
            image=self.addImgS,
            command=lambda: self.add_location(parent))
        add_locationBtn.image = self.addImgS
        add_locationBtn.grid(
            row=3, column=0, sticky='nw', padx=5, pady=2)
        # mlogger.debug('Created addlocBtn ({}, child of gridFrm {})'.format(
        #     add_locationBtn.winfo_id(), parent.winfo_id()))

    def create_grid(self, parent, row, loc=(None, '', '', '', '')):
        unitFrm = Frame(parent)
        unitFrm.grid(
            row=row, column=0, sticky='snew')
        # mlogger.debug(
        #     'New grid unitFrm ({}): row: {}, parent locsFrm: {}'.format(
        #         unitFrm.winfo_id(), row, parent.winfo_id()))
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

    def create_order_frame(self, parent, order):
        # Comboboxes and entries
        orderFrm = Frame(parent)
        orderFrm.grid(
            row=1, column=0, sticky='snew', padx=5, pady=5)

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
        oidEnt = Entry(orderFrm)
        oidEnt.grid(
            row=0, column=3, sticky='snew', padx=5, pady=2)
        if order.oid:
            oidEnt.insert(END, order.oid)
        oidEnt['state'] = 'readonly'

        Label(orderFrm, text='bib #: ').grid(
            row=1, column=2, sticky='snw', padx=2, pady=2)
        bidEnt = Entry(orderFrm,)
        bidEnt.grid(
            row=1, column=3, sticky='snew', padx=5, pady=2)
        if order.bid:
            bidEnt.insert(END, order.bid)
        bidEnt['state'] = 'readonly'

        Label(orderFrm, text='wlo #: ').grid(
            row=2, column=2, sticky='snw', padx=2, pady=2)
        wloEnt = Entry(orderFrm)
        wloEnt.grid(
            row=2, column=3, sticky='snew', padx=5, pady=2)
        if order.wlo:
            wloEnt.insert(END, order.wlo)
        wloEnt['state'] = 'readonly'

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
            'wloEnt': wloEnt,
        }

        snapshot = create_order_snapshot(tracker)

        return tracker, snapshot

    def create_resource_frame(self, parent, resource):
        resourceFrm = Frame(parent)
        resourceFrm.grid(
            row=0, column=0, columnspan=4, sticky='snew', padx=5, pady=5)
        resourceFrm.columnconfigure(3, minsize=710)

        # provide description data
        if resource.dup_catalog is None:
            catalogImg = self.notcheckedImg
            res_dup_msg = 'catalog dups\nnot checked'
        elif resource.dup_catalog:
            res_dup_msg = 'found catalog duplicate'
            catalogImg = self.foundImg
        else:
            res_dup_msg = 'no dups in catalog'
            catalogImg = self.notfoundImg

        if resource.isbn:
            keyword = resource.isbn
        elif resource.upc:
            keyword = resource.upc
        else:
            keyword = None
            res_dup_msg = 'unable to search catalog'

        catalogBtn = Button(
            resourceFrm,
            image=catalogImg,
            command=lambda: self.show_in_catalog(keyword))
        catalogBtn.grid(
            row=0, column=0, sticky='nw', padx=2, pady=5)
        self._createToolTip(catalogBtn, res_dup_msg)

        if resource.dup_babel:
            babeldupBtn = Button(
                resourceFrm,
                image=self.babeldupImg)
            babeldupBtn.grid(
                row=1, column=0, sticky='nw', padx=2, pady=5)
            self._createToolTip(babeldupBtn, 'previously ordered')

        # display Text widget
        resdataTxt = Text(
            resourceFrm,
            # width=65,
            height=8,
            background='SystemButtonFace',
            borderwidth=0)
        resdataTxt.grid(
            row=0, column=1, rowspan=10, columnspan=3,
            sticky='snew', padx=10, pady=5)

        self.populate_resource_data_widget(resdataTxt, resource)

        editBtn = Button(
            resourceFrm,
            image=self.editImgS,
            command=lambda: self.edit_resource(parent.master.winfo_id()))
        editBtn.image = self.editImgS
        editBtn.grid(
            row=0, column=4, sticky='ne', padx=5, pady=5)

        deleteBtn = Button(
            resourceFrm,
            image=self.deleteImgS,
            command=lambda: self.delete_resource(parent.master))
        deleteBtn.grid(
            row=0, column=5, sticky='ne', padx=2, pady=5)

        tracker = {
            'resource_id': resource.did,
            'resourcefrm': resourceFrm,
            'catalogBtn': catalogBtn,
            'resdataTxt': resdataTxt
        }

        return tracker

    def delete_cart(self):
        msg = 'Are you sure you want to delete entire cart?'
        if messagebox.askokcancel('Deletion', msg):
            delete_data_by_did(Cart, self.cart_id.get())
            self.controller.show_frame('CartsView')

    def delete_resource(self, ntb):
        msg = 'Are you sure you want to delete order?'
        if messagebox.askokcancel('Deletion', msg):
            order_id = self.tracker[ntb.winfo_id()]['order']['order_id']

            delete_data_by_did(Order, order_id)
            self.tracker.pop(ntb.winfo_id(), None)
            self.order_ids.remove(order_id)
            ntb.destroy()
            self.update_funds_tally()

    def display_selected_orders(self, order_ids):
        self.cur_manager.busy()
        self._redo_preview_frame()
        self.tracker = OrderedDict()
        self.previous_snapshot = dict()
        recs = get_orders_by_id(order_ids)
        row = 0
        cart_no = self.disp_start + 1
        for orec in recs:
            ntb = self.order_widget(
                self.preview_frame, row + 1, orec, cart_no)
            ntb.grid(
                row=row, column=0, sticky='snew', padx=2, pady=2)
            row += 1
            cart_no += 1
        self.cur_manager.notbusy()

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
                    # mlogger.debug(f'Active DistrSet {dist_rec}')
                    self.dist_id.set(dist_rec.did)

                    self.grid_idx = create_name_index(
                        DistGrid,
                        distset_id=dist_rec.did)

                    # populate gridCbx values
                    for values in self.tracker.values():
                        gridCbx = values['grid']['gridCbx']
                        values = sorted(self.grid_idx.values())
                        gridCbx['values'] = values
                        glob_grid_values = values[:]
                        glob_grid_values.insert(0, 'keep current')
                        self.globgridCbx['values'] = glob_grid_values

    def edit_resource(self, ntb_id=None):
        if ntb_id is not None:
            resource_id = self.tracker[ntb_id]['resource']['resource_id']
            edit_widget = EditResourceWidget(
                self, resource_id=resource_id, **self.app_data)
            self.wait_window(edit_widget.top)

            # update display
            resdataTxt = self.tracker[ntb_id]['resource']['resdataTxt']
            summaryTxt = self.tracker[ntb_id]['more_res']['summaryTxt']
            resource_rec = get_record(Resource, did=resource_id)
            self.populate_resource_data_widget(resdataTxt, resource_rec)
            self.populate_more_tab_summary(
                summaryTxt, resource_rec.misc, resource_rec.summary)

        self.update_funds_tally()

    def find_duplicates_widget(self):
        top = Toplevel(self)
        top.title('Duplicates search')

        status = StringVar()
        status.set('Click check button to begin.')

        frm = Frame(top)
        frm.grid(
            row=0, column=0, sticky='snew', padx=10, pady=10)
        frm.columnconfigure(0, minsize=120)
        frm.columnconfigure(1, minsize=120)

        statusLbl = Label(
            frm, textvariable=status)
        statusLbl.grid(
            row=0, column=0, columnspan=2, sticky='snew', padx=5, pady=5)
        progbar = Progressbar(
            frm,
            mode='determinate',
            orient=HORIZONTAL)
        progbar.grid(
            row=1, column=0, columnspan=2, sticky='snew', pady=5)

        startBtn = Button(
            frm,
            image=self.saveImg,
            command=lambda: self.run_duplicate_search(top, progbar, status))
        startBtn.grid(
            row=2, column=0, sticky='sne', padx=10, pady=10)

        cancelBtn = Button(
            frm,
            image=self.deleteImg,
            command=top.destroy)
        cancelBtn.grid(
            row=2, column=1, sticky='snw', padx=10, pady=10)

    def help(self):
        # link to Github wiki with documentation here
        open_url('https://github.com/BookOps-CAT/babel/wiki/Cart')

    def more_tab_widget(self, tab, resource):
        title = f'{resource.title} / {resource.author}.'
        Label(tab, text=title, font=RBFONT).grid(
            row=0, column=0, sticky='snw', padx=5, pady=5)
        urlBtn = Button(
            tab, text='link',
            width=10,
            command=lambda aurl=resource.desc_url: open_url(aurl))
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

        self.populate_more_tab_summary(
            summaryTxt, resource.misc, resource.summary)

        return {'summaryTxt': summaryTxt}

    def nav_end(self):
        self.cur_manager.busy()
        if self.disp_end < len(self.order_ids):
            self.save_cart()
            self.disp_start = len(self.order_ids) - self.disp_number
            if self.disp_start < 0:
                self.disp_start = 0
            self.disp_end = len(self.order_ids)
            self.selected_order_ids = self.order_ids[-self.disp_number:]
            # mlogger.debug(f'Nav previous: {self.disp_start}:{self.disp_end}')
            # mlogger.debug(f'Selected order ids: {self.selected_order_ids}')
            self.display_selected_orders(self.selected_order_ids)
            self.orders_displayed.set(
                'records {}-{} out of {}'.format(
                    self.disp_start + 1,
                    self.disp_end,
                    len(self.order_ids)))
        self.cur_manager.notbusy()

    def nav_next(self):
        self.cur_manager.busy()
        if self.disp_end < len(self.order_ids):
            self.save_cart()
            self.disp_start = self.disp_end
            self.disp_end = self.disp_end + self.disp_number
            if self.disp_end > len(self.order_ids):
                self.disp_end = len(self.order_ids)
            self.selected_order_ids = self.order_ids[
                self.disp_start:self.disp_end]
            # mlogger.debug(f'Nav next: {self.disp_start}:{self.disp_end}')
            # mlogger.debug(f'Selected order ids: {self.selected_order_ids}')
            self.display_selected_orders(self.selected_order_ids)
            self.orders_displayed.set(
                'records {}-{} out of {}'.format(
                    self.disp_start + 1,
                    self.disp_end,
                    len(self.order_ids)))
        self.cur_manager.notbusy()

    def nav_previous(self):
        self.cur_manager.busy()
        if self.disp_start > 0:
            self.save_cart()
            self.disp_end = self.disp_start
            self.disp_start = self.disp_end - self.disp_number
            if self.disp_start < 0:
                self.disp_start = 0
                self.disp_end = len(self.order_ids)
            self.selected_order_ids = self.order_ids[
                self.disp_start:self.disp_end]

            self.display_selected_orders(self.selected_order_ids)
            self.orders_displayed.set(
                'records {}-{} out of {}'.format(
                    self.disp_start + 1,
                    self.disp_end,
                    len(self.order_ids)))
        self.cur_manager.notbusy()

    def nav_start(self):
        self.cur_manager.busy()
        if self.disp_start > 0:
            self.save_cart()
            self.disp_start = 0
            if len(self.order_ids) < self.disp_number:
                self.disp_end = len(self.order_ids)
            else:
                self.disp_end = self.disp_number
            self.selected_order_ids = self.order_ids[
                self.disp_start:self.disp_end]

            self.display_selected_orders(self.selected_order_ids)
            self.orders_displayed.set(
                'records {}-{} out of {}'.format(
                    self.disp_start + 1,
                    self.disp_end,
                    len(self.order_ids)))
        self.cur_manager.notbusy()

    def order_widget(self, parent, no, orec, cart_no):
        # displays individual notebook for resource & order data

        ntb = Notebook(
            parent,
            width=1000)

        # main tab
        mainTab = Frame(ntb)

        res_tracker = self.create_resource_frame(mainTab, orec.resource)
        ord_tracker, ord_snapshot = self.create_order_frame(mainTab, orec)

        gridFrm = LabelFrame(mainTab, text='grid')
        gridFrm.grid(
            row=1, column=1, sticky='snew', padx=10)

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

        copyBtn = Button(
            gridFrm,
            image=self.copyImgS,
            command=lambda: self.copy_grid_to_template(ntb.winfo_id()))
        copyBtn.grid(
            row=0, column=6, sticky='snw', padx=5, pady=2)
        # copyBtn.image = self.copyImgS

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
        # mlogger.debug('New locsFrm ({}, child of gridfrm {})'.format(
            # locsFrm.winfo_id(), gridFrm.winfo_id()))

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

        grids_snapshot = create_grids_snapshot(grids)

        self.create_add_locationBtn(gridFrm)

        # miscellaneous tab
        moreTab = Frame(ntb)
        more_tracker = self.more_tab_widget(
            moreTab, orec.resource)
        ntb.add(mainTab, text=f'title {cart_no}')
        ntb.add(moreTab, text='more')

        self.tracker[ntb.winfo_id()] = {
            'resource': res_tracker,
            'more_res': more_tracker,
            'order': ord_tracker,
            'grid': {
                'gridCbx': gridCbx,
                'locsFrm': locsFrm,
                'locs': grids
            },
        }

        self.previous_snapshot[ntb.winfo_id()] = dict(
            ord_snapshot=ord_snapshot,
            grids_snapshot=grids_snapshot)

        return ntb

    def observer(self, *args):
        if self.activeW.get() == 'CartView':
            if self.profile.get() != 'All users':

                # mlogger.debug('CartView raised.')

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

                # library
                self.library_idx = create_name_index(Library)
                values = (sorted(self.library_idx.values()))
                self.libCbx['values'] = values

                if cart.library_id:
                    self.library.set(self.library_idx[cart.library_id])
                    self.libCbx['state'] = 'disable'
                else:
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
                mlogger.debug('CartView activation funds refresh: {}'.format(
                    sorted(self.fund_idx.values())))

                # branches
                self.branch_idx = create_code_index(
                    Branch,
                    system_id=self.system.get())

                # shelf codes
                self.shelf_idx = create_code_index(
                    ShelfCode,
                    system_id=self.system.get())

                self.order_ids = get_order_ids(self.cart_id.get())
                self.disp_start = 0
                if self.disp_number > len(self.order_ids):
                    self.disp_end = len(self.order_ids)
                else:
                    self.disp_end = self.disp_number
                self.selected_order_ids = self.order_ids[
                    self.disp_start:self.disp_end]
                self.orders_displayed.set(
                    'records {}-{} out of {}'.format(
                        self.disp_start + 1,
                        self.disp_end,
                        len(self.order_ids)))
                self.display_selected_orders(self.selected_order_ids)
                self.update_funds_tally()

    def populate_more_tab_summary(self, text_widget, misc, summary):
        """
        args:
            text_widget: tkinter text widget obj
            misc: str
            summary: str
        """

        text_widget['state'] = 'normal'
        text_widget.delete('1.0', END)
        text_widget.insert(END, f'Misc:\n{misc}\n\n')
        text_widget.insert(END, f'Summary:\n{summary}\n')
        text_widget['state'] = 'disable'

    def populate_resource_data_widget(self, widget, resource):
        """
        args:
            widget: tkinter Text widget obj
            resource: datastore Resource obj
        """

        # prep data for display
        line1 = f'{resource.title} / {resource.author}.\n'
        if resource.add_title:
            line2 = f'{resource.add_title}\n'
        line3 = f'\tpublisher: {resource.pub_place} : {resource.publisher}, {resource.pub_date}.\n'
        line4 = f'\tseries: {resource.series}\n'
        line5 = f'\tISBN: {resource.isbn} | UPC: {resource.upc} | other no.: {resource.other_no}\n'
        line6 = f'\tlist price: ${resource.price_list:.2f} | discount price: ${resource.price_disc:.2f}'

        # empty widget for cases when repopulated
        widget['state'] = 'normal'
        widget.delete('1.0', END)

        widget.insert(END, line1)
        if resource.add_title:
            widget.insert(END, line2)
        else:
            widget.insert(END, '\n')
        widget.insert(END, line3)
        widget.insert(END, line4)
        widget.insert(END, line5)
        widget.insert(END, line6)

        widget.tag_add('header', '1.0', '2.end')
        widget.tag_config('header', font=RBFONT)
        widget.tag_add('normal', '3.0', '5.end')
        widget.tag_config('normal', font=LFONT)
        widget.tag_add('price', '6.0', '6.end')
        widget.tag_config('price', font=LFONT, foreground='tomato2')

        widget['state'] = 'disabled'

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

    def rename_cart(self):
        if self.cart_name.get():
            self.cartEnt['state'] = '!disable'
            self.statusCbx['state'] = 'readonly'
            if self.system.get() == 2:
                self.libCbx['state'] = 'readonly'

    def remove_location(self, removeBtn):
        ntb_id = removeBtn.master.master.master.master.master.winfo_id()
        locs = self.tracker[ntb_id]['grid']['locs']
        n = 0
        for l in locs:
            if l['removeBtn'] == removeBtn:
                parent = l['unitFrm']
                break
            n += 1
        locs.pop(n)
        self.tracker[ntb_id]['grid']['locs'] = locs
        parent.destroy()

    def reset(self):
        mlogger.debug('Reseting CartView variables.')
        self.order_ids = []
        self.library.set('')
        self.dist_set.set('')
        self.glob_grid_template.set('keep current')
        self.lang.set('keep current')
        self.vendor.set('keep current')
        self.mattype.set('keep current')
        self.price.set('')
        self.discount.set('')
        self.audn.set('keep current')
        self.poperline.set('')
        self.note.set('')
        self.dist_template.set('')
        self.new_dist.set('')
        self.grid_template.set('')
        self.new_grid.set('')
        self.poChb_var.set(0)
        self.noteChb_var.set(0)
        self.priceChb_var.set(0)
        self.discountChb_var.set(0)
        self.funds_tally.set('')

    def run_duplicate_search(self, top, progbar, status_var):
        self.cur_manager.busy()
        try:
            find_matches(self.cart_id.get(), progbar, status_var)
            self.cur_manager.notbusy()
        except BabelError as e:
            self.cur_manager.notbusy()
            messagebox.showerror('Web scraping error', e, parent=top)
        finally:
            # update display
            self.display_selected_orders(self.selected_order_ids)

    def save_cart(self):
        try:
            needs_validation = determine_needs_validation(self.cart_id.get())
            mlogger.debug(
                f'Cart needs validation: {needs_validation}')

            # take a new snapshot
            self.current_snapshot = dict()
            changed = []
            for key, value in self.tracker.items():
                ord_snapshot = create_order_snapshot(value['order'])
                grids_snapshot = create_grids_snapshot(value['grid']['locs'])
                current_snapshot = dict(
                    ord_snapshot=ord_snapshot,
                    grids_snapshot=grids_snapshot)

                if self.previous_snapshot[key] != current_snapshot:
                    order_id = value['order']['order_id']
                    mlogger.debug(
                        f'Order no.: {order_id} changed.')
                    changed.append(
                        dict(
                            order=value['order'],
                            grid=value['grid']))

            save_displayed_order_data(changed)

            # save cart data
            if str(self.cartEnt['state']) != 'disable':
                kwargs = {}
                kwargs['name'] = self.cartEnt.get().strip()
                if self.system.get() == 2 and self.library.get() != '':
                    if self.library.get() == 'branches':
                        library_id = 1
                    elif self.library.get() == 'research':
                        library_id = 2
                    kwargs['library_id'] = library_id

                elif self.system.get() == 1:
                    kwargs['library_id'] = 1
                rec = get_record(Status, name=self.status.get())
                kwargs['status_id'] = rec.did
                kwargs['updated'] = datetime.now()

                save_data(
                    Cart, self.cart_id.get(), **kwargs)

                if self.status.get() == 'finalized' and \
                        needs_validation:

                    # run validation
                    self.validation_report(final=True)
                    self.wait_window(self.validTop)

                    if self.cart_valid:
                        # assign blanketPO and wlo numbers
                        try:
                            assign_wlo_to_cart(self.cart_id.get())
                        except BabelError as e:
                            messagebox.showerror(
                                'WLO number error',
                                f'Unable to assign wlo #.\nError: {e}')
                        try:
                            assign_blanketPO_to_cart(self.cart_id.get())

                        except BabelError as e:
                            messagebox.showerror(
                                'BlanketPo error',
                                f'Unable to assign blanketPo.\nError: {e}')

                        self._redo_preview_frame()
                        self.display_selected_orders(self.selected_order_ids)
                    else:
                        # revert status
                        self.status.set('in-works')
                        rec = get_record(Status, name='in-works')
                        kwargs = {}
                        kwargs['status_id'] = rec.did
                        kwargs['updated'] = datetime.now()
                        save_data(
                            Cart, self.cart_id.get(), **kwargs)

                # disable cart widgets
                self.cartEnt['state'] = 'disable'
                self.libCbx['state'] = 'disable'
                self.statusCbx['state'] = 'disable'

            self.update_funds_tally()

        except BabelError as e:
            messagebox.showerror('Database error', e)

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

    def selective_grids_widget(self):
        """Lauches a widget to selectively appply distributions"""

        if has_library_assigned:
            system_id = self.system.get()
            profile_id = get_id_from_index(
                self.profile.get(), self.profile_idx)

            grids_widget = ApplyGridsWidget(
                self, system_id, profile_id, self.distr, **self.app_data)

            # create model top widgetd
            grids_widget.top.focus_set()
            grids_widget.top.grab_set()
            grids_widget.top.transient(self)
            self.wait_window(grids_widget.top)

            # update display in the cart
            self.display_selected_orders(self.selected_order_ids)
        else:
            messgebox.showwarning(
                'Missing data', 'Please select and save library first.')

    def search_observer(self, *args):
        """Triggers display of particular resource/order"""
        mlogger.debug(
            'Search observer: updating displayed resources to see '
            f'Order.did={self.searched_order.get()}')

    def search_widget(self):
        """ Widget to search carts"""
        search_widget = SearchCartWidget(self, **self.app_data)

    def show_fund_widget(self):
        # enforce library selection before proceeding
        if str(self.libCbx['state']) != 'disable':
            messagebox.showwarning(
                'Unfinished business...',
                'Please make sure to complete and save\n'
                'any cart name edits or library assigment\n'
                'before proceeding.')
        elif not has_library_assigned(self.cart_id.get()):
            messagebox.showwargning(
                'Incomplete cart',
                'Please assign a library and save your changes before\n'
                'applying funds.')
        else:
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
            self._createToolTip(applyBtn, 'apply selected funds')

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

            mlogger.debug(
                'Fund listbox in fundTop widget values: {}'.format(
                    sorted(self.fund_idx.values())))
            for code in sorted(self.fund_idx.values()):
                listbox.insert(END, code)

    def show_in_catalog(self, keyword):
        if keyword:
            if self.system.get() == 1:
                url = BPL_SEARCH_URL
            elif self.system.get() == 2:
                url = NYPL_SEARCH_URL
            else:
                url = None
            if url:
                open_url(f'{url}{keyword}')

    def tabulate_cart_widget(self):
        CartSummary(self, **self.app_data)

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

    def update_funds_tally(self):
        tally = tabulate_funds(self.cart_id.get())
        self.funds_tally.set(' | '.join(tally))

    def validation_override(self):
        self.cart_valid = True
        self.validTop.destroy()

    def validation_report(self, final=False):
        self.cur_manager.busy()
        issues_count, issues = validate_cart_data(
            self.cart_id.get())
        self.cur_manager.notbusy()

        if issues_count == 0:
            self.cart_valid = True
        else:
            self.cart_valid = False

        try:
            affected_records = list(issues.keys())[-1]
        except IndexError:
            affected_records = 0

        # generate report widget
        self.validTop = Toplevel(self)
        self.validTop.title('Cart validation report')

        frm = Frame(self.validTop)
        frm.grid(
            row=0, column=0, sticky='snew', padx=10, pady=10)

        scrollbar = Scrollbar(frm, orient=VERTICAL)
        scrollbar.grid(row=0, column=0, rowspan=5, sticky='snw', pady=5)

        vrepTxt = Text(
            frm,
            background='SystemButtonFace',
            borderwidth=0,
            wrap='word',
            yscrollcommand=scrollbar.set)
        vrepTxt.grid(
            row=0, column=1, rowspan=3, columnspan=2, sticky='snew', padx=5, pady=5)
        scrollbar['command'] = vrepTxt.yview

        if affected_records:
            vrepTxt.insert(
                END,
                f'Found {issues_count} problems in '
                f'{affected_records} orders\n\n')
        else:
            vrepTxt.insert(
                END,
                'No problems found :-). The cart is good to go.')

        for ord_no, ord_iss in issues.items():
            if ord_no == 0:
                vrepTxt.insert(
                    END,
                    f'cart issues: {ord_iss}\n\n')
            else:
                vrepTxt.insert(
                    END, f'order {ord_no}:\n')
                if ord_iss[0]:
                    vrepTxt.insert(
                        END, '  missing: {}\n'.format(','.join(ord_iss[0])))
                for gno, loc in ord_iss[1].items():
                    vrepTxt.insert(
                        END, '\tlocation {}: missing {}\n'.format(
                            gno,
                            ','.join(loc)))

        vrepTxt.tag_add('header', '1.0', '1.end')
        vrepTxt.tag_config('header', font=RBFONT, foreground='tomato2')
        vrepTxt['state'] = 'disabled'

        if final:
            if not self.cart_valid:
                cancelBtn = Button(
                    frm,
                    text='cancel',
                    width=10,
                    command=self.validTop.destroy)
                cancelBtn.grid(
                    row=3, column=2, sticky='sne', padx=10, pady=10)
                ovrwBtn = Button(
                    frm,
                    text='override',
                    width=10,
                    command=self.validation_override)
                ovrwBtn.grid(
                    row=3, column=3, sticky='snw', padx=10, pady=10)

    def _preview(self):
        self.preview_frame = Frame(
            self.preview_base)
        self.xscrollbar.config(command=self.preview_base.xview)
        self.yscrollbar.config(command=self.preview_base.yview)
        self.preview_base.create_window(
            (0, 0), window=self.preview_frame, anchor="nw",
            tags="self.preview_frame")
        self.preview_frame.bind("<Configure>", self._onFrameConfigure)

    def _onFrameConfigure(self, event):
        self.preview_base.config(scrollregion=self.preview_base.bbox('all'))

    def _redo_preview_frame(self):
        self.preview_frame.destroy()
        self._preview()

    # def on_mousewheel(self, event):
    #     self.preview_base.yview_scroll(
    #         int(-1 * (event.delta / 120)), "units")

    def _onValidateName(self, i, W):
        valid = True
        if W == str(self.cartEnt):
            if int(i) >= 75:
                valid = False
        if W == str(self.priceEnt):
            pass
        if W == str(self.discEnt):
            pass
        return valid

    def _onValidateQty(self, i, d, P):
        valid = True
        if d == '1' and not P.isdigit():
            valid = False
        if int(i) > 2:
            valid = False
        if i == '0' and P == '0':
            valid = False
        return valid

    def _onValidatePrice(self, i, d, P):
        mlogger.debug(
            f'_onValidatePrice entered: {P}, index: {i}, action {d}')
        valid = True
        # case 1
        if i == '0' and not P.isdigit() and d == '1':
            mlogger.debug('Failed case 1')
            valid = False
        # case 2
        if d == '1' and int(i) > 0:
            e = P[int(i)]
            if not e.isdigit() and e != '.':
                mlogger.debug('Failed case 2')
                valid = False
        return valid

    def _onValidateDiscount(self, i, d, P):
        valid = self._onValidatePrice(i, d, P)
        # case 3
        if d != '0' and float(P) > 100:
            mlogger.debug('Failed case 3')
            valid = False
        return valid

    def _createToolTip(self, widget, text):
        toolTip = ToolTip(widget)

        def enter(event):
            toolTip.showtip(text)

        def leave(event):
            toolTip.hidetip()

        widget.bind('<Enter>', enter)
        widget.bind('<Leave>', leave)
