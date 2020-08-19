# -*- coding:utf-8 -*-
'''
/***************************************************************************
 folio_map_tool.py

 Folio map tool class allows to place a layout frame on map


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
from PyQt5.QtCore import Qt

from qgis.core import QgsProject, QgsWkbTypes, QgsPointXY, QgsGeometry, QgsRectangle, QgsExpressionContextUtils
from qgis.gui import QgsMapTool, QgsMapToolEmitPoint, QgsRubberBand

from .folio_geometry import FolioGeometry

class FolioMapTool(QgsMapToolEmitPoint):

    '''
    La création d'un folio de mise en page, se fait en 3 étapes:
    step 1: positionner le folio
    step 2: orienter le folio (clic droit place le folio sans rotation)
    step 3: positionner définitivement le folio
    '''

    def __init__(self, canvas, size_x, size_y, print_scale):
        self.canvas = canvas
        QgsMapToolEmitPoint.__init__(self, self.canvas)
        self.rubberBand = QgsRubberBand(self.canvas, QgsWkbTypes.PolygonGeometry)
        self.rubberBand.setStrokeColor(Qt.black)
        self.rubberBand.setWidth(2)

        QgsExpressionContextUtils.setProjectVariable(QgsProject.instance(), 'dict_print_scale', print_scale)
        self.__printScale = print_scale
        self.__size_x = size_x
        self.__size_y = size_y
        self.updateSizePoint()

        self.startPoint = QgsPointXY(0, 0)

        self.__layoutName = ''
        QgsExpressionContextUtils.setProjectVariable(QgsProject.instance(), 'dict_layout_name', self.__layoutName)
        self.__zRotation = 0.0
        self.folio_geometry = FolioGeometry()

        self.reset()

    def reset(self):
        self.startPoint = QgsPointXY(0,0)
        self.isEmittingPoint = True
        self.__zRotation = 0
        self.step = 1

    def setLayoutName(self, layout_name):
        #print('FolioMapTool.setLayoutName()', layout_name)
        self.__layoutName = layout_name
        QgsExpressionContextUtils.setProjectVariable(QgsProject.instance(), 'dict_layout_name', layout_name)

    def setPrintScale(self, print_scale):
        #print('FolioMapTool.setPrintScale()', print_scale)
        self.__printScale = print_scale
        QgsExpressionContextUtils.setProjectVariable(QgsProject.instance(), 'dict_print_scale', print_scale)
        self.updateSizePoint()

    def setSize(self, size_x, size_y):
        #print("FolioMapTool.setSize()", self.__size_x, self.__size_y)
        self.__size_x = size_x
        self.__size_y = size_y
        self.updateSizePoint()

    def updateSizePoint(self):
        self.__sizePoint = QgsPointXY(self.__size_x * self.__printScale, self.__size_y * self.__printScale)
        #print("FolioMapTool.updateSizePoint()", self.__sizePoint.x(), self.__sizePoint.y())

    '''
    def canvasClicked(self, point, button):
        if self.step == 1:
            step = 2
        elif step == 2:
            step = 3

    def canvasPressEvent(self, e):
        self.startPoint = self.toMapCoordinates(e.pos())
        self.endPoint = self.startPoint
        self.isEmittingPoint = True
        self.showRect(self.startPoint, self.endPoint)
    '''

    def canvasReleaseEvent(self, e):
        if e.button() == Qt.RightButton:
            self.__zRotation = 0
            if self.step == 2:
                self.step = 3
                self.showRect(self.startPoint, self.__sizePoint, self.__zRotation)
                self.folio_geometry.addFolio(self._geom, self.__printScale, self.__layoutName, self.__zRotation )
                self.rubberBand.reset(QgsWkbTypes.PolygonGeometry)
            else:
                self.step = 1
        else:
            if self.step == 1:
                self.startPoint = self.toMapCoordinates(e.pos())
                self.__zRotation = 0
                self.step = 2
            elif self.step == 2:
                self.__zRotation = self.startPoint.azimuth(self.toMapCoordinates(e.pos()))
                self.step = 3
            elif self.step == 3:
                self.folio_geometry.addFolio(self._geom, self.__printScale, self.__layoutName, self.__zRotation )
                self.rubberBand.reset(QgsWkbTypes.PolygonGeometry)

    def canvasMoveEvent(self, e):
        if not self.isEmittingPoint:
            return

        if self.step == 2:
            self.__zRotation = self.startPoint.azimuth(self.toMapCoordinates(e.pos()))
        else:
            self.startPoint = self.toMapCoordinates(e.pos())

        self.showRect(self.startPoint, self.__sizePoint, self.__zRotation)

    def showRect(self, startPoint, sizePoint, rotation):
        self.rubberBand.reset(QgsWkbTypes.PolygonGeometry)

        endPoint = QgsPointXY(startPoint.x() + self.__sizePoint.x(), startPoint.y() + self.__sizePoint.y())

        rect = QgsRectangle(self.startPoint, endPoint)
        self._geom = QgsGeometry.fromRect(rect)

        self._geom.rotate(self.__zRotation, self.startPoint)
        vertices = self._geom.vertices()
        while vertices.hasNext():
            pt = QgsPointXY(vertices.next())
            update = False if vertices.hasNext() else True
            self.rubberBand.addPoint(pt, update)

        self.rubberBand.show()

    def deactivate(self):
        self.rubberBand.reset(QgsWkbTypes.PolygonGeometry)
        QgsMapTool.deactivate(self)
        self.deactivated.emit()