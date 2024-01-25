# Importing python modules
import time
import math
import numpy as np
import pandas as pd
import mysql.connector
from tqdm import tqdm

def to_sql(
    host: str,
    user: str,
    password: str,
    database: str,
    df: pd.core.frame.DataFrame,
    table_name: str,
    column_dat_type: dict = None
):
    """
    Exports a pandas DataFrame to SQL Server

    Parameters
    ----------
    df: Pandas DataFrame
        The DataFrame to export to SQL Server
    table_name: string
        SQL table name by which df should be stored
    host: string
        MySQL host name/ IP address
    database: string
        SQL Server database name where it is to be stored
    user: string
        User name for access to the database
    password: string
        Password for the user name for access to the database
    column_dat_type: dictionary
        A dictionary of column name and their data type (in SQL format) specified by the user
        Selection the default option allows this function to understand and create the dictionary of datatypes by itself

    Returns
    -------
    A table in MySQL in the database and server specified
    """


    # replace unreadable characters in dataframe
    print("Checking column names for sql support")
    col_names = [x.replace(".", "_") for x in df.columns.values.tolist()]
    df.columns = col_names
    print("Column names for sql support: Checked")

    # creating a dictionary of column names and their data type
    print("Identifying column data types")
    col_dat_type = {}
    for col in col_names:
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
            if (np.nanmin(df[col]) >= -pow(2,7)) & (np.nanmax(df[col]) <= pow(2,7)-1):
                dat_type = "TINYINT"
                if np.nanmin(df[col]) < 0:
                    dat_len = "(" + str(max(df[col].apply(str).apply(len)) -1) + ")"
                else:
                    dat_len = "(" + str(max(df[col].apply(str).apply(len))) + ")"
            elif (np.nanmin(df[col]) >= -pow(2,15)) & (np.nanmax(df[col]) <= pow(2,15)-1):
                dat_type = "SMALLINT"
                if np.nanmin(df[col]) < 0:
                    dat_len = "(" + str(max(df[col].apply(str).apply(len)) -1) + ")"
                else:
                    dat_len = "(" + str(max(df[col].apply(str).apply(len))) + ")"
            elif (np.nanmin(df[col]) >= -pow(2,23)) & (np.nanmax(df[col]) <= pow(2,23)-1):
                dat_type = "MEDIUMINT"
                if np.nanmin(df[col]) < 0:
                    dat_len = "(" + str(max(df[col].apply(str).apply(len)) -1) + ")"
                else:
                    dat_len = "(" + str(max(df[col].apply(str).apply(len))) + ")"
            elif (np.nanmin(df[col]) >= -pow(2,31)) & (np.nanmax(df[col]) <= pow(2,31)-1):
                dat_type = "INT"
                if np.nanmin(df[col]) < 0:
                    dat_len = "(" + str(max(df[col].apply(str).apply(len)) -1) + ")"
                else:
                    dat_len = "(" + str(max(df[col].apply(str).apply(len))) + ")"
            elif (np.nanmin(df[col]) >= -pow(2,63)) & (np.nanmax(df[col]) <= pow(2,63)-1):
                dat_type = "BIGINT"
                if np.nanmin(df[col]) < 0:
                    dat_len = "(" + str(max(df[col].apply(str).apply(len)) -1) + ")"
                else:
                    dat_len = "(" + str(max(df[col].apply(str).apply(len))) + ")"

        elif str(df.dtypes[col])[:5] == "float":
            dat_type = "NUMERIC"
            splt = df[col].apply(str).str.split(pat=".", expand=True)
            
            length_num = max(splt[0].apply(str).apply(len))
            length_dec = max(splt[1].apply(str).apply(len))
            dat_len = "(" + str(length_num + length_dec) +\
                "," +\
                str(length_dec) +\
                ")"
            del length_num, length_dec

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

    # connecting to database
    mydb = mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        database=database
    )
    mycursor = mydb.cursor()  # creating a cursor

    # creating an empty table
    mycursor.execute(
        "CREATE TABLE " +\
        table_name + " ("+\
        col_dat_type + ")"
    )

   
    print("Reading data to memory")
    time.sleep(0.2)
    sql = "INSERT INTO " + table_name + " (" +\
        ", ".join(col_names) + ") VALUES (" +\
        ", ".join(np.repeat(r"%s", repeats=len(col_names))) + ")" 
    

    print("Inserting rows to {}".format(table_name))
    for row in tqdm(df.iterrows(), total = df.shape[0]):
        val = []
        for t in tuple(row[1].values):
            if isinstance(t, float):
                if math.isnan(t):
                    val = val+[None]
                else:
                    val = val+[t]
            else:
                val = val+[t]
        val = tuple(val)

        mycursor.execute(sql, val)

    mydb.commit()  # commit update
    print(
        '\nTable: "{}" imported successfully\n'.format(table_name)
    )

