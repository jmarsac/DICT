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
from PyQt5.QtWidgets import QAction, QMessageBox, QDialog, QProgressBar
from PyQt5.QtGui import QIcon, QDesktopServices

from qgis.core import Qgis, QgsApplication, QgsProject, QgsPointXY, QgsExpressionContextUtils, QgsVectorLayer \
    , QgsFeatureRequest, QgsFeature \
    , QgsLayoutAtlas, QgsLayoutItemMap, QgsLayoutExporter

# Initialize Qt resources from file resources.py
from . import resources
# Import the code for the dialog
from .DICT_about import DICTAbout
from .DICT_dialog import DICTDialog
from .DICT_dialog_config import DICTDialogConfig
from .DICT_xml import DICT_xml
from .DICT_geometrie import DICT_geometrie
from .dict_layout import DictLayout
from .fdf_buffer import FdfBuffer
from .folio_geometry import FolioGeometry
from .folio_map_tool import FolioMapTool
from .utils import Utils

import os
import sys
import tempfile
import subprocess
import shutil
import encodings
import datetime
import dateutil.parser

class DICT(object):
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        print("__init__")
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

        self.__dtdict = None

        # scale setting
        self.__dict_print_scale = 1

        # Layouts
        self.__dict_layout = DictLayout()
        self.__dict_layout.loadTemplates(self.dlg.comboBoxLayout)

        # geo PDF ?
        self.create_geo_pdf = False

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
        enabled_flag = True,
        add_to_menu = True,
        add_to_toolbar = True,
        status_tip = None,
        whats_this = None,
        parent = None):
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
        print("initGui")
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_configuration_path = ':/plugins/DICT/config.png'
        self.add_action(
            icon_configuration_path,
            text = self.tr('DICT configuration'),
            callback = self.runConfig,
            parent = self.iface.mainWindow())

        icon_path = ':/plugins/DICT/icon.png'
        self.add_action(
            icon_path,
            text = self.tr('DICT'),
            callback = self.run,
            parent = self.iface.mainWindow())

        self.add_action(
            '',
            text=self.tr('À propos'),
            callback = self.runAbout,
            parent = self.iface.mainWindow(),
            add_to_toolbar = False)

        self.add_action(
            '',
            text = self.tr('Aide'),
            callback = self.runHelp,
            parent = self.iface.mainWindow(),
            add_to_toolbar = False)

        icon_folio_path = ':/plugins/DICT/icon_folio.png'
        self.add_action(
            icon_folio_path,
            text=self.tr(u'Placer folio'),
            callback=self.place_folio_tool,
            parent=self.iface.mainWindow(),
            add_to_toolbar=True,
            add_to_menu=True)

        firstUse = QSettings().value("DICT/isFirstUse" , 1, type = int)
        if firstUse == 1:
            DictLayout.init_templates(True)
            QSettings().setValue("DICT/isFirstUse", 0)
            self.runAbout()

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        print("unload")
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr('&DICT'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    def run(self):
        """Run method that performs all the real work"""
        print("run")

        self.dlg.setWindowFlags(Qt.WindowStaysOnTopHint)
        # set buttons icons
        if True:
            self.dlg.toolButtonPlaceFolio.setIcon(QIcon(':/plugins/DICT/icon_folio.png'))
            self.dlg.toolButtonCreateMaps.setIcon(QIcon(':/plugins/DICT/icon_maps.png'))
            self.dlg.toolButtonEditForm.setIcon(QIcon(':/plugins/DICT/icon_edit_form.png'))
            self.dlg.toolButtonCleanCanvas.setIcon(QIcon(':/plugins/DICT/icon_clean_canvas.png'))

        # connect signals
        self.dlg.toolButtonPlaceFolio.clicked.connect(self.place_folio_tool)
        self.dlg.toolButtonCreateMaps.clicked.connect(self.create_pdf_maps)
        self.dlg.toolButtonEditForm.clicked.connect(self.edit_cerfa)
        self.dlg.toolButtonCleanCanvas.clicked.connect(self.clean_canvas)

        self.dlg.lineEdit.textChanged.connect(self.on_lineedit_text_changed)
        self.dlg.comboBoxPrintScale.currentTextChanged.connect(self.on_comboboxprintscale_text_changed)
        self.dlg.comboBoxLayout.currentTextChanged.connect(self.on_comboboxlayout_text_changed)

        self.pointTool = None

        # show the dialog
        self.dlg.show()

        # output files names prefix and suffix
        self.__prefix = QSettings().value("/DICT/prefRecep")
        QgsExpressionContextUtils.setProjectVariable(QgsProject.instance(), 'dict_prefix', self.__prefix)
        self.__suffix = QSettings().value("/DICT/sufRecep")
        QgsExpressionContextUtils.setProjectVariable(QgsProject.instance(), 'dict_suffix', self.__suffix)
        self.__map_prefix = QSettings().value("/DICT/prefPlan")
        QgsExpressionContextUtils.setProjectVariable(QgsProject.instance(), 'dict_map_prefix', self.__map_prefix)
        self.__map_suffix = QSettings().value("/DICT/sufPlan")
        QgsExpressionContextUtils.setProjectVariable(QgsProject.instance(), 'dict_map_suffix', self.__map_suffix)
        # exploitant infos
        self.__dico_exploitant = dict()

        # Raison sociale exploitant
        if QSettings().value("/DICT/coordDenom"):
            self.__dico_exploitant["RaisonSocialeExploitant"] = QSettings().value("/DICT/coordDenom")
        # Contact exploitant
        if QSettings().value("/DICT/coordPersonne"):
            self.__dico_exploitant["ContactExploitant"] = QSettings().value("/DICT/coordPersonne")
        # N° et voie exploitant
        if QSettings().value("/DICT/coordNumVoie"):
            self.__dico_exploitant["NoVoieExploitant"] = QSettings().value("/DICT/coordNumVoie")
        # Lieu-dit / boite postale exploitant
        if QSettings().value("/DICT/coordBP"):
            self.__dico_exploitant["LieuditBPExploitant"] = QSettings().value("/DICT/coordBP")
        # Code postal exploitant
        if QSettings().value("/DICT/coordCP"):
            self.__dico_exploitant["CodePostalExploitant"] = QSettings().value("/DICT/coordCP")
        # Commune exploitant
        if QSettings().value("/DICT/coordCommune"):
            self.__dico_exploitant["CommuneExploitant"] = QSettings().value("/DICT/coordCommune")
        # N° téléphone exploitant
        if QSettings().value("/DICT/coordTel"):
            self.__dico_exploitant["TelExploitant"] = QSettings().value("/DICT/coordTel")
        # N° fax exploitant
        if QSettings().value("/DICT/coordFax"):
            self.__dico_exploitant["FaxExploitant"] = QSettings().value("/DICT/coordFax")
        # Catégorie du 1er réseau (ex: EL)
        if QSettings().value("/DICT/yyy"):
            self.__dico_exploitant["CategorieReseau1"] = QSettings().value("/DICT/yyy")
        # Catégorie du 2ème réseau (ex: EL)
        if QSettings().value("/DICT/yyy"):
            self.__dico_exploitant["CategorieReseau2"] = QSettings().value("/DICT/yyy")
        # Catégorie du 3ème réseau (ex: EL)
        if QSettings().value("/DICT/yyy"):
            self.__dico_exploitant["CategorieReseau3"] = QSettings().value("/DICT/yyy")
        # Représentant exploitant
        if QSettings().value("/DICT/yyy"):
            self.__dico_exploitant["RepresentantExploitant"] = QSettings().value("/DICT/yyy")
        # N° téléphone représentant
        if QSettings().value("/DICT/yyy"):
            self.__dico_exploitant["TelModification"] = QSettings().value("/DICT/yyy")
        # Plans joints (Off/Oui)
        if QSettings().value("/DICT/yyy"):
            self.__dico_exploitant["PlansJoints"] = QSettings().value("/DICT/yyy")
        # Référence n° 1
        if QSettings().value("/DICT/yyy"):
            self.__dico_exploitant["Ref1"] = QSettings().value("/DICT/yyy")
        # echelle plan n° 1
        if QSettings().value("/DICT/yyy"):
            self.__dico_exploitant["Echelle1"] = QSettings().value("/DICT/yyy")
        # Jour d'édition du plan n° 1 (ex: 11)
        if QSettings().value("/DICT/yyy"):
            self.__dico_exploitant["JourEditionPlan1"] = QSettings().value("/DICT/yyy")
        # Mois d'édition du plan n° 1 (ex: 11)
        if QSettings().value("/DICT/yyy"):
            self.__dico_exploitant["MoisEditionPlan1"] = QSettings().value("/DICT/yyy")
        # Année d'édition du plan n° 1 (ex: 2011)
        if QSettings().value("/DICT/yyy"):
            self.__dico_exploitant["AnneeEdition1"] = QSettings().value("/DICT/yyy")
        # Réseau sensible sur plan n° 1 (Off/Oui)
        if QSettings().value("/DICT/yyy"):
            self.__dico_exploitant["Sensible1"] = QSettings().value("/DICT/yyy")
        # Profondeur réseau sur plan n° 1 (ex: 60)
        if QSettings().value("/DICT/yyy"):
            self.__dico_exploitant["Profondeur1"] = QSettings().value("/DICT/yyy")
        # Matériau réseau sur plan n° 1 (ex: PE)
        if QSettings().value("/DICT/yyy"):
            self.__dico_exploitant["Materiau1"] = QSettings().value("/DICT/yyy")
        # Référence n° 2
        if QSettings().value("/DICT/yyy"):
            self.__dico_exploitant["Ref2"] = QSettings().value("/DICT/yyy")
        # Echelle plan n° 2
        if QSettings().value("/DICT/yyy"):
            self.__dico_exploitant["Echelle2"] = QSettings().value("/DICT/yyy")
        # Jour d'édition du plan n° (ex: 12)
        if QSettings().value("/DICT/yyy"):
            self.__dico_exploitant["JourEditionPlan2"] = QSettings().value("/DICT/yyy")
        # Mois d'édition du plan n° (ex: 12)
        if QSettings().value("/DICT/yyy"):
            self.__dico_exploitant["MoisEditionPlan2"] = QSettings().value("/DICT/yyy")
        # Année d'édition du plan n° (ex: 2012)
        if QSettings().value("/DICT/yyy"):
            self.__dico_exploitant["AnneeEdition2"] = QSettings().value("/DICT/yyy")
        # Réseau sensible sur plan n° 2 (Off/Oui)
        if QSettings().value("/DICT/yyy"):
            self.__dico_exploitant["Sensible2"] = QSettings().value("/DICT/yyy")
        # Profondeur réseau sur plan n° 2 (ex: 62)
        if QSettings().value("/DICT/yyy"):
            self.__dico_exploitant["Profondeur2"] = QSettings().value("/DICT/yyy")
        # Matériau réseau sur plan n° 2 (ex: PVC)
        if QSettings().value("/DICT/yyy"):
            self.__dico_exploitant["Materiau2"] = QSettings().value("/DICT/yyy")
        # Case réunion chantier (Off/Oui)
        if QSettings().value("/DICT/yyy"):
            self.__dico_exploitant["ReunionChantierCase"] = QSettings().value("/DICT/yyy")
        # Rendez-vous d'un commun accord (Off/Oui)
        if QSettings().value("/DICT/yyy"):
            self.__dico_exploitant["DateRDV"] = QSettings().value("/DICT/yyy")
        # Jour de la réunion (ex: 11)
        if QSettings().value("/DICT/yyy"):
            self.__dico_exploitant["JourReunion"] = QSettings().value("/DICT/yyy")
        # Mois e la réunion (ex: 11)
        if QSettings().value("/DICT/yyy"):
            self.__dico_exploitant["MoisReunion"] = QSettings().value("/DICT/yyy")
        # Année de la réunion (ex: 2011)
        if QSettings().value("/DICT/yyy"):
            self.__dico_exploitant["AnneeReunion"] = QSettings().value("/DICT/yyy")
        # Heure de la réunion (ex: 11)
        if QSettings().value("/DICT/yyy"):
            self.__dico_exploitant["HeureReunion"] = QSettings().value("/DICT/yyy")
        # Date rdv à l'initiative du déclarant (Off/Oui)
        if QSettings().value("/DICT/yyy"):
            self.__dico_exploitant["RDVparDeclarant"] = QSettings().value("/DICT/yyy")
        # Jour appel non concluant (ex: 12)
        if QSettings().value("/DICT/yyy"):
            self.__dico_exploitant["AppelNonConcl_Jour"] = QSettings().value("/DICT/yyy")
        # Mois appel non concluant (ex: 12)
        if QSettings().value("/DICT/yyy"):
            self.__dico_exploitant["AppelNonConcl_Mois"] = QSettings().value("/DICT/yyy")
        # Année appel non concluant (ex: 2012)
        if QSettings().value("/DICT/yyy"):
            self.__dico_exploitant["AppelNonConcl_Annee"] = QSettings().value("/DICT/yyy")
        # Case respecter servitude (Off/Oui)
        if QSettings().value("/DICT/yyy"):
            self.__dico_exploitant["ServitudeCase"] = QSettings().value("/DICT/yyy")
        # Pas uniquement classe A; prévoir investigations supplémentaires (Off/Oui)
        if QSettings().value("/DICT/yyy"):
            self.__dico_exploitant["PasClasseACase"] = QSettings().value("/DICT/yyy")
        # Branchement sur réseau enterré (Off/Oui)
        if QSettings().value("/DICT/yyy"):
            self.__dico_exploitant["BranchementsCase"] = QSettings().value("/DICT/yyy")
        # Recommandations techniques spécifiques
        if QSettings().value("/DICT/yyy"):
            self.__dico_exploitant["Recommandations"] = QSettings().value("/DICT/yyy")
        # Rubriques guide technique
        if QSettings().value("/DICT/yyy"):
            self.__dico_exploitant["RubriquesGuide"] = QSettings().value("/DICT/yyy")
        # Mise hors tension (HT_Impossible / HT_Possible)
        if QSettings().value("/DICT/yyy"):
            self.__dico_exploitant["MiseHorsTension"] = QSettings().value("/DICT/yyy")
        # Mesures de sécurité
        if QSettings().value("/DICT/yyy"):
            self.__dico_exploitant["MesuresSecurite"] = QSettings().value("/DICT/yyy")
        # Mesures de sécurité 2ème ligne
        if QSettings().value("/DICT/yyy"):
            self.__dico_exploitant["MesuresSecurite2"] = QSettings().value("/DICT/yyy")
        # Dispositif de sécurité(Voir la liste .../Voir la localisation sur.../Aucun dans l'emprise)
        if QSettings().value("/DICT/yyy"):
            self.__dico_exploitant["DispositifsSecurite"] = QSettings().value("/DICT/yyy")
        # N° SDIS
        if QSettings().value("/DICT/yyy"):
            self.__dico_exploitant["Endommagement"] = QSettings().value("/DICT/yyy")
        # Responsable du dossier
        if QSettings().value("/DICT/respNom"):
            self.__dico_exploitant["NomResponsableDossier"] = QSettings().value("/DICT/respNom")
        # Service (ex: Cartographie)
        if QSettings().value("/DICT/respService"):
            self.__dico_exploitant["DésignationService"] = QSettings().value("/DICT/respService")
        # N° téléphone responsable du dossier
        if QSettings().value("/DICT/respTel"):
            self.__dico_exploitant["TelResponsableDossier"] = QSettings().value("/DICT/respTel")
        # Catégorie du 1er réseau (ex: EL)
        if QSettings().value("/DICT/yyy"):
            self.__dico_exploitant["CategorieReseau1"] = QSettings().value("/DICT/yyy")
        # Nom du signataire
        if QSettings().value("/DICT/signNom"):
            self.__dico_exploitant["NomSignataire"] = QSettings().value("/DICT/signNom")
        # N° téléphone en cas de dégradation
        if QSettings().value("/DICT/TelEndommagement"):
            self.__dico_exploitant["TelEndommagement"] = QSettings().value("/DICT/TelEndommagement")

    def searchPreferredMpSizeLayout(self, map_size, combo_box):
        for i in range(0, combo_box.count()):
            name = combo_box.itemText(i)
            if map_size.upper() in name:
                combo_box.setCurrentIndex(i)
                break

    def on_comboboxlayout_text_changed(self):
        if len(self.dlg.comboBoxLayout.currentText()) > 0:
            layout_name = self.dlg.comboBoxLayout.currentText()
            if DictLayout.layoutExists(layout_name):
                self.__dict_layout.removeLayoutByName(layout_name)
            full_filename = "{}/{}.qpt".format(
                QSettings().value("/DICT/configQPT", os.path.join(QgsApplication.qgisSettingsDirPath(), 'composer_templates'),type=str),
                layout_name)
            self.__dict_layout.loadLayout(full_filename, layout_name, layout_name)
            self.__dict_layout.setCurrentLayoutByName(layout_name)
            self.__dict_layout.setPrintScale(self.__dict_print_scale)
            if self.pointTool is not None:
                point_size = self.__dict_layout.folioPrintSize()
                self.pointTool.setSize(point_size.x(), point_size.y())

    def on_comboboxprintscale_text_changed(self):
        if len(self.dlg.comboBoxPrintScale.currentText()) > 0:
            self.__dict_print_scale = int(self.dlg.comboBoxPrintScale.currentText()[4:])
            QgsExpressionContextUtils.setProjectVariable(QgsProject.instance(), 'dict_print_scale', self.__dict_print_scale)
            if self.__dict_layout is not None:
                self.__dict_layout.setPrintScale(self.__dict_print_scale)
            if self.pointTool is not None:
                self.pointTool.setPrintScale(int(self.dlg.comboBoxPrintScale.currentText()[4:]))

    def on_lineedit_text_changed(self):
        titre = ""
        pdf = ""
        planPDF = []
        msgBox = QMessageBox()
        msgBox.setTextFormat(Qt.RichText)
        if len(self.dlg.lineEdit.text()) > 0:
            self.__dtdict = DICT_xml(self.dlg.lineEdit.text())

            QgsExpressionContextUtils.setProjectVariable(QgsProject.instance(), 'dict_type_demande', self.__dtdict.xml_demande.type_demande())
            self.filename = self.prefix() + " " + self.__dtdict.xml_demande.type_demande() \
                       + "-" + self.__dtdict.xml_demande.no_teleservice() \
                       + " " + self.suffix()
            self.filename = self.filename.strip().replace(" ", "-")
            QgsExpressionContextUtils.setProjectVariable(QgsProject.instance(), 'dict_filename', self.filename)
            self.titre = self.filename
            self.map_filename = self.mapPrefix() + " " + self.__dtdict.xml_demande.type_demande() \
                            + "-" + self.__dtdict.xml_demande.no_teleservice() \
                            + " " + self.mapSuffix()
            self.map_filename = self.map_filename.strip().replace(" ", "-")
            QgsExpressionContextUtils.setProjectVariable(QgsProject.instance(), 'dict_map_filename', self.map_filename)

            self.fdf_buffer = FdfBuffer()
            self.fdf_buffer.open(self.filename + ".pdf")
            type_demande = self.__dtdict.xml_demande.dictionnaire()["type_demande"]
            self.fdf_buffer.add_checkbox_value(type_demande == "DT", "Recepisse_DT")
            self.fdf_buffer.add_checkbox_value(type_demande == "DICT", "Recepisse_DICT")
            self.fdf_buffer.add_checkbox_value(type_demande == "DC", "Recepisse_DC")
            self.fdf_buffer.add_text_value(self.__dtdict.xml_demande.dictionnaire()["no_teleservice"], "NoGU")
            QgsExpressionContextUtils.setProjectVariable(QgsProject.instance(), 'dict_no_teleservice', self.__dtdict.xml_demande.no_teleservice())

            # update dialog infos
            self.dlg.labelType_demande.setText(self.__dtdict.xml_demande.dictionnaire()["type_demande"])
            self.dlg.labelNo_teleservice.setText(self.__dtdict.xml_demande.dictionnaire()["no_teleservice"])
            if "tvx_adresse" in self.dicoDeclarant():
                self.dlg.labelAdresse_travaux.setText(self.__dtdict.xml_demande.dictionnaire()["tvx_adresse"])
            else:
                self.dlg.labelAdresse_travaux.setText("")
            if "tvx_commune" in self.dicoDeclarant():
                self.dlg.labelCommune_travaux.setText(self.__dtdict.xml_demande.dictionnaire()["tvx_commune"])
            else:
                self.dlg.labelCommune_travaux.setText("")
            if "tvx_description" in self.dicoDeclarant():
                self.dlg.labelDescription_travaux.setText(self.__dtdict.xml_demande.dictionnaire()["tvx_description"])
            else:
                self.dlg.labelDescription_travaux.setText("")

            if "taille_des_plans" in self.dicoDeclarant():
                print( self.dicoDeclarant()["taille_des_plans"])
                self.searchPreferredMpSizeLayout( self.dicoDeclarant()["taille_des_plans"], self.dlg.comboBoxLayout)

            if "RaisonSocialeExploitant" in self.__dico_exploitant:
                self.fdf_buffer.add_text_value(self.__dico_exploitant["RaisonSocialeExploitant"], "RaisonSocialeExploitant")
            if "ContactExploitant" in self.__dico_exploitant:
                self.fdf_buffer.add_text_value(self.__dico_exploitant["ContactExploitant"], "ContactExploitant")
            if "NoVoieExploitant" in self.__dico_exploitant:
                self.fdf_buffer.add_text_value(self.__dico_exploitant["NoVoieExploitant"], "NoVoieExploitant")
            if "LieuditBPExploitant" in self.__dico_exploitant:
                self.fdf_buffer.add_text_value(self.__dico_exploitant["LieuditBPExploitant"], "LieuditBPExploitant")
            if "CodePostalExploitant" in self.__dico_exploitant:
                self.fdf_buffer.add_text_value(self.__dico_exploitant["CodePostalExploitant"], "CodePostalExploitant")
            if "CommuneExploitant" in self.__dico_exploitant:
                self.fdf_buffer.add_text_value(self.__dico_exploitant["CommuneExploitant"], "CommuneExploitant")
            if "TelExploitant" in self.__dico_exploitant:
                self.fdf_buffer.add_text_value(self.__dico_exploitant["TelExploitant"], "TelExploitant")
            if "FaxExploitant" in self.__dico_exploitant:
                self.fdf_buffer.add_text_value(self.__dico_exploitant["FaxExploitant"], "FaxExploitant")
            if "CategorieReseau1" in self.__dico_exploitant:
                self.fdf_buffer.add_text_value(self.__dico_exploitant["CategorieReseau1"], "CategorieReseau1")
            if "RepresentantExploitant" in self.__dico_exploitant:
                self.fdf_buffer.add_text_value(self.__dico_exploitant["RepresentantExploitant"], "RepresentantExploitant")
            if "TelModification" in self.__dico_exploitant:
                self.fdf_buffer.add_text_value(self.__dico_exploitant["TelModification"], "TelModification")
            if "TelEndommagement" in self.__dico_exploitant:
                self.fdf_buffer.add_text_value(self.__dico_exploitant["TelEndommagement"], "TelEndommagement")
            if "Endommagement" in self.__dico_exploitant:
                self.fdf_buffer.add_text_value(self.__dico_exploitant["Endommagement"], "Endommagement")
            if "NomResponsableDossier" in self.__dico_exploitant:
                self.fdf_buffer.add_text_value(self.__dico_exploitant["NomResponsableDossier"], "NomResponsableDossier")
            if "DésignationService" in self.__dico_exploitant:
                self.fdf_buffer.add_text_value(self.__dico_exploitant["DésignationService"], "DésignationService")
            if "TelResponsableDossier" in self.__dico_exploitant:
                self.fdf_buffer.add_text_value(self.__dico_exploitant["TelResponsableDossier"], "TelResponsableDossier")
            if "NomSignataire" in self.__dico_exploitant:
                self.fdf_buffer.add_text_value(self.__dico_exploitant["NomSignataire"], "NomSignataire")


            # declarant infos
            self.__dico_declarant = self.__dtdict.xml_demande.dictionnaire()

            if "no_teleservice" in self.__dico_declarant:
                self.fdf_buffer.add_text_value(self.__dico_declarant["no_teleservice"], "NoGU")
            if "dec_denomination" in self.__dico_declarant:
                self.fdf_buffer.add_text_value(self.__dico_declarant["dec_denomination"], "Denomination")
            if "dec_adresse2" in self.__dico_declarant:
                self.fdf_buffer.add_text_value(self.__dico_declarant["dec_adresse2"], "ComplementAdresse")
            if "dec_no_voie" in self.__dico_declarant and "dec_voie" in self.__dico_declarant:
                self.fdf_buffer.add_text_value(self.__dico_declarant["dec_no_voie"] + " " + self.__dico_declarant["dec_voie"], "NoVoie")
            elif "dec_voie" in self.__dico_declarant:
                self.fdf_buffer.add_text_value(self.__dico_declarant["dec_voie"], "NoVoie")
            if "dec_lieudit_bp" in self.__dico_declarant:
                self.fdf_buffer.add_text_value(self.__dico_declarant["dec_lieudit_bp"], "LieuditBP")
            if "dec_code_postal" in self.__dico_declarant:
                self.fdf_buffer.add_text_value(self.__dico_declarant["dec_code_postal"], "CodePostal")
            if "dec_commune" in self.__dico_declarant:
                self.fdf_buffer.add_text_value(self.__dico_declarant["dec_commune"], "Commune")
            if "dec_pays" in self.__dico_declarant:
                self.fdf_buffer.add_text_value(self.__dico_declarant["dec_pays"], "Pays")
            if "dec_affaire" in self.__dico_declarant:
                self.fdf_buffer.add_text_value(self.__dico_declarant["dec_affaire"], "NoAffaireDeclarant")
            if "dec_contact" in self.__dico_declarant:
                self.fdf_buffer.add_text_value(self.__dico_declarant["dec_contact"], "Personne_Contacter")
            if "declaration_at" in self.__dico_declarant:
                declaration_at = dateutil.parser.isoparse(self.__dico_declarant["declaration_at"])

                self.fdf_buffer.add_text_value(declaration_at.strftime("%d"), "JourReception")
                self.fdf_buffer.add_text_value(declaration_at.strftime("%m"), "MoisReception")
                self.fdf_buffer.add_text_value(declaration_at.strftime("%Y"), "AnneeReception")
            if "tvx_commune" in self.__dico_declarant:
                self.fdf_buffer.add_text_value(self.__dico_declarant["tvx_commune"], "CommuneTravaux")
            if "tvx_adresse" in self.__dico_declarant:
                self.fdf_buffer.add_text_value(self.__dico_declarant["tvx_adresse"], "AdresseTravaux")

            self.fdf_buffer.add_text_value(datetime.date.today().strftime("%d"), "JourRecepisse")
            self.fdf_buffer.add_text_value(datetime.date.today().strftime("%m"), "MoisRecepisse")
            self.fdf_buffer.add_text_value(datetime.date.today().strftime("%Y"), "AnneeRecepisse")

            self.fdf_buffer.close()

    def setPrefix(self, prefix):
        self.__prefix = prefix

    def prefix(self):
        return self.__prefix

    def suffix(self):
        return self.__suffix

    def setMapPrefix(self, prefix):
        self.__map_prefix = prefix

    def mapPrefix(self):
        return self.__map_prefix

    def mapSuffix(self):
        return self.__map_suffix

    def dtDict(self):
        return self.__dtdict

    def dicoExploitant(self):
        return self.__dico_exploitant

    def dicoDeclarant(self):
        return self.dtDict().xml_demande.dictionnaire()

    def run2(self):
        """Run method that performs all the real work"""
        print("run2")
        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:



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

    def open_file(self, fullfilename):
        if sys.platform == "win32":
            os.startfile(fullfilename)
        else:
            opener ="open" if sys.platform == "darwin" else "xdg-open"
            subprocess.call([opener, fullfilename])

    def place_folio_tool(self):
        if len(self.dlg.comboBoxLayout.currentText()) > 0:
            layout_name = self.dlg.comboBoxLayout.currentText()
            if DictLayout.layoutExists(layout_name):
                self.__dict_layout.removeLayoutByName(layout_name)
            full_filename = "{}/{}.qpt".format(
                QSettings().value("/DICT/configQPT", os.path.join(QgsApplication.qgisSettingsDirPath(), 'composer_templates'),type=str),
                layout_name)
            self.__dict_layout.loadLayout(full_filename, layout_name, layout_name)
            self.__dict_layout.setCurrentLayoutByName(layout_name)
        self.on_comboboxprintscale_text_changed()
        size = self.__dict_layout.folioPrintSize()
        # Create the map tool using the canvas reference
        self.pointTool = FolioMapTool(self.iface.mapCanvas(), size.x(), size.y(), self.__dict_print_scale)
        self.pointTool.setLayoutName(self.__dict_layout.currentLayout().name())
        self.iface.mapCanvas().setMapTool(self.pointTool)

    def edit_cerfa(self):
        source_path = os.path.join(os.path.dirname(__file__), "formulaire_pdf")
        source_pdf_form = os.path.join(source_path, 'cerfa_14435-04.pdf')
        target_path = Utils.expandVariablesInString(QSettings().value("/DICT/configRep"), True)
        os.makedirs(target_path, exist_ok=True)
        target_form = os.path.join(target_path, self.filename)

        # print("source=", source_pdf_form)
        # print("target=",target_form)
        shutil.copy2(source_pdf_form, target_form + ".pdf")
        try:
            fdf_file = open(target_form + '.fdf', "w", encoding="iso-8859-1")
            for line in self.fdf_buffer.get_buffer():
                print(line, file=fdf_file)
        except Exception as e:
            self.iface.messageBar().pushMessage("Impossible de créer fichier FDF", str(e), Qgis.Info)
        else:
            fdf_file.close()
            pdf = target_form + ".pdf"
            self.open_file(target_form + ".fdf")

    def clean_canvas(self):
        FolioGeometry.removeExistingFolios()
        DICT_geometrie.removeExistingGeometries()
        self.iface.mapCanvas().refresh()

        self.dlg.labelType_demande.setText("")
        self.dlg.labelNo_teleservice.setText("")
        self.dlg.labelAdresse_travaux.setText("")
        self.dlg.labelCommune_travaux.setText("")
        self.dlg.labelDescription_travaux.setText("")

        self.dlg.comboBoxLayout.setCurrentIndex(0)
        QgsExpressionContextUtils.removeProjectVariable(QgsProject.instance(), 'dict_type_demande')
        QgsExpressionContextUtils.removeProjectVariable(QgsProject.instance(), 'dict_no_teleservice')
        QgsExpressionContextUtils.removeProjectVariable(QgsProject.instance(), 'dict_prefix')
        QgsExpressionContextUtils.removeProjectVariable(QgsProject.instance(), 'dict_suffix')
        QgsExpressionContextUtils.removeProjectVariable(QgsProject.instance(), 'dict_map_prefix')
        QgsExpressionContextUtils.removeProjectVariable(QgsProject.instance(), 'dict_map_suffix')
        QgsExpressionContextUtils.removeProjectVariable(QgsProject.instance(), 'dict_filename')
        QgsExpressionContextUtils.removeProjectVariable(QgsProject.instance(), 'dict_map_filename')
        QgsExpressionContextUtils.removeProjectVariable(QgsProject.instance(), 'dict_layout_name')
        QgsExpressionContextUtils.removeProjectVariable(QgsProject.instance(), 'dict_print_scale')
        self.__dict_layout.removeProjectLayouts(True)

    def create_pdf_maps(self):
        #print("create_pdf_maps")
        if FolioGeometry.existsFoliosLayer():
            try:
                folios_layers = QgsProject.instance().mapLayersByName(FolioGeometry.layerName())
                if len(folios_layers) == 1:
                    folios_layer = folios_layers[0]
                    iterator = folios_layer.getFeatures()
                    feature = QgsFeature()
                    if iterator.nextFeature(feature):
                        layout_name = feature.attribute("layout")

                    self.map_filename = QgsExpressionContextUtils.projectScope(QgsProject.instance()).variable('dict_map_filename')

                    self.__dict_layout.setCurrentLayoutByName(layout_name)
                    '''
                    print("current layout", self.__dict_layout.currentLayout())

                    print("custom properties", self.__dict_layout.currentLayout().customProperties())
                    print('atlasRasterFormat', self.__dict_layout.currentLayout().customProperty('atlasRasterFormat'))
                    print('exportWorldFile', self.__dict_layout.currentLayout().customProperty('exportWorldFile'))
                    print('forceVector', self.__dict_layout.currentLayout().customProperty('forceVector'))
                    print('pdfAppendGeoreference',
                          self.__dict_layout.currentLayout().customProperty('pdfAppendGeoreference'))
                    print('pdfCreateGeoPdf', self.__dict_layout.currentLayout().customProperty('pdfCreateGeoPdf'))
                    print('pdfDisableRasterTiles',
                          self.__dict_layout.currentLayout().customProperty('pdfDisableRasterTiles'))
                    print('pdfExportThemes', self.__dict_layout.currentLayout().customProperty('pdfExportThemes'))
                    print('pdfIncludeMetadata', self.__dict_layout.currentLayout().customProperty('pdfIncludeMetadata'))
                    print('pdfLayerOrder', self.__dict_layout.currentLayout().customProperty('pdfLayerOrder'))
                    print('pdfOgcBestPracticeFormat', self.__dict_layout.currentLayout().customProperty('pdfOgcBestPracticeFormat'))
                    print('pdfTextFormat', self.__dict_layout.currentLayout().customProperty('pdfTextFormat'))
                    print('pdfSimplify', self.__dict_layout.currentLayout().customProperty('pdfSimplify'))
                    print('singleFile', self.__dict_layout.currentLayout().customProperty('singleFile'))
                    print('variableNames', self.__dict_layout.currentLayout().customProperty('variableNames'))
                    print('variableValues', self.__dict_layout.currentLayout().customProperty('variableValues'))
                    print('pdfOgcBestPracticeFormat', self.__dict_layout.currentLayout().customProperty('pdfOgcBestPracticeFormat'))
                    '''
                    atlas = self.__dict_layout.currentLayout().atlas()
                    atlas.setCoverageLayer(folios_layer)
                    atlas.setSortFeatures(True)
                    atlas.setSortAscending(True)
                    atlas.setEnabled(True)
                    atlas.setFilenameExpression("@dict_map_filename || '-' || @atlas_featurenumber")
                    '''
                    print("enabled", atlas.enabled())
                    print("coverageLayer()",atlas.coverageLayer())
                    print("count", atlas.count())
                    print("filenameExpression()", atlas.filenameExpression())
                    print("filterFeatures()", atlas.filterFeatures())
                    print("filterExpression()", atlas.filterExpression())
                    print("nameForPage()", atlas.nameForPage(1))
                    print("pageNameExpression()", atlas.pageNameExpression())
                    atlas.setFilenameExpression("dict_map_filename || '-' || @atlas_featureid")
                    print("filenameExpression()", atlas.filenameExpression())
                    '''

                    atlas.updateFeatures()

                    export_settings = QgsLayoutExporter.PdfExportSettings()

                    atlas.layout().setCustomProperty('pdfSimplify', True)
                    atlas.layout().setCustomProperty('pdfIncludeMetadata', True)
                    atlas.layout().setCustomProperty('forceVector', True)
                    atlas.layout().setCustomProperty('singleFile', False)
                    atlas.layout().setCustomProperty('pdfTextFormat', True)

                    atlas.layout().referenceMap().setAtlasDriven(True)
                    atlas.layout().referenceMap().setAtlasScalingMode(QgsLayoutItemMap.Fixed)

                    # disable grids if map is rotated
                    rotated = False
                    for folio in folios_layer.getFeatures():
                        if folio.attributes()[1] != 0:
                            rotated = True
                            break

                    exporter = QgsLayoutExporter(atlas.layout())
                    grid = atlas.layout().referenceMap().grid()

                    if rotated:
                        if grid:
                            grid.setEnabled(False)
                        atlas.layout().setCustomProperty('pdfCreateGeoPdf', False)
                    else:
                        atlas.layout().referenceMap().setMapRotation(0.0)
                        if grid:
                            grid.setEnabled(True)
                        if self.create_geo_pdf == True:
                            atlas.layout().setCustomProperty('pdfCreateGeoPdf', True)

                    no_teleservice = QgsExpressionContextUtils.projectScope(QgsProject.instance()).variable('dict_no_teleservice')
                    type_demande = QgsExpressionContextUtils.projectScope(QgsProject.instance()).variable('dict_type_demande')
                    target_path = Utils.expandVariablesInString(QSettings().value("/DICT/configRep"), True)
                    os.makedirs(target_path, exist_ok=True)
                    full_filename = Utils.resolve(self.map_filename + ".pdf", target_path)

                    if atlas.layout().customProperty('singleFile') == True:
                        # création un seul fichier
                        result = exporter.exportToPdf(
                            atlas,
                            Utils.resolve(self.map_filename + ".pdf", target_path),
                            QgsLayoutExporter.PdfExportSettings()
                            )
                        if result[0] == QgsLayoutExporter.Success:
                            msg1 = "Créer les plans PDF:"
                            msg2 = "Plans pour " + type_demande + " " + no_teleservice + " créés dans <a href=\"{}\">{}</a>".format(
                                QUrl.fromLocalFile(full_filename).toString(), QDir.toNativeSeparators(full_filename))
                            self.iface.messageBar().pushMessage(msg1, msg2, Qgis.Success, 10)
                        else:
                            msg1 = "Créer les plans PDF:"
                            msg2 = "Erreur " + str(result[0]) + "  lors de la création des plans pour " + type_demande + " " + no_teleservice
                            self.iface.messageBar().pushMessage(msg1, msg2, Qgis.Critical, 10)
                    else:
                        # création un fichier par folio
                        progressMessageBar = self.iface.statusBarIface()
                        progress = QProgressBar(progressMessageBar)
                        progress.setMaximum(atlas.count())
                        progress.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                        progressMessageBar.layout().addWidget(progress)
                        self.iface.statusBarIface().addPermanentWidget(progress, Qgis.Info)
                        '''
                        # Create and exporter Layout for each layout generate with Atlas
                        exporter = QgsLayoutExporter(atlas.layout())
                        export_settings = QgsLayoutExporter.PdfExportSettings()
                        # For 0 to Number of features in Atlas Selection
                        '''
                        atlas.beginRender()
                        atlas.first()
                        nb_errors = 0
                        for i in range(0, atlas.count()):
                            progress.setValue(i)
                            self.iface.statusBarIface().showMessage("Plan #{} sur {} pour {} {}".format(i+1, atlas.count(), type_demande, no_teleservice))
                            exporter = QgsLayoutExporter(atlas.layout())

                            # create PDF's File
                            full_filename = Utils.resolve(atlas.currentFilename() + ".pdf", target_path)
                            print("---- hide coverage ", atlas.hideCoverage())
                            result = exporter.exportToPdf(full_filename, QgsLayoutExporter.PdfExportSettings())
                            print("1")
                            print(target_path)
                            print(no_teleservice)
                            print(type_demande)
                            print("i", i)
                            if result == QgsLayoutExporter.Success:
                                self.iface.statusBarIface().showMessage("Plan #{} pour {} {} créé".format(i+1, type_demande, no_teleservice))
                            else:
                                nb_errors += 1
                                self.iface.statusBarIface().showMessage(
                                    "Erreur à la création du plan #{} sur {} pour {} {} sur {}".format(i+1, atlas.count(), type_demande, no_teleservice))
                            atlas.next()
                        atlas.endRender()
                        self.iface.statusBarIface().clearMessage()
                        self.iface.statusBarIface().removeWidget(progress)

                    if nb_errors == 0:
                        msg1 = "Créer les plans PDF:"
                        msg2 = "Plans pour " + type_demande + " " + no_teleservice + " créés dans <a href=\"{}\">{}</a>".format(
                            QUrl.fromLocalFile(target_path).toString(), QDir.toNativeSeparators(target_path))
                        self.iface.messageBar().pushMessage(msg1, msg2, Qgis.Success, 10)
                    else:
                        msg1 = "Créer les plans PDF:"
                        msg2 = "Erreurs  lors de la création des plans pour " + type_demande + " " + no_teleservice
                        self.iface.messageBar().pushMessage(msg1, msg2, Qgis.Critical, 10)

            except Exception as e:
                msg1 = "Folios introuvables:"
                msg2 = str(e)
                self.iface.messageBar().pushMessage(msg1, msg2, Qgis.Critical, 10)

