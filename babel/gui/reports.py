from datetime import date
import logging
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from tkinter import *
from tkinter.ttk import *


from data.datastore import System, Library
from data.transactions_reports import get_fy_summary
from logging_settings import LogglyAdapter
from gui.data_retriever import get_record
from gui.utils import (BusyManager, ToolTip, enable_widgets, disable_widgets,
                       get_ids_from_index)
from gui.fonts import RBFONT, RFONT
from reports.reports import generate_fy_summary_by_user_chart

mlogger = LogglyAdapter(logging.getLogger('babel'), None)


class ReportView():
    """
    Pop-up window displaying selected report
    """

    def __init__(self, parent, report_data, **app_data):
        self.parent = parent
        # self.app_data = app_data
        self.system_id = app_data['system'].get()

        self.top = Toplevel(master=self.parent)
        self.top.title('Report')
        max_height = int((self.top.winfo_screenheight() - 250))

        # local variables
        self.top.report_title = StringVar()

        # icons
        downloadImg = app_data['img']['downloadM']

        # layout
        self.baseFrm = Frame(self.top)
        self.baseFrm.grid(
            row=0, column=0, sticky='snew', padx=20, pady=20)
        self.baseFrm.columnconfigure(0, minsize=20)
        self.baseFrm.columnconfigure(4, minsize=20)
        self.baseFrm.rowconfigure(4, minsize=20)

        self.repTitleLbl = Label(
            self.baseFrm, textvariable=self.top.report_title,
            font=RBFONT, anchor=CENTER)
        self.repTitleLbl.grid(
            row=1, column=1, columnspan=2, sticky='snew', padx=10, pady=20)

        # scrollbars
        self.xscrollbar = Scrollbar(self.baseFrm, orient=HORIZONTAL)
        self.xscrollbar.grid(
            row=3, column=1, columnspan=2, sticky='swe')
        self.yscrollbar = Scrollbar(self.baseFrm, orient=VERTICAL)
        self.yscrollbar.grid(
            row=2, column=3, sticky='nse')

        self.report_base = Canvas(
            self.baseFrm,
            height=max_height,
            width=1200,
            xscrollcommand=self.xscrollbar.set,
            yscrollcommand=self.yscrollbar.set)
        self.report_base.grid(
            row=2, column=1, columnspan=2, sticky='nwe')

        self.preview()

        # populate report
        self.generate_report(report_data)

    def unitFrm(self, parent, row, col):
        unit_frame = Frame(parent)
        unit_frame.grid(
            row=row, column=col, rowspan=4, sticky='snew', padx=5, pady=5)
        textWidget = Text(
            unit_frame,
            font=RFONT,
            width=35,
            height=80,
            wrap=NONE,
            background='SystemButtonFace',
            relief='flat')
        textWidget.grid(
            row=0, column=0, sticky='snew')
        textWidget.tag_configure('tag-right', justify='right')
        textWidget.tag_configure('tag-left', justify='left')
        textWidget.tag_configure('tag-center', justify='center')
        textWidget.tag_configure(
            'tag-header', justify='center', font=RBFONT, background='#B9DEF6',
            relief='raised')

        return textWidget

    def create_report_title(self, report_type, users_lbl):
        """
        Returns report title as string
        """
        if self.system_id:
            system = get_record(System, did=self.system_id).name
        else:
            system = None

        if report_type == 1:
            date_today = date.today()
            if date_today.month > 6:
                years = f'{date_today.year}-{date_today.year + 1}'
            else:
                years = f'{date_today.year - 1} to {date_today.year}'
            self.top.report_title.set(
                f'{system} fiscal year {years} to date summary\n'
                f'users: {", ".join(users_lbl)}')

        elif report_type == 2:
            self.top.report_title.set(
                f'{system} orders audience breakdown'
                f'({self.date_from.get()} to{self.date_to.get()})\n'
                f'{users}')
        elif report_type == 3:
            self.top.report_title.set(
                f'{system} orders by branch '
                f'({self.date_from.get()} to {self.date_to.get()})\n'
                f'{users}')
        elif report_type == 4:
            self.top.report_title(
                f'{system} orders by fund '
                f'({self.date_from.get()} to {self.date_to.get()})\n'
                f'{users}')
        elif report_type == 5:
            self.top.report_title.set(
                f'{system} orders by language '
                f'({self.date_from.get()} to {self.date_to.get()})\n'
                f'{users}')
        elif report_type == 6:
            self.top.report_title.set(
                f'{system} orders by material type '
                f'({self.date_from.get()} to {self.date_to.get()})\n'
                f'{users}')
        elif report_type == 7:
            self.top.report_title.set(
                f'{system} orders by vendor '
                f'({self.date_from.get()} to {self.date_to.get()})\n'
                f'{users}')

    def generate_report(self, data):
        self.create_report_title(data['report_type'], data['users_lbl'])
        if data['report_type'] == 1:
            self.report_one(data)

    def report_one(self, data):
        reportTxt = self.unitFrm(self.reportFrm, 0, 0)

        reportTxt.insert(END, 'carts status\n', 'tag-header')
        cats = [f'{x}: {y}' for x, y in data['status'].items()]
        for c in cats:
            reportTxt.insert(END, f'{c}\n\n', 'tag-center')

        reportTxt.insert(END, 'quantities\n', 'tag-header')
        reportTxt.insert(END, f'orders: {data["orders"]:,}\n', 'tag-center')
        reportTxt.insert(END, f'copies: {data["copies"]:,}\n\n', 'tag-center')

        reportTxt.insert(END, 'funds\n', 'tag-header')
        reportTxt.insert(
            END, data['funds'].to_string(
                index=False, justify='right', header=False),
            'tag-right')
        reportTxt.insert(END, '\n\n')

        reportTxt.insert(END, 'languages\n', 'tag-header')
        reportTxt.insert(
            END, data['langs'].to_string(
                index=False, justify='right', header=False),
            'tag-right')
        reportTxt.insert(END, '\n\n')

        reportTxt.insert(END, 'audiences\n', 'tag-header')
        reportTxt.insert(
            END, data['audns'].to_string(
                index=False, header=False, justify='right'),
            'tag-right')
        reportTxt.insert(END, '\n\n')

        reportTxt.insert(END, 'material type\n', 'tag-header')
        reportTxt.insert(
            END, data['mats'].to_string(
                index=False, header=False, justify='right'),
            'tag-right')
        reportTxt.insert(END, '\n\n')

        reportTxt.insert(END, 'vendors\n', 'tag-header')
        reportTxt.insert(END, data['vendors'].to_string(
            index=False, header=False, justify='right'),
            'tag-right')

        reportTxt['state'] = DISABLED

        # draw chart(s)
        # somehow the chart or its canvas interfere with baseFrm scrollbars:
        # when exiting top window, tkinter throws TclError unable to find
        # destroyed scrollbar widgets; not severe problem, but clean up in the
        # future
        chartFrm = Frame(self.reportFrm)
        chartFrm.grid(
            row=0, column=1, sticky='snew', padx=20, pady=5)

        ch1, ch2 = generate_fy_summary_by_user_chart(
            data['users_time'], data['langs_time'])
        canvas1 = FigureCanvasTkAgg(ch1, chartFrm)
        canvas1.draw()
        canvas1.get_tk_widget().grid(
            row=0, column=1, sticky='ne')
        canvas2 = FigureCanvasTkAgg(ch2, chartFrm)
        canvas2.draw()
        canvas2.get_tk_widget().grid(
            row=1, column=1, sticky='ne')

    def preview(self):
        self.reportFrm = Frame(
            self.report_base)
        self.xscrollbar.config(command=self.report_base.xview)
        self.yscrollbar.config(command=self.report_base.yview)
        self.report_base.create_window(
            (0, 0), window=self.reportFrm, anchor="nw",
            tags="self.reportFrm")
        self.reportFrm.bind("<Configure>", self.onFrameConfigure)

    def onFrameConfigure(self, event):
        self.report_base.config(scrollregion=self.report_base.bbox('all'))


