# -*- coding: utf-8 -*-
import os
import sys
import ctypes
import sqlite3
from datetime import datetime

MB_OK = 0x0
MB_OKCXL = 0x01
MB_YESNOCXL = 0x03
MB_YESNO = 0x04
MB_HELP = 0x4000
ICON_WARN = 0x30
ICON_INFO = 0x40
ICON_ERROR = 0x10
IDYES = 6

MessageBox = ctypes.windll.user32.MessageBoxW

mypath = os.getcwd()

dbpath = mypath + r"\data.db"


# noinspection PyProtectedMember
def rpath():
    try:
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS)

        return os.path.join(os.path.abspath("."))
    except Exception as e:
        msg = "ERROR CRÍTICO: Imposible obtener path." + chr(10) +\
              e.__class__.__name__ + " " + str(e)
        print(msg)
        log_add(msg)
        MessageBox(None, msg, 'Error', ICON_ERROR)
        sys.exit()


def log_add(message, overwrite=False):

    try:
        file = mypath + chr(92) + "Log.txt"

        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")

        message += chr(10)

        file = open(file, "a" if not overwrite and os.path.isfile(file) else "w")
        file.write(dt_string + "|" + message)
        file.close()

    except Exception as e:
        msg = "WARNING: No se pudo añadir mensaje al log." + chr(10) +\
              "MENSAJE:" + chr(10) +\
              message + chr(10)*2 +\
              "DETALLE:" + chr(10) +\
              e.__class__.__name__ + " " + str(e)
        print(msg)


def crear_tablas(conn):
    try:
        cur = conn.cursor()

        cur.execute("CREATE TABLE IF NOT EXISTS FUENTES "
                    "(NOMBRE TEXT UNIQUE, ACTIVO INTEGER)")
        cur.execute("CREATE TABLE IF NOT EXISTS CLAVES "
                    "(CLAVE TEXT UNIQUE, INGLES TEXT UNIQUE)")
        cur.execute("CREATE TABLE IF NOT EXISTS DESTINATARIOS "
                    "(DESTINATARIO TEXT UNIQUE)")
        cur.execute("CREATE TABLE IF NOT EXISTS CONFIG "
                    "(DESCRIPCION TEXT UNIQUE, VALOR TEXT)")
        cur.execute("CREATE TABLE IF NOT EXISTS BITACORA "
                    "(FUENTE TEXT, NOTICIA TEXT, ESTADO TEXT)")
        cur.execute("CREATE TABLE IF NOT EXISTS PATH "
                    "(WSPATH TEXT)")

        cur.execute("INSERT INTO CONFIG (DESCRIPCION) " +
                    "SELECT 'AUT' " +
                    "WHERE NOT EXISTS(" +
                    "SELECT DESCRIPCION FROM CONFIG WHERE DESCRIPCION = 'AUT')")

        cur.execute("INSERT INTO CONFIG (DESCRIPCION, VALOR) " +
                    "SELECT 'LAPSO', '30' " +
                    "WHERE NOT EXISTS(" +
                    "SELECT DESCRIPCION FROM CONFIG WHERE DESCRIPCION = 'LAPSO')")

        cur.execute("INSERT INTO CONFIG (DESCRIPCION, VALOR) " +
                    "SELECT 'ADJUNTAR', 'down' " +
                    "WHERE NOT EXISTS(" +
                    "SELECT DESCRIPCION FROM CONFIG WHERE DESCRIPCION = 'ADJUNTAR')")

        cur.execute("INSERT INTO PATH (WSPATH) " +
                    "SELECT '" + rpath() + chr(92) + "WS' " +
                    "WHERE NOT EXISTS(" +
                    "SELECT WSPATH FROM PATH)")

        # cur.execute("UPDATE PATH SET WSPATH = '" + rpath() + chr(92) + "WS'")

        conn.commit()
    except Exception as e:
        msg = "ERROR CRÍTICO: Excepción módulo database función crear_tablas." + chr(10)*2 +\
              "Detalle:" + chr(10) + e.__class__.__name__ + " " + str(e) + chr(10)*2 +\
              "Si el problema persiste póngase en contacto con el desarrollador."
        print(msg)
        log_add(msg)
        MessageBox(None, msg, 'Error', ICON_ERROR)
        sys.exit()


def db_main(query=""):
    lst = []

    try:
        conn = sqlite3.connect(dbpath)
        crear_tablas(conn)

        if query != "":
            cur = conn.cursor()
            lst = cur.execute(query).fetchall()
            conn.commit()

        conn.close()

        return lst

    except Exception as e:
        msg = str(e)
        print(msg)
        log_add(msg)
        MessageBox(None, msg, 'Error', ICON_WARN)


def return_elements(tablename, index=None):
    columnname = ""
    lst = []

    if tablename == "FUENTES":
        columnname = "NOMBRE, ACTIVO"
    elif tablename == "CLAVES":
        columnname = "CLAVE, INGLES"
    elif tablename == "DESTINATARIOS":
        columnname = "DESTINATARIO"

    data = db_main("SELECT " + columnname + " FROM " + tablename + " ORDER BY " + columnname)

    if not index:
        lst = data
    else:
        for i in data:
            lst.append(i[index])

    return lst


def add_element(tablename, element):
    try:
        conn = sqlite3.connect(dbpath)
        crear_tablas(conn)
        cur = conn.cursor()

        if tablename != "FUENTES":
            cur.execute("INSERT INTO " + tablename + " VALUES ('" + element + "')")
            conn.commit()

        lst = return_elements(tablename)

        conn.close()

        log_add("ELEMENTO AÑADIDO A " + tablename + ": '" + element + "'")

        return lst

    except Exception as e:
        msg = "El elemento '" + element + "' no pudo ser añadido." + chr(10) * 2 + str(e)
        print(msg)
        log_add(msg)
        MessageBox(None, msg, 'Error', ICON_WARN)


def delete_element(tablename, element):
    lst = []
    columnname = ""

    if tablename == "CLAVES":
        columnname = "CLAVE"
    elif tablename == "DESTINATARIOS":
        columnname = "DESTINATARIO"

    if tablename != "FUENTES":
        db_main("DELETE FROM " + tablename + " WHERE " + columnname + " = '" + element + "'")
        lst = return_elements(tablename)

    log_add("ELEMENTO ELIMINADO DE " + tablename + ": '" + element + "'")

    return lst


def clear_binnacle(estado="REV"):

    if estado == "ALL":
        db_main("DELETE FROM BITACORA")
        log_add("BITÁCORA REINICIADA")

    else:
        db_main("DELETE FROM BITACORA WHERE ESTADO = '" + estado + "'")
        print("Elementos '" + estado + "' eliminados de bitácora")
        log_add("ELEMENTOS '" + estado + "' ELIMINADOS DE BITÁCORA")
