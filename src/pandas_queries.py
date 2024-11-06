from duckdb.duckdb import dtype


def query_01(dataset_path, scale):
    import pandas as pd
    import warnings
    warnings.simplefilter(action='ignore', category=FutureWarning)
    date = pd.Timestamp("1998-09-02")
    lineitem = pd.read_csv(f'{dataset_path}/lineitem.csv',
                           parse_dates=['l_shipdate', 'l_commitdate', 'l_receiptdate'])
    lineitem_filtered = lineitem.loc[
        :,
        [
            "l_quantity",
            "l_extendedprice",
            "l_discount",
            "l_tax",
            "l_returnflag",
            "l_linestatus",
            "l_shipdate",
            "l_orderkey",
        ],
    ]
    sel = lineitem_filtered.l_shipdate <= date
    lineitem_filtered = lineitem_filtered[sel]
    lineitem_filtered["avg_qty"] = lineitem_filtered.l_quantity
    lineitem_filtered["avg_price"] = lineitem_filtered.l_extendedprice
    lineitem_filtered["disc_price"] = lineitem_filtered.l_extendedprice * (
        1 - lineitem_filtered.l_discount
    )
    lineitem_filtered["charge"] = (
        lineitem_filtered.l_extendedprice
        * (1 - lineitem_filtered.l_discount)
        * (1 + lineitem_filtered.l_tax)
    )
    gb = lineitem_filtered.groupby(["l_returnflag", "l_linestatus"], as_index=False)[
        [
            "l_quantity",
            "l_extendedprice",
            "disc_price",
            "charge",
            "avg_qty",
            "avg_price",
            "l_discount",
            "l_orderkey",
        ]
    ]
    total = gb.agg(
        {
            "l_quantity": "sum",
            "l_extendedprice": "sum",
            "disc_price": "sum",
            "charge": "sum",
            "avg_qty": "mean",
            "avg_price": "mean",
            "l_discount": "mean",
            "l_orderkey": "count",
        }
    )
    # skip sort, Mars groupby enables sort
    # total = total.sort_values(["L_RETURNFLAG", "L_LINESTATUS"])
    return total


def query_02(dataset_path, scale):
    import pandas as pd
    import warnings
    warnings.simplefilter(action='ignore', category=FutureWarning)

    part = pd.read_csv(f'{dataset_path}/part.csv')
    partsupp = pd.read_csv(f'{dataset_path}/partsupp.csv')
    supplier = pd.read_csv(f'{dataset_path}/supplier.csv')
    nation = pd.read_csv(f'{dataset_path}/nation.csv')
    region = pd.read_csv(f'{dataset_path}/region.csv')
    nation_filtered = nation.loc[:, ["n_nationkey", "n_name", "n_regionkey"]]
    region_filtered = region[(region["r_name"] == "EUROPE")]
    region_filtered = region_filtered.loc[:, ["r_regionkey"]]
    r_n_merged = nation_filtered.merge(
        region_filtered, left_on="n_regionkey", right_on="r_regionkey", how="inner"
    )
    r_n_merged = r_n_merged.loc[:, ["n_nationkey", "n_name"]]
    supplier_filtered = supplier.loc[
        :,
        [
            "s_suppkey",
            "s_name",
            "s_address",
            "s_nationkey",
            "s_phone",
            "s_acctbal",
            "s_comment",
        ],
    ]
    s_r_n_merged = r_n_merged.merge(
        supplier_filtered, left_on="n_nationkey", right_on="s_nationkey", how="inner"
    )
    s_r_n_merged = s_r_n_merged.loc[
        :,
        [
            "n_name",
            "s_suppkey",
            "s_name",
            "s_address",
            "s_phone",
            "s_acctbal",
            "s_comment",
        ],
    ]
    partsupp_filtered = partsupp.loc[:, ["ps_partkey", "ps_suppkey", "ps_supplycost"]]
    ps_s_r_n_merged = s_r_n_merged.merge(
        partsupp_filtered, left_on="s_suppkey", right_on="ps_suppkey", how="inner"
    )
    ps_s_r_n_merged = ps_s_r_n_merged.loc[
        :,
        [
            "n_name",
            "s_name",
            "s_address",
            "s_phone",
            "s_acctbal",
            "s_comment",
            "ps_partkey",
            "ps_supplycost",
        ],
    ]
    part_filtered = part.loc[:, ["p_partkey", "p_mfgr", "p_size", "p_type"]]
    part_filtered = part_filtered[
        (part_filtered["p_size"] == 15)
        & (part_filtered["p_type"].str.endswith("BRASS"))
    ]
    part_filtered = part_filtered.loc[:, ["p_partkey", "p_mfgr"]]
    merged_df = part_filtered.merge(
        ps_s_r_n_merged, left_on="p_partkey", right_on="ps_partkey", how="inner"
    )
    merged_df = merged_df.loc[
        :,
        [
            "n_name",
            "s_name",
            "s_address",
            "s_phone",
            "s_acctbal",
            "s_comment",
            "ps_supplycost",
            "p_partkey",
            "p_mfgr",
        ],
    ]
    min_values = merged_df.groupby("p_partkey", as_index=False, sort=False)[
        "ps_supplycost"
    ].min()
    min_values.columns = ["p_partkey_cpy", "min_supplycost"]
    merged_df = merged_df.merge(
        min_values,
        left_on=["p_partkey", "ps_supplycost"],
        right_on=["p_partkey_cpy", "min_supplycost"],
        how="inner",
    )
    total = merged_df.loc[
        :,
        [
            "s_acctbal",
            "s_name",
            "n_name",
            "p_partkey",
            "p_mfgr",
            "s_address",
            "s_phone",
            "s_comment",
        ],
    ]
    total = total.sort_values(
        by=["s_acctbal", "n_name", "s_name", "p_partkey"],
        ascending=[False, True, True, True],
    )
    return total

