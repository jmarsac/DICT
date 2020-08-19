# -*- coding:utf-8 -*-
'''
/***************************************************************************
 dict_layout.py

 DictLayout class allows to manage layouts for DTDICT answers


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
from PyQt5.QtCore import QSizeF, QFileInfo, QSettings
from qgis.core import Qgis, QgsApplication, QgsProject, QgsLayout, QgsLayoutItemMap, QgsExpressionContextUtils, QgsPointXY
from .utils import Utils

import os, shutil

class DictLayout:
    DICT_LAYOUT_PREFIX = "DICT"
    TA_DICT_LAYOUT_PREFIX = "TA_DICT"

    def __init__(self):
        """Constructor"""
        self.__layout = None
        self.__refMap = None

    @classmethod
    def isDictLayoutName(cls, layout_name, check_extension:bool=False):
        if check_extension:
            filename, extension = os.path.splitext(layout_name)
            if not extension.lower() == ".qpt":
                return False

        if layout_name.upper().startswith(cls.DICT_LAYOUT_PREFIX):
            return True
        else:
            return False

    @classmethod
    def isTaDictLayoutName(cls, layout_name, check_extension:bool=False):
        if check_extension:
            filename, extension = os.path.splitext(layout_name)
            if not extension.lower() == ".qpt":
                return False

        if layout_name.upper().startswith(cls.TA_DICT_LAYOUT_PREFIX):
            return True
        else:
            return False

    @classmethod
    def layoutExists(cls, layout_name):
        projectInstance = QgsProject.instance()
        manager = projectInstance.layoutManager()
        layouts_list = manager.printLayouts()

        for layout in layouts_list:
            # to be used by DICT plugin, layout name must start with 'dict' (case insensitive)
            if layout.name().lower() == layout_name.lower():
                return True

        return False

    @classmethod
    def init_templates(cls, reset_all:bool=False):
        #print("init_templates")
        templates_dir = QSettings().value("/DICT/configQPT",
                          os.path.join(QgsApplication.qgisSettingsDirPath(), 'composer_templates'), type=str)
        os.makedirs(templates_dir, exist_ok=True)

        templates = [f.name for f in os.scandir(templates_dir) if f.is_file() and (cls.isDictLayoutName(f.name) or cls.isTaDictLayoutName(f.name))]
        if len(templates) == 0 or reset_all == True:
            to_copy = True
        else:
            to_copy = False

        if to_copy:
            templates = [f.name for f in os.scandir(templates_dir) if f.is_file() and (cls.isDictLayoutName(f.name) or cls.isTaDictLayoutName(f.name))]
            for t in templates:
                os.remove(os.path.join(templates_dir, t))

            source_path = Utils.resolve('layouts')
            templates = [f.name for f in os.scandir(source_path) if f.is_file() and (cls.isDictLayoutName(f.name) or cls.isTaDictLayoutName(f.name))]
            for t in templates:
                shutil.copy2(os.path.join(source_path, t), templates_dir)

    def loadTemplates(self, cbox=None):
        projectInstance = QgsProject.instance()
        manager = projectInstance.layoutManager()
        layouts_list = manager.printLayouts()
        if cbox is not None:
            cbox.clear()
            set_index = False

        profile_dir = QgsApplication.qgisSettingsDirPath()
        templates_dir = os.path.join(profile_dir, 'composer_templates')
        os.makedirs(templates_dir, exist_ok=True)

        # Search the templates folder and add files to templates list and sort it
        templates = [f.name for f in os.scandir(templates_dir) if f.is_file()]
        templates.reverse()

        # Get the project file name and if it exist the project title. Use for Title suggestion
        project_file_name = QFileInfo(QgsProject.instance().fileName()).baseName()
        project_title = QgsProject.instance().title()
        if project_title == '':
            project_title = project_file_name

        # Add all the templates from the list to the listWidget (only add files with *.qpt extension and prefixed
        # with 'dict' (case unsensitive))
        for template in templates:
            if self.isDictLayoutName(template, True):
                if cbox is not None:
                    filename, extension = os.path.splitext(template)
                    cbox.addItem(filename)
                    set_index = True

    # Python function that do the main work of setting up the print layout
    # The code in the function can work stand alone if you use the commented variables and edit their values
    def loadLayout(self, template_source, layout_name, title_text):
        """ Generate the layout """
        from qgis.core import (QgsProject,
                               QgsPrintLayout,
                               QgsReadWriteContext)
        from qgis.utils import iface
        from PyQt5.QtXml import QDomDocument

        # template_source = '/home/user/Document/Template.qpt'
        # layout_name = 'NewLayout'
        # title_text = 'New Title'

        # Create objects lm = layout manager, l = print layout
        lm = QgsProject.instance().layoutManager()
        l = QgsPrintLayout(QgsProject.instance())
        l.initializeDefaults()

        # Load template file and load it into the layout (l)
        template_file = open(template_source, 'r+', encoding='utf-8')
        template_content = template_file.read()
        template_file.close()
        document = QDomDocument()
        document.setContent(template_content)
        context = QgsReadWriteContext()
        l.loadFromTemplate(document, context)

        # Give the layout a name (must be unique)
        l.setName(layout_name)

        '''
        # Get current canvas extent and apply that to all maps (items) in layout
        # Replace any text "{{title}}" in any layout label with the dialog Title text
        canvas = iface.mapCanvas()
        for item in l.items():
            if item.type() == 65639:  # Map
                item.zoomToExtent(canvas.extent())
            if item.type() == 65641:  # Label
                item.setText(item.text().replace('{{title}}', title_text))
        '''
        # Add layout to layout manager
        l.refresh()
        lm.addLayout(l)

    def loadLayouts(self, cbox=None):
        projectInstance = QgsProject.instance()
        manager = projectInstance.layoutManager()
        layouts_list = manager.printLayouts()
        if cbox is not None:
            cbox.clear()
            set_index = False

        for layout in layouts_list:
            if self.isDictLayoutName(layout.name()):
                if cbox is not None:
                    cbox.addItem(layout.name())
                    set_index = True
                page = layout.pageCollection().pages()[0]
                '''
                map_item = layout.referenceMap()
                print("=========================")
                print(layout.name())
                print("displayName",map_item.displayName())
                print("map_item.sizeWithUnits()", map_item.sizeWithUnits().width(), map_item.sizeWithUnits().height())
                print("map_item.fixedSize()", map_item.fixedSize())
                print("displayName",map_item.displayName())
                print("atlasDriven",map_item.atlasDriven())
                print("atlasMargin",map_item.atlasMargin())
                print("atlasScalingMode",map_item.atlasScalingMode())
                print("extent",map_item.extent())
                print("scale",map_item.scale())
                print("mapRotation",map_item.mapRotation())
                print("presetCrs",map_item.presetCrs())
                print(".........................")
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

    def removeLayoutByName(self, layout_name):
        projectInstance = QgsProject.instance()
        manager = projectInstance.layoutManager()
        for layout in manager.printLayouts():
            if layout.name() == layout_name:
                if self.__layout is not None and self.__layout.name == layout_name:
                    self.__layout = None
                manager.removeLayout(layout)
                break;

        if not self.__layout:
            for layout in manager.printLayouts():
                self.__layout = layout
                break

    def removeProjectLayouts(self, remove_ta:bool=False):
        projectInstance = QgsProject.instance()
        manager = projectInstance.layoutManager()
        self.__layout = None
        for layout in manager.printLayouts():
            if self.isDictLayoutName(layout.name()):
                manager.removeLayout(layout)
            elif remove_ta and self.isTaDictLayoutName(layout.name()):
                manager.removeLayout(layout)

    def setCurrentLayoutByName(self, layout_name):
        projectInstance = QgsProject.instance()
        manager = projectInstance.layoutManager()
        for layout in manager.printLayouts():
            if layout.name() == layout_name:
                self.__layout = layout
                self.__refMap = layout.referenceMap()
                #print("setCurrentLayoutByName()", layout.name())
                break;

    def setPrintScale(self, print_scale):
        QgsExpressionContextUtils.setLayoutVariable(self.__layout, 'dict_print_scale', print_scale)
        self.__refMap.setScale(print_scale)

    def currentLayout(self):
        #print("currentLayout()", self.__layout.name() if self.__layout else 'None')
        return self.__layout

    def referenceMap(self):
        return self.__refMap

    def folioPrintSize(self):
        h = self.__refMap.sizeWithUnits().height()
        w = self.__refMap.sizeWithUnits().width()
        k = 0.001
        return QgsPointXY(w * k, h * k)

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

