from collections import OrderedDict

from pandas import DataFrame, Series, Grouper
from matplotlib.figure import Figure


def create_total_items_by_branch_dataframe(df: DataFrame) -> DataFrame:
    """
    Creates a dataframe with three columns: branch code, location, total items

    Args:
        df:                 `DataFrame` instance to be used as basis

    Returns:
        dataframe
    """
    rows = []
    for labels, data in df.groupby(["branch_code", "branch_name"]):
        branch_code = labels[0]
        branch_name = labels[1]
        copies = data["qty"].sum()
        rows.append(Series(dict(code=branch_code, location=branch_name, copies=copies)))

    return DataFrame(rows)


def create_branch_to_lang_audn_mat_dataframe(df: DataFrame) -> DataFrame:
    """
    Creates a dataframe showing locations brokend down by language, audience, material type.

    Args:
        df:                     `pandas.DataFrame` instance with base data

    Returns:
        `pandas.Dataframe` instance with filterd data
    """
    fdf = df[df["cart_status"] != "in-works"]
    rows = []
    codes = fdf["branch_code"].str.upper().sort_values().unique()

    # determine columns
    cols = []
    for label, _ in fdf.groupby(["lang_name", "audn", "mattype"], sort=True):
        cols.append(f"{label[0]} {label[1]} {label[2]}")

    for l, d in fdf.groupby(["branch_code", "branch_name"], sort=True):
        location = f"{l[0].upper()} / {l[1]}"
        extra_row_data = OrderedDict().fromkeys(cols)
        for ll, dd in d.groupby(["lang_name", "audn", "mattype"], sort=True):
            col = f"{ll[0]} {ll[1]} {ll[2]}"
            extra_row_data[col] = dd["qty"].sum()
        row = dict(location=location, **extra_row_data)
        rows.append(Series(row))

    return DataFrame(rows)


def create_lang_audn_mat_to_branch_dataframe(
    df: DataFrame,
) -> DataFrame:
    """
    Creates a dataframe showing language, audience, material type broken down
    by each location.

    Args:
        df:                     `pandas.DataFrame` instance with base data

    Returns:
        `pandas.Dataframe` instance with filterd data
    """
    fdf = df[df["cart_status"] != "in-works"]
    rows = []
    codes = fdf["branch_code"].str.upper().sort_values().unique()
    for labels, data in fdf.groupby(["lang_name", "audn", "mattype"], sort=True):
        lang = labels[0]
        audn = labels[1]
        mattype = labels[2]
        extra_row_data = OrderedDict().fromkeys(codes)
        for loc_code, loc_data in data.groupby(["branch_code"]):
            col_label = loc_code.upper()
            copies = loc_data["qty"].sum()
            extra_row_data[col_label] = copies

        row = dict(language=lang, audience=audn, mtype=mattype, **extra_row_data)
        rows.append(Series(row))

    return DataFrame(rows)


def generate_basic_stats(df: DataFrame, start_date: str, end_date: str) -> dict:
    """
    Creates a dictionary that includes dataframes with basic Babel stats.

    Args:
        df:                     `pandas.DataFrame` intance with base data
        start_date:             starting date
        end_date:               ending date

    Returns:
        data as dict
    """
    data = dict()
    data["start_date"] = start_date
    data["end_date"] = end_date

    fdf = df[df["cart_status"] != "in-works"]
    ndf = fdf[fdf["system_name"] == "NYP"]
    bdf = fdf[fdf["system_name"] == "BPL"]

    # total Babel orders
    rows = []
    rows.append(Series(dict(orders="total Babel", qty=fdf["order_id"].nunique())))
    rows.append(Series(dict(orders="total NYPL", qty=ndf["order_id"].nunique())))
    rows.append(Series(dict(orders="total BPL", qty=bdf["order_id"].nunique())))
    data["total_orders"] = DataFrame(rows)

    # total Babel copies
    rows = []
    rows.append(Series(dict(items="total Babel", qty=fdf["qty"].sum())))
    rows.append(Series(dict(items="total NYPL", qty=ndf["qty"].sum())))
    rows.append(Series(dict(items="total BPL", qty=bdf["qty"].sum())))
    data["total_items"] = DataFrame(rows)

    # total items by language in general
    rows = []
    for lang, d in fdf.groupby("lang_name"):
        rows.append(Series(dict(language=lang, qty=d["qty"].sum())))
    df = DataFrame(rows).sort_values("qty", ascending=False)
    data["babel_langs"] = df

    # total items by language for NYPL
    rows = []
    for lang, d in ndf.groupby("lang_name"):
        rows.append(Series(dict(language=lang, qty=d["qty"].sum())))
    df = DataFrame(rows)
    try:
        df = df.sort_values("qty", ascending=False)
    except KeyError:
        pass
    data["nypl_langs"] = df

    # total items by language for BPL
    rows = []
    for lang, d in bdf.groupby("lang_name"):
        rows.append(Series(dict(language=lang, qty=d["qty"].sum())))
    df = DataFrame(rows)
    try:
        df = df.sort_values("qty", ascending=False)
    except:
        pass
    data["bpl_langs"] = df

    # total Babel items by material type
    rows = []
    for mat, d in fdf.groupby("mattype"):
        rows.append(Series(dict(type=mat, qty=d["qty"].sum())))
    data["babel_mats"] = DataFrame(rows)

    # total NYPL items by material type
    rows = []
    for mat, d in ndf.groupby("mattype"):
        rows.append(Series(dict(type=mat, qty=d["qty"].sum())))
    data["nypl_mats"] = DataFrame(rows)

    # total BPl items by material type
    rows = []
    for mat, d in bdf.groupby("mattype"):
        rows.append(Series(dict(type=mat, qty=d["qty"].sum())))
    data["bpl_mats"] = DataFrame(rows)

    return data