def query_03(dataset_path, scale):
    import pandas as pd
    from datetime import datetime
    import warnings
    warnings.simplefilter(action='ignore', category=FutureWarning)
    lineitem = pd.read_csv(f'{dataset_path}/lineitem.csv',
                           parse_dates=['l_shipdate', 'l_commitdate', 'l_receiptdate'])
    orders = pd.read_csv(f'{dataset_path}/orders.csv', parse_dates=['o_orderdate'])
    customer = pd.read_csv(f'{dataset_path}/customer.csv')

    date = pd.Timestamp("1995-03-04")
    lineitem_filtered = lineitem.loc[
        :, ["l_orderkey", "l_extendedprice", "l_discount", "l_shipdate"]
    ]
    orders_filtered = orders.loc[
        :, ["o_orderkey", "o_custkey", "o_orderdate", "o_shippriority"]
    ]
    customer_filtered = customer.loc[:, ["c_mktsegment", "c_custkey"]]
    lsel = lineitem_filtered.l_shipdate > date
    osel = orders_filtered.o_orderdate < date
    csel = customer_filtered.c_mktsegment == "HOUSEHOLD"
    flineitem = lineitem_filtered[lsel]
    forders = orders_filtered[osel]
    fcustomer = customer_filtered[csel]
    jn1 = fcustomer.merge(forders, left_on="c_custkey", right_on="o_custkey")
    jn2 = jn1.merge(flineitem, left_on="o_orderkey", right_on="l_orderkey")
    jn2["tmp"] = jn2.l_extendedprice * (1 - jn2.l_discount)
    total = (
        jn2.groupby(
            ["l_orderkey", "o_orderdate", "o_shippriority"], as_index=False, sort=False
        )["tmp"]
        .sum()
        .sort_values(["tmp"], ascending=False)
    )
    res = total.loc[:, ["l_orderkey", "tmp", "o_orderdate", "o_shippriority"]]
    return res


def query_04(dataset_path, scale):
    import pandas as pd
    import warnings
    warnings.simplefilter(action='ignore', category=FutureWarning)
    lineitem = pd.read_csv(f'{dataset_path}/lineitem.csv',
                           parse_dates=['l_shipdate', 'l_commitdate', 'l_receiptdate'])
    orders = pd.read_csv(f'{dataset_path}/orders.csv', parse_dates=['o_orderdate'])
    date1 = pd.Timestamp("1993-11-01")
    date2 = pd.Timestamp("1993-08-01")
    lsel = lineitem.l_commitdate < lineitem.l_receiptdate
    osel = (orders.o_orderdate < date1) & (orders.o_orderdate >= date2)
    flineitem = lineitem[lsel]
    forders = orders[osel]
    jn = forders[forders["o_orderkey"].isin(flineitem["l_orderkey"])]
    total = (
        jn.groupby("o_orderpriority", as_index=False)["o_orderkey"].count()
        # skip sort when Mars enables sort in groupby
        # .sort_values(["O_ORDERPRIORITY"])
    )
    return total


def query_05(dataset_path, scale):
    import pandas as pd
    import warnings
    warnings.simplefilter(action='ignore', category=FutureWarning)

    lineitem = pd.read_csv(f'{dataset_path}/lineitem.csv',
                           parse_dates=['l_shipdate', 'l_commitdate', 'l_receiptdate'])
    orders = pd.read_csv(f'{dataset_path}/orders.csv', parse_dates=['o_orderdate'])
    customer = pd.read_csv(f'{dataset_path}/customer.csv')
    nation = pd.read_csv(f'{dataset_path}/nation.csv')
    region = pd.read_csv(f'{dataset_path}/region.csv')
    supplier = pd.read_csv(f'{dataset_path}/supplier.csv')

    date1 = pd.Timestamp("1996-01-01")
    date2 = pd.Timestamp("1997-01-01")
    rsel = region.r_name == "ASIA"
    osel = (orders.o_orderdate >= date1) & (orders.o_orderdate < date2)
    forders = orders[osel]
    fregion = region[rsel]
    jn1 = fregion.merge(nation, left_on="r_regionkey", right_on="n_regionkey")
    jn2 = jn1.merge(customer, left_on="n_nationkey", right_on="c_nationkey")
    jn3 = jn2.merge(forders, left_on="c_custkey", right_on="o_custkey")
    jn4 = jn3.merge(lineitem, left_on="o_orderkey", right_on="l_orderkey")
    jn5 = supplier.merge(
        jn4, left_on=["s_suppkey", "s_nationkey"], right_on=["l_suppkey", "n_nationkey"]
    )
    jn5["tmp"] = jn5.l_extendedprice * (1.0 - jn5.l_discount)
    gb = jn5.groupby("n_name", as_index=False, sort=False)["tmp"].sum()
    total = gb.sort_values("tmp", ascending=False)
    return total


def query_06(dataset_path, scale):
    import pandas as pd
    import warnings
    warnings.simplefilter(action='ignore', category=FutureWarning)

    lineitem = pd.read_csv(f'{dataset_path}/lineitem.csv',
                           parse_dates=['l_shipdate', 'l_commitdate', 'l_receiptdate'])

    date1 = pd.Timestamp("1996-01-01")
    date2 = pd.Timestamp("1997-01-01")
    lineitem_filtered = lineitem.loc[
        :, ["l_quantity", "l_extendedprice", "l_discount", "l_shipdate"]
    ]
    sel = (
        (lineitem_filtered.l_shipdate >= date1)
        & (lineitem_filtered.l_shipdate < date2)
        & (lineitem_filtered.l_discount >= 0.08)
        & (lineitem_filtered.l_discount <= 0.1)
        & (lineitem_filtered.l_quantity < 24)
    )
    flineitem = lineitem_filtered[sel]
    total = (flineitem.l_extendedprice * flineitem.l_discount).sum()
    return total


