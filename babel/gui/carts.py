import logging
from os import path
import shelve
from tkinter import *
from tkinter.ttk import *
from tkinter import messagebox, filedialog


from errors import BabelError
from data.datastore import Cart, Library, Status
from data.transactions_carts import (add_sierra_ids_to_orders,
                                     create_cart_copy,
                                     export_orders_to_marc_file,
                                     get_cart_data_for_order_sheet,
                                     get_carts_data)
from gui.data_retriever import get_record, delete_data_by_did
from gui.fonts import RFONT
from gui.utils import BusyManager, ToolTip, open_url
from ingest.xlsx import save2spreadsheet
from paths import USER_DATA, MY_DOCS
from reports.carts import summarize_cart


mlogger = logging.getLogger('babel_logger')


class CopyCartWidget:
    """
    Widget for copying entire cart
    """

    def __init__(self, parent, source_cart_id,
                 source_cart_name, **app_data):
        self.parent = parent
        self.source_cart_id = source_cart_id
        self.source_cart_name = source_cart_name
        self.app_data = app_data
        self.profile_idx = self.app_data['profile_idx']

        top = self.top = Toplevel(master=self.parent)
        top.title('Copy cart')
        self.cur_manager = BusyManager(self.top)

        # variables
        self.system = StringVar()
        self.profile = StringVar()
        self.profiles = sorted(self.profile_idx.values())
        self.new_cart_name = StringVar()
        self.status = StringVar()

        # icons
        saveImg = self.app_data['img']['save']
        closeImg = self.app_data['img']['delete']

        # register cart name validator
        self.vlcn = (top.register(self.onValidateCartName),
                     '%P')

        frm = Frame(top)
        frm.grid(
            row=0, column=0, sticky='snew', padx=20, pady=20)

        Label(frm, text=f'Copying "{self.source_cart_name}"').grid(
            row=0, column=0, columnspan=4, padx=10, pady=10, sticky='snew')

        Label(frm, text='system:').grid(
            row=1, column=0, sticky='snw', padx=10, pady=5)
        systemCbx = Combobox(
            frm,
            font=RFONT,
            values=['NYPL', 'BPL'],
            state='readonly',
            textvariable=self.system)
        systemCbx.grid(
            row=2, column=0, sticky='snew', padx=10, pady=5)

        Label(frm, text='profile:').grid(
            row=1, column=1, sticky='snw', padx=10, pady=5)
        profileCbx = Combobox(
            frm,
            font=RFONT,
            values=self.profiles,
            state='readonly',
            textvariable=self.profile)
        profileCbx.grid(
            row=2, column=1, sticky='snew', padx=10, pady=5)

        Label(frm, text='new cart name:').grid(
            row=3, column=0, columnspan=2, sticky='snw', padx=10, pady=5)
        cart_nameEnt = Entry(
            frm,
            font=RFONT,
            textvariable=self.new_cart_name,
            validate="key", validatecommand=self.vlcn)
        cart_nameEnt.grid(
            row=4, column=0, columnspan=2, sticky='snew', padx=10, pady=10)

        statusLbl = Label(
            frm,
            textvariable=self.status)
        statusLbl.grid(
            row=5, column=0, columnspan=2, sticky='snew', padx=10, pady=5)

        okBtn = Button(
            frm,
            image=saveImg,
            command=self.create_copy)
        okBtn.grid(
            row=6, column=0, sticky='sne', padx=25, pady=10)

        cancelBtn = Button(
            frm,
            image=closeImg,
            command=top.destroy)
        cancelBtn.grid(
            row=6, column=1, sticky='snw', padx=25, pady=10)

    def create_copy(self):
        try:
            self.cur_manager.busy()
            create_cart_copy(
                self.source_cart_id, self.system.get(),
                self.profile.get(), self.profile_idx,
                self.new_cart_name.get(), self.status)
            self.cur_manager.notbusy()
        except BabelError as e:
            self.cur_manager.notbusy()
            messagebox.showerror('Copying Error', e)

    def onValidateCartName(self, P):
        valid = True
        if len(P) > 50:
            valid = False
        if ('(' in P or ')' in P):
            valid = False

        return valid


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
        self.cur_manager = BusyManager(self)

        # local variables
        self.status_filter = StringVar()
        self.selected_cart_id = IntVar()
        self.selected_cart_name = StringVar()
        self.selected_cart_owner = StringVar()

        # images
        # addImg = self.app_data['img']['add']
        editImg = self.app_data['img']['edit']
        self.deleteImg = self.app_data['img']['delete']
        self.saveImg = self.app_data['img']['save']
        helpImg = self.app_data['img']['help']
        viewImg = self.app_data['img']['view']
        self.viewImgS = self.app_data['img']['viewS']
        copyImg = self.app_data['img']['copy']
        marcImg = self.app_data['img']['marc']
        sheetImg = self.app_data['img']['sheet']
        linkImg = self.app_data['img']['link']

        list_height = int((self.winfo_screenheight() - 100) / 25)

        Label(self, text='selected: ').grid(
            row=0, column=0, sticky='snw', padx=10, pady=5)
        self.selcartLbl = Label(
            self, textvariable=self.selected_cart_name, font=RFONT)
        self.selcartLbl.grid(
            row=0, column=0, sticky='sne', pady=5)

        # carts treeview
        columns = (
            'cart_id', 'cart', 'date', 'status', 'owner')

        self.cartTrv = Treeview(
            self,
            columns=columns,
            displaycolumns=columns[1:],
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
            image=viewImg,
            command=self.view_data)
        # self.viewBtn.image = self.viewImg
        self.viewBtn.grid(
            row=1, column=0, sticky='sw', padx=10, pady=5)
        self.createToolTip(self.viewBtn, 'view cart')

        self.editBtn = Button(
            self.actionFrm,
            image=editImg,
            command=self.edit_data)
        # self.editBtn.image = editImg
        self.editBtn.grid(
            row=2, column=0, sticky='sw', padx=10, pady=5)
        self.createToolTip(self.editBtn, 'edit cart')

        self.marcBtn = Button(
            self.actionFrm,
            image=marcImg,
            command=self.create_marc_file)
        # self.marcBtn.image = marcImg
        self.marcBtn.grid(
            row=3, column=0, sticky='sw', padx=10, pady=5)
        self.createToolTip(self.marcBtn, 'create MARC file')

        self.sheetBtn = Button(
            self.actionFrm,
            image=sheetImg,
            command=self.create_order_sheet)
        # self.sheetBtn.image = sheetImg
        self.sheetBtn.grid(
            row=4, column=0, sticky='sw', padx=10, pady=5)
        self.createToolTip(self.sheetBtn, 'create order sheet')

        self.copyBtn = Button(
            self.actionFrm,
            image=copyImg,
            command=self.copy_data)
        # self.copyBtn.image = copyImg
        self.copyBtn.grid(
            row=5, column=0, sticky='sw', padx=10, pady=5)
        self.createToolTip(self.copyBtn, 'copy cart')

        self.linkBtn = Button(
            self.actionFrm,
            image=linkImg,
            command=self.link_ids)
        # self.linkBtn.image = linkImg
        self.linkBtn.grid(
            row=6, column=0, sticky='sw', padx=10, pady=5)
        self.createToolTip(self.linkBtn, 'link IDs')

        self.deleteBtn = Button(
            self.actionFrm,
            image=self.deleteImg,
            command=self.delete_data)
        # self.deleteBtn.image = self.deleteImg
        self.deleteBtn.grid(
            row=7, column=0, sticky='sw', padx=10, pady=5)
        self.createToolTip(self.deleteBtn, 'delete cart')

        self.helpBtn = Button(
            self.actionFrm,
            image=helpImg,
            command=self.help)
        # self.helpBtn.image = helpImg
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
        self.cur_manager.busy()
        # reset cartdataTxt
        self.cartdataTxt['state'] = 'normal'
        self.cartdataTxt.delete(1.0, END)

        # display basic info
        summary = self.generate_cart_summary(self.selected_cart_id.get())
        if summary:
            self.cartdataTxt.insert(END, summary)

            self.cartdataTxt['state'] = 'disable'
            self.cur_manager.notbusy()
        else:
            self.cur_manager.notbusy()

    def generate_cart_summary(self, cart_id):
        cart_rec = get_record(Cart, did=cart_id)
        if cart_rec:
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
                lines.append(
                    f'\t{fund}: ${values["total_cost"]:.2f}, '
                    f'copies: {values["copies"]}, titles: {values["titles"]}')

            return '\n'.join(lines)

    def edit_data(self):
        if self.selected_cart_id.get():
            # figure out profile cart belongs to first
            self.profile.set(self.selected_cart_owner.get())
            self.active_id.set(self.selected_cart_id.get())
            self.controller.show_frame('CartView')

    def copy_data(self):
        if self.selected_cart_id.get():
            ccw = CopyCartWidget(
                self, self.selected_cart_id.get(),
                self.selected_cart_name.get(), **self.app_data)
            self.wait_window(ccw.top)
            self.observer()

    def delete_data(self):
        if self.selected_cart_id.get():
            msg = 'Are you sure you want to delete\n' \
                f'"{self.selected_cart_name.get()} ' \
                f'({self.selected_cart_owner.get()})" cart?'
            if messagebox.askokcancel('Deletion', msg):
                self.cur_manager.busy()
                delete_data_by_did(Cart, self.selected_cart_id.get())
                curItem = self.cartTrv.focus()
                self.cartTrv.delete(curItem)
                self.selected_cart_id.set(0)
                self.selected_cart_name.set('')
                self.cur_manager.notbusy()

    def link_ids(self):
        source_fh = self.ask_for_source()
        try:
            self.cur_manager.busy()
            add_sierra_ids_to_orders(source_fh, self.system.get())
            self.cur_manager.notbusy()
            messagebox.showinfo(
                'Linking IDs',
                'Sierra bib and order numbers linked successfully.')

        except BabelError as e:
            self.cur_manager.notbusy()
            messagebox.showerror(
                'Sierra IDs Error',
                f'Unable to link Sierra IDs. Error: {e}')

    def help(self):
        open_url('https://github.com/BookOps-CAT/babel/wiki/Carts')

    def ask_for_destination(self, parent, title, cart_name):
        # retrieve initial directory
        if 'MARC' in title:
            initialdir_key = 'marc_out'
            extention = 'mrc'
            file_types = ('marc file', '*.mrc')
        elif 'sheet' in title:
            initialdir_key = 'sheet_out'
            extention = 'xlsx'
            file_types = ('sheet file', '*xlsx')

        user_data = shelve.open(USER_DATA)
        if initialdir_key in user_data:
            initialdir = user_data[initialdir_key]
        else:
            initialdir = MY_DOCS

        dst_fh = filedialog.asksaveasfilename(
            parent=parent,
            title=title,
            filetypes=(file_types, ),
            initialfile=f'{cart_name}.{extention}',
            initialdir=initialdir)

        if dst_fh:
            user_data[initialdir_key] = path.dirname(dst_fh)
            user_data.close()
            self.dst_fh.set(dst_fh)
        else:
            user_data.close()

    def ask_for_source(self):
        user_data = shelve.open(USER_DATA)
        if 'ids_dir' in user_data:
            initialdir = user_data['ids_dir']
        else:
            initialdir = MY_DOCS
        source_fh = filedialog.askopenfilename(
            parent=self,
            title='Sierra IDs file',
            initialdir=initialdir)
        if source_fh:
            user_data['ids_dir'] = path.dirname(source_fh)
        user_data.close()
        return source_fh

    def create_to_marc_widget(self, cart_rec):

        top = Toplevel()
        top.title('Saving to MARC file')

        self.dst_fh = StringVar()
        self.saving_status = StringVar()

        frm = Frame(top)
        frm.grid(
            row=0, column=0, sticky='snew', padx=20, pady=20)

        Label(frm, text=f'"{cart_rec.name}" cart').grid(
            row=0, column=0, columnspan=4, sticky='snew')
        nameEnt = Entry(
            frm,
            justify='right',
            textvariable=self.dst_fh,
            state='readonly',
            width=60)
        nameEnt.grid(
            row=1, column=0, columnspan=3, sticky='snew', pady=10)

        dstBtn = Button(
            frm,
            image=self.viewImgS,
            command=lambda: self.ask_for_destination(
                top, 'Save to MARC file', cart_rec.name))
        dstBtn.grid(
            row=1, column=4, sticky='snw', padx=5, pady=10)

        progbar = Progressbar(
            frm,
            mode='determinate',
            orient=HORIZONTAL,)
        progbar.grid(
            row=2, column=0, columnspan=4, sticky='snew', pady=5)

        statusLbl = Label(
            frm,
            textvariable=self.saving_status)
        statusLbl.grid(
            row=3, column=0, columnspan=2, sticky='snew', pady=5)

        btnFrm = Frame(frm)
        btnFrm.grid(
            row=4, column=0, columnspan=4, sticky='snew')
        btnFrm.columnconfigure(0, minsize=100)

        okBtn = Button(
            btnFrm,
            image=self.saveImg,
            command=lambda: self.launch_save(top, cart_rec, progbar))
        okBtn.grid(
            row=4, column=1, sticky='snew', padx=25, pady=10)

        cancelBtn = Button(
            btnFrm,
            image=self.deleteImg,
            command=top.destroy)
        cancelBtn.grid(
            row=4, column=2, sticky='snew', padx=25, pady=10)

    def launch_save(self, top, cart_rec, progbar):
        if self.dst_fh.get():
            try:
                self.cur_manager.busy()
                export_orders_to_marc_file(
                    self.dst_fh.get(), self.saving_status,
                    cart_rec, progbar)
                self.cur_manager.notbusy()

            except BabelError as e:
                self.cur_manager.notbusy()
                messagebox.showerror(
                    'Saving Error',
                    'Unable to create MARC file.\n'
                    'Run cart validation to find and correct any problems.\n'
                    f'Error: {e}',
                    parent=top)

    def create_marc_file(self):
        cart_rec = get_record(Cart, did=self.selected_cart_id.get())
        if cart_rec:
            status = get_record(Status, did=cart_rec.status_id)
            if status.name == 'finalized':
                self.create_to_marc_widget(cart_rec)
            else:
                msg = f'Cart "{cart_rec.name}" is not finalized.\n' \
                    'Please change cart status to proceed.'
                messagebox.showwarning('Output to MARC file', msg)

    def create_to_sheet_widget(self, cart_rec, system, cart_data):

        top = Toplevel()
        top.title('Saving to spreadsheet')

        self.dst_fh = StringVar()
        self.saving_status = StringVar()

        frm = Frame(top)
        frm.grid(
            row=0, column=0, sticky='snew', padx=20, pady=20)

        Label(frm, text=f'"{cart_rec.name}" cart').grid(
            row=0, column=0, columnspan=4, sticky='snew')
        nameEnt = Entry(
            frm,
            justify='right',
            textvariable=self.dst_fh,
            state='readonly',
            width=60)
        nameEnt.grid(
            row=1, column=0, columnspan=3, sticky='snew', pady=10)

        dstBtn = Button(
            frm,
            image=self.viewImgS,
            command=lambda: self.ask_for_destination(
                top, 'Save to spreadsheet', cart_rec.name))
        dstBtn.grid(
            row=1, column=4, sticky='snw', padx=5, pady=10)

        statusLbl = Label(
            frm,
            textvariable=self.saving_status)
        statusLbl.grid(
            row=2, column=0, columnspan=2, sticky='snew', pady=5)

        btnFrm = Frame(frm)
        btnFrm.grid(
            row=4, column=0, columnspan=4, sticky='snew')
        btnFrm.columnconfigure(0, minsize=100)

        okBtn = Button(
            btnFrm,
            image=self.saveImg,
            command=lambda: save2spreadsheet(
                self.dst_fh.get(), self.saving_status,
                system, cart_data) if self.dst_fh.get() else None)
        okBtn.grid(
            row=4, column=1, sticky='snew', padx=25, pady=10)

        cancelBtn = Button(
            btnFrm,
            image=self.deleteImg,
            command=top.destroy)
        cancelBtn.grid(
            row=4, column=2, sticky='snew', padx=25, pady=10)

    def create_order_sheet(self):
        if self.selected_cart_id.get():
            cart_rec = get_record(Cart, did=self.selected_cart_id.get())
            status = get_record(Status, did=cart_rec.status_id)

            if cart_rec.system_id == 1:
                systemLbl = 'Brooklyn Public Library'
            else:
                systemLbl = 'New York Public Library'

            if status.name == 'finalized':

                cart_data = []
                try:
                    cart_data = get_cart_data_for_order_sheet(
                        self.selected_cart_id.get())
                except BabelError as e:
                    messagebox.showerror(
                        'Retrieval Error',
                        'Unable to retrieve records from database.\n'
                        f'Error: {e}')

                if cart_data:
                    try:
                        self.create_to_sheet_widget(
                            cart_rec, systemLbl, cart_data)
                    except BabelError as e:
                        messagebox.showerror(
                            'Saving error', e)
            else:
                msg = f'Cart "{cart_rec.name}" is not finalized.\n' \
                    'Please change cart status to proceed.'
                messagebox.showwarning('Output to spreadsheet', msg)

    def selectItem(self, a):
        curItem = self.cartTrv.focus()
        try:
            self.selected_cart_id.set(
                self.cartTrv.item(curItem)['values'][0])
            self.selected_cart_name.set(
                self.cartTrv.item(curItem)['values'][1])
            self.selected_cart_owner.set(
                self.cartTrv.item(curItem)['values'][4])
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

            for cart in carts:
                self.cartTrv.insert(
                    '', END, values=cart)

    def createToolTip(self, widget, text):
        toolTip = ToolTip(widget)

        def enter(event):
            toolTip.showtip(text)

        def leave(event):
            toolTip.hidetip()

        widget.bind('<Enter>', enter)
        widget.bind('<Leave>', leave)
