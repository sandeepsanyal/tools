import numpy as np
import pandas as pd
import re
import pyodbc
from tqdm import tqdm

def to_sql(
    df: pd.core.frame.DataFrame,
    table_name: str,
    server: str,
    database: str,
    user: str,
    password: str,
    driver: str = "SQL Server",
    trusted: str = "yes",
    column_dat_type: dict = None
):
    """

    """

# replace unreadable characters in dataframe
print("Checking column names for sql support")
col_names = [x.replace(".", "_") for x in df.columns.values.tolist()]
df.columns = col_names
print("Column names for sql support: Checked")

# creating a dictionary of column names and their data type
print("Identifying column data types")
col_dat_type = {}
for col in tqdm(col_names):
    if column_dat_type is not None:
        if col in column_dat_type.keys():
            col_dat_type = {
                **col_dat_type,
                **{
                    col: column_dat_type[col]
                }
            }
            continue
        else:
            pass
    else:
        pass
    if df.dtypes[col] == "object":
        dat_type = "VARCHAR"
        dat_len = "(" + str(max(df[col].apply(str).apply(len))) + ")"

    elif str(df.dtypes[col])[:3] == "int":
        # if (np.nanmin(df[col]) == 0) & (np.nanmax(df[col]) == 1):
        #     dat_type = "BINARY"
        #     dat_len = "(" + str(2) + ")"
        if (np.nanmin(df[col]) >= 0) & (np.nanmax(df[col]) <= 255):
            dat_type = "TINYINT"
            dat_len = ""
        elif abs(np.nanmax(df[col])) < pow(2,15):
            dat_type = "SMALLINT"
            dat_len = ""
        elif abs(np.nanmax(df[col])) < pow(2,31):
            dat_type = "INT"
            dat_len = ""
        else:
            dat_type = "BIGINT"
            dat_len = ""

    elif str(df.dtypes[col])[:5] == "float":
        dat_type = "NUMERIC"
        length = df[col].apply(str).apply(len)
        if type(
            df.loc[
                length == max(length),
                col
            ]) == pd.core.series.Series:
                max_value = df.loc[
                    length == max(length),
                    col
                ].reset_index(drop=True)[0]
        else:
            max_value = df.loc[
                length == max(length),
                col
            ]
        dat_len = "(" + str(len(str(max_value))) +\
            "," +\
            str(len(re.split(re.escape(r"."), str(max_value))[1])) +\
            ")"
        del length, max_value
    col_dat_type = {
        **col_dat_type,
        **{
            col: [dat_type + dat_len, "NULL"]
        }
    }
    del dat_type, dat_len
del col

col_dat_type = ", ".join(
    [i + " " + " ".join(col_dat_type[i]) for i in col_dat_type.keys()]
)
print("Column Data types identified")

# connecting to the database
conn = pyodbc.connect(
    "Driver={" + driver + "};"
    "Server=" + server + ";"
    "Database=" + database + ";"
    "UID=" + user + ";"
    "PWD=" + password + ";"
    "Trusted_Connection=" + trusted + ";"
)
cursor = conn.cursor()  # creating a cursor

# creating an empty table
print("Creating an empty SQL table: {}".format(table_name))
cursor.execute(
    "CREATE TABLE [" +\
    database + "].[dbo].[" + table_name + "] ("+\
    col_dat_type + ")"
)
conn.commit()  # ececuting sql query

# plugging in data row by row
print("Inserting rows to {}".format(table_name))
for row in tqdm(df.iterrows()):
    cursor.execute(
        "INSERT INTO [" +\
        database + "].[dbo].[" +\
        table_name + "] (" + ', '.join(col_names) +\
        ") VALUES " + "(" + ", ".join([r"?"]*len(col_names)) + ")",
        tuple(row[1].values)
    )
conn.commit()  # ececuting sql query

cursor.close()  # closing cursor
conn.close()  # closing database connection

print(
    '\nTable: "{}" imported successfully'.format(table_name)
)