def query_07(dataset_path, scale):
    import pandas as pd
    import warnings
    warnings.simplefilter(action='ignore', category=FutureWarning)

    lineitem = pd.read_csv(f'{dataset_path}/lineitem.csv',
                           parse_dates=['l_shipdate', 'l_commitdate', 'l_receiptdate'])
    orders = pd.read_csv(f'{dataset_path}/orders.csv', parse_dates=['o_orderdate'])
    customer = pd.read_csv(f'{dataset_path}/customer.csv')
    nation = pd.read_csv(f'{dataset_path}/nation.csv')
    supplier = pd.read_csv(f'{dataset_path}/supplier.csv')
    """This version is faster than q07_old. Keeping the old one for reference"""
    lineitem_filtered = lineitem[
        (lineitem["l_shipdate"] >= pd.Timestamp("1995-01-01"))
        & (lineitem["l_shipdate"] < pd.Timestamp("1997-01-01"))
    ]
    lineitem_filtered["l_year"] = lineitem_filtered["l_shipdate"].dt.year
    lineitem_filtered["volume"] = lineitem_filtered["l_extendedprice"] * (
        1.0 - lineitem_filtered["l_discount"]
    )
    lineitem_filtered = lineitem_filtered.loc[
        :, ["l_orderkey", "l_suppkey", "l_year", "volume"]
    ]
    supplier_filtered = supplier.loc[:, ["s_suppkey", "s_nationkey"]]
    orders_filtered = orders.loc[:, ["o_orderkey", "o_custkey"]]
    customer_filtered = customer.loc[:, ["c_custkey", "c_nationkey"]]
    n1 = nation[(nation["n_name"] == "FRANCE")].loc[:, ["n_nationkey", "n_name"]]
    n2 = nation[(nation["n_name"] == "GERMANY")].loc[:, ["n_nationkey", "n_name"]]

    # ----- do nation 1 -----
    N1_C = customer_filtered.merge(
        n1, left_on="c_nationkey", right_on="n_nationkey", how="inner"
    )
    N1_C = N1_C.drop(columns=["c_nationkey", "n_nationkey"]).rename(
        columns={"n_name": "cust_nation"}
    )
    N1_C_O = N1_C.merge(
        orders_filtered, left_on="c_custkey", right_on="o_custkey", how="inner"
    )
    N1_C_O = N1_C_O.drop(columns=["c_custkey", "o_custkey"])

    N2_S = supplier_filtered.merge(
        n2, left_on="s_nationkey", right_on="n_nationkey", how="inner"
    )
    N2_S = N2_S.drop(columns=["s_nationkey", "n_nationkey"]).rename(
        columns={"n_name": "supp_nation"}
    )
    N2_S_L = N2_S.merge(
        lineitem_filtered, left_on="s_suppkey", right_on="l_suppkey", how="inner"
    )
    N2_S_L = N2_S_L.drop(columns=["s_suppkey", "l_suppkey"])

    total1 = N1_C_O.merge(
        N2_S_L, left_on="o_orderkey", right_on="l_orderkey", how="inner"
    )
    total1 = total1.drop(columns=["o_orderkey", "l_orderkey"])

    # ----- do nation 2 -----
    N2_C = customer_filtered.merge(
        n2, left_on="c_nationkey", right_on="n_nationkey", how="inner"
    )
    N2_C = N2_C.drop(columns=["c_nationkey", "n_nationkey"]).rename(
        columns={"n_name": "cust_nation"}
    )
    N2_C_O = N2_C.merge(
        orders_filtered, left_on="c_custkey", right_on="o_custkey", how="inner"
    )
    N2_C_O = N2_C_O.drop(columns=["c_custkey", "o_custkey"])

    N1_S = supplier_filtered.merge(
        n1, left_on="s_nationkey", right_on="n_nationkey", how="inner"
    )
    N1_S = N1_S.drop(columns=["s_nationkey", "n_nationkey"]).rename(
        columns={"n_name": "supp_nation"}
    )
    N1_S_L = N1_S.merge(
        lineitem_filtered, left_on="s_suppkey", right_on="l_suppkey", how="inner"
    )
    N1_S_L = N1_S_L.drop(columns=["s_suppkey", "l_suppkey"])

    total2 = N2_C_O.merge(
        N1_S_L, left_on="o_orderkey", right_on="l_orderkey", how="inner"
    )
    total2 = total2.drop(columns=["o_orderkey", "l_orderkey"])

    # concat results
    total = pd.concat([total1, total2])

    return total.groupby(["supp_nation", "cust_nation", "l_year"], as_index=False).agg(
        REVENUE=pd.NamedAgg(column="volume", aggfunc="sum")
    )
    # skip sort when Mars groupby does sort already
    # total = total.sort_values(
    #     by=["SUPP_NATION", "CUST_NATION", "L_YEAR"], ascending=[True, True, True]
    # )


