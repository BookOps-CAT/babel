from datetime import date
import logging

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from pandas import DataFrame
from tkinter import *
from tkinter import messagebox, filedialog
from tkinter.ttk import *


from data.datastore import System, Library
from data.transactions_reports import (
    get_basic_stats,
    get_branch_breakdown,
    get_branch_lang,
    get_categories_breakdown,
    get_fy_summary,
    get_lang_breakdown,
    get_lang_branch,
)
from logging_settings import LogglyAdapter
from gui.data_retriever import get_record
from gui.utils import (
    BusyManager,
    ToolTip,
    enable_widgets,
    disable_widgets,
    get_ids_from_index,
    open_url,
)
from gui.fonts import RBFONT, RFONT
from paths import MY_DOCS
from reports.reports import generate_fy_summary_by_user_chart


mlogger = LogglyAdapter(logging.getLogger("babel"), None)


class ReportView:
    """
    Pop-up window displaying selected report
    """

    def __init__(self, parent, report_data, **app_data):
        self.parent = parent
        # self.app_data = app_data
        self.system_id = app_data["system"].get()

        self.top = Toplevel(master=self.parent)
        self.top.title("Report")
        max_height = int((self.top.winfo_screenheight() - 250))

        # local variables
        self.top.report_title = StringVar()
        self.reports_idx = dict()

        # icons
        self.downloadImg = app_data["img"]["downloadS"]

        # layout
        self.baseFrm = Frame(self.top)
        self.baseFrm.grid(row=0, column=0, sticky="snew", padx=20, pady=20)
        self.baseFrm.columnconfigure(0, minsize=20)
        self.baseFrm.columnconfigure(4, minsize=20)
        self.baseFrm.rowconfigure(4, minsize=20)

        self.repTitleLbl = Label(
            self.baseFrm, textvariable=self.top.report_title, font=RBFONT, anchor=CENTER
        )
        self.repTitleLbl.grid(
            row=1, column=1, columnspan=2, sticky="snew", padx=10, pady=20
        )

        # scrollbars
        self.xscrollbar = Scrollbar(self.baseFrm, orient=HORIZONTAL)
        self.xscrollbar.grid(row=3, column=1, columnspan=2, sticky="swe")
        self.yscrollbar = Scrollbar(self.baseFrm, orient=VERTICAL)
        self.yscrollbar.grid(row=2, column=3, sticky="nse")

        self.report_base = Canvas(
            self.baseFrm,
            height=max_height,
            width=1125,
            xscrollcommand=self.xscrollbar.set,
            yscrollcommand=self.yscrollbar.set,
        )
        self.report_base.grid(row=2, column=1, columnspan=2, sticky="nwe")

        self._preview()

        # populate report
        self.generate_report(report_data)

    def store_report_data(self, widget_id, df):
        if df is not None:
            self.reports_idx[widget_id] = df

    def download_report(self, widget_id):

        dst_fh = filedialog.asksaveasfilename(
            parent=self.top,
            title="Save as",
            defaultextension=".csv",
            filetypes=(("cvs file", "*.csv"),),
            initialfile=f"",
            initialdir=MY_DOCS,
        )

        if dst_fh:
            df = self.reports_idx[widget_id]
            df.to_csv(dst_fh, index=False, encoding="utf-8")

    def create_report_widget(self, parent, height, row, col, df=None):
        unit_frame = Frame(parent)
        unit_frame.grid(row=row, column=col, sticky="snew", padx=5, pady=5)  # rowspan=4
        textWidget = Text(
            unit_frame,
            font=RFONT,
            width=45,
            height=height + 5,
            wrap=NONE,
            background="SystemButtonFace",
            relief="flat",
        )
        textWidget.grid(row=0, column=0, sticky="snew")

        # add dowload button
        if df is not None:
            downloadBtn = Button(
                textWidget,
                image=self.downloadImg,
                command=lambda: self.download_report(textWidget.winfo_id()),
            )
            textWidget.window_create(END, window=downloadBtn)

        textWidget.tag_configure("tag-right", justify="right")
        textWidget.tag_configure("tag-left", justify="left")
        textWidget.tag_configure("tag-center", justify="center")
        textWidget.tag_configure(
            "tag-header",
            justify="center",
            font=RBFONT,
            background="#B9DEF6",
            relief="raised",
        )

        self.store_report_data(textWidget.winfo_id(), df)

        return textWidget

    def create_report_title(self, report_type, users_lbl, start_date, end_date):
        """Returns report title as string"""
        if self.system_id:
            system = get_record(System, did=self.system_id).name
        else:
            system = None

        if report_type == 1:
            date_today = date.today()
            if date_today.month > 6:
                years = f"{date_today.year}/{date_today.year + 1}"
            else:
                years = f"{date_today.year - 1}/{date_today.year}"

            self.top.report_title.set(
                f"{system} fiscal year-to-date summary ({years})\n"
                f'users: {", ".join(users_lbl)}'
            )

        elif report_type == 2:
            self.top.report_title.set(
                f"Babel totals in quarterly reporting format\n"
                f"from {start_date} to {end_date}"
            )

        elif report_type == 3:
            self.top.report_title.set(
                f"{system} cumulative report\n"
                f"from {start_date} to {end_date}\n"
                f'users: {", ".join(users_lbl)}'
            )
        elif report_type == 4:
            self.top.report_title.set(
                f"{system} individual branches and their languages\n"
                f"(from {start_date} to {end_date})\n"
                f'users: {", ".join(users_lbl)}'
            )

        elif report_type == 5:
            self.top.report_title.set(
                f"{system} individual languages and their branches\n"
                f"from {start_date} to {end_date}\n"
                f"users: {', '.join(users_lbl)}"
            )

    def generate_report(self, data):
        # reset report index
        self.reports_idx = dict()

        self.create_report_title(
            data["report_type"], data["users_lbl"], data["start_date"], data["end_date"]
        )
        if data["report_type"] == 1:
            self.report_one(data)
        elif data["report_type"] == 2:
            self.report_two(data)
        elif data["report_type"] == 3:
            self.report_three(data)
        elif data["report_type"] == 4:
            self.report_four("branches", data)
        elif data["report_type"] == 5:
            self.report_four("languages", data)

    def report_one(self, data):
        """Current fiscal year summary"""
        reportTxt = self.create_report_widget(self.reportFrm, 100, 0, 0)

        reportTxt.insert(END, "carts status\n", "tag-header")
        cats = [f"{x}: {y}" for x, y in data["status"].items()]
        for c in cats:
            reportTxt.insert(END, f"{c}\n", "tag-center")
        reportTxt.insert(END, "\n")

        reportTxt.insert(END, "quantities\n", "tag-header")
        reportTxt.insert(END, f'orders: {data["orders"]:,}\n', "tag-center")
        reportTxt.insert(END, f'copies: {data["copies"]:,}\n\n', "tag-center")

        reportTxt.insert(END, "funds\n", "tag-header")
        reportTxt.insert(
            END,
            data["funds"].to_string(index=False, justify="right", header=False),
            "tag-right",
        )
        reportTxt.insert(END, "\n\n")

        reportTxt.insert(END, "languages\n", "tag-header")
        reportTxt.insert(
            END,
            data["langs"].to_string(index=False, justify="right", header=False),
            "tag-right",
        )
        reportTxt.insert(END, "\n\n")

        reportTxt.insert(END, "audiences\n", "tag-header")
        reportTxt.insert(
            END,
            data["audns"].to_string(index=False, header=False, justify="right"),
            "tag-right",
        )
        reportTxt.insert(END, "\n\n")

        reportTxt.insert(END, "material type\n", "tag-header")
        reportTxt.insert(
            END,
            data["mats"].to_string(index=False, header=False, justify="right"),
            "tag-right",
        )
        reportTxt.insert(END, "\n\n")

        reportTxt.insert(END, "vendors\n", "tag-header")
        reportTxt.insert(
            END,
            data["vendors"].to_string(index=False, header=False, justify="right"),
            "tag-right",
        )

        reportTxt["state"] = DISABLED

        # draw chart(s)
        # somehow the chart or its canvas interfere with baseFrm scrollbars:
        # when exiting top window, tkinter throws TclError unable to find
        # destroyed scrollbar widgets; not severe problem, but clean up in the
        # future
        chartFrm = Frame(self.reportFrm)
        chartFrm.grid(row=0, column=1, sticky="snew", padx=20, pady=5)

        ch1, ch2 = generate_fy_summary_by_user_chart(
            data["users_time"], data["langs_time"]
        )
        canvas1 = FigureCanvasTkAgg(ch1, chartFrm)
        canvas1.get_tk_widget().grid(row=0, column=1, sticky="ne")
        canvas1.draw()

        canvas2 = FigureCanvasTkAgg(ch2, chartFrm)
        canvas2.get_tk_widget().grid(row=1, column=1, sticky="ne")
        canvas2.draw()

    def report_two(self, data):
        """Basic Babel stats"""
        ordsTxt = self.create_report_widget(
            self.reportFrm, data["total_orders"].shape[0], 0, 0, data["total_orders"]
        )
        ordsTxt.insert(END, "\ttotal Babel orders\n", "tag-header")
        ordsTxt.insert(END, data["total_orders"].to_string(index=False))

        itemsTxt = self.create_report_widget(
            self.reportFrm, data["total_items"].shape[0], 0, 1, data["total_items"]
        )
        itemsTxt.insert(END, "\ttotal Babel items\n", "tag-header")
        itemsTxt.insert(END, data["total_items"].to_string(index=False))

        itemLangTotalTxt = self.create_report_widget(
            self.reportFrm, data["babel_langs"].shape[0], 1, 0, data["babel_langs"]
        )
        itemLangTotalTxt.insert(END, "\ttotal Babel items by lang\n", "tag-header")
        itemLangTotalTxt.insert(END, data["babel_langs"].to_string(index=False))

        itemLangNyplTxt = self.create_report_widget(
            self.reportFrm, data["nypl_langs"].shape[0], 1, 1, data["nypl_langs"]
        )
        itemLangNyplTxt.insert(END, "\tNYPL items by lang\n", "tag-header")
        itemLangNyplTxt.insert(END, data["nypl_langs"].to_string(index=False))

        itemLangBplTxt = self.create_report_widget(
            self.reportFrm, data["bpl_langs"].shape[0], 1, 2, data["bpl_langs"]
        )
        itemLangBplTxt.insert(END, "\tBPL items by lang\n", "tag-header")
        itemLangBplTxt.insert(END, data["bpl_langs"].to_string(index=False))

        itemMatTotalTxt = self.create_report_widget(
            self.reportFrm, data["babel_mats"].shape[0], 2, 0, data["babel_mats"]
        )
        itemMatTotalTxt.insert(END, "\tBabel items by mat type\n", "tag-header")
        itemMatTotalTxt.insert(END, data["babel_mats"].to_string(index=False))

        itemMatNyplTxt = self.create_report_widget(
            self.reportFrm, data["nypl_mats"].shape[0], 2, 1, data["nypl_mats"]
        )
        itemMatNyplTxt.insert(END, "\tNYPL items by mat type\n", "tag-header")
        itemMatNyplTxt.insert(END, data["nypl_mats"].to_string(index=False))

        itemMatBplTxt = self.create_report_widget(
            self.reportFrm, data["bpl_mats"].shape[0], 2, 2, data["bpl_mats"]
        )
        itemMatBplTxt.insert(END, "\tBPL items by mat type\n", "tag-header")
        itemMatBplTxt.insert(END, data["bpl_mats"].to_string(index=False))

    def report_three(self, data):
        """Detailed breakdown by each category"""

        # left panel
        # audience box
        leftAudnTxt = self.create_report_widget(
            self.reportFrm, data["audns"].shape[0], 0, 0, data["audns"]
        )
        leftAudnTxt.insert(END, "\t\taudience\n", "tag-header")
        leftAudnTxt.insert(END, data["audns"].to_string(index=False))

        # languages boxes
        leftLangTxt = self.create_report_widget(
            self.reportFrm, data["langs"].shape[0], 1, 0, data["langs"]
        )
        leftLangTxt.insert(END, "\t\tlanguage\n", "tag-header")
        leftLangTxt.insert(END, data["langs"].to_string(index=False))

        leftLangAudnTxt = self.create_report_widget(
            self.reportFrm, data["langs_audns"].shape[0], 2, 0, data["langs_audns"]
        )
        leftLangAudnTxt.insert(END, "\t\tlanguages by audience\n", "tag-header")
        leftLangAudnTxt.insert(END, data["langs_audns"].to_string(index=False))

        # center panel
        # vendors
        centerVendTxt = self.create_report_widget(
            self.reportFrm, data["vendors"].shape[0], 0, 1, data["vendors"]
        )

        centerVendTxt.insert(END, "\t\tvendors\n", "tag-header")
        centerVendTxt.insert(END, data["vendors"].to_string(index=False))

        # funds
        centerFundTxt = self.create_report_widget(
            self.reportFrm, data["funds"].shape[0], 1, 1, data["funds"]
        )
        centerFundTxt.insert(END, "\t\tfunds\n", "tag-header")
        centerFundTxt.insert(END, data["funds"].to_string(index=False))

        # funds and languages
        centerFundLangTxt = self.create_report_widget(
            self.reportFrm, data["funds_langs"].shape[0], 2, 1, data["funds_langs"]
        )
        centerFundLangTxt.insert(END, "\t\tfunds and languages\n", "tag-header")
        centerFundLangTxt.insert(
            END,
            data["funds_langs"].to_string(index=False),
        )

        # right panel
        # material types
        rightMatTypeTxt = self.create_report_widget(
            self.reportFrm, data["mattypes"].shape[0], 0, 2, data["mattypes"]
        )
        rightMatTypeTxt.insert(END, "\t\tmaterial types\n", "tag-header")
        rightMatTypeTxt.insert(END, data["mattypes"].to_string(index=False))

        # material type by language
        rightMatTypeLangTxt = self.create_report_widget(
            self.reportFrm,
            data["mattypes_langs"].shape[0],
            1,
            2,
            data["mattypes_langs"],
        )
        rightMatTypeLangTxt.insert(END, "\t\tmaterial type by language\n", "tag-header")
        rightMatTypeLangTxt.insert(
            END,
            data["mattypes_langs"].to_string(index=False),
        )

        # total items by branch
        itemsBranchTxt = self.create_report_widget(
            self.reportFrm,
            data["total_item_branch"].shape[0],
            2,
            2,
            data["total_item_branch"],
        )
        itemsBranchTxt.insert(END, "\t\ttotal branch items\n", "tag-header")
        itemsBranchTxt.insert(
            END,
            data["total_item_branch"].to_string(index=False),
        )

        # read-only mode
        for f in self.reportFrm.winfo_children():
            for w in f.winfo_children():
                w["state"] = DISABLED

    def report_four(self, key, data):
        """
        Breakdown by branch or language

        Args:
            key:                'branches' or 'languages'
            data:               dict that includes dataframe
        """

        rows, cols, heights = self._determine_widgets_layout(key, data)
        n = 0
        for name, data in data[key].items():
            wTxt = self.create_report_widget(
                self.reportFrm, heights[n], rows[n], cols[n], data
            )

            wTxt.insert(END, f"\t{name}\n", "tag-header")
            wTxt.insert(END, data.to_string(index=False))
            wTxt.insert(END, "\n\n")
            wTxt["state"] = DISABLED
            mlogger.debug(
                f"Report layout: {name}=row:{rows[n]}, "
                f"col={cols[n]}, heights={heights[n]}"
            )

            n += 1

    def _determine_widgets_layout(self, key, data):
        # divide branch data into groups of three for each column
        grouped_sizes = []
        row_sizes = []
        for _, data in data[key].items():
            if len(row_sizes) == 3:
                grouped_sizes.append(row_sizes)
                row_sizes = []
            elif len(row_sizes) > 3:
                mlogger.error("Error while determining branches report layout.")

            # calculate number of records in a dataframe
            row_sizes.append(data.shape[0])

        # pick up any leftovers
        if len(row_sizes) <= 3:
            grouped_sizes.append(row_sizes)

        mlogger.debug(f"Determined # of required report rows: {len(grouped_sizes)}.")

        # determine layout location and height
        cols = []
        rows = []
        heights = []

        r = 0
        for row_sizes in grouped_sizes:
            for c in range(len(row_sizes)):
                rows.append(r)
                cols.append(c)
                max_height = row_sizes[row_sizes.index(max(row_sizes))] + 1
                heights.append(max_height)
            r += 1

        return rows, cols, heights

    def _preview(self):
        self.reportFrm = Frame(self.report_base)
        self.xscrollbar.config(command=self.report_base.xview)
        self.yscrollbar.config(command=self.report_base.yview)
        self.report_base.create_window(
            (0, 0), window=self.reportFrm, anchor="nw", tags="self.reportFrm"
        )
        self.reportFrm.bind("<Configure>", self.onFrameConfigure)

    def onFrameConfigure(self, event):
        self.report_base.config(scrollregion=self.reportFrm.bbox("all"))


