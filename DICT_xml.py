#!/usr/bin/env python
# -*- coding:utf-8 -*-

from qgis.core import Qgis
from qgis.utils import iface
from xml.dom import minidom
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import QMessageBox
from .DICT_geometrie import DICT_geometrie
from .DICT_dialog_wizard import DICTDialogWizard

from .xml_consultation_reseaux import XmlConsultationReseaux

from dateutil import parser
import tempfile
import os
import sys
import datetime
import subprocess

class DICT_xml(object):
    def __init__(self, xml_file):
        msgBox = QMessageBox()
        msgBox.setTextFormat(Qt.RichText)

        self.xml_demande = XmlConsultationReseaux()

        if self.xml_demande.open(xml_file) in ["DT", "DICT", "DC", "ATU"]:
            #print(self.xml_demande.type_demande(), self.xml_demande.no_teleservice())
            self.xml_demande.extract_data()
            #print(self.xml_demande.emprise_epsg())
            #print(self.xml_demande.emprise_dimension())
            #print(self.xml_demande.emprise_gml_geom())
            #print(self.xml_demande.emprise_gml_geom())
            #self.xml_demande.view_dictionnaire()

        try:
            if "taille_des_plans" in self.xml_demande.dictionnaire():
                self._taillePlan = self.xml_demande.dictionnaire()["taille_des_plans"]
            else:
                self.taillePlan = "A4"
            # Dessine la géométrie
            err_msg = "Erreur analyse XML"
            self.geom = DICT_geometrie(self.xml_demande.emprise_gml_geom(),self.xml_demande.emprise_epsg())
            err_msg = "Erreur ajout géométrie"
            self.geom.addGeometrie()
        except Exception as e:
            iface.messageBar().pushMessage(err_msg, str(e), Qgis.Info )
            msgBox.setText(err_msg)
            msgBox.exec_()
            return

    def geometriePDF(self, titre):
        return self.geom.geometriePDF(titre, self._taillePlan)
