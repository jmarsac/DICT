# -*- coding: utf-8 -*-
"""
/***************************************************************************
 DICT
                                 A QGIS plugin
 DICT
                              -------------------
        begin                : 2015-08-19
        git sha              : $Format:%H$
        copyright            : (C) 2015 by Loïc BARTOLETTI
        email                : lbartoletti@tuxfamily.org
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from PyQt5.QtCore import (QSettings, QTranslator, qVersion,
                          QCoreApplication, QDir, QFileInfo,
                          QFile, Qt, QUrl)
from PyQt5.QtWidgets import QAction, QMessageBox, QDialog
from PyQt5.QtGui import QIcon, QDesktopServices
# Initialize Qt resources from file resources.py
from . import resources
# Import the code for the dialog
from .DICT_about import DICTAbout
from .DICT_dialog import DICTDialog
from .DICT_dialog_config import DICTDialogConfig
from .DICT_xml import DICT_xml

import os.path
import sys
import tempfile
import subprocess


class DICT(object):
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'DICT_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Create the dialog (after translation) and keep reference
        self.dlg = DICTDialog()
        self.dlgConfig = DICTDialogConfig()

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr('&DICT')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar('DICT')
        self.toolbar.setObjectName('DICT')

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('DICT', message)

    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_configuration_path = ':/plugins/DICT/config.png'
        self.add_action(
            icon_configuration_path,
            text=self.tr('DICT configuration'),
            callback=self.runConfig,
            parent=self.iface.mainWindow())

        icon_path = ':/plugins/DICT/icon.png'
        self.add_action(
            icon_path,
            text=self.tr('DICT'),
            callback=self.run,
            parent=self.iface.mainWindow())

        self.add_action(
            '',
            text=self.tr('À propos'),
            callback=self.runAbout,
            parent=self.iface.mainWindow(),
            add_to_toolbar=False)

        self.add_action(
            '',
            text=self.tr('Aide'),
            callback=self.runHelp,
            parent=self.iface.mainWindow(),
            add_to_toolbar=False)

        firstUse = QSettings().value("DICT/isFirstUse" , 1, type=int)
        if firstUse == 1:
            QSettings().setValue("DICT/isFirstUse", 0)
            self.runAbout()

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr('&DICT'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    def run(self):
        """Run method that performs all the real work"""
        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            msgBox = QMessageBox()
            msgBox.setTextFormat(Qt.RichText)
            dtdict = DICT_xml(self.dlg.lineEdit.text())
            # Prépare le formulaire
            titre, pdf = dtdict.formulaire()
            if titre is None:
                return
            try:
                planPDF = dtdict.geometriePDF(titre)
            except :
                msgBox.setText("Erreur lors de la création du plan, vérifiez si votre composition est correctement configurée")
                msgBox.exec_()
                msgBox = QMessageBox()
                msgBox.setTextFormat(Qt.RichText)
            if QFile.exists(pdf) and \
                    all([QFile.exists(p) for p in planPDF]) and \
                    pdf and len(planPDF) > 0:
                out = QSettings().value("/DICT/configRep")

                fusion = QSettings().value("/DICT/fusionPDF")

                if(fusion and
                   self.__checkPdftk(QSettings().value("/DICT/configPDFTK"))):
                    # Utilise pdftk pour fusionner les documents
                    s = os.path.join(out, "envoi_" + titre + ".pdf")
                    subprocess.call([QSettings().value(
                                    "/DICT/configPDFTK"), pdf] +
                                    planPDF + ["cat", "output"] + [s])

                    msgBox.setText("Vous pouvez envoyer le fichier :" +
                                   "<br><a href='file:///" + s.replace('\\', '/') + "'>" +
                                   s.replace('\\', '/') + "</a>")

                    os.remove(pdf)
                    for p in planPDF:
                        os.remove(p)
                else:
                    msgBox.setText("Vous pouvez envoyer les fichiers :" +
                                   "<br>Récepissé : <a href='file:///" + pdf.replace('\\', '/') + "'>" + pdf.replace('\\', '/')+ "</a><br>" +
                                   "Plans : " + '<br>'.join(["<a href='file:///" + s.replace('\\', '/') + "'>" + s.replace('\\', '/') + "</a>" for s in planPDF]) + "<br>")

            else:
                msgBox.setText("Erreur lors de la création des fichiers :\
                \nRécepissé : " + pdf.replace('\\', '/') + "\n \
                Plan : "+ str([s.replace('\\', '/') for s in planPDF]) )

            msgBox.exec_()

            # Save xml

    def runConfig(self):
        """Run method that performs all the real work"""
        # show the dialog
        self.dlgConfig.show()
        # Run the dialog event loop
        result = self.dlgConfig.exec_()
        # See if OK was pressed
        if result:
            pass

    def runAbout(self):
        """ Run about dialog """
        dialog = DICTAbout()
        dialog.exec_()

    def runHelp(self):
        QDesktopServices.openUrl(QUrl("https://github.com/Oslandia/DICT"))

    def __checkPdftk(self, chemin):
        ret = -1
        try:
            if sys.platform == 'win32':
                fd, err = tempfile.mkstemp()
                proc = subprocess.Popen([chemin, "--version"], shell=True,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.STDOUT,
                                        stdin=subprocess.PIPE)
                proc.stdin.close()
                proc.wait()
                result = proc.returncode
                txt = proc.stdout.read()
                ret = txt.find(b"pdftk")
                os.close(fd)
                os.remove(err)
            else:
                txt = subprocess.check_output(["/usr/local/bin/pdftk",
                                               "--version"])
                ret = txt.find("pdftk")
        except Exception as e:
            msgBox = QMessageBox()
            msgBox.setWindowTitle('Error with pdftk')
            msgBox.setText(str(e))
            msgBox.exec_()

        return ret >= 0
