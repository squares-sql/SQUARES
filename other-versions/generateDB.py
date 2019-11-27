#!/usr/bin/python
# File: generateDB.py
# Description:  
# Author:   Pedro M Orvalho
# Created on:   21-02-2019 10:46:39
# Usage:    python generateDB.py
# Python version:   3.6.4

import sqlite3
from sqlite3 import Error
 
# functions from SQLite tutorial 
 
def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    try:
        conn = sqlite3.connect(db_file)
        return conn
        # print(sqlite3.version)
    except Error as e:
        print(e)
 
def create_table(conn, create_table_sql):
    """ create a table from the create_table_sql statement
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(e)

def import_table(cnn, sql_import_table):
    try:
        c = conn.cursor()
        c.execute('.import tables/{name}.txt {name}'.format(name=sql_import_table))
        # print(_script)
        # _script)
    except Error as e:
        print(e)


if __name__ == '__main__':
    database = "squares.db"

    conn = create_connection(database)

    sql_create_faculty_table = """ CREATE TABLE IF NOT EXISTS faculty(
                        fid number(9,0) primary key,
                        fname varchar2(30),
                        deptid number(2,0)
                        );"""
    sql_create_class_table  = """CREATE table IF NOT EXISTS class(
                                name varchar2(40) primary key,
                                meets_at varchar2(20),
                                room varchar2(10),
                                fid number(9,0),
                                foreign key(fid) references faculty
                                );"""

    sql_create_student_table = """ CREATE table IF NOT EXISTS student(
                                snum number(9,0) primary key,
                                sname varchar2(30),
                                major varchar2(25),
                                standing varchar2(2),
                                age number(3,0)
                                );"""
    sql_create_enrolled_table = """ CREATE table IF NOT EXISTS enrolled(
                                snum number(9,0),
                                cname varchar2(40),
                                primary key(snum,cname),
                                foreign key(snum) references student,
                                foreign key(cname) references class(name)
                                );"""
    if conn is not None:
       # create projects table
       create_table(conn, sql_create_faculty_table)
       create_table(conn, sql_create_class_table)
       create_table(conn, sql_create_student_table)
       create_table(conn, sql_create_enrolled_table)
       # import_table(conn, "faculty")
       # import_table(conn, "class")
       # import_table(conn, "student")
       # import_table(conn, "enrolled")
    else:
       print("Error! cannot create the database connection.")

    conn.close()