def generate_fy_summary_by_user_chart(user_data, language_data):
    # try refactoring it with one figure and two subplots
    f1 = Figure(figsize=(7.3, 4), dpi=100, tight_layout=True, frameon=False)
    f2 = Figure(figsize=(7.3, 4), dpi=100, tight_layout=True, frameon=False)
    a = f1.add_subplot(111)
    b = f2.add_subplot(111)

    users = user_data.keys()
    langs = language_data.keys()
    month_lbl = [
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
    ]
    for user, y in user_data.items():
        a.plot(month_lbl, y)

    for lang, y in language_data.items():
        b.plot(month_lbl, y)

    a.set_xlabel("months")
    b.set_xlabel("months")
    a.set_ylabel("dollars allocated")
    b.set_ylabel("dollars allocated")
    a.spines["top"].set_visible(False)
    a.spines["right"].set_visible(False)
    b.spines["top"].set_visible(False)
    b.spines["right"].set_visible(False)
    a.legend(users)
    b.legend(langs)
    a.set_title("funds allocation in current FY by user")
    b.set_title("funds allocation in current FY by language")

    return f1, f2


def generate_fy_summary_for_display(df):
    data = dict()
    data["start_date"] = None
    data["end_date"] = None

    # unique carts by status
    status = dict()
    for k, d in df.groupby("cart_status"):
        cart_count = d["cart_id"].nunique()
        status[k] = cart_count
    data["status"] = status

    fdf = df[df["cart_status"] != "in-works"]
    # number of orders/titles
    data["orders"] = fdf["order_id"].nunique()

    # number of copies
    data["copies"] = fdf["qty"].sum()

    # funds
    funds = []
    for k, d in fdf.groupby("fund"):
        amount = (d["qty"] * d["price"]).sum()
        funds.append(Series(dict(fund=k, amount=f"${amount:,.2f}")))
    data["funds"] = DataFrame(funds)

    # languages
    langs = []
    lang_time = dict()
    for k, d in fdf.groupby("lang_code"):
        amount = (d["qty"] * d["price"]).sum()
        langs.append(Series(dict(lang=k, amount=f"${amount:,.2f}")))

        # languages in time chart data
        y = [0] * 12
        for m, md in d.groupby(Grouper(key="cart_date", freq="M")):
            m_amount = (md["price"] * md["qty"]).sum()
            pos = m.month
            if pos <= 6:
                y[pos + 5] = m_amount
            else:
                y[pos - 7] = m_amount
        lang_time[k] = y

    data["langs"] = DataFrame(langs)
    data["langs_time"] = lang_time

    # audiences
    audns = []
    for k, d in fdf.groupby("audn"):
        amount = (d["qty"] * d["price"]).sum()
        audns.append(Series(dict(audn=k, amount=f"${amount:,.2f}")))
    data["audns"] = DataFrame(audns)

    # material types
    mats = []
    for k, d in fdf.groupby("mattype"):
        amount = (d["qty"] * d["price"]).sum()
        mats.append(Series(dict(type=k, amount=f"${amount:,.2f}")))
    data["mats"] = DataFrame(mats)

    # vendors
    vendors = []
    for k, d in fdf.groupby("vendor"):
        amount = (d["qty"] * d["price"]).sum()
        vendors.append(Series(dict(vendor=k, amount=f"${amount:,.2f}")))

    data["vendors"] = DataFrame(vendors)

    # users in time
    users = dict()
    for k, d in fdf.groupby("user"):
        y = [0] * 12
        for m, md in d.groupby(Grouper(key="cart_date", freq="M")):
            amount = (md["price"] * md["qty"]).sum()
            pos = m.month
            if pos <= 6:
                y[pos + 5] = amount
            else:
                y[pos - 7] = amount
        users[k] = y

    data["users_time"] = users

    return data