class ReportWizView(Frame):
    """
    Guides user through report criteria
    """

    def __init__(self, parent, controller, **app_data):
        self.parent = parent
        Frame.__init__(self, parent)
        self.controller = controller
        self.app_data = app_data
        self.activeW = app_data['activeW']
        self.activeW.trace('w', self.observer)
        self.system = app_data['system']
        self.system.trace('w', self.system_observer)
        self.max_height = int((self.winfo_screenheight() - 200))
        self.cur_manager = BusyManager(self)

        # icons
        self.runImg = app_data['img']['runM']
        self.helpImg = app_data['img']['help']

        # variables
        self.date_from = StringVar()
        self.date_to = StringVar()
        self.library = StringVar()
        self.report = IntVar()

        # layout
        self.rowconfigure(3, minsize=15)

        # register date validation
        self.vldt = (self.register(self.onValidateDate),
                     '%i', '%d', '%P')

        # widgets
        genRepBtn = Button(
            self,
            image=self.runImg,
            command=self.generate_report)
        genRepBtn.grid(
            row=0, column=0, sticky='sw', padx=20, pady=5)
        self.createToolTip(genRepBtn, 'generate report')

        helpBtn = Button(
            self,
            image=self.helpImg,
            command=self.help)
        helpBtn.grid(
            row=1, column=0, sticky='sw', padx=20, pady=5)
        self.createToolTip(helpBtn, 'help')

        # criteria frame
        critFrm = LabelFrame(self, text='report wizard')
        critFrm.grid(
            row=0, column=1, rowspan=20, sticky='snew', padx=25, pady=10)
        critFrm.columnconfigure(0, minsize=20)
        critFrm.columnconfigure(5, minsize=20)
        critFrm.rowconfigure(14, minsize=10)

        Label(critFrm, text='criteria:', font=RBFONT).grid(
            row=1, column=1, columnspan=4, sticky='snw', padx=2, pady=10)
        Label(critFrm, text='date from:').grid(
            row=2, column=1, sticky='sne', padx=2, pady=5)
        dateFromEnt = Entry(
            critFrm, textvariable=self.date_from,
            font=RFONT,
            width=17,
            validate='key', validatecommand=self.vldt)
        self.createToolTip(dateFromEnt, 'YYYY-MM-DD')
        dateFromEnt.grid(
            row=2, column=2, sticky='snw', padx=2, pady=5)
        Label(critFrm, text='to:').grid(
            row=2, column=3, sticky='snew', padx=2, pady=5)
        dateToEnt = Entry(
            critFrm, textvariable=self.date_to,
            font=RFONT,
            width=17,
            validate='key', validatecommand=self.vldt)
        dateToEnt.grid(
            row=2, column=4, sticky='snw', padx=2, pady=5)
        self.createToolTip(dateToEnt, 'YYYY-MM-DD')

        Label(critFrm, text='library:').grid(
            row=3, column=1, sticky='sne', padx=2, pady=5)
        self.libCbx = Combobox(
            critFrm, textvariable=self.library,
            font=RFONT,
            width=15,
            state='readonly')
        self.libCbx.grid(
            row=3, column=2, sticky='snew', padx=2, pady=5)

        # users
        Label(critFrm, text='users:').grid(
            row=4, column=1, sticky='ne', padx=2, pady=5)
        scrollbar = Scrollbar(critFrm, orient=VERTICAL)
        scrollbar.grid(
            row=4, column=3, sticky='snw', pady=5)
        self.userLst = Listbox(
            critFrm,
            font=RFONT,
            selectmode=EXTENDED,
            width=15,
            yscrollcommand=scrollbar.set)
        self.userLst.grid(
            row=4, column=2, sticky='snew', pady=5)
        scrollbar.config(command=self.userLst.yview)

        Separator(critFrm, orient=HORIZONTAL).grid(
            row=5, column=1, columnspan=4, sticky='snew', padx=2, pady=15)

        # report types
        Label(critFrm, text='report type:', font=RBFONT).grid(
            row=6, column=1, columnspan=4, sticky='snw', padx=2, pady=10)
        fyBtn = Radiobutton(
            critFrm, text='current FY summary',
            variable=self.report, value=1)
        fyBtn.grid(
            row=7, column=1, columnspa=2, sticky='snw', padx=2, pady=5)
        audnBtn = Radiobutton(
            critFrm, text='audience',
            variable=self.report, value=2)
        audnBtn.grid(
            row=8, column=1, columnspan=2, sticky='snw', padx=2, pady=5)
        branchBtn = Radiobutton(
            critFrm, text='branch',
            variable=self.report, value=3)
        branchBtn.grid(
            row=9, column=1, columnspan=2, sticky='snw', padx=2, pady=5)
        fundBtn = Radiobutton(
            critFrm, text='fund',
            variable=self.report, value=4)
        fundBtn.grid(
            row=10, column=1, columnspan=2, sticky='snw', padx=2, pady=5)
        langBtn = Radiobutton(
            critFrm, text='language',
            variable=self.report, value=5)
        langBtn.grid(
            row=11, column=1, columnspa=2, sticky='snw', padx=2, pady=5)
        matBtn = Radiobutton(
            critFrm, text='material type',
            variable=self.report, value=6)
        matBtn.grid(
            row=12, column=1, columnspa=2, sticky='snw', padx=2, pady=5)
        vendorBtn = Radiobutton(
            critFrm, text='vendor',
            variable=self.report, value=7)
        vendorBtn.grid(
            row=13, column=1, columnspan=2, sticky='snw', padx=2, pady=5)

    def validate_criteria(self):
        """
        Returns formated msg to be dispolayed to user about
        any possible criteria issues
        """
        # validate all required elemnets are set
        issues = []
        msg = None

        if self.system.get() not in (1, 2):
            issues.append('- library system not defined')
        if self.report.get() != 1 and not self.date_from.get():
            issues.append('- undefined starting date')
        if self.report.get() != 1 and not self.date_to.get():
            issues.append('- undefined ending date')
        if not self.report.get():
            issues.append('- unspecified report type')

        # validate dates
        try:
            if self.report.get() != 1:
                date.fromisoformat(self.date_from.get())
                date.fromisoformat(self.date_to.get())
        except ValueError:
            issues.append('- invalid date format')

        if issues:
            msg = '\n'.join(issues)

        return msg

    def generate_report(self):
        """
        Creates specified report in a pop up window
        """
        criteria_issues = self.validate_criteria()
        if not criteria_issues:
            report_data = self.analyze_data()
            if report_data:
                ReportView(
                    self, report_data, **self.app_data)
            else:
                messagebox.showinfo(
                    'Info', 'No data matching criteria')

        else:
            messagebox.showwarning(
                'Criteria error', f'Errors:\n{criteria_issues}')

    def map_selected_users_to_datastore_id(self, users):
        """
        Maps selected users to datastore user.did
        returns:
            datastore_user_ids: list of int, list of datastore user dids
        """
        datastore_user_ids = [x for x in get_ids_from_index(
            users, self.app_data['profile_idx'])]

        return datastore_user_ids

    def get_selected_users(self):
        """
        Returns a list of selected user names
        """
        lst_ids = self.userLst.curselection()
        users = [self.userLst.get(i) for i in lst_ids]
        return users

    def analyze_data(self):
        report_data = None
        system_id = self.system.get()
        users = self.get_selected_users()
        user_ids = self.map_selected_users_to_datastore_id(users)

        if self.library.get() == 'any':
            library_id = None
        else:
            library_id = get_record(Library, name=self.library.get()).did

        try:
            if self.report.get() == 1:
                report_data = get_fy_summary(
                    system_id, library_id, user_ids)

            report_data['report_type'] = self.report.get()
            if users:
                report_data['users_lbl'] = users
            else:
                report_data['users_lbl'] = 'All users'

        except BabelError as e:
            messagebox.showerror(
                'Report error', e)
        finally:
            return report_data

    def help(self):
        print('display online help here')

    def system_observer(self, *args):
        if self.activeW.get() == 'ReportWizView':
            if self.system.get() == 1:
                self.library.set('branches')
                disable_widgets([self.libCbx])
            else:
                enable_widgets([self.libCbx])
                self.libCbx['state'] = 'readonly'
                self.library.set('any')

    def observer(self, *args):
        if self.activeW.get() == 'ReportWizView':

            self.libCbx['values'] = (
                'any',
                'branches',
                'research'
            )

            self.userLst.delete(0, END)
            self.userLst.insert(END, 'all')
            for user in sorted(self.app_data['profile_idx'].values()):
                self.userLst.insert(END, user)
            self.system_observer()

    def onValidateDate(self, i, d, P):
        mlogger.debug(
            f'onValidteDate: index={i}, action={d}, string={P}')
        valid = True
        if int(i) < 4:
            if i == '0' and d == '1':
                if P != '2':
                    valid = False

            if i == '1' and d == '1':
                if P != '20':
                    valid = False

        if i == '4' and d == '1':
            if P[int(i)][-1] != '-':
                valid = False

        if i == '5' and d == '1':
            if P[int(i)][-1] not in ('0', '1'):
                valid = False

        if i == '6' and d == '1':
            if not P[int(i)][-1].isdigit():
                valid = False

        if i == '7' and d == '1':
            if P[int(i)][-1] != '-':
                valid = False

        if i == '8' and d == '1':
            if P[int(i)][-1] not in ('0', '1', '2', '3'):
                valid = False

        if i == '9' and d == '1':
            if not P[int(i)][-1].isdigit():
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
