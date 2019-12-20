from datetime import date
import logging
from tkinter import *
from tkinter.ttk import *


from data.datastore import System, Library
from data.transactions_reports import get_fy_summary
from logging_settings import LogglyAdapter
from gui.data_retriever import get_record
from gui.utils import (BusyManager, ToolTip, enable_widgets, disable_widgets,
                       get_id_from_index)
from gui.fonts import RBFONT, RFONT


mlogger = LogglyAdapter(logging.getLogger('babel'), None)


class ReportUnitBase(Frame):
    """
    Factory for a individual report frames
    """

    def __init__(self, parent, heading, **app_data):
        self.parent = parent
        Frame.__init__(self, parent)
        self.app_data = app_data
        self.heading = StringVar()
        self.heading.set(heading)

        headingLbl = Label(
            self, textvariable=self.heading,
            font=RFONT)
        headingLbl.grid(
            row=0, column=0, sticky='snew', padx=10, pady=2)

        print(self.heading.get())


class ReportView():
    """
    Pop-up window displaying selected report
    """

    def __init__(self, parent, report_title, report_data, **app_data):
        self.parent = parent
        # self.app_data = app_data
        self.system_id = app_data['system'].get()
        self.user = app_data['profile'].get()

        self.top = Toplevel(master=self.parent)
        self.top.title('Report')

        # local variables
        self.top.report_title = StringVar()
        self.top.report_title.set(report_title)

        # icons
        downloadImg = app_data['img']['downloadM']

        # layout
        self.baseFrm = Frame(self.top)
        self.baseFrm.grid(
            row=0, column=0, sticky='snew', padx=20, pady=20)
        self.baseFrm.columnconfigure(0, minsize=20)
        # self.baseFrm.columnconfigure(1, minsize=600)
        self.baseFrm.columnconfigure(3, minsize=20)
        self.baseFrm.rowconfigure(0, minsize=20)
        self.baseFrm.rowconfigure(4, minsize=20)

        self.repTitleLbl = Label(
            self.baseFrm, textvariable=self.top.report_title,
            font=RBFONT, anchor=CENTER)
        self.repTitleLbl.grid(
            row=1, column=1, sticky='snew', padx=10, pady=20)

        # scrollbars
        self.xscrollbar = Scrollbar(self.baseFrm, orient=HORIZONTAL)
        self.xscrollbar.grid(
            row=3, column=1, sticky='swe')
        self.yscrollbar = Scrollbar(self.baseFrm, orient=VERTICAL)
        self.yscrollbar.grid(
            row=2, column=2, sticky='nse')

        self.reportTxt = Text(
            self.baseFrm,
            font=RFONT,
            width=200,
            height=50,
            xscrollcommand=self.xscrollbar.set,
            yscrollcommand=self.yscrollbar.set)
        self.reportTxt.grid(
            row=2, column=1, sticky='snew', padx=2)
        self.xscrollbar['command'] = self.reportTxt.xview
        self.yscrollbar['command'] = self.reportTxt.yview

        # populate report
        self.generate_report(report_data)

    def generate_report(self, data):
        for k, v in data.items():
            self.reportTxt.insert(END, f'{k}\n')
            if type(v).__name__ == 'DataFrame':
                self.reportTxt.insert(END, f'{v.to_string()}\n\n')
            else:
                self.reportTxt.insert(END, f'{v}\n')


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
        self.profile = app_data['profile']
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
        critFrm.columnconfigure(0, minsize=10)

        Label(critFrm, text='date from:').grid(
            row=1, column=1, sticky='snw', padx=2, pady=5)
        dateFromEnt = Entry(
            critFrm, textvariable=self.date_from,
            font=RFONT,
            validate='key', validatecommand=self.vldt)
        self.createToolTip(dateFromEnt, 'YYYY-MM-DD')
        dateFromEnt.grid(
            row=1, column=2, sticky='snw', padx=2, pady=5)
        Label(critFrm, text='to:').grid(
            row=1, column=3, sticky='snew', padx=2, pady=5)
        dateToEnt = Entry(
            critFrm, textvariable=self.date_to,
            font=RFONT,
            validate='key', validatecommand=self.vldt)
        dateToEnt.grid(
            row=1, column=4, sticky='snw', padx=2, pady=5)
        self.createToolTip(dateToEnt, 'YYYY-MM-DD')

        Label(critFrm, text='library:').grid(
            row=2, column=1, sticky='sne', padx=25, pady=5)
        self.libCbx = Combobox(
            critFrm, textvariable=self.library,
            font=RFONT,
            state='readonly')
        self.libCbx.grid(
            row=2, column=2, sticky='snew', padx=2, pady=5)

        # report types
        fyBtn = Radiobutton(
            critFrm, text='current FY summary',
            variable=self.report, value=1)
        fyBtn.grid(
            row=4, column=1, columnspa=3, sticky='snw', padx=2, pady=5)
        audnBtn = Radiobutton(
            critFrm, text='audience',
            variable=self.report, value=2)
        audnBtn.grid(
            row=5, column=1, columnspan=3, sticky='snw', padx=2, pady=5)
        branchBtn = Radiobutton(
            critFrm, text='branch',
            variable=self.report, value=3)
        branchBtn.grid(
            row=6, column=1, columnspan=3, sticky='snw', padx=2, pady=5)
        fundBtn = Radiobutton(
            critFrm, text='fund',
            variable=self.report, value=4)
        fundBtn.grid(
            row=7, column=1, columnspan=3, sticky='snw', padx=2, pady=5)
        langBtn = Radiobutton(
            critFrm, text='language',
            variable=self.report, value=5)
        langBtn.grid(
            row=8, column=1, columnspa=3, sticky='snw', padx=2, pady=5)
        matBtn = Radiobutton(
            critFrm, text='material type',
            variable=self.report, value=6)
        matBtn.grid(
            row=9, column=1, columnspa=3, sticky='snw', padx=2, pady=5)
        vendorBtn = Radiobutton(
            critFrm, text='vendor',
            variable=self.report, value=7)
        vendorBtn.grid(
            row=10, column=1, columnspan=3, sticky='snw', padx=2, pady=5)

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

    def create_report_title(self):
        """
        Returns report title as string
        """
        if self.system.get():
            system = get_record(System, did=self.system.get()).name
        else:
            system = None

        if self.report.get() == 1:
            date_today = date.today()
            if date_today.month > 6:
                years = f'{date_today.year}-{date_today.year + 1}'
            else:
                years = f'{date_today.year - 1} to {date_today.year}'
            report_title = f'{system} fiscal year {years} to date summary\n' \
                f'{self.profile.get()}'

        elif self.report.get() == 2:
            report_title = f'{system} orders audience breakdown' \
                f'({self.date_from.get()} to{self.date_to.get()})\n' \
                f'{self.profile.get()}'
        elif self.report.get() == 3:
            report_title = f'{system} orders by branch ' \
                f'({self.date_from.get()} to {self.date_to.get()})\n' \
                f'{self.profile.get()}'
        elif self.report.get() == 4:
            report_title = f'{system} orders by fund ' \
                f'({self.date_from.get()} to {self.date_to.get()})\n' \
                f'{self.profile.get()}'
        elif self.report.get() == 5:
            report_title = f'{system} orders by language ' \
                f'({self.date_from.get()} to {self.date_to.get()})\n' \
                f'{self.profile.get()}'
        elif self.report.get() == 6:
            report_title = f'{system} orders by material type ' \
                f'({self.date_from.get()} to {self.date_to.get()})\n' \
                f'{self.profile.get()}'
        elif self.report.get() == 7:
            report_title = f'{system} orders by vendor ' \
                f'({self.date_from.get()} to {self.date_to.get()})\n' \
                f'{self.profile.get()}'

        return report_title

    def generate_report(self):
        """
        Creates specified report in a pop up window
        """
        criteria_issues = self.validate_criteria()
        if not criteria_issues:
            report_title = self.create_report_title()
            report_data = self.analyze_data()

            if report_data:
                ReportView(
                    self, report_title, report_data, **self.app_data)

        else:
            messagebox.showwarning(
                'Criteria error', f'Errors:\n{criteria_issues}')

    def analyze_data(self):
        report_data = None
        system_id = self.system.get()
        if self.profile.get() != 'All users':
            user_id = get_id_from_index(
                self.profile.get(), self.app_data['profile_idx'])
        else:
            user_id = None

        if self.library.get() == 'any':
            library_id = None
        else:
            library_id = get_record(Library, name=self.library.get())

        try:
            if self.report.get() == 1:
                report_data = get_fy_summary(
                    system_id, library_id, user_id)

            return report_data
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
                self.library.set('any')

    def observer(self, *args):
        if self.activeW.get() == 'ReportWizView':

            self.libCbx['values'] = (
                'any',
                'branches',
                'research'
            )
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
