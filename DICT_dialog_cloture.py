# -*- coding: utf-8 -*-
"""
/***************************************************************************

 DICT_dialog_cloture.py

 DICTDialogCloture dialog class for "Cloturer DT/DICT/DC/ATU"

                              -------------------
        begin                : 2020-08-05
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
from PyQt5 import QtCore, QtGui, uic, QtWidgets

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'DICT_dialog_cloture.ui'))


class DICTDialogCloture(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(DICTDialogCloture, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
