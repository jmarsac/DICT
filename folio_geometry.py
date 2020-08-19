# -*- coding:utf-8 -*-
'''
/***************************************************************************
 folio_geometry.py

 FolioGeometry class allows to add layout frame geometry to 
 "Folios de mise en page" memory layer


        begin                : 2020-06-02
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
from qgis.core import *
from qgis.gui import *
from qgis.utils import iface
from PyQt5.QtCore import *
from PyQt5.QtGui import QPainter, QFont
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtWidgets import QMessageBox
from .DICT_dialog_composer import DICTDialogComposer
from math import ceil, pow
from osgeo import ogr
import os, math


class FolioGeometry(object):

    __layerName = "Folios"

    def __init__(self, epsg=2154):

        self._epsg = epsg
        self._geom = []
        self._features = []
        self.__memLayer = None
        self.__loadExistingFolios(self.__layerName)

    @classmethod
    def foliosLayer(cls):
        layers = QgsProject.instance().mapLayersByName(cls.__layerName)
        return layers[0]

    @classmethod
    def layerName(cls):
        return cls.__layerName

    @classmethod
    def existsFoliosLayer(cls):
        #print("FolioGeometry.__layerName", cls.__layerName)
        for layer in QgsProject.instance().mapLayersByName(cls.__layerName):
            return True
        return False

    @classmethod
    def removeExistingFolios(cls):
        for layer in QgsProject.instance().mapLayersByName(cls.__layerName):
            QgsProject.instance().removeMapLayer(layer.id())

    def __loadExistingFolios(self, layer_name):
        try:
            memLayers = QgsProject.instance().mapLayersByName(layer_name)
            if len(memLayers) == 1:
                self.__memLayer = memLayers[0]
                print("Loading existing folios...")
        except Exception as e:
            print(str(e))

    def __addFoliosLayer(self, layer_name, size):
        if self.__memLayer is None:
            vl = "polygon?crs=epsg:" + str(self._epsg) + "&index=yes"
            fields = QgsFields()
            fields.append(QgsField("layout", QVariant.String ))
            fields.append(QgsField("print_scale", QVariant.Int ))
            fields.append(QgsField("z_rotation", QVariant.Double ))
            self.__memLayer = QgsVectorLayer(vl, layer_name, "memory")
            self.__memLayer.dataProvider().addAttributes(fields.toList())

            # set Folios feature id as label on frame center
            pal_layer = QgsPalLayerSettings()
            pal_layer.fieldName = '$id'
            pal_layer.isExpression = True
            pal_layer.enabled = True
            pal_layer.placement = QgsPalLayerSettings.OverPoint
            prop_coll = QgsPropertyCollection("properties")
            prop = QgsProperty()
            prop.setField("z_rotation")
            prop_coll.setProperty(QgsPalLayerSettings.LabelRotation, prop)

            font = QFont("Tahoma", 10, QFont.Normal)
            font.setItalic(False)
            text_format = QgsTextFormat().fromQFont(font)
            text_format.setSize(size)
            text_format.setSizeUnit(QgsUnitTypes.RenderMapUnits)
            text_format.setSizeMapUnitScale(QgsMapUnitScale())
            pal_layer.setFormat(text_format)

            prop_coll.setProperty(QgsPalLayerSettings.Italic, QgsProperty.fromValue(False))
            prop_coll.setProperty(QgsPalLayerSettings.AlwaysShow, QgsProperty.fromValue(True))

            pal_layer.setDataDefinedProperties(prop_coll)
            context = QgsExpressionContext()
            context.appendScope(QgsExpressionContextUtils.globalScope())
            context.appendScope(QgsExpressionContextUtils.projectScope(QgsProject.instance()))
            labels = QgsVectorLayerSimpleLabeling(pal_layer)
            self.__memLayer.setLabeling(labels)
            self.__memLayer.setLabelsEnabled(True)

            QgsProject.instance().addMapLayer(self.__memLayer)


    def addFolio(self, geom, print_scale, layout, z_rotation):
        if self.__memLayer is None:
            area = geom.area()
            size = math.sqrt(area) * 0.75
            self.__addFoliosLayer(self.__layerName, size)

        self.__memLayer.startEditing()
        pr = self.__memLayer.dataProvider()

        nb = 0
        self._features.clear()
        self._features.append(QgsFeature())
        self._features[0].initAttributes(3)
        self._features[0].setAttribute(0, layout)
        self._features[0].setAttribute(1, print_scale)
        self._features[0].setAttribute(2, z_rotation)

        layerCRSSrsid = self.__memLayer.crs().authid()
        projectCRSSrsid = iface.mapCanvas().mapSettings().destinationCrs().authid()

        sourceCrs = QgsCoordinateReferenceSystem(projectCRSSrsid)
        targetCrs = QgsCoordinateReferenceSystem(layerCRSSrsid)
        tr = QgsCoordinateTransform(sourceCrs, targetCrs, QgsProject.instance())
        geom.transform(tr)

        self._features[nb].setGeometry(geom)
        nb += 1

        pr.addFeatures(self._features)
        self.__memLayer.commitChanges()
        self.__memLayer.updateExtents()
        prop = self.__memLayer.renderer().symbol().symbolLayers()[0].properties()
        prop['color'] = '0,0,255,10'
        self.__memLayer.renderer().setSymbol(QgsFillSymbol.createSimple(prop))

        '''
        self._geomBB = geomBB.boundingBox()
        mc.setExtent(self._geomBB)
        mc.zoomScale(mc.scale() * 2)
        '''

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