def generate_detailed_breakdown(df, start_date, end_date):
    """
    Creates report data in form of a dictionary
    based on Pandas dataframe

    args:
        df:                 Pandas dataframe
        start_date:         str, report starting date (inclusive)
        end_date:           str, report ending date (inclusive)

    returns:
        data: dict, data in form of dictionary
    """
    data = dict()
    data["start_date"] = start_date
    data["end_date"] = end_date

    # filter out carts that are not finilized
    fdf = df[df["cart_status"] != "in-works"]

    # breakdown by audience
    audns = []
    for k, d in fdf.groupby("audn"):
        orders_qty = d["order_id"].nunique()
        copies_qty = d["qty"].sum()
        amount = (d["price"] * d["qty"]).sum()
        audns.append(
            Series(
                dict(
                    audience=k,
                    orders=orders_qty,
                    copies=copies_qty,
                    amount=f"${amount:,.2f}",
                )
            )
        )

    data["audns"] = DataFrame(audns)

    # breakdown by language
    langs = []
    langs_audns = []
    for k, d in fdf.groupby("lang_name"):
        orders_qty = d["order_id"].nunique()
        copies_qty = d["qty"].sum()
        amount = (d["price"] * d["qty"]).sum()
        langs.append(
            Series(
                dict(
                    language=k,
                    orders=orders_qty,
                    copies=copies_qty,
                    amount=f"${amount:,.2f}",
                )
            )
        )

        for kk, dd in d.groupby("audn"):
            la_orders_qty = dd["order_id"].nunique()
            la_copies_qty = dd["qty"].sum()
            la_amount = (dd["price"] * dd["qty"]).sum()
            langs_audns.append(
                Series(
                    dict(
                        language=k,
                        audience=kk,
                        orders=la_orders_qty,
                        copies=la_copies_qty,
                        amount=f"${la_amount:,.2f}",
                    )
                )
            )

    data["langs"] = DataFrame(langs)
    data["langs_audns"] = DataFrame(langs_audns)

    # vendors
    vendors = []
    for k, d in fdf.groupby("vendor"):
        orders_qty = d["order_id"].nunique()
        copies_qty = d["qty"].sum()
        amount = (d["price"] * d["qty"]).sum()
        vendors.append(
            Series(
                dict(
                    vendor=k,
                    orders=orders_qty,
                    copies=copies_qty,
                    amount=f"${amount:,.2f}",
                )
            )
        )

    data["vendors"] = DataFrame(vendors)

    # funds
    funds = []
    funds_langs = []
    for k, d in fdf.groupby("fund"):
        orders_qty = d["order_id"].nunique()
        copies_qty = d["qty"].sum()
        amount = (d["price"] * d["qty"]).sum()
        funds.append(
            Series(
                dict(
                    fund=k,
                    orders=orders_qty,
                    copies=copies_qty,
                    amount=f"${amount:,.2f}",
                )
            )
        )

        # breakdown by language
        for lk, ld in d.groupby("lang_name"):
            amount = (ld["price"] * ld["qty"]).sum()
            funds_langs.append(Series(dict(fund=k, lang=lk, amount=f"${amount:,.2f}")))

    data["funds"] = DataFrame(funds)
    data["funds_langs"] = DataFrame(funds_langs)

    # material types
    mattypes = []
    mattypes_langs = []
    for k, d in fdf.groupby("mattype"):
        orders_qty = d["order_id"].nunique()
        copies_qty = d["qty"].sum()
        amount = (d["price"] * d["qty"]).sum()
        mattypes.append(
            Series(
                dict(
                    type=k,
                    orders=orders_qty,
                    copies=copies_qty,
                    amount=f"${amount:,.2f}",
                )
            )
        )

        for kk, dd in d.groupby("lang_name"):
            l_orders_qty = dd["order_id"].nunique()
            l_copies_qty = dd["qty"].sum()
            l_amount = (dd["price"] * dd["qty"]).sum()
            mattypes_langs.append(
                Series(
                    dict(
                        type=k,
                        language=kk,
                        orders=l_orders_qty,
                        copies=l_copies_qty,
                        amount=f"${l_amount:,.2f}",
                    )
                )
            )

    data["mattypes"] = DataFrame(mattypes)
    data["mattypes_langs"] = DataFrame(mattypes_langs)

    # total items ordered for each branch
    total_item_branch_df = create_total_items_by_branch_dataframe(fdf)
    data["total_item_branch"] = total_item_branch_df

    return data