def query_08(dataset_path, scale):
    import pandas as pd
    import warnings
    warnings.simplefilter(action='ignore', category=FutureWarning)

    lineitem = pd.read_csv(f'{dataset_path}/lineitem.csv',
                           parse_dates=['l_shipdate', 'l_commitdate', 'l_receiptdate'])
    orders = pd.read_csv(f'{dataset_path}/orders.csv', parse_dates=['o_orderdate'])
    customer = pd.read_csv(f'{dataset_path}/customer.csv')
    nation = pd.read_csv(f'{dataset_path}/nation.csv')
    region = pd.read_csv(f'{dataset_path}/region.csv')
    supplier = pd.read_csv(f'{dataset_path}/supplier.csv')
    part = pd.read_csv(f'{dataset_path}/part.csv')
    part_filtered = part[(part["p_type"] == "ECONOMY ANODIZED STEEL")]
    part_filtered = part_filtered.loc[:, ["p_partkey"]]
    lineitem_filtered = lineitem.loc[:, ["l_partkey", "l_suppkey", "l_orderkey"]]
    lineitem_filtered["volume"] = lineitem["l_extendedprice"] * (
        1.0 - lineitem["l_discount"]
    )
    total = part_filtered.merge(
        lineitem_filtered, left_on="p_partkey", right_on="l_partkey", how="inner"
    )
    total = total.loc[:, ["l_suppkey", "l_orderkey", "volume"]]
    supplier_filtered = supplier.loc[:, ["s_suppkey", "s_nationkey"]]
    total = total.merge(
        supplier_filtered, left_on="l_suppkey", right_on="s_suppkey", how="inner"
    )
    total = total.loc[:, ["l_orderkey", "volume", "s_nationkey"]]
    orders_filtered = orders[
        (orders["o_orderdate"] >= pd.Timestamp("1995-01-01"))
        & (orders["o_orderdate"] < pd.Timestamp("1997-01-01"))
    ]
    orders_filtered["o_year"] = orders_filtered["o_orderdate"].dt.year
    orders_filtered = orders_filtered.loc[:, ["o_orderkey", "o_custkey", "o_year"]]
    total = total.merge(
        orders_filtered, left_on="l_orderkey", right_on="o_orderkey", how="inner"
    )
    total = total.loc[:, ["volume", "s_nationkey", "o_custkey", "o_year"]]
    customer_filtered = customer.loc[:, ["c_custkey", "c_nationkey"]]
    total = total.merge(
        customer_filtered, left_on="o_custkey", right_on="c_custkey", how="inner"
    )
    total = total.loc[:, ["volume", "s_nationkey", "o_year", "c_nationkey"]]
    n1_filtered = nation.loc[:, ["n_nationkey", "n_regionkey"]]
    n2_filtered = nation.loc[:, ["n_nationkey", "n_name"]].rename(
        columns={"n_name": "nation"}
    )
    total = total.merge(
        n1_filtered, left_on="c_nationkey", right_on="n_nationkey", how="inner"
    )
    total = total.loc[:, ["volume", "s_nationkey", "o_year", "n_regionkey"]]
    total = total.merge(
        n2_filtered, left_on="s_nationkey", right_on="n_nationkey", how="inner"
    )
    total = total.loc[:, ["volume", "o_year", "n_regionkey", "nation"]]
    region_filtered = region[(region["r_name"] == "AMERICA")]
    region_filtered = region_filtered.loc[:, ["r_regionkey"]]
    total = total.merge(
        region_filtered, left_on="n_regionkey", right_on="r_regionkey", how="inner"
    )
    total = total.loc[:, ["volume", "o_year", "nation"]]

    def udf(df):
        demonimator = df["volume"].sum()
        df = df[df["nation"] == "BRAZIL"]
        numerator = df["volume"].sum()
        return numerator / demonimator

    total = total.groupby("o_year", as_index=False).apply(udf)
    total.columns = ["o_year", "mkt_share"]
    total = total.sort_values(by=["o_year"], ascending=[True])
    return total

def query_09(dataset_path, scale):
    import pandas as pd
    import warnings
    warnings.simplefilter(action='ignore', category=FutureWarning)

    lineitem = pd.read_csv(f'{dataset_path}/lineitem.csv',
                           parse_dates=['l_shipdate', 'l_commitdate', 'l_receiptdate'])
    orders = pd.read_csv(f'{dataset_path}/orders.csv', parse_dates=['o_orderdate'])
    nation = pd.read_csv(f'{dataset_path}/nation.csv')
    supplier = pd.read_csv(f'{dataset_path}/supplier.csv')
    part = pd.read_csv(f'{dataset_path}/part.csv')
    partsupp = pd.read_csv(f'{dataset_path}/partsupp.csv')

    psel = part.p_name.str.contains("ghost")
    fpart = part[psel]
    jn1 = lineitem.merge(fpart, left_on="l_partkey", right_on="p_partkey")
    jn2 = jn1.merge(supplier, left_on="l_suppkey", right_on="s_suppkey")
    jn3 = jn2.merge(nation, left_on="s_nationkey", right_on="n_nationkey")
    jn4 = partsupp.merge(
        jn3, left_on=["ps_partkey", "ps_suppkey"], right_on=["l_partkey", "l_suppkey"]
    )
    jn5 = jn4.merge(orders, left_on="l_orderkey", right_on="o_orderkey")
    jn5["tmp"] = jn5.l_extendedprice * (1 - jn5.l_discount) - (
        (1 * jn5.ps_supplycost) * jn5.l_quantity
    )
    jn5["o_year"] = jn5.o_orderdate.dt.year
    gb = jn5.groupby(["n_name", "o_year"], as_index=False, sort=False)["tmp"].sum()
    total = gb.sort_values(["n_name", "o_year"], ascending=[True, False])
    return total


def query_10(dataset_path, scale):
    import pandas as pd
    import warnings
    warnings.simplefilter(action='ignore', category=FutureWarning)

    lineitem = pd.read_csv(f'{dataset_path}/lineitem.csv',
                           parse_dates=['l_shipdate', 'l_commitdate', 'l_receiptdate'])
    orders = pd.read_csv(f'{dataset_path}/orders.csv', parse_dates=['o_orderdate'])
    customer = pd.read_csv(f'{dataset_path}/customer.csv')
    nation = pd.read_csv(f'{dataset_path}/nation.csv')

    date1 = pd.Timestamp("1994-11-01")
    date2 = pd.Timestamp("1995-02-01")
    osel = (orders.o_orderdate >= date1) & (orders.o_orderdate < date2)
    lsel = lineitem.l_returnflag == "R"
    forders = orders[osel]
    flineitem = lineitem[lsel]
    jn1 = flineitem.merge(forders, left_on="l_orderkey", right_on="o_orderkey")
    jn2 = jn1.merge(customer, left_on="o_custkey", right_on="c_custkey")
    jn3 = jn2.merge(nation, left_on="c_nationkey", right_on="n_nationkey")
    jn3["tmp"] = jn3.l_extendedprice * (1.0 - jn3.l_discount)
    gb = jn3.groupby(
        [
            "c_custkey",
            "c_name",
            "c_acctbal",
            "c_phone",
            "n_name",
            "c_address",
            "c_comment",
        ],
        as_index=False,
        sort=False,
    )["tmp"].sum()
    total = gb.sort_values("tmp", ascending=False)
    return total

