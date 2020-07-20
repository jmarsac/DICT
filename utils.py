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
import os

class Utils(object):
    """QGIS Plugin utils."""

    def __init__(self):
        """Constructor."""
        print('__init__')


    @classmethod
    def resolve(cls, name, basepath=None):
        if not basepath:
            basepath = os.path.dirname(os.path.realpath(__file__))
        return os.path.join(basepath, name)