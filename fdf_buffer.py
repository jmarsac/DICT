# -*- coding:utf-8 -*-
'''
/***************************************************************************
 fdf_buffer.py

 FdfBuffer class prepare FDF file in memory

 For FDF specifications see :
 https://www.adobe.com/content/dam/acom/en/devnet/acrobat/pdfs/fdf_data_exchange.pdf

        begin                : 2020-03-07
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

class FdfBuffer:
    def __init__(self):
        """Constructor"""
        self.__fdf_version = "1.4"
        self.__buffer = []

    def open(self,filename):
        self.__buffer.append("%FDF-{}".format(self.__fdf_version))
        self.__buffer.append("%âãÏÓ")
        self.__buffer.append("1 0 obj")
        self.__buffer.append("<</FDF<<")
        self.__buffer.append("/F (" + filename + ")")
        self.__buffer.append("/UF (" + filename + ")")
        self.__buffer.append("/Type /Catalog")
        self.__buffer.append("/Fields[")

    def close(self):
        self.__buffer.append("]>>>>")
        self.__buffer.append("endobj")
        self.__buffer.append("trailer")
        self.__buffer.append("<</Root 1 0 R>>")
        self.__buffer.append("%%EOF")

    def add_checkbox_value(self,true_false,tag_name):
        on_off = "Oui" if true_false == True else "Off"
        self.__buffer.append("<</V({})/T({})>>".format(on_off,tag_name))

    def add_text_value(self, value, tag_name):
        if value is not None and tag_name is not None:
            self.__buffer.append("<</V({})/T({})>>".format(self.__clean_fdf_value(value), tag_name))

    def __clean_fdf_value(self,s_value):
        import re
        # remove non ascii chars
        s_value =  re.sub(r'[^\x00-\x7f]',r'', s_value)
        return s_value.replace("(","{").replace(")","}")

    def get_buffer(self):
        return self.__buffer