def query_11(dataset_path, scale):
    import pandas as pd
    import warnings
    warnings.simplefilter(action='ignore', category=FutureWarning)

    nation = pd.read_csv(f'{dataset_path}/nation.csv')
    partsupp = pd.read_csv(f'{dataset_path}/partsupp.csv')
    supplier = pd.read_csv(f'{dataset_path}/supplier.csv')

    partsupp_filtered = partsupp.loc[:, ["ps_partkey", "ps_suppkey"]]
    partsupp_filtered["total_cost"] = (
        partsupp["ps_supplycost"] * partsupp["ps_availqty"]
    )
    supplier_filtered = supplier.loc[:, ["s_suppkey", "s_nationkey"]]
    ps_supp_merge = partsupp_filtered.merge(
        supplier_filtered, left_on="ps_suppkey", right_on="s_suppkey", how="inner"
    )
    ps_supp_merge = ps_supp_merge.loc[:, ["ps_partkey", "s_nationkey", "total_cost"]]
    nation_filtered = nation[(nation["n_name"] == "GERMANY")]
    nation_filtered = nation_filtered.loc[:, ["n_nationkey"]]
    ps_supp_n_merge = ps_supp_merge.merge(
        nation_filtered, left_on="s_nationkey", right_on="n_nationkey", how="inner"
    )
    ps_supp_n_merge = ps_supp_n_merge.loc[:, ["ps_partkey", "total_cost"]]
    sum_val = ps_supp_n_merge["total_cost"].sum() * 0.0001
    total = ps_supp_n_merge.groupby(["ps_partkey"], as_index=False, sort=False).agg(
        value=pd.NamedAgg(column="total_cost", aggfunc="sum")
    )
    total = total[total["value"] > sum_val]
    total = total.sort_values("value", ascending=False)
    return total

def query_12(dataset_path, scale):
    import pandas as pd
    import warnings
    warnings.simplefilter(action='ignore', category=FutureWarning)

    lineitem = pd.read_csv(f'{dataset_path}/lineitem.csv',
                           parse_dates=['l_shipdate', 'l_commitdate', 'l_receiptdate'])
    orders = pd.read_csv(f'{dataset_path}/orders.csv', parse_dates=['o_orderdate'])

    date1 = pd.Timestamp("1994-01-01")
    date2 = pd.Timestamp("1995-01-01")
    sel = (
        (lineitem.l_receiptdate < date2)
        & (lineitem.l_commitdate < date2)
        & (lineitem.l_shipdate < date2)
        & (lineitem.l_shipdate < lineitem.l_commitdate)
        & (lineitem.l_commitdate < lineitem.l_receiptdate)
        & (lineitem.l_receiptdate >= date1)
        & ((lineitem.l_shipmode == "MAIL") | (lineitem.l_shipmode == "SHIP"))
    )
    flineitem = lineitem[sel]
    jn = flineitem.merge(orders, left_on="l_orderkey", right_on="o_orderkey")

    def g1(x):
        return ((x == "1-URGENT") | (x == "2-HIGH")).sum()

    def g2(x):
        return ((x != "1-URGENT") & (x != "2-HIGH")).sum()

    total = jn.groupby("l_shipmode", as_index=False)["o_orderpriority"].agg((g1, g2))
    total = total.reset_index()  # reset index to keep consistency with pandas
    # skip sort when groupby does sort already
    # total = total.sort_values("L_SHIPMODE")
    return total

def query_13(dataset_path, scale):
    import pandas as pd
    import warnings
    warnings.simplefilter(action='ignore', category=FutureWarning)

    orders = pd.read_csv(f'{dataset_path}/orders.csv', parse_dates=['o_orderdate'])
    customer = pd.read_csv(f'{dataset_path}/customer.csv')

    customer_filtered = customer.loc[:, ["c_custkey"]]
    orders_filtered = orders[
        ~orders["o_comment"].str.contains(r"special[\S|\s]*requests")
    ]
    orders_filtered = orders_filtered.loc[:, ["o_orderkey", "o_custkey"]]
    c_o_merged = customer_filtered.merge(
        orders_filtered, left_on="c_custkey", right_on="o_custkey", how="left"
    )
    c_o_merged = c_o_merged.loc[:, ["c_custkey", "o_orderkey"]]
    count_df = c_o_merged.groupby(["c_custkey"], as_index=False, sort=False).agg(
        c_count=pd.NamedAgg(column="o_orderkey", aggfunc="count")
    )
    total = count_df.groupby(["c_count"], as_index=False, sort=False).size()
    total.columns = ["c_count", "custdist"]
    total = total.sort_values(by=["custdist", "c_count"], ascending=[False, False])
    return total

def query_14(dataset_path, scale):
    import pandas as pd
    import warnings
    warnings.simplefilter(action='ignore', category=FutureWarning)

    lineitem = pd.read_csv(f'{dataset_path}/lineitem.csv',
                           parse_dates=['l_shipdate', 'l_commitdate', 'l_receiptdate'])
    part = pd.read_csv(f'{dataset_path}/part.csv')

    startDate = pd.Timestamp("1994-03-01")
    endDate = pd.Timestamp("1994-04-01")
    p_type_like = "PROMO"
    part_filtered = part.loc[:, ["p_partkey", "p_type"]]
    lineitem_filtered = lineitem.loc[
        :, ["l_extendedprice", "l_discount", "l_shipdate", "l_partkey"]
    ]
    sel = (lineitem_filtered.l_shipdate >= startDate) & (
        lineitem_filtered.l_shipdate < endDate
    )
    flineitem = lineitem_filtered[sel]
    jn = flineitem.merge(part_filtered, left_on="l_partkey", right_on="p_partkey")
    jn["tmp"] = jn.l_extendedprice * (1.0 - jn.l_discount)
    total = jn[jn.p_type.str.startswith(p_type_like)].tmp.sum() * 100 / jn.tmp.sum()
    return total