def generate_branch_breakdown(df, start_date, end_date):
    """
    Creates individual branches report data in form of a dictionary
    based on Pandas dataframe

    args:
        df:                 Pandas dataframe
        start_date:         str, report starting date (inclusive)
        end_date:           str, report ending date (inclusive)

    returns:
        data:               dict, data in form of dictionary
    """
    data = dict()
    data["start_date"] = start_date
    data["end_date"] = end_date

    # filter out carts that are not finilized
    fdf = df[df["cart_status"] != "in-works"]

    # group by branch
    branches = OrderedDict()
    for branch_name, d in fdf.groupby("branch_name"):
        branch_code = d["branch_code"].unique()[0].upper()
        branch = []
        total_copies = d["qty"].sum()
        ad = d[d["audn"] == "adult"]
        adult_copies = ad["qty"].sum()
        yd = d[d["audn"] == "young adult"]
        ya_copies = yd["qty"].sum()
        jd = d[d["audn"] == "juvenile"]
        juv_copies = jd["qty"].sum()
        for kk, dd in d.groupby("lang_name"):
            total_lang_copies = dd["qty"].sum()
            add = dd[dd["audn"] == "adult"]
            adult_lang_copies = add["qty"].sum()
            ydd = dd[dd["audn"] == "juvenile"]
            juv_lang_copies = ydd["qty"].sum()
            ydd = dd[dd["audn"] == "young adult"]
            ya_lang_copies = ydd["qty"].sum()

            branch.append(
                Series(
                    {
                        "": kk,
                        "adult": adult_lang_copies,
                        "ya": ya_lang_copies,
                        "juv": juv_lang_copies,
                        "total": total_lang_copies,
                    }
                )
            )
        branch.append(
            Series(
                {
                    "": "combined",
                    "adult": adult_copies,
                    "ya": ya_copies,
                    "juv": juv_copies,
                    "total": total_copies,
                }
            )
        )

        bdf = DataFrame(branch)
        if not bdf.empty:
            branches[f"{branch_name} ({branch_code})"] = bdf

    data["branches"] = branches

    return data


def generate_language_breakdown(df: DataFrame, start_date: str, end_date: str) -> dict:
    """
    Creates individual languages report data in form of a dictionary
    based on Pandas dataframe

    args:
        df:                 `pandas.DataFrame` instance with base data
        start_date:         str, report starting date (inclusive)
        end_date:           str, report ending date (inclusive)

    returns:
        data:               dict, data in form of dictionary
    """
    data = dict()
    data["start_date"] = start_date
    data["end_date"] = end_date

    # filter out carts that are not finilized
    fdf = df[df["cart_status"] != "in-works"]

    languages = OrderedDict()

    # determine columns
    cols = []
    for label, _ in fdf.groupby(["audn", "mattype"], sort=True):
        cols.append(f"{label[0]} {label[1]}")

    for lang_name, lang_data in fdf.groupby(["lang_name"], sort=True):
        language = []

        for branch_labels, branch_data in lang_data.groupby(
            ["branch_code", "branch_name"], sort=True
        ):

            extra_row_data = OrderedDict().fromkeys(cols)

            total_copies = branch_data["qty"].sum()

            for type_label, type_data in branch_data.groupby(
                ["audn", "mattype"], sort=True
            ):
                copies = type_data["qty"].sum()
                col = f"{type_label[0]} {type_label[1]}"
                extra_row_data[col] = copies
            row = dict(
                code=branch_labels[0].upper(),
                location=branch_labels[1],
                **extra_row_data,
                total=total_copies,
            )
            language.append(Series(row))

        # create a separate dataframe for each language
        ldf = DataFrame(language)
        if not ldf.empty:
            languages[lang_name] = ldf

    data["languages"] = languages

    return data