class ReportWizView(Frame):
    """
    Guides user through report criteria
    """

    def __init__(self, parent, controller, **app_data):
        self.parent = parent
        Frame.__init__(self, parent)
        self.controller = controller
        self.app_data = app_data
        self.activeW = app_data["activeW"]
        self.activeW.trace("w", self.observer)
        self.system = app_data["system"]
        self.system.trace("w", self.system_observer)
        self.max_height = int((self.winfo_screenheight() - 200))
        self.cur_manager = BusyManager(self)

        # icons
        self.runImg = app_data["img"]["runM"]
        self.helpImg = app_data["img"]["help"]

        # variables
        self.date_from = StringVar()
        self.date_to = StringVar()
        self.library = StringVar()
        self.report = IntVar()

        # layout
        self.rowconfigure(3, minsize=15)

        # register date validation
        self.vldt = (self.register(self.onValidateDate), "%i", "%d", "%P")

        # widgets
        genRepBtn = Button(self, image=self.runImg, command=self.generate_report)
        genRepBtn.grid(row=0, column=0, sticky="sw", padx=20, pady=5)
        self.createToolTip(genRepBtn, "generate report")

        helpBtn = Button(self, image=self.helpImg, command=self.help)
        helpBtn.grid(row=1, column=0, sticky="sw", padx=20, pady=5)
        self.createToolTip(helpBtn, "help")

        # criteria frame
        critFrm = LabelFrame(self, text="report wizard")
        critFrm.grid(row=0, column=1, rowspan=20, sticky="snew", padx=25, pady=10)
        critFrm.columnconfigure(0, minsize=20)
        critFrm.columnconfigure(5, minsize=20)
        critFrm.rowconfigure(14, minsize=10)

        Label(critFrm, text="criteria:", font=RBFONT).grid(
            row=1, column=1, columnspan=4, sticky="snw", padx=2, pady=10
        )
        Label(critFrm, text="date from:").grid(
            row=2, column=1, sticky="sne", padx=2, pady=5
        )
        dateFromEnt = Entry(
            critFrm,
            textvariable=self.date_from,
            font=RFONT,
            width=17,
            validate="key",
            validatecommand=self.vldt,
        )
        self.createToolTip(dateFromEnt, "YYYY-MM-DD")
        dateFromEnt.grid(row=2, column=2, sticky="snw", padx=2, pady=5)
        Label(critFrm, text="to:").grid(row=2, column=3, sticky="snew", padx=2, pady=5)
        dateToEnt = Entry(
            critFrm,
            textvariable=self.date_to,
            font=RFONT,
            width=17,
            validate="key",
            validatecommand=self.vldt,
        )
        dateToEnt.grid(row=2, column=4, sticky="snw", padx=2, pady=5)
        self.createToolTip(dateToEnt, "YYYY-MM-DD")

        Label(critFrm, text="library:").grid(
            row=3, column=1, sticky="sne", padx=2, pady=5
        )
        self.libCbx = Combobox(
            critFrm, textvariable=self.library, font=RFONT, width=15, state="readonly"
        )
        self.libCbx.grid(row=3, column=2, sticky="snew", padx=2, pady=5)

        # users
        Label(critFrm, text="users:").grid(row=4, column=1, sticky="ne", padx=2, pady=5)
        scrollbar = Scrollbar(critFrm, orient=VERTICAL)
        scrollbar.grid(row=4, column=3, sticky="snw", pady=5)
        self.userLst = Listbox(
            critFrm,
            font=RFONT,
            selectmode=EXTENDED,
            width=15,
            yscrollcommand=scrollbar.set,
        )
        self.userLst.grid(row=4, column=2, sticky="snew", pady=5)
        scrollbar.config(command=self.userLst.yview)

        Separator(critFrm, orient=HORIZONTAL).grid(
            row=5, column=1, columnspan=4, sticky="snew", padx=2, pady=15
        )

        # report types
        Label(critFrm, text="report type:", font=RBFONT).grid(
            row=6, column=1, columnspan=4, sticky="snw", padx=2, pady=10
        )
        fyBtn = Radiobutton(
            critFrm, text="view current FY summary", variable=self.report, value=1
        )
        fyBtn.grid(row=7, column=1, columnspa=2, sticky="snw", padx=2, pady=5)

        basicStatsBtn = Radiobutton(
            critFrm,
            text="view Babel totals in quarterly reporting format",
            variable=self.report,
            value=2,
        )
        basicStatsBtn.grid(row=8, column=1, columnspan=2, sticky="snw", padx=2, pady=2)

        audnBtn = Radiobutton(
            critFrm, text="view cumulative reports", variable=self.report, value=3
        )
        audnBtn.grid(row=9, column=1, columnspan=2, sticky="snw", padx=2, pady=5)
        branchBtn = Radiobutton(
            critFrm,
            text="view individual branches and their languages",
            variable=self.report,
            value=4,
        )
        branchBtn.grid(row=10, column=1, columnspan=2, sticky="snw", padx=2, pady=5)

        langBtn = Radiobutton(
            critFrm,
            text="view individual languages and their branches",
            variable=self.report,
            value=5,
        )
        langBtn.grid(row=11, column=1, columnspan=2, sticky="snw", padx=2, pady=2)

        getLangBranchBtn = Radiobutton(
            critFrm,
            text="export language/branch cumulative report",
            variable=self.report,
            value=6,
        )
        getLangBranchBtn.grid(
            row=12, column=1, columnspan=2, sticky="snw", padx=2, pady=5
        )

        getBranchLangBtn = Radiobutton(
            critFrm,
            text="export branch/language cumulative report",
            variable=self.report,
            value=7,
        )
        getBranchLangBtn.grid(
            row=13, column=1, columnspan=2, sticky="snw", padx=2, pady=2
        )

    def download_widget(self, report_data: DataFrame) -> None:
        """
        Opens widget to save the report as csv file

        Args:
            report_data:                `pandas.DataFrame` instance to be output
                                        to csv file
        """
        dst_fh = filedialog.asksaveasfilename(
            parent=self.parent,
            title="Save as",
            defaultextension=".csv",
            filetypes=(("cvs file", "*.csv"),),
            initialfile=f"",
            initialdir=MY_DOCS,
        )

        if dst_fh:
            report_data.to_csv(dst_fh, index=False, encoding="utf-8")

    def validate_criteria(self):
        """
        Returns formated msg to be dispolayed to user about
        any possible criteria issues
        """
        # validate all required elemnets are set
        issues = []
        msg = None

        if self.report.get() != 2 and self.system.get() not in (1, 2):
            issues.append("- library system not defined")
        if self.report.get() != 1 and not self.date_from.get():
            issues.append("- undefined starting date")
        if self.report.get() != 1 and not self.date_to.get():
            issues.append("- undefined ending date")
        if not self.report.get():
            issues.append("- unspecified report type")

        # validate dates
        try:
            if self.report.get() != 1:
                date.fromisoformat(self.date_from.get())
                date.fromisoformat(self.date_to.get())
        except ValueError:
            issues.append("- invalid date format")

        if issues:
            msg = "\n".join(issues)

        return msg

    def generate_report(self):
        """
        Creates specified report in a pop up window
        """
        criteria_issues = self.validate_criteria()
        if not criteria_issues:
            mlogger.debug(f"Generating report number {self.report.get()}")
            report_data = self.analyze_data()
            if report_data is not None and self.report.get() < 6:
                mlogger.debug("Viewing reports 1-5.")
                ReportView(self, report_data, **self.app_data)
            elif report_data is not None and self.report.get() >= 6:
                mlogger.debug("Downloading reports 6+.")
                # save instead of showing
                self.download_widget(report_data)
            elif report_data is None:
                messagebox.showinfo("Info", "No data matching criteria")

        else:
            messagebox.showwarning("Criteria error", f"Errors:\n{criteria_issues}")

    def map_selected_users_to_datastore_id(self, users):
        """
        Maps selected users to datastore user.did
        returns:
            datastore_user_ids: list of int, list of datastore user dids
        """
        datastore_user_ids = [
            x for x in get_ids_from_index(users, self.app_data["profile_idx"])
        ]

        return datastore_user_ids

    def get_selected_users(self):
        """
        Returns a list of selected user names
        """
        lst_ids = self.userLst.curselection()
        users = [self.userLst.get(i) for i in lst_ids]
        return users

    def analyze_data(self):
        self.cur_manager.busy()
        report_data = None
        system_id = self.system.get()
        users = self.get_selected_users()
        user_ids = self.map_selected_users_to_datastore_id(users)

        if self.library.get() == "any":
            library_id = None
        else:
            library_id = get_record(Library, name=self.library.get()).did

        if self.report.get() == 1:
            report_data = get_fy_summary(system_id, library_id, user_ids)

        elif self.report.get() == 2:
            report_data = get_basic_stats(self.date_from.get(), self.date_to.get())

        elif self.report.get() == 3:
            report_data = get_categories_breakdown(
                system_id,
                library_id,
                user_ids,
                self.date_from.get(),
                self.date_to.get(),
            )

        elif self.report.get() == 4:
            report_data = get_branch_breakdown(
                system_id,
                library_id,
                user_ids,
                self.date_from.get(),
                self.date_to.get(),
            )
        elif self.report.get() == 5:
            report_data = get_lang_breakdown(
                system_id,
                library_id,
                user_ids,
                self.date_from.get(),
                self.date_to.get(),
            )

        elif self.report.get() == 6:
            # downloable only
            report_data = get_lang_branch(
                system_id,
                library_id,
                user_ids,
                self.date_from.get(),
                self.date_to.get(),
            )
        elif self.report.get() == 7:
            # downloable only
            report_data = get_branch_lang(
                system_id,
                library_id,
                user_ids,
                self.date_from.get(),
                self.date_to.get(),
            )

        # reports 4+ have different format
        if self.report.get() < 6:

            report_data["report_type"] = self.report.get()
            if users:
                report_data["users_lbl"] = users
            else:
                report_data["users_lbl"] = ["All users"]

        self.cur_manager.notbusy()
        mlogger.debug(f"Analysis returned {type(report_data)} obj.")
        return report_data

    def help(self):
        # link to Github wiki with documentation here
        open_url("https://github.com/BookOps-CAT/babel/wiki/Reports")

    def system_observer(self, *args):
        if self.activeW.get() == "ReportWizView":
            if self.system.get() == 1:
                self.library.set("branches")
                disable_widgets([self.libCbx])
            else:
                enable_widgets([self.libCbx])
                self.libCbx["state"] = "readonly"
                self.library.set("any")

    def observer(self, *args):
        if self.activeW.get() == "ReportWizView":

            self.libCbx["values"] = ("any", "branches", "research")

            self.userLst.delete(0, END)
            self.userLst.insert(END, "all")
            for user in sorted(self.app_data["profile_idx"].values()):
                self.userLst.insert(END, user)
            self.system_observer()

    def onValidateDate(self, i, d, P):
        mlogger.debug(f"onValidteDate: index={i}, action={d}, string={P}")
        valid = True
        if int(i) < 4:
            if i == "0" and d == "1":
                if P != "2":
                    valid = False

            if i == "1" and d == "1":
                if P != "20":
                    valid = False

        if i == "4" and d == "1":
            if P[int(i)][-1] != "-":
                valid = False

        if i == "5" and d == "1":
            if P[int(i)][-1] not in ("0", "1"):
                valid = False

        if i == "6" and d == "1":
            if not P[int(i)][-1].isdigit():
                valid = False

        if i == "7" and d == "1":
            if P[int(i)][-1] != "-":
                valid = False

        if i == "8" and d == "1":
            if P[int(i)][-1] not in ("0", "1", "2", "3"):
                valid = False

        if i == "9" and d == "1":
            if not P[int(i)][-1].isdigit():
                valid = False

        return valid

    def createToolTip(self, widget, text):
        toolTip = ToolTip(widget)

        def enter(event):
            toolTip.showtip(text)

        def leave(event):
            toolTip.hidetip()

        widget.bind("<Enter>", enter)
        widget.bind("<Leave>", leave)
