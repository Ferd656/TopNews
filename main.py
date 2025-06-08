# -*- coding: utf-8 -*-
import base64
import shutil
import getpass
import smtplib
import subprocess
import database as db
import mailnews as mn
from kivy import clock
from kivy.app import App
from kivy.clock import Clock
from re import match, search
from kivy.config import Config
from KivyListbox import Listbox
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.switch import Switch
from kivy.uix.button import Button
from googletrans import Translator
from urllib.request import urlopen
from kivy.graphics import Rectangle
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition, FadeTransition

Config.set("graphics", "resizable", False)
Config.set("graphics", "width", "400")
Config.set("graphics", "height", "380")

from kivy.core.window import Window
Window.clearcolor = (0.095, 0.095, 0.095, 1)

from kivy.uix.actionbar import ActionBar
from kivy.uix.actionbar import ActionView
from kivy.uix.actionbar import ActionGroup
from kivy.uix.actionbar import ActionButton
from kivy.uix.actionbar import ActionPrevious

db.db_main("DELETE FROM PATH")

# Modificar mediante el fichero MY_INFO.txt
my_name = "<TopNews/>"
my_version = ""

srvr = None

platform = "Outlook"

abc = ""

my_info_path = db.rpath() + r"\MY_INFO.txt"

if db.os.path.exists(my_info_path):
    myinfofile = open(my_info_path, "r")
    my_name = myinfofile.readline().split("|")[1].replace(chr(10), "")
    my_version = myinfofile.readline().split("|")[1].replace(chr(10), "")


def abrir_guia_de_uso(abrir=False):
    file = {"path": db.rpath() + r"\GUIA_DE_USO.pdf",
            "destination":  db.mypath + r"\GUIA_DE_USO.pdf"}

    try:
        if file["path"] != file["destination"]:
            if db.os.path.exists(file["destination"]):
                db.os.remove(file["destination"])

            shutil.copy(file["path"], db.mypath)

    except Exception as e:
        msg = "No fue posible obtener la guía de uso. " + chr(10) +\
              "Verifique sus permisos sobre el directorio que se está utilizando. " + chr(10)*2 +\
              "Visite https://www.linkedin.com/in/ferdinandfeoli para ponerse en contacto con " +\
              "el Desarrollador. " + chr(10)*2 + str(e)
        db.log_add(msg.replace(chr(10), ""))
        db.MessageBox(None, msg, db.ICON_WARN)

    else:
        try:
            if abrir:
                subprocess.Popen(file["destination"], shell=True)
        except Exception as e:
            msg = "No fue posible abrir " + file["destination"] + ". " + chr(10) * 2 + str(e)
            db.log_add(msg.replace(chr(10), ""))
            db.MessageBox(None, msg, db.ICON_WARN)


abrir_guia_de_uso()


class MainApp(App):
    title = my_name + " (" + my_version + ")" if my_version else my_name
    App.icon = db.rpath() + "/Media/icon.png"

    @staticmethod
    def build():
        return MultiPage()

    @staticmethod
    def on_stop():
        db.log_add("CERRANDO APLICACIÓN")


class MultiPage(ScreenManager):
    def __init__(self):
        super().__init__()
        self.size_hint = (None, None)
        self.size = (400, 380)

        self.Selec = SelecScreen(self)
        self.Login = LoginScreen(self)
        self.Inicio = AppScreen(self)

        wid = Screen(name="selec")
        wid.add_widget(self.Selec)
        self.add_widget(wid)

        wid = Screen(name="login")
        wid.add_widget(self.Login)
        self.add_widget(wid)

        wid = Screen(name="inicio")
        wid.add_widget(self.Inicio)
        self.add_widget(wid)

        self.transition = FadeTransition()

        self.current = "selec"

    def goto_inicio(self, *args):

        # ws.class_init()
        # - - - - - - - class_init - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        # ACTUALIZAR
        lst = ["El Financiero", "Bloomberg", "La Republica", "CNN"]

        db.db_main("DELETE FROM FUENTES WHERE NOMBRE NOT IN " + str(lst).replace("[", "(").replace("]", ")"))

        for i in lst:

            db.db_main("INSERT INTO FUENTES (NOMBRE, ACTIVO) " +
                       "SELECT '" + i + "', 0 " +
                       "WHERE NOT EXISTS(" +
                       "SELECT NOMBRE FROM FUENTES WHERE NOMBRE = '" + i + "')")

        # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

        fuentes = db.db_main("SELECT NOMBRE, ACTIVO FROM FUENTES")

        tfc = ToggleFieldContainer(self.Inicio.content, fuentes,
                                   pos_hint={"x": -0.1, "y": 0.22},
                                   size_hint=(1, None),
                                   size=(300, 240))

        self.Inicio.content.Pagina1.add_widget(tfc)

        self.transition = FadeTransition()
        self.current = 'inicio'

    def goto_login(self, *args):
        def_user = db.db_main("SELECT * FROM CONFIG WHERE DESCRIPCION = 'AUT'")[0][1]
        self.Login.usuario.text = def_user if def_user else getpass.getuser()
        self.transition = FadeTransition()
        self.current = 'login'

    def goto_selec(self, *args):
        global platform
        global abc
        global srvr

        self.Inicio.menu.floatspace.timer.flag = False

        if self.Login.server_opened:
            abc = ""
            print("Cerrando servidor Office 365 . . .")
            db.log_add("Cerrando servidor Office 365 . . .")
            try:
                srvr.quit()
                self.Login.server_opened = False
                print("Servidor Office 365 cerrado.")
                db.log_add("Servidor Office 365 cerrado.")
            except Exception as e:
                print(e.__class__.__name__ + chr(10) + str(e))
                db.log_add("Excepción al cerrar servidor Office 365: " +
                           e.__class__.__name__ + " " + str(e))
        platform = "Outlook"
        self.transition = SlideTransition(direction="right")
        self.current = 'selec'


