# -*- coding:utf-8 -*-
'''
/***************************************************************************
 dict_email.py

 DictLayout class allows to send link to answer in an email


        begin                : 2020-07-22
        git sha              : $Format:%H$
        copyright            : (C) 2020 by Jean-Marie Arsac
        email                : jmarsac@azimut.fr
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 '''

# use python3

import time
import getopt, sys
import smtplib

from email.message import EmailMessage
from email.headerregistry import Address
from email.utils import make_msgid
from qgis.core import Qgis

class DictEmail(object):
    def __init__(self, server, port, user):
        self.server = server
        self.user = user
        self.sender_surname = 'S.D.E.V'
        self.sender_name = "dtdict"
        self.sender_domain = "smdev.fr"
        self.receiver = ""
        self.port = port
        self.setSubject()
        self.setReference()
        self.setHyperlink()
        # corps du mail en texte
        self.text_body = '''\
$reference
    
Madame, monsieur,
    
Vous pouvez télécharger les fichiers de réponse à votre demande en utilisant le lien suivant.

<$hyperlink>

Pour cela, copiez le dans votre navigateur et validez.

Cordialement.

L'équipe DT/DICT

Syndicat Départemental d'Electricité des Vosges

28 rue de la Clé d'or

88004 EPINAL
'''

        # corps du mail en HTML
        self.html_body = '''\
<html><head></head>
<body>
$reference
<br /><br />
Madame, monsieur,
<br /><br />
Vous pouvez télécharger les <a href="$hyperlink">fichiers de réponse à votre demande</a>. 
<br /><br />
Cordialement.
<br /><br />
L'équipe DT/DICT
<br /><br />
-----------------------------------------------
<br />
Syndicat Départemental d'Electricité des Vosges
<br />
28 rue de la Clé d'or
<br />
88004 EPINAL
</body>
</html>
'''

    def setSubject(self, subject:str="Récépissé DT/DICT/ATU"):
        self.subject = subject

    def setReference(self, reference:str=""):
        self.reference = reference

    def setHyperlink(self, hyperlink:str=""):
        self.hyperlink = hyperlink

    def buildAndSendMail(self, password, receiver_email, iface=None, receiver_fullname:str=""):

        receiver_name, receiver_domain = receiver_email.split('@')
        if not receiver_fullname:
            receiver_fullname = receiver_name
        # Create the base text message.
        msg = EmailMessage()
        msg['Subject'] = self.subject
        msg['From'] = Address(self.sender_surname, self.sender_name, self.sender_domain)
        msg['To'] = Address(receiver_fullname, receiver_name, receiver_domain)
        msg['Message-ID'] = make_msgid()

        textBody = self.text_body
        if self.reference and "$reference" in textBody:
            textBody = textBody.replace("$reference", self.reference)
        if self.hyperlink and "$hyperlink" in textBody:
            textBody = textBody.replace("$hyperlink", self.hyperlink)
        msg.set_content(textBody)

        htmlBody = self.html_body
        if self.reference and "$reference" in htmlBody:
            htmlBody = htmlBody.replace("$reference", self.reference)
        if self.hyperlink and "$hyperlink" in htmlBody:
            htmlBody = htmlBody.replace("$hyperlink", self.hyperlink)

        # Add the html version.  This converts the message into a multipart/alternative
        # container, with the original text message as the first part and the new html
        # message as the second part.
        msg.add_alternative(htmlBody, subtype='html')
        if password:
            with smtplib.SMTP(self.server, self.port) as s:
                try:
                    smtp_ie = 0
                    #s.set_debuglevel(True)
                    # identify ourselves, prompting server for supported features
                    s.ehlo()

                    # If we can encrypt this session, do it
                    if s.has_extn('STARTTLS'):
                        s.starttls()
                        s.ehlo()  # re-identify ourselves over TLS connection

                    s.login(self.user, password)
                    smtp_ie = s.send_message(msg)
                    s.quit()
                    if iface:
                        iface.messageBar().pushMessage("Courriel envoyé à {}@{}".format(receiver_name, receiver_domain), "", Qgis.Success, 10)

                except Exception as e:
                    if iface:
                        iface.messageBar().pushMessage("impossible d'envoyer le courriel à {}@{}".format(receiver_name, receiver_domain), str(e), Qgis.Critical, 10)
                    else:
                        print(str(e))

