# -*- coding: utf-8 -*-
import re
import time
import random
import scrapy
import shutil
import requests
from abc import ABC
from lxml import html
import wsdatabase as db
from xhtml2pdf import pisa
from selenium import webdriver
import matplotlib.pyplot as plt
from scrapy.crawler import CrawlerProcess
from selenium.webdriver.chrome.options import Options

my_name = "<TopNews/>"
my_version = ""
DEFAULT_IMG = "TopNewsDefaultImage"
LINK_ICON = "TopNewsLinkIcon"

# ACTUALIZAR
MIN_SCORE = 5

# ACTUALIZAR
# FIG_REDIM = 0.83
FIG_WIDTH = 800
FIG_HEIGHT = 480

my_info_path = db.my_path[:len(db.my_path)-(db.my_path[::-1].find(chr(92))+1)] + r"\MY_INFO.txt"

if db.os.path.exists(my_info_path):
    f = open(my_info_path, "r")
    my_name = f.readline().split("|")[1].replace(chr(10), "")
    my_version = f.readline().split("|")[1]
else:
    print("Archivo 'MY_INFO' no encontrado.")

HEAD_HTML = r"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
.footer {
left: 0;
position:fixed;
bottom:0;
width: 100%;
font-family:Calibri;
color: #808080;
text-align: center;
}
</style>
</head>
<body>"""

FOOTER_HTML = chr(10) + r"""
    <br>
    <div class="footer">
    Análisis realizado y documentado automáticamente por bot 
    <a href='https://github.com/Ferd656/TopNews' style='text-decoration:none;color:#808080;' target='_blank'>
    &#60TopNews&#47&#62</a>
    </div>
