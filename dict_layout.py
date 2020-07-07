# -*- coding:utf-8 -*-
'''
/***************************************************************************
 layout.py

 Layout class allows to manage layouts for DTDICT answers


        begin                : 2020-06-22
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
from PyQt5.QtCore import QSizeF
from qgis.core import Qgis, QgsProject, QgsLayout, QgsLayoutItemMap, QgsRectangle, QgsPointXY

class DictLayout:
    def __init__(self):
        """Constructor"""
        self.__layout = None
        self.__refMap = None

    def loadLayouts(self, cbox=None):
        projectInstance = QgsProject.instance()
        manager = projectInstance.layoutManager()
        layouts_list = manager.printLayouts()
        if cbox is not None:
            cbox.clear()
            set_index = False

        for layout in layouts_list:
            # to be used by DICT plugin, layout name must start with 'dict' (case insensitive)
            if layout.name().lower()[0:4] == 'dict':
                if cbox is not None:
                    cbox.addItem(layout.name())
                    set_index = True
                page = layout.pageCollection().pages()[0]
                map_item = QgsLayoutItemMap(layout)
                '''
                print(map_item)
                print("displayName",map_item.displayName())
                print("atlasDriven",map_item.atlasDriven())
                print("atlasMargin",map_item.atlasMargin())
                print("atlasScalingMode",map_item.atlasScalingMode())
                print("extent",map_item.extent())
                print("scale",map_item.scale())
                print("mapRotation",map_item.mapRotation())
                print("presetCrs",map_item.presetCrs())
                print("delta",dx,dy)
                print("delta",dx / ref_map.scale(), dy / ref_map.scale())
                print("ref_map.rotation", ref_map.rotation())
                print("ref_map.scale", ref_map.scale())
                '''
                if self.__layout is None:
                    self.__layout = layout
                    self.__refMap = layout.referenceMap()

        if cbox is not None and set_index == True:
            cbox.setCurrentIndex(0)

    def setCurrentLayoutByName(self, layout_name):
        projectInstance = QgsProject.instance()
        manager = projectInstance.layoutManager()
        layouts_list = manager.printLayouts()
        for layout in layouts_list:
            if layout.name() == layout_name:
                self.__layout = layout
                self.__refMap = layout.referenceMap()
                break;

    def currentLayout(self):
        return self.__layout

    def referenceMap(self):
        return self.__refMap

    def folioPrintSize(self):
        dx = self.__refMap.extent().xMaximum() - self.__refMap.extent().xMinimum()
        dy = self.__refMap.extent().yMaximum() - self.__refMap.extent().yMinimum()
        return QgsPointXY(dx / self.__refMap.scale(), dy / self.__refMap.scale())

    def folioLandSize(self):
        dx = self.__refMap.extent().xMaximum() - self.__refMap.extent().xMinimum()
        dy = self.__refMap.extent().yMaximum() - self.__refMap.extent().yMinimum()
        return QgsPointXY(dx, dy)

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