class SelecScreen(BoxLayout):
    def __init__(self, mainwid):
        super().__init__()
        self.mainwid = mainwid
        self.orientation = "vertical"
        self.add_widget(SpecialButton(text="Office365",
                                      img_source=db.rpath() + "/Media/Office365.png",
                                      img_size=(120, 120),
                                      font_size=18,
                                      on_press=lambda *args: self.platform_selection("Office365")))

        self.add_widget(SpecialButton(text="Outlook",
                                      img_source=db.rpath() + "/Media/Outlook.png",
                                      img_size=(120, 120),
                                      font_size=18,
                                      on_press=lambda *args: self.platform_selection("Outlook")))

    def platform_selection(self, selection):
        global platform
        if selection == "Office365":
            platform = "Office365"
            self.mainwid.goto_login()
        else:
            platform = "Outlook"
            self.mainwid.goto_inicio()

        print("Plataforma de mensajería seleccionada: " + platform)


# ============= Login ==================================================================================================


class LoginScreen(FloatLayout):
    def __init__(self, mainwid):
        super().__init__()

        self.validated = False
        self.mainwid = mainwid
        self.size_hint = (None, None)
        self.size = (400, 380)
        self.orientation = "vertical"
        self.spacing = 10
        self.intentos = 3
        self.def_user = ""
        self.server_opened = False
        self.window = Window
        self.window.bind(on_key_down=self._on_keyboard_down)

        self.canvas.add(
            Rectangle(pos=self.pos,
                      size=self.size,
                      source=db.rpath() + "/Media/Background.png"))

        self.notification_label = Label(text="", bold=True, halign='center', width=380,
                                        pos_hint={"center_y": 0.38, "center_x": 0.5})

        self.notification_label.bind(
            width=lambda *x:
            self.notification_label.setter('text_size')
            (self.notification_label,
             (self.notification_label.width, None)))

        self.clave = TextInput(size_hint=(None, None), font_size=12,
                               height=30, width=200, password=True,
                               pos_hint={"center_y": 0.55, "center_x": 0.5},
                               multiline=False, write_tab=False,
                               on_touch_down=self.set_button_to_normal,
                               on_text_validate=self.focusboton)

        self.usuario = TextInput(font_size=12, size_hint=(None, None),
                                 height=30, width=200,
                                 pos_hint={"center_y": 0.8, "center_x": 0.5},
                                 multiline=False, write_tab=False,
                                 on_touch_down=self.set_button_to_normal,
                                 on_text_validate=self.focusclave)

        self.add_widget(Label(text="Usuario",
                              pos_hint={"center_y": 0.87, "center_x": 0.5}))
        self.add_widget(Label(text="Contraseña",
                              pos_hint={"center_y": 0.62, "center_x": 0.5}))

        self.validbtn = Button(text="Ingresar", size_hint=(None, None),
                               height=30, width=100,
                               pos_hint={"center_y": 0.18, "center_x": 0.3},
                               on_press=self.update_label)

        self.add_widget(Button(text="Volver", size_hint=(None, None),
                               height=30, width=100,
                               pos_hint={"center_y": 0.18, "center_x": 0.7},
                               on_press=self.mainwid.goto_selec))

        self.add_widget(self.notification_label)
        self.add_widget(self.usuario)
        self.add_widget(self.clave)
        self.add_widget(self.validbtn)

        self.focusclave()

    @staticmethod
    def salir(*args):
        App.get_running_app().stop()

    def _on_keyboard_down(self, instance, keyboard, keycode, text, modifiers):
        if not self.validated and self.validbtn.background_normal == '' and keycode == 40:  # 40 - Enter key pressed
            self.update_label()

    def set_button_to_normal(self, *args):
        self.validbtn.background_normal = 'atlas://data/images/defaulttheme/button'
        self.validbtn.background_color = [1, 1, 1, 1]

    def focusclave(self, *args):
        self.clave.focus = True

    def focusboton(self, *args):
        self.validbtn.background_normal = ''
        self.validbtn.background_color = [0, 0.66, 1, 1]
        self.validbtn.focus = True

    def update_label(self, *args):
        self.notification_label.color = (0.8, 0.8, 0, 1)
        self.notification_label.font_size = 16
        self.notification_label.text = "Validando . . ."
        print("Validando login Office365 . . .")
        db.log_add("Validando login Office365 . . .")

        clock.Clock.schedule_once(self.validar, 0.5)

    def validar(self, *args):
        global srvr
        global abc
        self.server_opened = False

        # Validar conexión a internet
        try:
            stri = "https://www.google.com"
            data = urlopen(stri)
        except Exception as e:
            self.notification_label.color = (1, 0.2, 0.2, 1)
            self.notification_label.font_size = 12
            self.notification_label.text = "Sin conexión a internet"
            self.validated = False
            print("Error en conexión a internet: " + e.__class__.__name__ + " " + str(e))
            db.log_add("Error en conexión a internet: " + e.__class__.__name__ + " " + str(e))
            return False

        # Validar acceso cuenta office365
        try:
            srvr = smtplib.SMTP(host="smtp.office365.com", port=587)
            print("Servidor Office365 abierto.")
            db.log_add("Servidor Office365 abierto.")
            self.server_opened = True
            # srvr.ehlo()
            srvr.starttls()
            srvr.ehlo()
            srvr.login(self.usuario.text, self.clave.text)
            # self.usr = self.usuario.text
            abc = base64.b64encode(self.clave.text.encode("utf-8"))
            self.clave.text = ""
            self.notification_label.text = ""
            self.set_button_to_normal()
            self.intentos = 3
            self.validated = True
        except smtplib.SMTPAuthenticationError as ath_err:
            self.validated = False
            self.intentos -= 1
            self.notification_label.color = (1, 0.2, 0.2, 1)
            self.notification_label.font_size = 12
            self.notification_label.text =\
                str(ath_err) + chr(10) +\
                "Autenticación Office365 no fue exitosa." + chr(10) +\
                "Verifique credenciales y conexión a internet." + chr(10)*2 +\
                "Intentos restantes = " + str(self.intentos)

            print(str(ath_err))
            db.log_add(str(ath_err))
        except smtplib.SMTPException as smtp_err:
            self.validated = False
            self.notification_label.color = (1, 0.2, 0.2, 1)
            self.notification_label.font_size = 12
            self.notification_label.text = "Excepción en smtp:" + chr(10) + str(smtp_err)
            print("Excepción en smtp:" + str(smtp_err))
            db.log_add("Excepción en smtp:" + str(smtp_err))
        except Exception as e:
            self.validated = False
            self.notification_label.color = (1, 0.2, 0.2, 1)
            self.notification_label.font_size = 12
            self.notification_label.text = "Excepción:" + chr(10) + str(e)
            print("Excepción: " + e.__class__.__name__ + " " + str(e))
            db.log_add("Excepción: " + e.__class__.__name__ + " " + str(e))

        if not self.validated:

            if self.server_opened:
                abc = ""
                print("Cerrando servidor Office365.")
                db.log_add("Cerrando servidor Office365.")
                try:
                    srvr.quit()
                    self.server_opened = False
                    print("Servidor Office365 cerrado")
                    db.log_add("Servidor Office365 cerrado.")
                except Exception as e:
                    print(e.__class__.__name__ + " " + str(e))
                    db.log_add(e.__class__.__name__ + " " + str(e))

            if self.intentos <= 0:
                self.notification_label.text = ""
                self.set_button_to_normal()
                self.mainwid.goto_selec()

        elif self.validated:
            self.notification_label.text = ""
            self.set_button_to_normal()
            self.validated = False

            if self.usuario.text != self.def_user:
                db.db_main("UPDATE CONFIG SET VALOR = '" +
                           self.usuario.text + "' WHERE DESCRIPCION = 'AUT'")

            self.mainwid.goto_inicio()