</div>"""

mail_html = []
report_content = []

classes = []

# ============= SUPER CLASS ====================================================================================


class Scanner(scrapy.Spider, ABC):
    def __init__(self, lang, **kwargs):
        super().__init__(**kwargs)
        self.lang = lang
        classes.append(self)

        if self.name != "":
            db.db_main("INSERT INTO FUENTES (NOMBRE, ACTIVO) " +
                       "SELECT '" + self.name + "', 0 " +
                       "WHERE NOT EXISTS(" +
                       "SELECT NOMBRE FROM FUENTES WHERE NOMBRE = '" + self.name + "')")

    def get_name(self):
        return self.name

    def get_status(self):
        return db.db_main("SELECT ACTIVO FROM FUENTES WHERE NOMBRE = '" + self.name + "'")[0][0]

    def registrar(self, noticia, estado):
        db.db_main("INSERT INTO BITACORA (FUENTE, NOTICIA, ESTADO) VALUES ('" +
                   self.name + "','" + noticia + "','" + estado + "')")

    def mi_bitacora(self):
        response = []
        lst = db.db_main("SELECT NOTICIA FROM BITACORA WHERE FUENTE = '" + self.name + "'")
        for i in lst:
            response.append(i[0])
        return response

    @staticmethod
    def claves(lang):
        response = []
        if lang == "es":
            lst = db.db_main("SELECT CLAVE FROM CLAVES")
            for i in lst:
                response.append(i[0])
            return response
        else:
            lst = db.db_main("SELECT INGLES FROM CLAVES")
            for i in lst:
                response.append(i[0])
            return response

    @staticmethod
    def poop_txt(source, name, content):
        folderpath = db.main_app_path + r"\Articles"
        name = source + " - " + name
        try:
            name = remove_special_char(name)

            if not db.os.path.exists(folderpath):
                db.os.makedirs(folderpath)

            if len(name) > 100:
                name = name[0:100]

            file = open(folderpath + chr(92) + name + ".txt", "w")
            file.write(content)
            file.close()

        except Exception as e:
            msg = "Error al crear NOTICIA.TXT."
            print(msg + chr(10) + e.__class__.__name__ + " " + str(e))
            db.log_add(msg + e.__class__.__name__ + " " + str(e))


# ==============================================================================================================

# ============= SPIDERS ========================================================================================


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# PLANTILLA

class PlantillaSpyder(Scanner):

    def __init__(self, **kwargs):
        super().__init__(" ",  # poner aquí el idioma (en, es)
                         name=" ",  # poner aquí el nombre
                         start_urls=[" "],  # poner aquí la url
                         **kwargs)

    def parse(self, response):
        if self.get_status() == 1:
            try:
                bitacora = self.mi_bitacora()

                print("Escaneando '" + self.name + "' . . .")
                db.log_add("Escaneando '" + self.name + "' . . .")

                start_time = time.time()

                # Código del spider

                elapsed_time = time.time() - start_time

                msg = "Escaneo de '" + self.name + "' finalizado." + chr(10) + \
                      "Tiempo transcurrido: " + scs_in_hhmmss(elapsed_time)

                print(msg)
                db.log_add(msg.replace(chr(10), " "))

            except Exception as e:
                msg = "ERROR: Ha ocurrido un error accediendo a la data de '" + self.name + "'." + chr(10)*2 +\
                      "Detalle del error:" + chr(10) + \
                      e.__class__.__name__ + " " + str(e) + chr(10)*2 +\
                      "Quizás el proceso webscraping requiera una actualización " +\
                      "debido a nuevos métodos de seguridad implementados en la fuente " +\
                      "de los datos. En ese caso póngase " +\
                      "en contacto con el desarrollador para realizar los ajustes necesarios."
                print(msg)
                db.log_add(msg)

    # No olvidar usar la función 'utf_8_compatible' para los contenidos y 'remove_special_char' para los títulos

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -


class ElFinanciero(Scanner):

    def __init__(self, **kwargs):
        super().__init__("es",
                         name="El Financiero",
                         start_urls=["https://www.elfinancierocr.com/economia-y-politica/"],
                         **kwargs)

    def parse(self, response):
        if self.get_status() == 1:
            try:
                bitacora = self.mi_bitacora()

                print("Escaneando '" + self.name + "' . . .")
                db.log_add("Escaneando '" + self.name + "' . . .")

                start_time = time.time()

                core = "//div[@class='generic-results-list-main-wrapper']/div/article/header/div/"
                titulos = response.xpath(core + "div/figure/a/h4/text()")
                enlaces = response.xpath(core + "div/a/@href")
                imagenes = response.xpath(core + "div/a/div/img/@data-original")
                descripcion = response.xpath(core + "div[2]/figure/p/span/text()")

                titulos = list(filter(lambda item: item != ' ', titulos.extract()))

                for i in range(len(titulos)):

                    print("Validando items: " + str(i + 1) + " de " + str(len(titulos)))
                    titulo = remove_special_char(titulos[i])

                    if not titulo:
                        msg = "No hay título en noticia." + chr(10) + "Fuente: " + self.name
                        print(msg)
                        db.log_add(msg)

                    elif titulo not in bitacora:

                        source = "https://www.elfinancierocr.com" + enlaces[i].extract()
                        myscores = self.scores(titulo, source)

                        if len(myscores) >= MIN_SCORE:

                            try:
                                summary = descripcion[i].extract()
                            except Exception as e:
                                summary = titulo
                                msg = "No se obtuvo el resumen para " + titulo + "." + chr(10) +\
                                      e.__class__.__name__ + " " + str(e)
                                print(msg)
                                db.log_add(msg)

                            try:
                                img = imagenes[i].extract()
                            except Exception as e:
                                img = ""
                                msg = "No se obtuvo la imagen para " + titulo + "." + chr(10) +\
                                      e.__class__.__name__ + " " + str(e)
                                print(msg)
                                db.log_add(msg)

                            if not img:
                                img = DEFAULT_IMG
                            else:
                                img += "' width='200' height='150"

                            report_content.append({"item": titulo,
                                                   "score": len(myscores),
                                                   "source": self.name,
                                                   "source_url": source,
                                                   "summary": summary,
                                                   "scores": myscores})

                            mail_html.append((
                                chr(10) +
                                """<tr>
                                <td bgcolor='black' style= 'width:150px; height:100px; vertical-align:middle;
                                text-align:center;'>
                                <img src='""" + img + """'>
                                </td>
                                <td class='container'>
                                <div class='news'>&nbsp;""" + titulo + """"</div>
                                <div class='paragraph'>""" + summary + """"</div>
                                <br><div class='source'>Fuente: """ + self.name + """</div></br>
                                <a href='""" + source + """'>
                                <span><img src='""" + LINK_ICON + """' height='15'/>
                                &nbsp; Leer noticia &nbsp;&nbsp;</span>
                                </a>
                                </td>
                                </tr>""", len(myscores)))

                            self.registrar(titulo, "PEND")
                            print("Item " + str(i + 1) + " validado y almacenado.")
                            db.log_add("Registrado item: '" + titulo +
                                       "' Estado: 'PEND' Score: '" + str(len(myscores)) + "'")

                        else:
                            self.registrar(titulo, "REV")
                            db.log_add("Registrado item: '" + titulo +
                                       "' Estado: 'REV' Score: '" + str(len(myscores)) + "'")

                elapsed_time = time.time() - start_time

                msg = "Escaneo de '" + self.name + "' finalizado." + chr(10) + \
                      "Tiempo transcurrido: " + scs_in_hhmmss(elapsed_time)

                print(msg)
                db.log_add(msg.replace(chr(10), " "))

            except Exception as e:
                msg = "ERROR: Ha ocurrido un error accediendo a la data de '" + self.name + "'." + chr(10)*2 +\
                      "Detalle del error:" + chr(10) + \
                      e.__class__.__name__ + " " + str(e) + chr(10)*2 +\
                      "Quizás el proceso webscraping requiera una actualización " +\
                      "debido a nuevos métodos de seguridad implementados en la fuente " +\
                      "de los datos. En ese caso póngase " +\
                      "en contacto con el desarrollador para realizar los ajustes necesarios."
                print(msg)
                db.log_add(msg)

    def scores(self, name, link):
        scores = []
        try:
            page = requests.get(link)
            tree = html.fromstring(page.content)
            content = utf_8_compatible(chr(10).join(tree.xpath("//p[@class='element element-paragraph']/text()")))

            claves = self.claves(self.lang)

            for c in claves:
                coincidences = len(re.findall(c, content, re.IGNORECASE))
                if coincidences > 0:
                    scores.append([c, coincidences])

        except Exception as e:
            msg = "ERROR: Error al obtener score para '" + name +\
                  "'." + chr(10) + e.__class__.__name__ + " " + str(e)
            print(msg)
            db.log_add(msg)
            return []
        else:
            if len(scores) >= MIN_SCORE:
                self.poop_txt(self.name.upper(), name, content + chr(10)*2 + "Claves: " + str(scores))

            return scores


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -


class LaRepublica(Scanner):

    def __init__(self, **kwargs):
        super().__init__("es",
                         name="La Republica",
                         start_urls=["https://www.larepublica.net/seccion/ultima-hora"],
                         **kwargs)

    def parse(self, response):
        if self.get_status() == 1:
            try:
                bitacora = self.mi_bitacora()

                print("Escaneando '" + self.name + "' . . .")
                db.log_add("Escaneando '" + self.name + "' . . .")

                start_time = time.time()

                core = "//div[@class='column is-8 column-padding-right']/section/article/"
                titulos = response.xpath(core + "/a/h2/text()")
                enlaces = response.xpath(core + "/figure/a/@href")
                imagenes = response.xpath(core + "/figure/a//@src | " + core + "/figure/a//@lsrc")
                descripcion = response.xpath(core + "/p[@class='is-size-5 paddin-bottom-2' or " +
                                             "@class='is-size-4 paddin-bottom-3']/text()")

                titulos = list(filter(lambda item: item != ' ', titulos.extract()))

                for i in range(len(titulos)):

                    print("Validando items: " + str(i + 1) + " de " + str(len(titulos)))
                    titulo = remove_special_char(titulos[i])

                    if not titulo:
                        msg = "No hay título en noticia." + chr(10) + "Fuente: " + self.name
                        print(msg)
                        db.log_add(msg)

                    elif titulo not in bitacora:

                        source = enlaces[i].extract()
                        myscores = self.scores(titulo, source)

                        if len(myscores) >= MIN_SCORE:

                            try:
                                summary = descripcion[i].extract()
                            except Exception as e:
                                summary = titulo
                                msg = "No se obtuvo el resumen para " + titulo + "." + chr(10) +\
                                      e.__class__.__name__ + " " + str(e)
                                print(msg)
                                db.log_add(msg)

                            try:
                                img = imagenes[i].extract()
                            except Exception as e:
                                img = ""
                                msg = "No se obtuvo la imagen para " + titulo + "." + chr(10) +\
                                      e.__class__.__name__ + " " + str(e)
                                print(msg)
                                db.log_add(msg)

                            if not img:
                                img = DEFAULT_IMG
                            else:
                                img += "' width='200' height='150"

                            report_content.append({"item": titulo,
                                                   "score": len(myscores),
                                                   "source": self.name,
                                                   "source_url": source,
                                                   "summary": summary,
                                                   "scores": myscores})

                            mail_html.append((
                                chr(10) +
                                """<tr>
                                <td bgcolor='black' style= 'width:150px; height:100px; vertical-align:middle;
                                text-align:center;'>
                                <img src='""" + img + """'>
                                </td>
                                <td class='container'>
                                <div class='news'>&nbsp;""" + titulo + """"</div>
                                <div class='paragraph'>""" + summary + """"</div>
                                <br><div class='source'>Fuente: """ + self.name + """</div></br>
                                <a href='""" + source + """'>
                                <span><img src='""" + LINK_ICON + """' height='15'/>
                                &nbsp; Leer noticia &nbsp;&nbsp;</span>
                                </a>
                                </td>
                                </tr>""", len(myscores)))

                            self.registrar(titulo, "PEND")
                            print("Item " + str(i + 1) + " validado y almacenado.")
                            db.log_add("Registrado item: '" + titulo +
                                       "' Estado: 'PEND' Score: '" + str(len(myscores)) + "'")

                        else:
                            self.registrar(titulo, "REV")
                            db.log_add("Registrado item: '" + titulo +
                                       "' Estado: 'REV' Score: '" + str(len(myscores)) + "'")

                elapsed_time = time.time() - start_time

                msg = "Escaneo de '" + self.name + "' finalizado." + chr(10) + \
                      "Tiempo transcurrido: " + scs_in_hhmmss(elapsed_time)

                print(msg)
                db.log_add(msg.replace(chr(10), " "))

            except Exception as e:
                msg = "ERROR: Ha ocurrido un error accediendo a la data de '" + self.name + "'." + chr(10) * 2 + \
                      "Detalle del error:" + chr(10) + \
                      e.__class__.__name__ + " " + str(e) + chr(10) * 2 + \
                      "Quizás el proceso webscraping requiera una actualización " + \
                      "debido a nuevos métodos de seguridad implementados en la fuente " + \
                      "de los datos. En ese caso póngase " + \
                      "en contacto con el desarrollador para realizar los ajustes necesarios."
                print(msg)
                db.log_add(msg)

    def scores(self, name, link):
        scores = []
        try:
            content = ""

            page = requests.get(link)
            tree = html.fromstring(page.content)
            contentlst = tree.xpath("//div[@class='is-size-4 has-text-black has-text-justified article']//text()")

            for i in contentlst:
                if i != chr(10) and i[:10].replace(chr(10), "") != "Lea más: ":
                    if content:
                        content += chr(10) + utf_8_compatible(i)
                    else:
                        content = utf_8_compatible(i)

            claves = self.claves(self.lang)

            for c in claves:
                coincidences = len(re.findall(c, content, re.IGNORECASE))
                if coincidences > 0:
                    scores.append([c, coincidences])

        except Exception as e:
            msg = "ERROR: Error al obtener score para '" + name +\
                  "'." + chr(10) + e.__class__.__name__ + " " + str(e)
            print(msg)
            db.log_add(msg)
            return []
        else:
            if len(scores) >= MIN_SCORE:
                self.poop_txt(self.name.upper(), name, content + chr(10)*2 + "Claves: " + str(scores))

            return scores


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -


class CNN(Scanner):

    def __init__(self, **kwargs):
        super().__init__("en",
                         name="CNN",
                         start_urls=["https://edition.cnn.com/business"],
                         **kwargs)

    def parse(self, response):
        if self.get_status() == 1:
            try:
                bitacora = self.mi_bitacora()

                print("Escaneando '" + self.name + "' . . .")
                db.log_add("Escaneando '" + self.name + "' . . .")

                start_time = time.time()

                core = "//*[@id='us-zone-1']/div[2]/div/div" +\
                       "[@class='column zn__column--idx-0']/ul/li/article/div/div/h3[@class='cd__headline']/a"
                titulos = response.xpath(core + "/span[@class='cd__headline-text']/text()")
                enlaces = response.xpath(core + "/@href")

                for i in range(len(titulos)):

                    print("Validando items: " + str(i + 1) + " de " + str(len(titulos)))
                    titulo = remove_special_char(titulos[i].extract())

                    if titulo and titulo not in bitacora:
                        self.get_data(titulo, "https://edition.cnn.com" + enlaces[i].extract())

                elapsed_time = time.time() - start_time

                msg = "Escaneo de '" + self.name + "' finalizado." + chr(10) + \
                      "Tiempo transcurrido: " + scs_in_hhmmss(elapsed_time)

                print(msg)
                db.log_add(msg.replace(chr(10), " "))

            except Exception as e:
                msg = e.__class__.__name__ + " " + str(e)
                print(msg)
                db.log_add(msg)

    def get_data(self, titulo, source):
        img = ""
        try:
            page = requests.get(source, verify=False)
            tree = html.fromstring(page.content)

            content = " ".join(tree.xpath("//*[@id='body-text']//div[@class='zn-body__paragraph speakable']//text()"))

            if content:
                content += chr(10)

            content += " ".join(tree.xpath("//*[@id='body-text']//div[@class='zn-body__paragraph']//text()"))

            if content != "":

                try:
                    summary = " ".join(tree.xpath(
                        "//*[@id='body-text']//div[@class='el__leafmedia el__leafmedia--sourced-paragraph']/p//text()"))
                    if not summary:
                        summary = " ".join(tree.xpath(
                            "//div[@class='media__video-description media__video-description--inline']/text()"))
                except Exception as e:
                    summary = titulo
                    msg = "No se obtuvo el resumen para " + titulo + "." + chr(10) + \
                          e.__class__.__name__ + " " + str(e)
                    print(msg)
                    db.log_add(msg)

                content = utf_8_compatible(summary + chr(10) + content)

                myscores = self.scores(titulo, content)

                if len(myscores) >= MIN_SCORE:
                    try:
                        img = tree.xpath("//img[@class='media__image media__image--responsive']/@data-src-small")[0]
                    except Exception as e:
                        img = ""
                        msg = "No se obtuvo la imagen para " + titulo + "." + chr(10) + \
                              e.__class__.__name__ + " " + str(e)
                        print(msg)
                        db.log_add(msg)

                    if not img:
                        img = DEFAULT_IMG
                    else:
                        img = "https:" + img + "' width='200' height='150"

                    report_content.append({"item": titulo,
                                           "score": len(myscores),
                                           "source": self.name,
                                           "source_url": source,
                                           "summary": summary,
                                           "scores": myscores})

                    mail_html.append((
                        chr(10) +
                        """<tr>
                        <td bgcolor='black' style= 'width:150px; height:100px; vertical-align:middle;
                        text-align:center;'>
                        <img src='""" + img + """'>
                        </td>
                        <td class='container'>
                        <div class='news'>&nbsp;""" + titulo + """"</div>
                        <div class='paragraph'>""" + summary + """"</div>
                        <br><div class='source'>Fuente: """ + self.name + """</div></br>
                        <a href='""" + source + """'>
                        <span><img src='""" + LINK_ICON + """' height='15'/>
                        &nbsp; Leer noticia &nbsp;&nbsp;</span>
                        </a>
                        </td>
                        </tr>""", len(myscores)))

                    self.registrar(titulo, "PEND")
                    print("Item  validado y almacenado.")
                    db.log_add("Registrado item: '" + titulo +
                               "' Estado: 'PEND' Score: '" + str(len(myscores)) + "'")

                else:
                    self.registrar(titulo, "REV")
                    db.log_add("Registrado item: '" + titulo +
                               "' Estado: 'REV' Score: '" + str(len(myscores)) + "'")
            else:
                self.registrar(titulo, "REV")
                db.log_add("Registrado item: '" + titulo +
                           "' Estado: 'REV' Score: 'sin contenido'")

        except Exception as e:
            msg = "ERROR: Ha ocurrido un error accediendo a la data de '" + self.name + "'." + chr(10)*2 +\
                  "Detalle del error:" + chr(10) + \
                  e.__class__.__name__ + " " + str(e) + chr(10)*2 +\
                  "Quizás el proceso webscraping requiera una actualización " +\
                  "debido a nuevos métodos de seguridad implementados en la fuente " +\
                  "de los datos. En ese caso póngase " +\
                  "en contacto con el desarrollador para realizar los ajustes necesarios."
            print(msg)
            db.log_add(msg)

    def scores(self, name, content):
        scores = []
        try:
            claves = self.claves(self.lang)

            for c in claves:
                coincidences = len(re.findall(c, content, re.IGNORECASE))
                if coincidences > 0:
                    scores.append([c, coincidences])

        except Exception as e:
            msg = "ERROR: Error al obtener score para '" + name + \
                  "'." + chr(10) + e.__class__.__name__ + " " + str(e)
            print(msg)
            db.log_add(msg)
            return []
        else:
            if len(scores) >= MIN_SCORE:
                self.poop_txt(self.name.upper(), name, content + chr(10) * 2 + "Claves: " + str(scores))

            return scores


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -


class Bloomberg(Scanner):

    def __init__(self, **kwargs):
        super().__init__("en",
                         name="Bloomberg",
                         start_urls=["https://www.bloomberg.com/markets/economics"],
                         **kwargs)

        self.driver = db.main_app_path + r"\chromedriver.exe"

    def parse(self, response):

        if self.get_status() == 1:
            try:
                bitacora = self.mi_bitacora()

                print("Escaneando '" + self.name + "' . . .")
                db.log_add("Escaneando '" + self.name + "' . . .")

                start_time = time.time()

                if not db.os.path.isfile(self.driver):
                    msg = "Webdriver no encontrado en '" + self.driver + "'. Se usará versión por defecto."
                    print(msg)
                    db.log_add(msg)
                    self.driver = db.my_path + r"\chromedriver.exe"
                    print("Buscando Webdriver en '" + self.driver + "'")

                options = Options()
                prefs = {'profile.managed_default_content_settings.javascript': 2,
                         'disk-cache-size': 4096}

                options.add_experimental_option('prefs', prefs)

                browser = webdriver.Chrome(executable_path=self.driver,
                                           options=options)

                browser.get(self.start_urls[0])

                source_html = browser.page_source.encode("ascii", errors="ignore").decode()

                if "<title>Bloomberg - Are you a robot?</title>" in source_html:
                    msg = "Bloomberg ha detectado nuestro proceso automático, y por " +\
                          "lo tanto nos ha bloqueado el acceso a la data. Quizás " + \
                          "esto sea temporal y en el " +\
                          "próximo intento podramos obtener la información." + chr(10) + \
                          "Si a pesar de todo el problema persiste, solamente el " +\
                          "desarrollador(o un hacker ruso) " +\
                          "podrá actualizar el proceso de webscraping en este programa de forma " +\
                          "que el mismo pueda sobrepasar los procesos de detección de robots."
                    print(msg)
                    db.log_add(msg)
                    return

                else:

                    tree = html.fromstring(source_html)

                    # Elemento mayor
                    xpath_str = "//*[@class='single-story-module__headline-link']"
                    try:
                        titulo = remove_special_char(tree.xpath(xpath_str + "/text()")[0])
                    except Exception as e:
                        msg = "ERROR: No se pudo obtener la noticia relacionada al " +\
                              "elemento mayor en Bloomberg." + chr(10)*2 +\
                              "Detalle de la excepción:" + chr(10) + e.__class__.__name__ + " " + str(e) + \
                              chr(10)*2 + "Expresión XPATH= " + chr(10) + xpath_str +\
                              chr(10)*2 + "Si el problema persiste póngase en contcato " +\
                              "con el desarrollador."
                        print(msg)
                        db.log_add(msg.replace(chr(10), ""))
                    else:
                        try:
                            url = "https://www.bloomberg.com/" + tree.xpath(xpath_str + "/@href")[0]
                        except Exception as e:
                            msg = "WARNING: No se pudo obtener URL del " + \
                                  "elemento mayor en Bloomberg." + chr(10) * 2 + \
                                  "Detalle de la excepción:" + chr(10) + e.__class__.__name__ + " " + str(e) + \
                                  chr(10) + "Se asignará la URL por defecto: " +\
                                  self.start_urls[0]
                            print(msg)
                            db.log_add(msg.replace(chr(10), ""))
                            url = self.start_urls[0]

                        if titulo and titulo not in bitacora:
                            self.get_data(browser, titulo, xpath_str, url)
                            try:
                                time.sleep(random.randint(2, 4))
                                browser.execute_script("window.history.go(-1)")
                            except Exception as e:
                                msg = "ERROR: Error posterior a la obtención del elemento mayor en " +\
                                      "Bloomberg." + chr(10)*2 +\
                                      "Detalle de la excepción:" + chr(10) + e.__class__.__name__ + " " + str(e) +\
                                      chr(10)*2 + "Si el problema persiste póngase en contcato " +\
                                      "con el desarrollador."
                                print(msg)
                                db.log_add(msg.replace(chr(10), ""))

                    # Por cada related stories...
                    xpath_str = "//*[@class='single-story-module__related-stories']//div//a"
                    rs = tree.xpath(xpath_str)

                    if not rs:
                        msg = "WARNING: No se encontraron elementos 'related stories' en Bloomberg." + chr(10) +\
                              "XPATH = " + xpath_str
                        print(msg)
                        db.log_add(msg)

                    counter = 1
                    for i in rs:

                        titulo = remove_special_char(i.text)

                        try:
                            url = "https://www.bloomberg.com/" + i.xpath('@href')[0]
                        except Exception as e:
                            msg = "WARNING: No se pudo obtener URL de " + \
                                  "related story en Bloomberg." + chr(10) * 2 + \
                                  "Detalle de la excepción:" + chr(10) + e.__class__.__name__ + " " + str(e) + \
                                  chr(10) + "Se asignará la URL por defecto: " +\
                                  self.start_urls[0]
                            print(msg)
                            db.log_add(msg.replace(chr(10), ""))
                            url = self.start_urls[0]

                        if titulo and titulo not in bitacora:
                            self.get_data(browser, titulo,
                                          "(//*[@class='single-story-module__related-stories']//div)[position()=" +
                                          str(counter) + "]//a", url)
                            try:
                                time.sleep(random.randint(2, 4))
                                browser.execute_script("window.history.go(-1)")
                            except Exception as e:
                                msg = "ERROR: Error posterior a la obtención de related story en " + \
                                      "Bloomberg." + chr(10) * 2 + \
                                      "Detalle de la excepción:" + chr(10) + e.__class__.__name__ + " " + str(e) + \
                                      chr(10) * 2 + "Si el problema persiste póngase en contcato " + \
                                      "con el desarrollador."
                                print(msg)
                                db.log_add(msg.replace(chr(10), ""))
                                break
                        counter += 1

                    # Por cada story package module...
                    xpath_str =\
                        "//section[@class='hub-zone-righty__content']//*[@class='story-package-module__story']//h3//a"
                    spm = tree.xpath(xpath_str)

                    if not spm:
                        msg = "WARNING: No se encontraron elementos 'story package module' en Bloomberg." + chr(10)*2 +\
                              "XPATH = " + xpath_str
                        print(msg)
                        db.log_add(msg)

                    counter = 1
                    for i in spm:

                        titulo = remove_special_char(i.text.replace("  ", ""))

                        try:
                            url = "https://www.bloomberg.com/" + i.xpath('@href')[0]
                        except Exception as e:
                            msg = "WARNING: No se pudo obtener URL de " + \
                                  "story package module en Bloomberg." + chr(10) * 2 + \
                                  "Detalle de la excepción:" + chr(10) + e.__class__.__name__ + " " + str(e) + \
                                  chr(10) + "Se asignará la URL por defecto: " +\
                                  self.start_urls[0]
                            print(msg)
                            db.log_add(msg)
                            url = self.start_urls[0]

                        if titulo and titulo not in bitacora:
                            time.sleep(random.randint(2, 4))
                            self.get_data(browser, titulo,
                                          "(//section[@class='hub-zone-righty__content']" +
                                          "//*[@class='story-package-module__story'])[position()=" +
                                          str(counter) + "]//h3//a", url)
                            try:
                                time.sleep(random.randint(2, 4))
                                browser.execute_script("window.history.go(-1)")
                            except Exception as e:
                                msg = "ERROR: Error posterior a la obtención de story package module en " + \
                                      "Bloomberg." + chr(10) * 2 + \
                                      "Detalle de la excepción:" + chr(10) + e.__class__.__name__ + " " + str(e) + \
                                      chr(10) * 2 + "Si el problema persiste póngase en contcato " + \
                                      "con el desarrollador."
                                print(msg)
                                db.log_add(msg)
                                break
                        counter += 1

                    browser.quit()

                    elapsed_time = time.time() - start_time

                    msg = "Escaneo de '" + self.name + "' finalizado." + chr(10) +\
                          "Tiempo transcurrido: " + scs_in_hhmmss(elapsed_time)

                    print(msg)
                    db.log_add(msg.replace(chr(10), " "))

            except Exception as e:
                msg = "ERROR: Ha ocurrido un error accediendo a la data de '" + self.name + "'." + chr(10)*2 +\
                      "Detalle del error:" + chr(10) + \
                      e.__class__.__name__ + " " + str(e) + chr(10)*2 +\
                      "Verifique que el webdriver no se encuentre desactualizado." + chr(10) + \
                      "Si el problema persiste quizás el proceso webscraping requiera una actualización " +\
                      "debido a nuevos métodos de seguridad implementados en la fuente " +\
                      "de los datos. En ese caso póngase " +\
                      "en contacto con el desarrollador para realizar los ajustes necesarios."
                print(msg)
                db.log_add(msg)

    def get_data(self, browser, titulo, xpath_str, url):

        print("escaneando " + titulo)

        source_html = browser.page_source.encode("ascii", errors="ignore").decode()

        if "<title>Bloomberg - Are you a robot?</title>" in source_html:
            msg = "Bloomberg ha detectado nuestro proceso automático, y por " + \
                  "lo tanto nos ha bloqueado el acceso a la data de '" + titulo + \
                  "'. Quizás esto sea temporal y en el " + \
                  "próximo intento podramos obtener la información." + chr(10) + \
                  "Si a pesar de todo el problema persiste, póngase en contacto " + \
                  "con el desarrollador para actualizar el proceso de webscraping de forma " + \
                  "que el mismo pueda sobrepasar los procesos de detección de robots."
            print(msg)
            db.log_add(msg)
            return

        else:

            try:
                browser.find_element_by_xpath(xpath_str).click()

                source_html = utf_8_compatible(browser.page_source)

                tree = html.fromstring(source_html)

                content = ""

                try:
                    if "body-copy-v2 fence-body" in source_html:
                        content = " ".join(tree.xpath("//div[@class='body-copy-v2 fence-body']//p/text()"))
                    elif "body-copy fence-body" in source_html:
                        content = " ".join(tree.xpath("//div[@class='body-copy fence-body']//p/text()"))
                    else:
                        content = ""
                except Exception as e:
                    msg = "WARNING: Contenido no encontrado en Bloomberg " +\
                          "para '" + titulo + "'." + chr(10)*2 +\
                          "Detalle:" + chr(10) + e.__class__.__name__ + " " + str(e)
                    print(msg)
                    db.log_add(msg)

                if content != "":
                    content = utf_8_compatible(content)
                    myscores = self.scores(titulo, content)

                    if len(myscores) >= MIN_SCORE:

                        try:
                            if "lede-large-image-v2__image" in source_html:
                                img = tree.xpath("//*[@class='lede-large-image-v2__image']/@style")[0] +\
                                      "' width='200' height='150"
                            elif "lazy-img__image" in source_html:
                                img = tree.xpath("//*[@class='lazy-img__image']/@data-native-src")[0] + \
                                      "' width='200' height='150"
                            elif "video-player__container" in source_html:
                                img = tree.xpath("//*[@class='video-player__container']/@data-poster")[0] + \
                                      "' width='200' height='150"
                            elif "video-player__container in-lede fade-large" in source_html:
                                img = tree.xpath(
                                    "//*[@class='video-player__container in-lede fade-large']/@data-poster")[0] + \
                                      "' width='200' height='150"
                            else:
                                img = DEFAULT_IMG

                            img = img.replace("background-image: url('", "").replace("')", "")

                        except Exception as e:
                            msg = "WARNING: Imagen no encontrada en Bloomberg " + \
                                  "para '" + titulo + "'. " + chr(10) + \
                                  "Detalle: " + chr(10) + e.__class__.__name__ + " " + str(e) + \
                                  ". Se utilizará imagen por defecto."
                            print(msg)
                            db.log_add(msg.replace(chr(10), ""))
                            img = DEFAULT_IMG

                        try:
                            summary = ""
                            if "abstract-v2__item-text" in source_html:
                                summary = " ".join(
                                    tree.xpath("//*[@class='abstract-v2__item-text']/text()")).\
                                    replace("  ", "").replace(chr(10), "")
                            elif "lede-text-v2__dek" in source_html:
                                summary = " ".join(
                                    tree.xpath("//div[@class='lede-text-v2__dek']//p/text()")). \
                                    replace("  ", "").replace(chr(10), "")
                            elif "lede-text-only__highlight" in source_html:
                                summary = " ".join(
                                    tree.xpath("//span[@class='lede-text-only__highlight']//p/text()")).\
                                    replace("  ", "").replace(chr(10), "")

                            if len(summary) <= 5:
                                if len(content) > 130:
                                    summary = content[:130] + "..."
                                else:
                                    summary = content

                            summary = summary

                        except Exception as e:
                            msg = "WARNING: Resumen no encontrado en Bloomberg " + \
                                  "para '" + titulo + "'." + chr(10) * 2 + \
                                  "Detalle:" + chr(10) + e.__class__.__name__ + " " + str(e) + chr(10) * 2 + \
                                  "Se utilizará un resumen extraído del contenido."
                            print(msg)
                            db.log_add(msg)

                            if len(content) > 130:
                                summary = content[:130] + "..."
                            else:
                                summary = content

                        report_content.append({"item": titulo,
                                               "score": len(myscores),
                                               "source": self.name,
                                               "source_url": url,
                                               "summary": summary,
                                               "scores": myscores})

                        mail_html.append((
                            chr(10) +
                            """<tr>
                            <td bgcolor='black' style= 'width:150px; height:100px; vertical-align:middle;
                            text-align:center;'>
                            <img src='""" + img + """'>
                            </td>
                            <td class='container'>
                            <div class='news'>&nbsp;""" + titulo + """"</div>
                            <div class='paragraph'>""" + summary + """"</div>
                            <br><div class='source'>Fuente: """ + self.name + """</div></br>
                            <a href='""" + url + """'>
                            <span><img src='""" + LINK_ICON + """' height='15'/>
                            &nbsp; Leer noticia &nbsp;&nbsp;</span>
                            </a>
                            </td>
                            </tr>""", len(myscores)))

                        self.registrar(titulo, "PEND")
                        print("Item validado y almacenado.")
                        db.log_add("Registrado item: '" + titulo +
                                   "' Estado: 'PEND' Score: '" + str(len(myscores)) + "'")

                    else:
                        self.registrar(titulo, "REV")
                        db.log_add("Registrado item: '" + titulo +
                                   "' Estado: 'REV' Score: '" + str(len(myscores)) + "'")
                else:
                    msg = "WARNING: No fue encontrado contenido para '" + titulo + "' en " + \
                          self.name + ". La noticia no se procesará." + chr(10)*2 + \
                          "Es posible que el contenido exista, pero que la expresión " +\
                          "XPath utilizada actualmente está desactualizada respecto a " +\
                          "la estructura HTML de la fuente." + chr(10) +\
                          "Si el problema persiste póngase en contacto con el desarrollador " +\
                          "para realizar los ajustes necesarios en el módulo de webscraping."
                    print(msg)
                    db.log_add(msg)
                    return

            except Exception as e:
                msg = "ERROR: Excepción obteniendo data de Bloomberg: " + e.__class__.__name__ + " " + str(e)
                print(msg)
                db.log_add(msg)

    def scores(self, name, content):
        scores = []
        try:
            claves = self.claves(self.lang)

            for c in claves:
                coincidences = len(re.findall(c, content, re.IGNORECASE))
                if coincidences > 0:
                    scores.append([c, coincidences])

        except Exception as e:
            msg = "ERROR: Error al obtener score para '" + name +\
                  "'." + chr(10) + e.__class__.__name__ + " " + str(e)
            print(msg)
            db.log_add(msg)
            return []
        else:
            if len(scores) >= MIN_SCORE:
                self.poop_txt(self.name.upper(), name, content + chr(10)*2 + "Claves: " + str(scores))

            return scores


# ==============================================================================================================

def remove_special_char(strng):
    new_strng = strng.replace('#', '').replace('%', 'prcnt').replace('*', '').replace('<', '').replace('>', '').\
                replace('¿', '').replace('?', '').replace('!', '').replace('¡', '').\
                replace('|', '-').replace('"', '').replace('Å', '').replace('.', '').replace(chr(92), '').\
                replace('/', '').replace(':', '').replace("'", '').replace(chr(10), '')

    return new_strng


def utf_8_compatible(strng):

    try:
        new_strng = strng.replace("€", "EUR").replace("₡", "CRC").\
            replace("$", "USD").encode("utf-8", errors="ignore").decode()
    except Exception as e:
        msg = "WARNING: No se pudo convertir la string a compatible con UTF-8. "
        new_strng = strng
        db.log_add(msg + e.__class__.__name__ + " " + str(e))
        print(msg + chr(10) + e.__class__.__name__ + " " + str(e))

    return new_strng


def scs_in_hhmmss(secs):
    if secs >= 3600:
        base = secs / 60 / 60
        hours = int(base)
        mins = int((base - hours) * 60)
        scs = int(round((((base - hours) * 60) - mins) * 60, 0))
    else:
        hours = 0
        if secs >= 60:
            base = secs / 60
            mins = int(base)
            scs = int(round((base - mins) * 60, 0))
        else:
            mins = 0
            scs = int(round(secs, 0))

    counter_str = "0" + str(hours) if hours < 10 else str(hours)
    counter_str += ":" + ("0" + str(mins) if mins < 10 else str(mins))
    counter_str += ":" + ("0" + str(scs) if scs < 10 else str(scs))

    return counter_str


def poop_plot(path, scores):

    try:
        keys = []
        values = []

        scores.sort(key=lambda value: -value[1])

        for i in scores:
            keys.append(i[0])
            values.append(i[1])

        plt.figure(figsize=(FIG_WIDTH/100, FIG_HEIGHT/100))
        plt.bar(range(len(keys)), values, align="center")
        plt.xticks(range(len(keys)), keys, rotation='vertical')
        plt.ylabel("Frecuencia")
        plt.xlabel("Claves")
        # plt.title("Sentimiento")
        plt.savefig(path, bbox_inches='tight')
        plt.close()
    except Exception as e:
        msg = "WARNING: No fue posible generar gráfico. Póngase en contacto con el desarrollador."
        db.log_add(msg + e.__class__.__name__ + " " + str(e))
        print(msg + chr(10) + e.__class__.__name__ + " " + str(e))


def timestr():
    try:
        timenow = db.datetime.now()
        timenow_str =\
            str(timenow.day) + "-" + \
            str(timenow.month) + "-" + \
            str(timenow.year) + "_"

        hh = str(timenow.hour)
        mm = str(timenow.minute)

        if len(hh) < 2:
            hh = "0" + hh

        if len(mm) < 2:
            mm = "0" + mm

        timenow_str += hh + "hh" + mm + "mm"

        return timenow_str

    except Exception as e:
        msg = "Módulo Webscraping. No fue posible generar string de tiempo. Póngase en contacto con el desarrollador."
        db.log_add(msg + e.__class__.__name__ + " " + str(e))
        print(msg + chr(10) + e.__class__.__name__ + " " + str(e))
        return ""


def store_report(report_fullname):
    try:
        path = db.main_app_path + r"\Analysis"
        db.os.makedirs(path) if not db.os.path.exists(path) else None
        shutil.copy(report_fullname, path)
        print("Reporte de análisis almacenado en '" + path + "'")
        db.log_add("Reporte de análisis almacenado en '" + path + "'")
    except Exception as e:
        msg = "Módulo Webscraping. No fue posible almacenar reporte análsisis de sentimiento en " +\
              "la carpeta Analysis. Póngase en contacto con el desarrollador."
        db.log_add(msg + e.__class__.__name__ + " " + str(e))
        print(msg + chr(10) + e.__class__.__name__ + " " + str(e))


def build_report():
    report_html_str = ""
    if report_content:

        sorted_report_content = sorted(report_content, key=lambda k: k["score"], reverse=True)

        plots_folder = db.my_path + r"\PLOTS"

        db.os.makedirs(plots_folder) if not db.os.path.exists(plots_folder) else None

        nplot = 0

        for i in sorted_report_content:
            nplot += 1
            plotpath = plots_folder + r"\PLOT_" + str(nplot) + ".png"
            poop_plot(plotpath, i.get("scores", None))

            report_html_str += r"""
