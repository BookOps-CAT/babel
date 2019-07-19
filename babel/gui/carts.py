import logging
import shelve
from tkinter import *
from tkinter.ttk import *
from tkinter import messagebox, filedialog


from errors import BabelError
from data.datastore import Cart, Library, Status
from data.transactions_carts import (get_carts_data,
                                     export_orders_to_marc_file)
from gui.data_retriever import get_record
from gui.fonts import RFONT
from gui.utils import ToolTip, open_url
from paths import USER_DATA, MY_DOCS
from reports.carts import summarize_cart


mlogger = logging.getLogger('babel_logger')


class CartsView(Frame):
    """
    Gui for managing carts
    """

    def __init__(self, parent, controller, **app_data):
        self.parent = parent
        Frame.__init__(self, parent)
        self.controller = controller
        self.app_data = app_data
        self.activeW = app_data['activeW']
        self.activeW.trace('w', self.observer)
        self.system = app_data['system']
        self.system.trace('w', self.observer)
        self.profile = app_data['profile']
        self.profile.trace('w', self.observer)
        self.profile_idx = app_data['profile_idx']
        self.active_id = app_data['active_id']

        # local variables
        self.status_filter = StringVar()
        self.selected_cart = StringVar()
        self.cart_owner = StringVar()

        # images
        # addImg = self.app_data['img']['add']
        editImg = self.app_data['img']['edit']
        deleteImg = self.app_data['img']['delete']
        # saveImg = self.app_data['img']['save']
        helpImg = self.app_data['img']['help']
        self.viewImg = self.app_data['img']['view']
        copyImg = self.app_data['img']['copy']
        marcImg = self.app_data['img']['marc']
        sheetImg = self.app_data['img']['sheet']
        linkImg = self.app_data['img']['link']

        list_height = int((self.winfo_screenheight() - 100) / 25)

        Label(self, text='selected: ').grid(
            row=0, column=0, sticky='snw', padx=10, pady=5)
        self.selcartLbl = Label(
            self, textvariable=self.selected_cart, font=RFONT)
        self.selcartLbl.grid(
            row=0, column=0, sticky='sne', pady=5)

        # carts treeview
        columns = (
            'cart', 'date', 'status', 'owner')

        self.cartTrv = Treeview(
            self,
            columns=columns,
            displaycolumns=columns,
            show='headings',
            height=list_height)

        # sorting columns functionality
        for col in columns:
            self.cartTrv.heading(
                col,
                text=col,
                command=lambda _col=col: self.treeview_sort_column(
                    self.cartTrv, _col, False))

        self.cartTrv.column('cart', width=200)
        self.cartTrv.column('date', width=120, anchor='center')
        self.cartTrv.column('status', width=100, anchor='center')
        self.cartTrv.column('owner', width=100, anchor='center')
        self.cartTrv.grid(
            row=1, column=0, rowspan=20, sticky='snew')

        # cart treeview scrollbar
        scrollbar = Scrollbar(
            self, orient="vertical", command=self.cartTrv.yview)
        scrollbar.grid(row=1, column=1, rowspan=20, sticky='ns')
        self.cartTrv.configure(yscrollcommand=scrollbar.set)

        self.cartTrv.bind('<ButtonRelease-1>', self.selectItem)

        # action buttons frame
        self.actionFrm = Frame(self)
        self.actionFrm.grid(
            row=1, column=2, sticky='snew', padx=5, pady=10)

        self.viewBtn = Button(
            self.actionFrm,
            image=self.viewImg,
            command=self.view_data)
        self.viewBtn.image = self.viewImg
        self.viewBtn.grid(
            row=1, column=0, sticky='sw', padx=10, pady=5)
        self.createToolTip(self.viewBtn, 'view cart')

        self.editBtn = Button(
            self.actionFrm,
            image=editImg,
            command=self.edit_data)
        self.editBtn.image = editImg
        self.editBtn.grid(
            row=2, column=0, sticky='sw', padx=10, pady=5)
        self.createToolTip(self.editBtn, 'edit cart')

        self.marcBtn = Button(
            self.actionFrm,
            image=marcImg,
            command=self.create_marc_file)
        self.marcBtn.image = marcImg
        self.marcBtn.grid(
            row=3, column=0, sticky='sw', padx=10, pady=5)
        self.createToolTip(self.marcBtn, 'create MARC file')

        self.sheetBtn = Button(
            self.actionFrm,
            image=sheetImg,
            command=self.create_order_sheet)
        self.sheetBtn.image = sheetImg
        self.sheetBtn.grid(
            row=4, column=0, sticky='sw', padx=10, pady=5)
        self.createToolTip(self.sheetBtn, 'create order sheet')

        self.copyBtn = Button(
            self.actionFrm,
            image=copyImg,
            command=self.copy_data)
        self.copyBtn.image = copyImg
        self.copyBtn.grid(
            row=5, column=0, sticky='sw', padx=10, pady=5)
        self.createToolTip(self.copyBtn, 'copy cart')

        self.linkBtn = Button(
            self.actionFrm,
            image=linkImg,
            command=self.link_ids)
        self.linkBtn.image = linkImg
        self.linkBtn.grid(
            row=6, column=0, sticky='sw', padx=10, pady=5)
        self.createToolTip(self.linkBtn, 'link IDs')

        self.deleteBtn = Button(
            self.actionFrm,
            image=deleteImg,
            command=self.delete_data)
        self.deleteBtn.image = deleteImg
        self.deleteBtn.grid(
            row=7, column=0, sticky='sw', padx=10, pady=5)
        self.createToolTip(self.deleteBtn, 'delete cart')

        self.helpBtn = Button(
            self.actionFrm,
            image=helpImg,
            command=self.help)
        self.helpBtn.image = helpImg
        self.helpBtn.grid(
            row=8, column=0, sticky='sw', padx=10, pady=5)
        self.createToolTip(self.helpBtn, 'help')

        # cart data frame
        self.cartdataFrm = Frame(self)
        self.cartdataFrm.grid(
            row=1, column=3, rowspan=20, sticky='snew', padx=10, pady=5)

        self.cartdataTxt = Text(
            self.cartdataFrm,
            width=65,
            state=('disabled'),
            background='SystemButtonFace',
            borderwidth=0)
        self.cartdataTxt.grid(
            row=0, column=0, sticky='nsw')

    def view_data(self):
        self.active_id.set(self.cart_idx[self.selected_cart.get()])

        # reset cartdataTxt
        self.cartdataTxt['state'] = 'normal'
        self.cartdataTxt.delete(1.0, END)

        # display basic info
        summary = self.generate_cart_summary(self.active_id.get())
        self.cartdataTxt.insert(END, summary)

        self.cartdataTxt['state'] = 'disable'

    def generate_cart_summary(self, cart_id):
        cart_rec = get_record(Cart, did=self.active_id.get())
        owner = self.profile_idx[cart_rec.user_id]
        try:
            library = get_record(Library, did=cart_rec.library_id).name
        except AttributeError:
            library = ''

        stat_rec = get_record(Status, did=cart_rec.status_id)

        lines = []
        lines.append(f'cart: {cart_rec.name}')
        lines.append(f'status: {stat_rec.name}')
        lines.append(f'owner: {owner}')
        lines.append(
            f'created: {cart_rec.created} | updated: {cart_rec.updated}')
        lines.append(f'library: {library}')
        lines.append(f'blanketPO: {cart_rec.blanketPO}')

        # cart_details data
        details = summarize_cart(cart_id)
        lines.append(f'languages: {details["langs"]}')
        lines.append(f'vendors: {details["vendors"]}')
        lines.append(f'material types: {details["mattypes"]}')
        lines.append(f'audiences: {details["audns"]}')

        lines.append(f'funds:')
        for fund, values in details["funds"].items():
            lines.append(f'\t{fund}: ${values["damage"]:.2f}, copies: {values["copies"]}, titles: {values["titles"]}')

        return '\n'.join(lines)

    def edit_data(self):
        # figure out profile cart belongs to first
        self.profile.set(self.cart_owner.get())
        self.active_id.set(self.cart_idx[self.selected_cart.get()])
        self.controller.show_frame('CartView')

    def copy_data(self):
        pass

    def delete_data(self):
        pass

    def link_ids(self):
        pass

    def help(self):
        open_url('https://github.com/BookOps-CAT/babel/wiki/Carts')

    def ask_for_destination(self, parent, title, cart_name):
        # retrieve initial directory
        if 'MARC' in title:
            initialdir = 'marc_out'
            extention = 'mrc'
        elif 'sheet' in title:
            initialdir = 'sheet_out'
            extention = 'xlsx'
        else:
            initialdir = MY_DOCS
            extention = 'out'

        user_data = shelve.open(USER_DATA)
        if initialdir in user_data:
            initialdir = user_data[initialdir]
        else:
            initialdir = MY_DOCS

        dst_fh = filedialog.asksaveasfilename(
            parent=parent,
            title='Save to MARC file',
            filetypes=(('marc file', '*.mrc'),
                       ('sheet file', '*xlsx')),
            initialfile=f'{cart_name}.{extention}',
            initialdir=initialdir)

        if dst_fh:
            user_data[initialdir] = initialdir
            user_data.close()
            self.dst_fh.set(dst_fh)

    def create_to_marc_widget(self, cart_rec):

        top = Toplevel()
        top.title('Saving to MARC file')

        self.dst_fh = StringVar()
        self.saving_status = StringVar()

        frm = Frame(top)
        frm.grid(
            row=0, column=0, sticky='snew', padx=20, pady=20)
        Label(frm, text='file path:').grid(
            row=0, column=0, sticky='snew')
        nameEnt = Entry(
            frm,
            justify='right',
            textvariable=self.dst_fh)
        nameEnt.grid(
            row=1, column=0, columnspan=2, sticky='snew', pady=10)

        dstBtn = Button(
            frm,
            image=self.viewImg,
            command=lambda: self.ask_for_destination(
                top, 'Save to MARC file', cart_rec.name))
        dstBtn.grid(
            row=1, column=2, sticky='snw', padx=5, pady=10)

        statusLbl = Label(
            frm,
            textvariable=self.saving_status)
        statusLbl.grid(
            row=2, column=0, columnspan=2, sticky='snew', pady=10)

        progbar = Progressbar(
            frm,
            mode='determinate',
            orient=HORIZONTAL,)
        progbar.grid(
            row=3, column=0, columnspan=3, sticky='snew', pady=10)

        okBtn = Button(
            frm,
            text='create',
            command=lambda: export_orders_to_marc_file(
                self.dst_fh.get(), self.saving_status,
                cart_rec, progbar) if self.dst_fh.get() else None)
        okBtn.grid(
            row=4, column=0, sticky='snew', padx=25, pady=10)
        cancelBtn = Button(
            frm,
            text='close',
            command=top.destroy)
        cancelBtn.grid(
            row=4, column=1, sticky='snew', padx=25, pady=10)

        # top.wait_window()

    def create_marc_file(self):
        self.active_id.set(self.cart_idx[self.selected_cart.get()])
        cart_rec = get_record(Cart, did=self.active_id.get())
        status = get_record(Status, did=cart_rec.status_id)
        if status.name == 'finalized':
            try:
                self.create_to_marc_widget(cart_rec)
            except BabelError as e:
                messagebox.showerror(
                    'Saving error', e)
        else:
            msg = f'Cart {cart_rec.name} is not finalized.\n' \
                  'Please change cart status to proceed.'
            messagebox.showwarning('MARC file', msg)

    def create_order_sheet(self):
        pass

    def selectItem(self, a):
        curItem = self.cartTrv.focus()
        try:
            self.selected_cart.set(self.cartTrv.item(curItem)['values'][0])
            self.cart_owner.set(self.cartTrv.item(curItem)['values'][3])
        except IndexError:
            pass

    def treeview_sort_column(self, tv, col, reverse):
        tree_list = [(tv.set(k, col), k) for k in tv.get_children('')]
        tree_list.sort(reverse=reverse)

        # rearrange items in sorted positions
        for index, (val, k) in enumerate(tree_list):
            tv.move(k, '', index)

        # reverse sort next time
        tv.heading(
            col,
            command=lambda: self.treeview_sort_column(tv, col, not reverse))

    def observer(self, *args):
        if self.activeW.get() == 'CartsView':
            # delete current values
            self.cartTrv.delete(*self.cartTrv.get_children())

            # populate carts tree
            try:
                carts = get_carts_data(
                    self.system.get(), self.profile.get(),
                    self.status_filter.get())
            except BabelError as e:
                carts = {}
                messagebox.showerror(
                    'Retrieval error', e)

            self.cart_idx = {}
            for cart_id, cart in carts:
                self.cartTrv.insert(
                    '', END, values=cart)
                self.cart_idx[cart[0]] = cart_id

    def createToolTip(self, widget, text):
        toolTip = ToolTip(widget)

        def enter(event):
            toolTip.showtip(text)

        def leave(event):
            toolTip.hidetip()

        widget.bind('<Enter>', enter)
        widget.bind('<Leave>', leave)