def query_15(dataset_path, scale):
    import pandas as pd
    import warnings
    warnings.simplefilter(action='ignore', category=FutureWarning)

    lineitem = pd.read_csv(f'{dataset_path}/lineitem.csv',
                           parse_dates=['l_shipdate', 'l_commitdate', 'l_receiptdate'])
    supplier = pd.read_csv(f'{dataset_path}/supplier.csv')

    lineitem_filtered = lineitem[
        (lineitem["l_shipdate"] >= pd.Timestamp("1996-01-01"))
        & (
            lineitem["l_shipdate"]
            < (pd.Timestamp("1996-01-01") + pd.DateOffset(months=3))
        )
    ]
    lineitem_filtered["revenue_parts"] = lineitem_filtered["l_extendedprice"] * (
        1.0 - lineitem_filtered["l_discount"]
    )
    lineitem_filtered = lineitem_filtered.loc[:, ["l_suppkey", "revenue_parts"]]
    revenue_table = (
        lineitem_filtered.groupby("l_suppkey", as_index=False, sort=False)
        .agg(total_revenue=pd.NamedAgg(column="revenue_parts", aggfunc="sum"))
        .rename(columns={"l_suppkey": "supplier_no"})
    )
    max_revenue = revenue_table["total_revenue"].max()
    revenue_table = revenue_table[revenue_table["total_revenue"] == max_revenue]
    supplier_filtered = supplier.loc[:, ["s_suppkey", "s_name", "s_address", "s_phone"]]
    total = supplier_filtered.merge(
        revenue_table, left_on="s_suppkey", right_on="supplier_no", how="inner"
    )
    total = total.loc[
        :, ["s_suppkey", "s_name", "s_address", "s_phone", "total_revenue"]
    ]
    return total


def query_16(dataset_path, scale):
    import pandas as pd
    import warnings
    warnings.simplefilter(action='ignore', category=FutureWarning)

    part = pd.read_csv(f'{dataset_path}/part.csv')
    partsupp = pd.read_csv(f'{dataset_path}/partsupp.csv')
    supplier = pd.read_csv(f'{dataset_path}/supplier.csv')

    part_filtered = part[
        (part["p_brand"] != "Brand#45")
        & (~part["p_type"].str.contains("^MEDIUM POLISHED"))
        & part["p_size"].isin([49, 14, 23, 45, 19, 3, 36, 9])
    ]
    part_filtered = part_filtered.loc[:, ["p_partkey", "p_brand", "p_type", "p_size"]]
    partsupp_filtered = partsupp.loc[:, ["ps_partkey", "ps_suppkey"]]
    total = part_filtered.merge(
        partsupp_filtered, left_on="p_partkey", right_on="ps_partkey", how="inner"
    )
    total = total.loc[:, ["p_brand", "p_type", "p_size", "ps_suppkey"]]
    supplier_filtered = supplier[
        supplier["s_comment"].str.contains(r"Customer(\S|\s)*Complaints")
    ]
    supplier_filtered = supplier_filtered.loc[:, ["s_suppkey"]].drop_duplicates()
    # left merge to select only PS_SUPPKEY values not in supplier_filtered
    total = total.merge(
        supplier_filtered, left_on="ps_suppkey", right_on="s_suppkey", how="left"
    )
    total = total[total["s_suppkey"].isna()]
    total = total.loc[:, ["p_brand", "p_type", "p_size", "ps_suppkey"]]
    total = total.groupby(["p_brand", "p_type", "p_size"], as_index=False, sort=False)[
        "ps_suppkey"
    ].nunique()
    total.columns = ["p_brand", "p_type", "p_size", "supplier_cnt"]
    total = total.sort_values(
        by=["supplier_cnt", "p_brand", "p_type", "p_size"],
        ascending=[False, True, True, True],
    )
    return total


def query_17(dataset_path, scale):
    import pandas as pd
    import warnings
    warnings.simplefilter(action='ignore', category=FutureWarning)

    lineitem = pd.read_csv(f'{dataset_path}/lineitem.csv',
                           parse_dates=['l_shipdate', 'l_commitdate', 'l_receiptdate'])
    part = pd.read_csv(f'{dataset_path}/part.csv')

    left = lineitem.loc[:, ["l_partkey", "l_quantity", "l_extendedprice"]]
    right = part[((part["p_brand"] == "Brand#23") & (part["p_container"] == "MED BOX"))]
    right = right.loc[:, ["p_partkey"]]
    line_part_merge = left.merge(
        right, left_on="l_partkey", right_on="p_partkey", how="inner"
    )
    line_part_merge = line_part_merge.loc[
        :, ["l_quantity", "l_extendedprice", "p_partkey"]
    ]
    lineitem_filtered = lineitem.loc[:, ["l_partkey", "l_quantity"]]
    lineitem_avg = lineitem_filtered.groupby(
        ["l_partkey"], as_index=False, sort=False
    ).agg(avg=pd.NamedAgg(column="l_quantity", aggfunc="mean"))
    lineitem_avg["avg"] = 0.2 * lineitem_avg["avg"]
    lineitem_avg = lineitem_avg.loc[:, ["l_partkey", "avg"]]
    total = line_part_merge.merge(
        lineitem_avg, left_on="p_partkey", right_on="l_partkey", how="inner"
    )
    total = total[total["l_quantity"] < total["avg"]]
    total = pd.DataFrame({"avg_yearly": [total["l_extendedprice"].sum() / 7.0]})
    return total

def query_18(dataset_path, scale):
    import pandas as pd
    import warnings
    warnings.simplefilter(action='ignore', category=FutureWarning)

    lineitem = pd.read_csv(f'{dataset_path}/lineitem.csv',
                           parse_dates=['l_shipdate', 'l_commitdate', 'l_receiptdate'])
    orders = pd.read_csv(f'{dataset_path}/orders.csv', parse_dates=['o_orderdate'])
    customer = pd.read_csv(f'{dataset_path}/customer.csv')

    gb1 = lineitem.groupby("l_orderkey", as_index=False, sort=False)["l_quantity"].sum()
    fgb1 = gb1[gb1.l_quantity > 300]
    jn1 = fgb1.merge(orders, left_on="l_orderkey", right_on="o_orderkey")
    jn2 = jn1.merge(customer, left_on="o_custkey", right_on="c_custkey")
    gb2 = jn2.groupby(
        ["c_name", "c_custkey", "o_orderkey", "o_orderdate", "o_totalprice"],
        as_index=False,
        sort=False,
    )["l_quantity"].sum()
    total = gb2.sort_values(["o_totalprice", "o_orderdate"], ascending=[False, True])
    return total