<div style="page-break-after:always">
    <article>
        <header>
            <h1>""" + i.get("item", None) + """</h1>
            <p><font size='4'><i>Fuente: """ + i.get("source", None) + """</i></font></p>
        <p><font color='blue' size='4'><a href='""" + i.get("source_url", None) + """'>
        Leer noticia</a></font></p>
        </header>
        <p><font size='4'>""" + i.get("summary", None) + """</font></p>
        <img src='""" + \
                plotpath + \
                """' align='middle'>
    </article>""" + FOOTER_HTML

        if report_html_str:

            report_html_str = HEAD_HTML + chr(10) + report_html_str

            try:
                analysis_path = db.my_path + r"\Analysis"
                shutil.rmtree(analysis_path) if db.os.path.exists(analysis_path) else None
                db.os.makedirs(analysis_path)
                nombre_archivo = r"\Análisis_de_sentimiento_" + timestr() + ".pdf"
                report_fullname = analysis_path + nombre_archivo
                report = open(report_fullname, "w+b")
                pisa_status = pisa.CreatePDF(report_html_str, dest=report)
                report.close()
                print("Archivo '" + nombre_archivo + "' creado.")
                db.log_add("Archivo '" + nombre_archivo + "' creado.")
            except Exception as e:
                msg = "WARNING: No fue posible crear reporte análisis de sentimiento. " + \
                      "Reinicie la herramienta e inténtelo de nuevo. " +\
                      "Si el problema persisite póngase en contacto con el desarrollador."
                db.log_add(msg + e.__class__.__name__ + " " + str(e))
                print(msg + chr(10) + e.__class__.__name__ + " " + str(e))
                report_fullname = ""

            store_report(report_fullname) if report_fullname else None

        shutil.rmtree(plots_folder) if db.os.path.exists(plots_folder) else None


def htmlbody_export():
    if mail_html:
        mail_html.sort(key=lambda notica: -notica[1])
        file = open(db.my_path + r"\htmlbody.txt", "w")
        file.write(chr(10).join([i[0] for i in mail_html]))
        file.close()
        print("Cuerpo html generado")
    else:
        print("No se generó ningún cuerpo html")


def clear_pend():
    db.db_main("DELETE FROM BITACORA WHERE ESTADO = 'PEND'")


def webscraping():
    db.log_add("INICIANDO WEBSCRAPING")
    process = CrawlerProcess({
        'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)',
        'DOWNLOAD_HANDLERS': {'s3': None},
        'LOG_ENABLED': False
    })

    db.log_add("Limpiando items pendientes . . .")
    print("Limpiando pendientes . . .")
    # RECORDAR: habilitar borrado de pend
    clear_pend()

    # ACTUALIZAR
    # Agregar aquí los crawlers
    process.crawl(ElFinanciero)
    process.crawl(Bloomberg)
    process.crawl(LaRepublica)
    process.crawl(CNN)

    try:

        db.log_add("Crawler iniciado.")
        print("Crawler iniciado . . .")
        process.start()

        db.log_add("Crawler finalizado.")
        print("Crawler finalizado . . .")
        htmlbody_export()
        print("Construyendo reporte . . .")
        build_report()

        db.log_add("Webscraping finalizado con éxito")
        print("Webscraping finalizado con éxito")

    except Exception as e:
        print("Excepción modulo Webscraping: " + chr(10) + e.__class__.__name__ + " " + str(e))


webscraping()