# ======================================================================================================================

# ============= GUI ====================================================================================================


class AppScreen(BoxLayout):
    def __init__(self, mainwid):
        super().__init__()

        self.mainwid = mainwid
        self.orientation = 'horizontal'
        self.content = ContentScreen(self)
        self.menu = Menu(self)

        self.add_widget(self.menu)
        self.add_widget(self.content)

    def validate(self, display=False):
        # fuentes
        if db.db_main("SELECT COUNT(*) FROM FUENTES WHERE ACTIVO = 1")[0][0] == 0:
            self.displaywarning(display)
            return False
        # claves
        if db.db_main("SELECT COUNT(*) FROM CLAVES")[0][0] == 0:
            self.displaywarning(display)
            return False
        # destinatarios
        if db.db_main("SELECT COUNT(*) FROM DESTINATARIOS")[0][0] == 0:
            self.displaywarning(display)
            return False

        return True

    def displaywarning(self, display):
        self.menu.floatspace.button.default_status()
        if display:
            db.MessageBox(None,
                          "No se ha podido iniciar el proceso porque falta alguno o varios de los " +
                          "siguientes elementos:" + chr(10) * 2 +
                          "  - Al menos una fuente de información activa." + chr(10) +
                          "  - Al menos una palabra clave registrada." + chr(10) +
                          "  - Al menos un destinatario registrado." + chr(10) * 2 +
                          "Realice las correcciones necesarias y reintente.",
                          'Falta input',
                          db.ICON_WARN)


class Menu(GridLayout):
    def __init__(self, mainwid):
        super().__init__()

        self.mainwid = mainwid
        self.size_hint_x = .45
        self.rows = 5
        self.cols = 1

        self.floatspace = FloatSpace(self.mainwid)

        self.add_widget(SpecialButton(text="Fuentes de información",
                                      img_source=db.rpath() + "/Media/sources.png",
                                      img_size=(40, 40),
                                      font_size=11,
                                      on_press=self.mainwid.content.goto_p1))
        self.add_widget(SpecialButton(text="Palabras clave",
                                      img_source=db.rpath() + "/Media/keywords.png",
                                      img_size=(40, 40),
                                      font_size=11,
                                      on_press=self.mainwid.content.goto_p2))
        self.add_widget(SpecialButton(text="Destinatarios",
                                      img_source=db.rpath() + "/Media/recipients.png",
                                      img_size=(40, 40),
                                      font_size=11,
                                      on_press=self.mainwid.content.goto_p3))
        self.add_widget(SpecialButton(text="Principal",
                                      img_source=db.rpath() + "/Media/config.png",
                                      img_size=(40, 40),
                                      font_size=11,
                                      on_press=self.mainwid.content.goto_p4))
        self.add_widget(self.floatspace)


