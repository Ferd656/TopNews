# -*- coding: utf-8 -*-
import base64
import smtplib
import pywintypes
import win32com.client as win32
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

DEF_MSG = "Elemento e-mail generado exitosamente."

HTML_TEMPLATE_UPPER = r"""
<html>
<head>
<meta charset="UTF-8">
<style>
table, td {
border: 4px solid #ffffff;
border-collapse: collapse;
text-align: left;
}
.container {
    vertical-align: 'text-top';
}
.header {
background:rgb(0, 0, 33);
color: white;
font-size: 22;
font-weight: bold;
}
.news {
background:#7979d2;
font-family:Arial;
color: white;
font-size: 20;
}
.source {
font-family:Arial;
color: #000033;
font-size: 12;
font-style: italic;
}
.paragraph {
font-size: 17;
}
span {
background:#808080;
font-family:Arial;
font-size: 12;
color: white;
border-radius: 50px 50px 50px;
border: 3px solid #808080;
}
.footer {
left: 0;
bottom: 0;
width: 100%;
font-family:Calibri;
font-size: 12;
background-color: #1a1a1a;
color: #808080;
text-align: center;
}
</style>
</head>
<body>
<div class="header"><img src='Media\Header.png'/></div>
<table style='width:100%' bgcolor='#ccccff'>"""

HTML_TEMPLATE_BOTTOM = r"""
</table>
</body>
<div class="footer">
Mensaje generado automáticamente por bot 
<a href='https://github.com/Ferd656/TopNews' style='text-decoration:none;color:#808080;'>&#60TopNews&#47&#62</a>
</div>
</html>"""

# MAIL_HEADER = db.rpath() + r"\Media\Header.png"
# MAIL_HEADER = "https://i.imgur.com/fKutlDH.png"
# MAIL_HEADER = "https://drive.google.com/uc?export=view&id=1E1iamlwjnZdTCzWWD26AcDGdNLho9cxF"

# DEFAULT_IMG = r"\defaultimg.png"
# DEFAULT_IMG = "https://i.imgur.com/32RhV0q.png"
# DEFAULT_IMG = "https://drive.google.com/uc?export=view&id=1_hPyJKe9R-tZXwimrtG9otXkB6CBmjCD"

# NEWS_ICON = db.my_path[:len(db.my_path)-(db.my_path[::-1].find(chr(92))+1)] + r"\Media\Iconread.png"
# NEWS_ICON = "https://i.imgur.com/C04wLa7.png"
# NEWS_ICON = "https://drive.google.com/uc?export=view&id=1b5XMebA0zivCt5z1OgPTljGm8ZN81jFa"


reconnected_server = None


def sendmail(myname, platform, htmlstr, receivers, rpath, server=None, sender=None, attachment=None, abc=None):

    global reconnected_server

    if platform == "Office365":
        myinfofile = open(rpath + r"\webassets.txt", "r")

        # Modificar mediante el fichero webassets.txt
        default_image = "'" + myinfofile.readline().split("|")[1].replace(chr(10), "") + "'"
        header_image = "'" + myinfofile.readline().split("|")[1].replace(chr(10), "") + "'"
        icon_image = "'" + myinfofile.readline().split("|")[1].replace(chr(10), "") + "'"

    else:

        default_image = "'" + rpath + r"\Media\defaultimg.png'"
        header_image = "'" + rpath + r"\Media\Header.png'"
        icon_image = "'" + rpath + r"\Media\Iconread.png'"

    subject = "NOTICIAS"
    recv = None
    msg = DEF_MSG

    htmlstr = htmlstr.replace("'TopNewsDefaultImage'", default_image).replace("'TopNewsLinkIcon'", icon_image)

    head = HTML_TEMPLATE_UPPER.replace(r"'Media\Header.png'", header_image)

    htmlbody = head + htmlstr + HTML_TEMPLATE_BOTTOM

    # print(htmlbody)

    for i in receivers:
        if recv:
            recv += ";" + i[0]
        else:
            recv = i[0]

    if platform == "Office365" and (not server or not sender):
        msg = "ERROR: Módulo MailNews. No se creó item Office365. Falta servidor o emisor. " +\
              "Póngase en contacto con el desarrollador."

    elif platform == "Office365":

        try:

            mail_item = MIMEMultipart()

            mail_item.attach(MIMEText(htmlbody, "html"))

            mail_item["Subject"] = subject
            mail_item["From"] = sender
            mail_item["To"] = recv

            if attachment:
                openedfile = open(attachment, "rb").read()

                attachedfile = MIMEApplication(openedfile, _subtype="pdf")
                attachedfile.add_header('content-disposition', 'attachment', filename=attachment.split(chr(92))[-1])
                mail_item.attach(attachedfile)

        except Exception as e:
            msg = "ERROR: Módulo MailNews. Error al crear mensajería Office365. " + \
                  "Póngase en contacto con el desarrollador. " + "DETALLE: " + e.__class__.__name__ + \
                  chr(10) + str(e)

        else:

            try:

                server.sendmail(sender, recv, mail_item.as_string())
                msg = "Status de mensajería a establecer como ENV. Office365. Mensajería electrónica enviada."

            except smtplib.SMTPServerDisconnected:

                print("Reintentando inicio de servidor . . .")
                server = smtplib.SMTP(host="smtp.office365.com", port=587)
                server.starttls()
                server.ehlo()
                server.login(sender, base64.b64decode(abc).decode("utf-8"))

                server.sendmail(sender, recv, mail_item.as_string())

                reconnected_server = server

            except Exception as e:
                msg = "ERROR: Módulo MailNews. Error al enviar mensajería Office365. " + \
                      "Póngase en contacto con el desarrollador. " + "DETALLE: " + e.__class__.__name__ + \
                      chr(10) + str(e)

    else:
        try:
            outlook = win32.Dispatch('outlook.application')
            mail_item = outlook.CreateItem(0)
            mail_item.To = recv
            mail_item.Subject = subject
            mail_item.HTMLbody = htmlbody

            if attachment:
                mail_item.Attachments.Add(attachment)

            mail_item.Display(True)

        except Exception as e:
            msg = "ERROR: Módulo MailNews. Error al enviar mensajería Outlook. " + \
                  "Póngase en contacto con el desarrollador. " + "DETALLE: " + e.__class__.__name__ + \
                  chr(10) + str(e)

        else:
            try:
                if mail_item.Sent:
                    msg = "Status de mensajería a establecer como ENV. Outlook. Mensajería electrónica enviada."
                else:
                    msg = "Outlook. Mensajería electrónica no enviada."
            except pywintypes.com_error as enverr:
                if "The RPC server is unavailable." in str(enverr):
                    msg = "Outlook. Mensajería electrónica no enviada. " + str(enverr)
                else:
                    msg = "Status de mensajería a establecer como ENV. Outlook. WARNING: " + str(enverr)
            except Exception as e:
                msg = "WARNING: Módulo MailNews. Comprobación envío Outlook. " +\
                      "DETALLE: " + e.__class__.__name__ + \
                      chr(10) + str(e)

    print(msg)
    return msg
