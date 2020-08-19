#!/usr/bin/env python
# -*- coding:utf-8 -*-

from qgis.core import Qgis
from qgis.utils import iface
from .DICT_geometrie import DICT_geometrie

from .xml_consultation_reseaux import XmlConsultationReseaux

from dateutil import parser
import tempfile
import os
import sys
import datetime
import subprocess

class DICT_xml(object):
    def __init__(self, xml_file):
        self.xml_demande = XmlConsultationReseaux()
        self.xml_filename = xml_file

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
            self.__geom = DICT_geometrie(self.xml_demande.emprise_gml_geom(), self.xml_demande.emprise_epsg())
            err_msg = "Erreur suppression emprises existantes"
            self.__geom.removeExistingGeometries()
            err_msg = "Erreur ajout emprise"
            self.__geom.addFeature(self.xml_demande.type_demande(), self.xml_demande.no_teleservice())
        except Exception as e:
            iface.messageBar().pushMessage(err_msg, str(e), Qgis.Critical)
            return

    def geometry(self):
        return self.__geom.empriseGeometry()

