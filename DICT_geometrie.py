#!/usr/bin/env python
# -*- coding:utf-8 -*-

from qgis.core import *
from qgis.utils import iface
from PyQt5.QtCore import *
from PyQt5.QtWidgets import QMessageBox
from .DICT_dialog_composer import DICTDialogComposer
from osgeo import ogr
import os


class DICT_geometrie(object):

    __layerName = "Emprise du chantier"

    def __init__(self, gml, epsg=4326):

        msgBox = QMessageBox()
        msgBox.setTextFormat(Qt.RichText)
        self.__layer = None
        self._epsg = epsg
        try:
            self._geom = self.dictGmlGeom2qgisGeom(gml)
        except:
            msgBox.setText("Erreur d'analyse de la géométrie.")
            msgBox.exec_()
            return

    @staticmethod
    def dictGmlGeom2qgisGeom(gml):
        try:
            l = len(gml)
            if l > 0:
                polygons = []
                wkts = []
                for gml_string in gml:
                    wkts.append(ogr.CreateGeometryFromGML(gml_string).ExportToWkt()[8:])
                multi_wkt = "MULTIPOLYGON (" + ",".join(wkts) + ")"
                qgs_geometry = QgsGeometry.fromWkt(multi_wkt)
            else:
                iface.messageBar().pushMessage("Erreur analyse GML", "Le bloc GML est vide", Qgis.Critical)

        except Exception as e:
            qgs_geometry = QgsGeometry()
            iface.messageBar().pushMessage("Erreur analyse GML", str(e) + gml_string, Qgis.Critical )

        return qgs_geometry

    @classmethod
    def removeExistingGeometries(cls):
        for layer in QgsProject.instance().mapLayersByName(cls.__layerName):
            QgsProject.instance().removeMapLayer(layer.id())

    @classmethod
    def empriseLayer(cls):
        return QgsProject.instance().mapLayersByName(cls.__layerName)[0]

    def addFeature(self, type_demande: str=None, no_teleservice: str=None):
        vl = "multipolygon?crs=epsg:" + self._epsg + "&index=yes"
        mem_layer = QgsVectorLayer(vl, self.__layerName, "memory")
        pr = mem_layer.dataProvider()

        fields = QgsFields()
        fields.append(QgsField("type_demande", QVariant.String))
        fields.append(QgsField("no_teleservice", QVariant.String))
        pr.addAttributes(fields.toList())
        feature = QgsFeature(fields)
        if type_demande:
            feature.setAttribute(0, type_demande)
        if no_teleservice:
            feature.setAttribute(1, no_teleservice)
        feature.setGeometry(self._geom)

        pr.addFeatures([feature])
        mem_layer.commitChanges()
        mem_layer.updateExtents()
        prop = mem_layer.renderer().symbol().symbolLayers()[0].properties()
        prop['color'] = '255,0,0,20'
        mem_layer.renderer().setSymbol(QgsFillSymbol.createSimple(prop))
        QgsProject.instance().addMapLayer(mem_layer)

        layerCRSSrsid = mem_layer.crs().authid()
        mc = iface.mapCanvas()
        projectCRSSrsid = mc.mapSettings().destinationCrs().authid()

        sourceCrs = QgsCoordinateReferenceSystem(layerCRSSrsid)
        destCrs = QgsCoordinateReferenceSystem(projectCRSSrsid)
        tr = QgsCoordinateTransform(sourceCrs, destCrs, QgsProject.instance())
        geomBB = QgsGeometry.fromRect(mem_layer.extent())
        geomBB.transform(tr)
        self._geomBB = geomBB.boundingBox()
        mc.setExtent(self._geomBB)
        mc.zoomScale(mc.scale() * 2)
        mem_layer.reload()

    def empriseGeometry(self):
        return self._geom

    def geometriePDF(self, titre, taillePlan):
        # Display layout list
        dlgConfigComposers = DICTDialogComposer(taillePlan)
        dlgConfigComposers.show()
        result = dlgConfigComposers.exec_()

        idx_plan = []

        if result:
            idx_plan = dlgConfigComposers.listComposers.selectedItems()
        # Sortie du plan en PDF
            manager = QgsProject.instance().layoutManager()

        out = []
        if len(idx_plan) > 0:
            for i, idx in enumerate(idx_plan):
                id_plan = dlgConfigComposers.listComposers.row(idx_plan[i])
                layout_name = dlgConfigComposers.layout_listArray[id_plan]
                layout = manager.layoutByName(layout_name)

                # Retrieve the layout's map Item
                mapItem = layout.referenceMap()
                mapItem.zoomToExtent(iface.mapCanvas().extent())
                # Only mean to edit an existing item found so far is getting said item's ID
                # there's the layoutItems() method to get the list of items from a layout
                # but as of now is exclusive to C++ plugins

                # Output
                out_dir = QSettings().value("/DICT/configRep")
                if QDir(out_dir).exists() is False or out_dir is None:
                    out_dir = str(QDir.homePath())

                pdf = os.path.join(out_dir,
                    QSettings().value("/DICT/prefPlan", "") + titre + \
                    QSettings().value("/DICT/sufPlan", "") + "_" + str(i) + ".pdf")

                if QFile.exists(pdf):
                    pdf = os.path.join(out_dir,
                        QSettings().value("/DICT/prefPlan", "") + "plan_" + titre + \
                        QSettings().value("/DICT/sufPlan", "") + "_" + str(i) + ".pdf")

                exported_layout = QgsLayoutExporter(layout)
                exported_layout.exportToPdf(pdf, QgsLayoutExporter.PdfExportSettings())
                out.append(pdf)

        return out
