# -*- coding: utf-8 -*-
"""
/***************************************************************************
 UTILS
                         utilities class for plugins
                              -------------------
        begin                : 2020-06-19
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
"""
from PyQt5.QtCore import (QSettings, QTranslator, qVersion,
                          QCoreApplication, QDir, QFileInfo,
                          QFile, Qt, QUrl)
from qgis.core import QgsApplication, QgsSettings, QgsProject, QgsExpressionContextUtils, QgsExpressionContext, QgsExpression
from qgis.PyQt.QtCore import QRegularExpression, QRegularExpressionMatch
import os

class Utils(object):
    """QGIS Plugin utils."""

    def __init__(self):
        """Constructor."""
        print('__init__')

    @classmethod
    def stringContainsVariable(cls, str_to_check):
        regex = QRegularExpression("@[a-zA-Z][a-zA-Z0-9_]*")
        return regex.match(str_to_check).hasMatch()

    @classmethod
    def expandVariablesInString(cls, str_to_expand, use_system_separator:bool=False):
        regex = QRegularExpression("@[a-zA-Z][a-zA-Z0-9_]*")
        if regex.match(str_to_expand).hasMatch():
            context = QgsExpressionContext()
            context.appendScope(QgsExpressionContextUtils.globalScope())
            context.appendScope(QgsExpressionContextUtils.projectScope(QgsProject.instance()))
            iter = regex.globalMatch(str_to_expand)
            while iter.hasNext():
                match = iter.next()
                if context.hasVariable(match.captured()[1:]):
                    str_to_expand = str_to_expand.replace(match.captured(), context.variable(match.captured()[1:]))

            return QDir.toNativeSeparators(str_to_expand) if use_system_separator else str_to_expand
        else:
            return str_to_expand

    @classmethod
    def resolve(cls, name, basepath=None):
        if not basepath:
            basepath = os.path.dirname(os.path.realpath(__file__))
        return os.path.join(basepath, name)