class SpecialButton(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__()

        self.orientation = 'vertical'

        if "text" in kwargs:
            self.text = kwargs["text"]
        else:
            self.text = ""

        if "font_size" in kwargs:
            self.font_size = kwargs["font_size"]
        else:
            self.font_size = 12

        if "on_press" in kwargs:
            self.add_widget(Button(pos_hint={"center_y": 0.5, "center_x": 0.5},
                                   on_press=kwargs["on_press"]))
        else:
            self.add_widget(Button(pos_hint={"center_y": 0.5, "center_x": 0.5}))

        self.add_widget(Label(text=self.text,
                              font_size=self.font_size,
                              pos_hint={"center_y": 0.9, "center_x": 0.5}))

        if "img_source" in kwargs:
            self.img_source = kwargs["img_source"]
            if "img_size" in kwargs:
                self.img_size = kwargs["img_size"]
                self.add_widget(Image(source=self.img_source,
                                      size_hint=(None, None),
                                      pos_hint={"center_y": 0.5, "center_x": 0.5},
                                      size=self.img_size))
            else:
                self.add_widget(Image(source=self.img_source))


class FloatSpace(FloatLayout):
    def __init__(self, mainwid):
        super().__init__()

        self.mainwid = mainwid

        self.timer = CountDown(self, size_hint=(None, None),
                               pos_hint={"center_y": 0.3, "center_x": 0.5},
                               font_size=12)
        self.button = BtRun(self)

        self.add_widget(self.timer)
        self.add_widget(self.button)


class BtRun(Button):
    def __init__(self, mainwid):
        super().__init__()

        self.mainwid = mainwid

        self.background_normal = ""
        self.pos_hint = {'center_y': 0.7, 'center_x': 0.5}
        self.size_hint = (0.7, 0.4)
        self.font_size = 12

        self.default_status()

        self.on_press = self.action_button

        self.text = ""
        self.background_color = (0.0, 0.0, 0.0, 0.0)

    def default_status(self):
        self.text = "Detenido"
        self.action()
        self.background_color = (1.0, 0.0, 0.0, 1.0)

    def action_button(self):
        if not self.mainwid.mainwid.validate(True):
            pass
        elif self.text == "Detenido":
            self.text = "En ejecución"
            self.background_color = (0.0, 0.4, 0.0, 1.0)
            self.action()
        else:
            self.text = "Detenido"
            self.background_color = (1.0, 0.0, 0.0, 1.0)
            self.action()

    def action(self):
        if self.text == "En ejecución":
            # RECORDAR TIEMPO EN MINUTOS = lapso*60
            lapso = int(db.db_main("SELECT VALOR FROM CONFIG WHERE DESCRIPCION = 'LAPSO'")[0][0])*60
            self.mainwid.timer.flag = True
            self.mainwid.timer.countdown(lapso, 0.8 / lapso)
        else:
            self.mainwid.timer.flag = False


class ContentScreen(ScreenManager):
    def __init__(self, mainpage):
        super().__init__()

        self.mainwid = mainpage

        self.Pagina1 = Pagina1(self)
        self.Pagina2 = PaginaConLista(self, "CLAVES", "Palabras clave")
        self.Pagina3 = PaginaConLista(self, "DESTINATARIOS", "Destinatarios")
        self.Pagina4 = PaginaPrincipal(self, "Principal")

        wid = Screen(name="p1")
        wid.add_widget(self.Pagina1)
        self.add_widget(wid)

        wid = Screen(name="p2")
        wid.add_widget(self.Pagina2)
        self.add_widget(wid)

        wid = Screen(name="p3")
        wid.add_widget(self.Pagina3)
        self.add_widget(wid)

        wid = Screen(name="p4")
        wid.add_widget(self.Pagina4)
        self.add_widget(wid)

        self.InputScreen = InputScreen(self, self.current)

        self.input_screen = Screen(name="i_s")
        self.input_screen.add_widget(self.InputScreen)
        self.add_widget(self.input_screen)

        self.transition = SlideTransition(direction="left")

        self.current = 'p4'

    def goto_p1(self, *args):
        self.current = "p1"

    def goto_p2(self, *args):
        self.transition = SlideTransition(direction="left")
        self.current = 'p2'

    def goto_p3(self, *args):
        self.transition = SlideTransition(direction="left")
        self.current = 'p3'

    def goto_p4(self, *args):
        self.transition = SlideTransition(direction="left")
        self.current = 'p4'

    def goto_i_s(self, tablename, *args):
        self.remove_widget(self.input_screen)
        self.InputScreen = InputScreen(self, tablename)
        self.input_screen = Screen(name="i_s")
        self.input_screen.add_widget(self.InputScreen)
        self.add_widget(self.input_screen)
        self.transition = FadeTransition()
        self.current = "i_s"


class Pagina(FloatLayout):
    def __init__(self):
        super().__init__()

        self.canvas.before.add(
            Rectangle(size=(276, 380),
                      source=db.rpath() + "/Media/Background.png"))


class Pagina1(Pagina):
    def __init__(self, mainwid):
        super().__init__()

        self.mainwid = mainwid

        self.add_widget(Label(text="Fuentes de infromación",
                              size_hint=(1, None),
                              font_size=16,
                              bold=True,
                              color=(0.7, 0.7, 1, 1),
                              pos_hint={"x": 0, "y": 0.815}))


class ToggleFieldContainer(ScrollView):
    def __init__(self, mainwid, data, **kwargs):
        super().__init__(**kwargs)

        self.mainwid = mainwid
        self.data = data

        self.layout = GridLayout(cols=1, spacing=10, size_hint_y=None, size_hint_x=None)
        self.layout.bind(minimum_height=self.layout.setter('height'))

        for i in self.data:
            field = ToggleField(self.mainwid, i[0], default=i[1] == 1, size_hint_y=None, height=40)
            self.layout.add_widget(field)

        self.add_widget(self.layout)


class ToggleField(BoxLayout):
    def __init__(self, mainwid, text, default, font_size=13, **kwargs):
        super().__init__(**kwargs)
        self.mainwid = mainwid

        self.orientation = "horizontal"

        self.label = Label(text=text,
                           font_size=font_size,
                           size_hint=(None, None),
                           width=200,
                           height=self.height)

        self.add_widget(self.label)

        self.switch = Switch(active=default,
                             size_hint=(None, None),
                             width=60,
                             height=self.height)

        self.add_widget(self.switch)

        self.switch.bind(active=self.switch_toggle)

    def switch_toggle(self, switchobject, switchvalue):
        db.db_main("UPDATE FUENTES SET ACTIVO = " +
                   str(1 if switchvalue else 0) +
                   " WHERE NOMBRE = '" + self.label.text + "'")
        self.mainwid.mainwid.validate()


class PaginaConLista(Pagina):
    def __init__(self, mainwid, tablareferencia, encabezado):
        super().__init__()

        self.mainwid = mainwid
        self.tablareferencia = tablareferencia
        self.listbox = None
        self.add_widget(Label(text=encabezado,
                              size_hint=(1, None),
                              font_size=16,
                              bold=True,
                              color=(0.7, 0.7, 1, 1),
                              pos_hint={"x": 0, "y": 0.815}))

        self.setlistbox()
        self.add_widget(self.listbox) if self.listbox else None

    def setlistbox(self):
        data = []
        datas = db.return_elements(self.tablareferencia)
        for i in datas:
            data.append(i[0])

        if not self.listbox:
            self.listbox = ListboxContainer(self, data=data,
                                            pos_hint={"x": 0.1, "y": 0.25},
                                            size_hint=(None, None), size=(440, 230))

        else:
            self.listbox.clear_widgets()
            self.listbox.__init__(self, data=data,
                                  pos_hint={"x": 0.1, "y": 0.25},
                                  size_hint=(None, None), size=(440, 230))

    def add_function(self):
        self.mainwid.goto_i_s(self.tablareferencia)

    def del_function(self):
        db.delete_element(self.tablareferencia, self.listbox.listbox.usrselection)
        db.clear_binnacle() if self.tablareferencia == "CLAVES" else None
        self.setlistbox()
        self.mainwid.mainwid.validate()


class ListboxContainer(BoxLayout):
    def __init__(self, mainwid, data, **kwargs):
        super().__init__(**kwargs)

        self.mainwid = mainwid
        self.orientation = "horizontal"
        self.listbox = Listbox(self, data=data,
                               size_hint=(1, 1))
        self.spacing = 4

        self.add_widget(self.listbox)
        grid = GridLayout(rows=3, cols=1)

        self.addbutton = SpecialButton2(self, "add", size_hint=(None, None), size=(20, 30))
        grid.add_widget(self.addbutton)

        self.delbutton = SpecialButton2(self, "del", size_hint=(None, None), size=(20, 30))
        grid.add_widget(self.delbutton)

        grid.add_widget(BoxLayout(size_hint=(None, None)))
        self.add_widget(grid)


# noinspection PyAttributeOutsideInit
class SpecialButton2(Image):
    def __init__(self, mainwid, action, **kwargs):
        super().__init__(**kwargs)

        self.mainwid = mainwid
        self.action = action
        self.ishidden = True

        if action == "del":
            self.source = db.rpath() + "/Media/del.png"
            self.hidden()
        else:
            self.source = db.rpath() + "/Media/add.png"

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            if self.action == "del":
                self.mainwid.mainwid.del_function()
            else:
                self.mainwid.mainwid.add_function()

    def hidden(self, dohide=True):
        if hasattr(self, 'saved_attrs'):
            if not dohide:
                self.height, self.size_hint_y, self.opacity, self.disabled = self.saved_attrs
                del self.saved_attrs
                self.ishidden = False
        elif dohide:
            self.saved_attrs = self.height, self.size_hint_y, self.opacity, self.disabled
            self.height, self.size_hint_y, self.opacity, self.disabled = 0, None, 0, True
            self.ishidden = True


# noinspection RegExpRedundantEscape
class InputScreen(Pagina):
    def __init__(self, mainwid, tablename):
        super().__init__()

        self.mainwid = mainwid
        self.tablename = tablename
        self.textinput = MyTextInput(size_hint=(None, None), size=(250, 160),
                                     font_size=12,
                                     foreground_color=(0.4, 0.4, 0.4, 1),
                                     pos_hint={"x": 0.05, "y": 0.40})
        self.add_widget(self.textinput)
        self.add_widget(Button(text="Agregar", on_press=self.agregar,
                               size_hint=(None, None),
                               size=(120, 30),
                               pos_hint={"x": 0.1, "y": 0.29}))
        self.add_widget(Button(text="Cancelar", on_press=self.devolverse,
                               size_hint=(None, None),
                               size=(100, 30),
                               pos_hint={"x": 0.59, "y": 0.29}))

    def agregar(self, *args):
        no_agregados = []
        no_traducidos = []

        if self.textinput.text == "" or \
                self.textinput.foreground_color == [0.4, 0.4, 0.4, 1] or \
                not search("[a-zA-Z]", self.textinput.text):
            db.MessageBox(None, "Introduzca un texto en el campo", "Agregar valores", db.ICON_WARN)
        else:
            items = self.textinput.text.replace(",", "").split(";")

            if self.tablename == "CLAVES":
                for item in items:

                    item = item.lower().replace(",", "")

                    if len(item) > 40 or len(item) < 3:
                        no_agregados.append(item)
                    else:
                        if len(item) > 1 and item[0] == "#":
                            db.add_element(
                                self.tablename,
                                item.upper().replace("#", "") +
                                "','" +
                                item.upper().replace("#", ""))
                            db.clear_binnacle()
                        else:
                            try:
                                print(Translator().detect(item))
                                db.log_add("MÓDULO DE TRADUCCIÓN: Palabra='" +
                                           item.upper() +
                                           "' Resultado= " +
                                           str(Translator().detect(item)))
                                lang = Translator().detect(item).lang
                            except Exception as e:
                                print("Módulo de traducción: " + e.__class__.__name__ + " " + str(e))
                                db.log_add("Módulo de traducción: " + e.__class__.__name__ + " " + str(e))
                                no_traducidos.append(item)
                                lang = ""

                            if lang == "en":
                                db.add_element(
                                    self.tablename,
                                    Translator().translate(text=item, dest='es').text.upper().replace(",", "") +
                                    "','" +
                                    item.upper())
                                db.clear_binnacle()
                            elif lang == "es":
                                db.add_element(
                                    self.tablename,
                                    item.upper() +
                                    "','" +
                                    Translator().translate(text=item, dest='en').text.upper().replace(",", ""))
                                db.clear_binnacle()
                            else:
                                db.add_element(
                                    self.tablename,
                                    item.upper() +
                                    "','" +
                                    item.upper())
                                db.clear_binnacle()

                self.mainwid.Pagina2.setlistbox()

            elif self.tablename == "DESTINATARIOS":
                for item in items:
                    if len(item) <= 40 and \
                            (match(r"^[A-Za-z0-9\.\+_-]+@[A-Za-z0-9\._-]+\.[a-zA-Z]*$", item) or
                             (len(item) > 1 and item[0] == "#")):

                        db.add_element(self.tablename, item)
                    else:
                        no_agregados.append(item)

                self.mainwid.Pagina3.setlistbox()

            if no_agregados:
                warning_msg = "Los siguientes elementos no fueron agregados:" + chr(10) * 2
                for i in no_agregados:
                    warning_msg += "  - " + i + chr(10)
                warning_msg +=\
                    chr(10) +\
                    "Esto se debe a alguna(s) de las posibles opciones:" + chr(10)*2 + \
                    "  - Se excede el límite de 40 caracteres." + chr(10) + \
                    "  - Ya existe el mismo ítem previamente registrado." + chr(10) + \
                    "  - El ítem está vacío." + chr(10) + \
                    "  - Para el caso de los destinatarios, el item no parece ser una dirección e-mail válida."

                db.log_add(warning_msg)
                db.MessageBox(None, warning_msg, 'Advertencia', db.ICON_WARN)

            if no_traducidos:
                warning_msg = "Los siguientes elementos no fueron traducidos al inglés:" + chr(10) * 2
                for i in no_traducidos:
                    warning_msg += "  - " + i + chr(10)
                warning_msg +=\
                    chr(10) +\
                    "Esto se debe a alguna(s) de las posibles opciones:" + chr(10)*2 + \
                    "  - Se perdió la conexión a internet." + chr(10) + \
                    "  - Alguna configuración de red está impidiendo la conexión con el servicio Google Traductor." +\
                    chr(10)*2 + \
                    "Una vez realizados los ajustes correspondientes puede eliminar los items y volver a " +\
                    "agregarlos para incluír su traducción al inglés."

                db.log_add(warning_msg)
                db.MessageBox(None, warning_msg, 'Advertencia', db.ICON_WARN)

            self.devolverse()

    def devolverse(self, *args):
        if self.tablename == "CLAVES":
            self.mainwid.goto_p2()
        else:
            self.mainwid.goto_p3()


class MyTextInput(TextInput):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.defaultext = "Digite en este espacio el elemento que desea agregar." + \
                          "También puede añadir una lista de elementos separándolos con " + \
                          "punto y coma(;)." + chr(10) * 2 + "Ejemplo:" + chr(10) + \
                          "Elemento1;Elemento2;Elemento3;Elemento4;Elemento5"
        self.text = self.defaultext

        self.foreground_color = (0, 0, 0, 0)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos) and self.text == self.defaultext:
            self.text = ""
            self.foreground_color = (0, 0, 0, 1)
            return True
        return super(MyTextInput, self).on_touch_down(touch)


