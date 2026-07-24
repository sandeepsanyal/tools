# Importing python modules
from typing import Optional
import numpy as np
import pandas as pd
import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_values
from tqdm import tqdm

def to_sql(
    df: pd.core.frame.DataFrame,
    table_name: str,
    host: str,
    database: str,
    user: str,
    password: str,
    port: int = 5432,
    schema: str = "public",
    column_dat_type: Optional[dict] = None
) -> None:
    """
    Exports a pandas DataFrame to PostgreSQL

    Parameters
    ----------
    df: Pandas DataFrame
        The DataFrame to export to PostgreSQL. It is not modified in place.
    table_name: string
        SQL table name by which df should be stored
    host: string
        PostgreSQL host name/ IP address
    database: string
        PostgreSQL database name where it is to be stored
    user: string
        User name for access to the database
    password: string
        Password for the user name for access to the database
    port: int
        PostgreSQL port. Default: 5432
    schema: string
        Schema in which the table should be created. Default: "public"
    column_dat_type: dictionary
        A dictionary of column name (post "." -> "_" sanitisation) and their data type (in SQL format)
        specified by the user, e.g. {"my_col": ["NUMERIC(10,2)", "NOT NULL"]}
        Omitting a column here lets this function infer its data type automatically

    Returns
    -------
    None. A table is created in the specified PostgreSQL database/schema and populated with df's rows.

    Raises
    ------
    TypeError
        If a column's dtype cannot be auto-mapped to a SQL type (e.g. bool, datetime).
        Supply an explicit entry in column_dat_type for that column instead.
    """

    # sanitise column names for SQL support without mutating the caller's DataFrame
    print("Checking column names for sql support")
    sanitised_columns = [str(x).replace(".", "_") for x in df.columns]
    print("Column names for sql support: Checked")

    # inferring each column's SQL data type
    print("Identifying column data types")
    column_definitions = {}
    for source_col, col in tqdm(list(zip(df.columns, sanitised_columns))):
        if column_dat_type is not None and col in column_dat_type:
            column_definitions[col] = column_dat_type[col]
            continue

        # is_string_dtype (not `== "object"`) also catches pandas's newer "str" dtype
        if pd.api.types.is_string_dtype(df[source_col]):
            dat_type = "VARCHAR"
            if df[source_col].empty:
                dat_len = ""  # no rows to size from; fall back to unbounded VARCHAR
            else:
                # size the column to the longest value actually present so no row gets rejected on insert
                dat_len = "(" + str(max(df[source_col].apply(str).apply(len))) + ")"

        elif str(df.dtypes[source_col])[:3] == "int":
            if df[source_col].empty:
                dat_type = "BIGINT"  # no rows to infer a tighter bound from; BIGINT is a safe superset
            else:
                col_min = np.nanmin(df[source_col])
                col_max = np.nanmax(df[source_col])
                # bound on BOTH min and max: e.g. [-40000, 10] has a small max but overflows SMALLINT's floor
                if (col_min >= -pow(2,15)) & (col_max <= pow(2,15)-1):
                    dat_type = "SMALLINT"
                elif (col_min >= -pow(2,31)) & (col_max <= pow(2,31)-1):
                    dat_type = "INTEGER"
                else:
                    dat_type = "BIGINT"
            dat_len = ""

        elif str(df.dtypes[source_col])[:5] == "float":
            dat_type = "NUMERIC"
            # derive precision/scale from actual digit counts so "-" and "." aren't counted as digits
            str_vals = df[source_col].dropna().apply(str)
            if str_vals.empty:
                dat_len = ""  # column is entirely null; fall back to unbounded NUMERIC
            else:
                int_part, _, dec_part = zip(*(v.partition(".") for v in str_vals))
                precision = max(
                    len(i.lstrip("-")) + len(d) for i, d in zip(int_part, dec_part)
                )
                scale = max(len(d) for d in dec_part)
                dat_len = "(" + str(precision) + "," + str(scale) + ")"

        else:
            # bool/datetime/etc. have no auto-mapping here; fail loudly instead of leaving dat_type undefined
            raise TypeError(
                "Unsupported dtype '{}' for column {}. "
                "Pass an explicit entry in column_dat_type for this column.".format(
                    df.dtypes[source_col], col
                )
            )

        column_definitions[col] = (dat_type + dat_len, "NULL")
    print("Column Data types identified")

    # connecting to the database
    conn = psycopg2.connect(
        host=host,
        port=port,
        dbname=database,
        user=user,
        password=password
    )
    cursor = conn.cursor()  # creating a cursor

    # try/finally so the cursor and connection are always released, even if CREATE TABLE or insert raises
    try:
        # creating an empty table; sql.Identifier quotes/escapes schema, table and column names safely
        print("Creating an empty SQL table: {}".format(table_name))
        create_stmt = sql.SQL("CREATE TABLE {}.{} ({})").format(
            sql.Identifier(schema),
            sql.Identifier(table_name),
            sql.SQL(", ").join(
                sql.SQL("{} {} {}").format(sql.Identifier(col), sql.SQL(dat_type), sql.SQL(nullable))
                for col, (dat_type, nullable) in column_definitions.items()
            )
        )
        cursor.execute(create_stmt)
        conn.commit()  # executing sql query

        # bulk inserting data
        print("Inserting rows to {}".format(table_name))
        # NaN -> None so psycopg2 writes SQL NULL instead of erroring on a missing value
        records = df.astype(object).where(pd.notnull(df), None).to_numpy().tolist()
        if records:
            insert_stmt = sql.SQL("INSERT INTO {}.{} ({}) VALUES %s").format(
                sql.Identifier(schema),
                sql.Identifier(table_name),
                sql.SQL(", ").join(sql.Identifier(col) for col in column_definitions)
            )
            # execute_values batches all rows into one round trip instead of cursor.execute() per row
            execute_values(cursor, insert_stmt, records)
            conn.commit()  # executing sql query
        else:
            print("No rows to insert: skipped")
    finally:
        cursor.close()  # closing cursor
        conn.close()  # closing database connection

    print(
        '\nTable: "{}" imported successfully'.format(table_name)
    )