def query_19(dataset_path, scale):
    import pandas as pd
    import warnings
    warnings.simplefilter(action='ignore', category=FutureWarning)

    lineitem = pd.read_csv(f'{dataset_path}/lineitem.csv',
                           parse_dates=['l_shipdate', 'l_commitdate', 'l_receiptdate'])
    part = pd.read_csv(f'{dataset_path}/part.csv')

    Brand31 = "Brand#31"
    Brand43 = "Brand#43"
    SMBOX = "SM BOX"
    SMCASE = "SM CASE"
    SMPACK = "SM PACK"
    SMPKG = "SM PKG"
    MEDBAG = "MED BAG"
    MEDBOX = "MED BOX"
    MEDPACK = "MED PACK"
    MEDPKG = "MED PKG"
    LGBOX = "LG BOX"
    LGCASE = "LG CASE"
    LGPACK = "LG PACK"
    LGPKG = "LG PKG"
    DELIVERINPERSON = "DELIVER IN PERSON"
    AIR = "AIR"
    AIRREG = "AIRREG"
    lsel = (
        (
            ((lineitem.l_quantity <= 36) & (lineitem.l_quantity >= 26))
            | ((lineitem.l_quantity <= 25) & (lineitem.l_quantity >= 15))
            | ((lineitem.l_quantity <= 14) & (lineitem.l_quantity >= 4))
        )
        & (lineitem.l_shipinstruct == DELIVERINPERSON)
        & ((lineitem.l_shipmode == AIR) | (lineitem.l_shipmode == AIRREG))
    )
    psel = (part.p_size >= 1) & (
        (
            (part.p_size <= 5)
            & (part.p_brand == Brand31)
            & (
                (part.p_container == SMBOX)
                | (part.p_container == SMCASE)
                | (part.p_container == SMPACK)
                | (part.p_container == SMPKG)
            )
        )
        | (
            (part.p_size <= 10)
            & (part.p_brand == Brand43)
            & (
                (part.p_container == MEDBAG)
                | (part.p_container == MEDBOX)
                | (part.p_container == MEDPACK)
                | (part.p_container == MEDPKG)
            )
        )
        | (
            (part.p_size <= 15)
            & (part.p_brand == Brand43)
            & (
                (part.p_container == LGBOX)
                | (part.p_container == LGCASE)
                | (part.p_container == LGPACK)
                | (part.p_container == LGPKG)
            )
        )
    )
    flineitem = lineitem[lsel]
    fpart = part[psel]
    jn = flineitem.merge(fpart, left_on="l_partkey", right_on="p_partkey")
    jnsel = (
        (jn.p_brand == Brand31)
        & (
            (jn.p_container == SMBOX)
            | (jn.p_container == SMCASE)
            | (jn.p_container == SMPACK)
            | (jn.p_container == SMPKG)
        )
        & (jn.l_quantity >= 4)
        & (jn.l_quantity <= 14)
        & (jn.p_size <= 5)
        | (jn.p_brand == Brand43)
        & (
            (jn.p_container == MEDBAG)
            | (jn.p_container == MEDBOX)
            | (jn.p_container == MEDPACK)
            | (jn.p_container == MEDPKG)
        )
        & (jn.l_quantity >= 15)
        & (jn.l_quantity <= 25)
        & (jn.p_size <= 10)
        | (jn.p_brand == Brand43)
        & (
            (jn.p_container == LGBOX)
            | (jn.p_container == LGCASE)
            | (jn.p_container == LGPACK)
            | (jn.p_container == LGPKG)
        )
        & (jn.l_quantity >= 26)
        & (jn.l_quantity <= 36)
        & (jn.p_size <= 15)
    )
    jn = jn[jnsel]
    total = (jn.l_extendedprice * (1.0 - jn.l_discount)).sum()
    return total

def query_20(dataset_path, scale):
    import pandas as pd
    import warnings
    warnings.simplefilter(action='ignore', category=FutureWarning)

    lineitem = pd.read_csv(f'{dataset_path}/lineitem.csv',
                           parse_dates=['l_shipdate', 'l_commitdate', 'l_receiptdate'])
    part = pd.read_csv(f'{dataset_path}/part.csv')
    partsupp = pd.read_csv(f'{dataset_path}/partsupp.csv')
    nation = pd.read_csv(f'{dataset_path}/nation.csv')
    supplier = pd.read_csv(f'{dataset_path}/supplier.csv')

    date1 = pd.Timestamp("1996-01-01")
    date2 = pd.Timestamp("1997-01-01")
    psel = part.p_name.str.startswith("azure")
    nsel = nation.n_name == "JORDAN"
    lsel = (lineitem.l_shipdate >= date1) & (lineitem.l_shipdate < date2)
    fpart = part[psel]
    fnation = nation[nsel]
    flineitem = lineitem[lsel]
    jn1 = fpart.merge(partsupp, left_on="p_partkey", right_on="ps_partkey")
    jn2 = jn1.merge(
        flineitem,
        left_on=["ps_partkey", "ps_suppkey"],
        right_on=["l_partkey", "l_suppkey"],
    )
    gb = jn2.groupby(
        ["ps_partkey", "ps_suppkey", "ps_availqty"], as_index=False, sort=False
    )["l_quantity"].sum()
    gbsel = gb.ps_availqty > (0.5 * gb.l_quantity)
    fgb = gb[gbsel]
    jn3 = fgb.merge(supplier, left_on="ps_suppkey", right_on="s_suppkey")
    jn4 = fnation.merge(jn3, left_on="n_nationkey", right_on="s_nationkey")
    jn4 = jn4.loc[:, ["s_name", "s_address"]]
    total = jn4.sort_values("s_name").drop_duplicates()
    return total