class PaginaPrincipal(Pagina):
    def __init__(self, mainwid, encabezado):
        super().__init__()
        self.mainwid = mainwid

        self.freq = db.db_main("SELECT * FROM CONFIG WHERE DESCRIPCION = 'LAPSO'")[0][1]
        self.attach = db.db_main("SELECT * FROM CONFIG WHERE DESCRIPCION = 'ADJUNTAR'")[0][1]

        self.minutesinput = MinutesInput(self, text=self.freq,
                                         font_size=13, size_hint=(None, None),
                                         height=28, width=30,
                                         pos_hint={"center_y": 0.78, "center_x": 0.70},
                                         multiline=False, write_tab=False)
        self.attachment = ToggleButton(text="Adjuntar",
                                       font_size=13,
                                       size_hint=(None, None),
                                       size=(70, 30),
                                       pos_hint={"center_y": 0.62, "center_x": 0.70},
                                       state=self.attach,
                                       on_press=self.validar_config)

        self.actionbar = ActionBar(size_hint=(1, None), pos_hint={"top": 1, "center_x": 0.50})

        self.actionprevious = ActionPrevious(with_previous=False)
        self.actionprevious.clear_widgets()
        self.actionprevious.add_widget(
            Label(text=encabezado,
                  size_hint=(None, None),
                  font_size=16,
                  bold=True,
                  color=(0.7, 0.7, 1, 1),
                  pos_hint={"x": 0, "y": -0.5}))

        self.actionview = ActionView(action_previous=self.actionprevious)

        self.actiongroup = ActionGroup(text="  Documentos  ")
        self.actiongroup.add_widget(
            ActionButton(text="Manual de uso",
                         on_press=self.doc))
        self.actiongroup.add_widget(
            ActionButton(text="Artículos",
                         on_press=lambda *args: self.open_folder("Articles")))
        self.actiongroup.add_widget(
            ActionButton(text="Análisis",
                         on_press=lambda *args: self.open_folder("Analysis")))

        self.actionview.add_widget(self.actiongroup)
        self.actionbar.add_widget(self.actionview)
        self.add_widget(self.actionbar)

        self.add_widget(Label(text="Frecuencia de escaneo:" + chr(10) + "(minutos)",
                              font_size=13,
                              pos_hint={"center_y": 0.78, "center_x": 0.35}))
        self.add_widget(Label(text="Adjuntar análisis en " + chr(10) + "correspondencia:",
                              font_size=13,
                              pos_hint={"center_y": 0.63, "center_x": 0.32}))

        self.save = Button(text="Guardar cambios",
                           font_size=13,
                           size_hint=(None, None),
                           size=(120, 35),
                           pos_hint={"center_y": 0.18, "center_x": 0.32},
                           disabled=True,
                           on_press=self.savechanges)

        self.add_widget(Button(text="Volver",
                               font_size=13,
                               size_hint=(None, None),
                               size=(80, 35),
                               pos_hint={"center_y": 0.18, "center_x": 0.75},
                               on_press=self.mainwid.mainwid.mainwid.goto_selec))

        self.add_widget(Button(text="Olvidar bitácora",
                               font_size=13,
                               size_hint=(None, None),
                               size=(120, 35),
                               pos_hint={"center_y": 0.46, "center_x": 0.32},
                               on_press=self.eliminarf_bitacora))

        self.add_widget(self.minutesinput)
        self.add_widget(self.attachment)
        self.add_widget(self.save)

    @staticmethod
    def doc(*args):
        abrir_guia_de_uso(True)

    @staticmethod
    def open_folder(foldername="", *args):
        try:
            path = db.mypath + chr(92) + foldername

            if not db.os.path.exists(path):
                db.os.makedirs(path)

            db.os.startfile(path)

        except Exception as e:
            msg = "ERROR: No se pudo abrir el directorio. " +\
                  "Póngase en contacto con el desarrollador."
            print(msg + e.__class__.__name__ + " " + str(e))
            db.log_add(msg + e.__class__.__name__ + " " + str(e))
            db.MessageBox(None, msg + chr(10) + e.__class__.__name__ + " " + str(e),
                          "Abrir directorio", db.ICON_ERROR)

    @staticmethod
    def eliminarf_bitacora(*args):
        resp = db.MessageBox(None,
                             "ADVERTENCIA:" + chr(10) +
                             "Si las noticias son olvidadas, el programa podría " +
                             "reenviar noticias que ya fueron enviadas con anterioridad." + chr(10)*2 +
                             "¿Desea que el programa olvide las noticias enviadas?",
                             "Olvidar noticias",
                             db.MB_YESNO)

        if resp == db.IDYES:
            db.clear_binnacle("ALL")
            db.log_add("Bitácora borrada.")
            db.MessageBox(None, "Listo! Noticias olvidadas.", "Olvidar noticias", db.ICON_INFO)

    def validar_config(self, *args):
        if self.minutesinput.text != "" and\
                self.minutesinput.text != "0" and\
                self.minutesinput.text != "00" and\
                (self.minutesinput.text != self.freq or
                 self.attachment.state != self.attach):

            self.save.disabled = False
        else:
            self.save.disabled = True

    def savechanges(self, *args):
        if self.minutesinput.text == "" or self.minutesinput.text == "0" or \
                self.minutesinput.text == "00":
            self.minutesinput.text = self.freq

        if self.minutesinput.text != self.freq or \
                self.attachment.state != self.attach:

            if self.minutesinput.text[0] == "0":
                self.minutesinput.text = self.minutesinput.text[1]

            try:
                db.db_main("UPDATE CONFIG SET VALOR = '" + self.minutesinput.text + "' WHERE DESCRIPCION = 'LAPSO'")
                self.freq = self.minutesinput.text

                db.db_main("UPDATE CONFIG SET VALOR = '" + self.attachment.state + "' WHERE DESCRIPCION = 'ADJUNTAR'")
                self.attach = self.attachment.state

                db.MessageBox(None, "Cambios guardados!", "Configuración", db.ICON_INFO)
                db.log_add("Cambios guardados en configuración.")

            except Exception as e:
                msg = "ERROR: Cambios no guardados." + chr(10) +\
                      "DETALLE: " + e.__class__.__name__ + " " + str(e)
                print(msg)
                db.log_add(msg)

        self.save.disabled = True
        if not self.minutesinput.text == self.freq:
            self.minutesinput.text = self.freq

        if not self.attachment.state == self.attach:
            self.attachment.state = self.attach


