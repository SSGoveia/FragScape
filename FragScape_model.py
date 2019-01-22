# -*- coding: utf-8 -*-
"""
/***************************************************************************
 MeffDialog
                                 A QGIS plugin
 This plugin computes mesh effective size
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2018-11-05
        git sha              : $Format:%H$
        copyright            : (C) 2018 by Mathieu Chailloux
        email                : mathieu@chailloux.org
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

from .shared import utils
from .steps import params, landuse, fragm,  reporting

class FragScapeModel:

    def __init__(self):
        self.paramsModel = params.ParamsModel(self)
        self.landuseModel = landuse.LanduseModel(self)
        self.fragmModel = fragm.FragmModel(self)
        self.reportingModel = reporting.ReportingModel(self)
        self.parser_name = "FragScapeModel"
        
    def checkWorkspaceInit(self):
        self.paramsModel.checkWorkspaceInit()
            
    # Returns relative path w.r.t. workspace directory.
    # File separator is set to common slash '/'.
    def normalizePath(self,path):
        return self.paramsModel.normalizePath(path)
            
    # Returns absolute path from normalized path (cf 'normalizePath' function)
    def getOrigPath(self,path):
        return self.paramsModel.getOrigPath(path)
    
    def mkOutputFile(self,name):
        return self.paramsModel.mkOutputFile(name)
        
    def toXML(self,indent=""):
        xmlStr = indent + "<" + self.parser_name
        new_indent = " "
        if self.paramsModel:
            xmlStr += self.paramsModel.toXML(indent=new_indent)
        if self.landuseModel:
            xmlStr += self.landuseModel.toXML(indent=new_indent)
        if self.fragmModel:
            xmlStr += self.fragmModel.toXML(indent=new_indent)
        if self.reportingModel:
            xmlStr += self.reportingModel.toXML(indent=new_indent)
        xmlStr += indent + "</" + self.parser_name + ">"
        
    def fromXMLRoot(self,root):
        for child in root:
            utils.debug("tag = " + str(child.tag))
            if child.tag == self.paramsModel.parser_name:
                self.paramsModel.fromXMLRoot(child)
                self.paramsModel.layoutChanged.emit()
            elif child.tag == self.landuseModel.parser_name:
                self.landuseModel.fromXMLRoot(child)
                self.landuseModel.layoutChanged.emit()
            elif child.tag == self.fragmModel.parser_name:
                self.fragmModel.fromXMLRoot(child)
                self.fragmModel.layoutChanged.emit()
            elif child.tag == self.reportingModel.parser_name:
                self.reportingModel.fromXMLRoot(child)
                self.reportingModel.layoutChanged.emit()
        
    