def query_21(dataset_path, scale):
    import pandas as pd
    import warnings
    warnings.simplefilter(action='ignore', category=FutureWarning)

    lineitem = pd.read_csv(f'{dataset_path}/lineitem.csv',
                           parse_dates=['l_shipdate', 'l_commitdate', 'l_receiptdate'])
    orders = pd.read_csv(f'{dataset_path}/orders.csv', parse_dates=['o_orderdate'])
    nation = pd.read_csv(f'{dataset_path}/nation.csv')
    supplier = pd.read_csv(f'{dataset_path}/supplier.csv')

    lineitem_filtered = lineitem.loc[
        :, ["l_orderkey", "l_suppkey", "l_receiptdate", "l_commitdate"]
    ]

    # Keep all rows that have another row in linetiem with the same orderkey and different suppkey
    lineitem_orderkeys = (
        lineitem_filtered.loc[:, ["l_orderkey", "l_suppkey"]]
        .groupby("l_orderkey", as_index=False, sort=False)["l_suppkey"]
        .nunique()
    )
    lineitem_orderkeys.columns = ["l_orderkey", "nunique_col"]
    lineitem_orderkeys = lineitem_orderkeys[lineitem_orderkeys["nunique_col"] > 1]
    lineitem_orderkeys = lineitem_orderkeys.loc[:, ["l_orderkey"]]

    # Keep all rows that have l_receiptdate > l_commitdate
    lineitem_filtered = lineitem_filtered[
        lineitem_filtered["l_receiptdate"] > lineitem_filtered["l_commitdate"]
    ]
    lineitem_filtered = lineitem_filtered.loc[:, ["l_orderkey", "l_suppkey"]]

    # Merge Filter + Exists
    lineitem_filtered = lineitem_filtered.merge(
        lineitem_orderkeys, on="l_orderkey", how="inner"
    )

    # Not Exists: Check the exists condition isn't still satisfied on the output.
    lineitem_orderkeys = lineitem_filtered.groupby(
        "l_orderkey", as_index=False, sort=False
    )["l_suppkey"].nunique()
    lineitem_orderkeys.columns = ["l_orderkey", "nunique_col"]
    lineitem_orderkeys = lineitem_orderkeys[lineitem_orderkeys["nunique_col"] == 1]
    lineitem_orderkeys = lineitem_orderkeys.loc[:, ["l_orderkey"]]

    # Merge Filter + Not Exists
    lineitem_filtered = lineitem_filtered.merge(
        lineitem_orderkeys, on="l_orderkey", how="inner"
    )

    orders_filtered = orders.loc[:, ["o_orderstatus", "o_orderkey"]]
    orders_filtered = orders_filtered[orders_filtered["o_orderstatus"] == "F"]
    orders_filtered = orders_filtered.loc[:, ["o_orderkey"]]
    total = lineitem_filtered.merge(
        orders_filtered, left_on="l_orderkey", right_on="o_orderkey", how="inner"
    )
    total = total.loc[:, ["l_suppkey"]]

    supplier_filtered = supplier.loc[:, ["s_suppkey", "s_nationkey", "s_name"]]
    total = total.merge(
        supplier_filtered, left_on="l_suppkey", right_on="s_suppkey", how="inner"
    )
    total = total.loc[:, ["s_nationkey", "s_name"]]
    nation_filtered = nation.loc[:, ["n_name", "n_nationkey"]]
    nation_filtered = nation_filtered[nation_filtered["n_name"] == "SAUDI ARABIA"]
    total = total.merge(
        nation_filtered, left_on="s_nationkey", right_on="n_nationkey", how="inner"
    )
    total = total.loc[:, ["s_name"]]
    total = total.groupby("s_name", as_index=False, sort=False).size()
    total.columns = ["s_name", "numwait"]
    total = total.sort_values(by=["numwait", "s_name"], ascending=[False, True])
    return total


def query_22(dataset_path, scale):
    import pandas as pd
    import warnings
    warnings.simplefilter(action='ignore', category=FutureWarning)

    orders = pd.read_csv(f'{dataset_path}/orders.csv', parse_dates=['o_orderdate'])
    customer = pd.read_csv(f'{dataset_path}/customer.csv')

    customer_filtered = customer.loc[:, ["c_acctbal", "c_custkey"]]
    customer_filtered["cntrycode"] = customer["c_phone"].str.slice(0, 2)
    customer_filtered = customer_filtered[
        (customer["c_acctbal"] > 0.00)
        & customer_filtered["cntrycode"].isin(
            ["13", "31", "23", "29", "30", "18", "17"]
        )
    ]
    avg_value = customer_filtered["c_acctbal"].mean()
    customer_filtered = customer_filtered[customer_filtered["c_acctbal"] > avg_value]
    # Select only the keys that don't match by performing a left join and only selecting columns with an na value
    orders_filtered = orders.loc[:, ["o_custkey"]].drop_duplicates()
    customer_keys = customer_filtered.loc[:, ["c_custkey"]].drop_duplicates()
    customer_selected = customer_keys.merge(
        orders_filtered, left_on="c_custkey", right_on="o_custkey", how="left"
    )
    customer_selected = customer_selected[customer_selected["o_custkey"].isna()]
    customer_selected = customer_selected.loc[:, ["c_custkey"]]
    customer_selected = customer_selected.merge(
        customer_filtered, on="c_custkey", how="inner"
    )
    customer_selected = customer_selected.loc[:, ["cntrycode", "c_acctbal"]]
    agg1 = customer_selected.groupby(["cntrycode"], as_index=False, sort=False).size()
    agg1.columns = ["cntrycode", "numcust"]
    agg2 = customer_selected.groupby(["cntrycode"], as_index=False, sort=False).agg(
        totacctbal=pd.NamedAgg(column="c_acctbal", aggfunc="sum")
    )
    total = agg1.merge(agg2, on="cntrycode", how="inner")
    total = total.sort_values(by=["cntrycode"], ascending=[True])
    return total