class MinutesInput(TextInput):
    def __init__(self, mainwid, **kwargs):
        super().__init__(**kwargs)
        self.mainwid = mainwid
        self.unchange = True

    def insert_text(self, substring, from_undo=False):
        try:
            if substring == "":
                self.unchange = True
            elif not isinstance(int(substring), int):
                self.unchange = True
            else:
                if int(substring) < 0:
                    self.unchange = True
                else:
                    substring = substring[:2 - len(self.text)]
                    self.unchange = super(MinutesInput, self).insert_text(substring, from_undo=from_undo)
        except Exception as e:
            self.unchange = True
            print(e.__class__.__name__ + " " + str(e))

        self.mainwid.validar_config() if not self.unchange else None
        return self.unchange


class CountDown(Label):
    def __init__(self, mainwid, **kwargs):
        super().__init__(**kwargs)
        self.mainwid = mainwid
        self.c_b = 0.2
        self.text = "00:00:00"
        self.color = (0.4, 1, 1, 1)
        self.flag = False

    @staticmethod
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

    def go(self, *args):
        global platform
        global abc
        global srvr
        sender = None
        attachment = None
        try:
            wsexe = db.rpath() + r"\WS\webscraping.exe"

            print("Ejecutando " + wsexe)
            # RECORDAR TIMEOUT
            result = subprocess.run(wsexe,
                                    shell=False,
                                    check=True,
                                    timeout=900)
            print(result)

            htmlbody_path = db.rpath() + r"\WS\htmlbody.txt"

            if db.os.path.isfile(htmlbody_path):
                f = open(htmlbody_path, "r")
                htmlbody = f.read()
                f.close()
                db.os.remove(htmlbody_path)
                print("Archivo removido '" + htmlbody_path + "'")

                if htmlbody:

                    if platform != "Outlook":
                        sender = db.db_main("SELECT VALOR FROM CONFIG WHERE DESCRIPCION = 'AUT'")[0][0]

                    if db.db_main("SELECT VALOR FROM CONFIG WHERE DESCRIPCION = 'ADJUNTAR'")[0][0] == "down":
                        attachment_folder = db.rpath() + r"\WS\Analysis"
                        if db.os.path.exists(attachment_folder):
                            listdir = db.os.listdir(attachment_folder)
                            if len(listdir) > 0:
                                attachment = attachment_folder + chr(92) + listdir[0]

                    sendmail_result =\
                        mn.sendmail(my_name,
                                    platform,
                                    htmlbody,
                                    db.return_elements("DESTINATARIOS"),
                                    db.rpath(),
                                    srvr,
                                    sender,
                                    attachment,
                                    abc)

                    if "Status de mensajería a establecer como ENV." in sendmail_result:
                        db.db_main("UPDATE BITACORA SET ESTADO = 'ENV' WHERE ESTADO = 'PEND'")

                    if mn.reconnected_server:
                        srvr = mn.reconnected_server
                        mn.reconnected_server = None

                    db.log_add(sendmail_result.replace(chr(10), ""))

                else:
                    print("No hay datos en" + chr(10) + htmlbody_path)
                    db.log_add("WARNING: El cuerpo HTML está vacío.")
            else:
                print("No se encontró archivo" + chr(10) + htmlbody_path)
                db.log_add("No se generó ningún cuerpo HTML durante la ejecución del Webscraping. " +
                           "Por lo tanto no se generó mensajería electrónica.")

        except subprocess.TimeoutExpired as e:
            msg = "WARNING: " + e.__class__.__name__ + " " + str(e)
            print(msg)
        except Exception as e:
            msg = "ERROR: Ocurrió una excepción durante iteración programada: " +\
                  e.__class__.__name__ + chr(10) + str(e)
            print(msg)
            db.log_add(msg)
        # No salir de la función antes de que se ejecute esto
        Window.show()

        self.mainwid.button.action()

    def countdown(self, secs, grad):

        if self.flag:
            secs -= 1

            self.text = self.scs_in_hhmmss(secs)
            self.c_b += grad
            self.color = (0.4, 1, self.c_b, 1)

            if secs > 0:
                Clock.schedule_once(lambda dt: self.countdown(secs, grad), 1)
            else:
                Window.hide()
                Clock.schedule_once(self.go, 0.5)

        else:
            self.set_values()

    def set_values(self):
        self.text = "00:00:00"
        self.c_b = 0.2
        self.color = (0.4, 1, 1, 1)
        self.flag = False


def confirm_pend():
    db.db_main("UPDATE BITACORA SET ESTADO = 'ENV' WHERE ESTADO = 'PEND'")


if __name__ == "__main__":
    db.log_add("INICIO DE APLICACIÓN", overwrite=True)
    try:
        MainApp().run()
    except Exception as crit_e:
        msg_crit = "ERROR CRÍTICO: Error crítico iniciando aplicación. " +\
                   crit_e.__class__.__name__ + chr(10)*2 + \
                   "Detalle:" + chr(10) + str(crit_e)
        print(msg_crit)
        db.log_add(msg_crit)
        db.MessageBox(None, msg_crit, 'Error', db.ICON_ERROR)
        db.sys.exit()

# ======================================================================================================================
