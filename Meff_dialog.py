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

import os
import sys
import traceback
from io import StringIO

from PyQt5 import uic
from PyQt5 import QtWidgets
from PyQt5.QtCore import QTranslator, qVersion, QCoreApplication

from qgis.gui import QgsFileWidget

from .shared import utils
from .shared import progress
from .shared import config_parsing
from . import params
from . import landuse
from .shared import log
from . import tabs

#from MeffAbout_dialog import MeffAboutDialog


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'Meff_dialog_base.ui'))


class MeffDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(MeffDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

    def initTabs(self):
        paramsConnector = params.ParamsConnector(self)
        params.params = paramsConnector.model
        self.landuseConnector = landuse.LanduseConnector(self)
        logConnector = log.LogConnector(self)
        progressConnector = progress.ProgressConnector(self)
        progress.progressConnector = progressConnector
        tabConnector = tabs.TabConnector(self)
        self.connectors = {"Params" : paramsConnector,
                           "Log" : logConnector,
                           "Landuse" : self.landuseConnector,
                           "Progress" : progressConnector,
                           "Tabs" : tabConnector}
        self.recomputeParsers()
        
    def initGui(self):
        for k, tab in self.connectors.items():
            tab.initGui()
        
    # Exception hook, i.e. function called when exception raised.
    # Displays traceback and error message in log tab.
    # Ignores CustomException : exception raised from Meff and already displayed.
    def bioDispHook(self,excType, excValue, tracebackobj):
        utils.debug("bioDispHook")
        if excType == utils.CustomException:
            utils.debug("Ignoring custom exception : " + str(excValue))
        else:
            tbinfofile = StringIO()
            traceback.print_tb(tracebackobj, None, tbinfofile)
            tbinfofile.seek(0)
            tbinfo = tbinfofile.read()
            errmsg = str(excType) + " : " + str(excValue)
            separator = '-' * 80
            sections = [separator, errmsg, separator]
            utils.debug(str(sections))
            msg = '\n'.join(sections)
            utils.debug(str(msg))
            final_msg = tbinfo + "\n" + msg
            utils.error_msg(final_msg,prefix="Unexpected error")
        self.mTabWidget.setCurrentWidget(self.logTab)
        progress.progressConnector.clear()
        
    # Connects view and model components for each tab.
    # Connects global elements such as project file and language management.
    def connectComponents(self):
        for k, tab in self.connectors.items():
            tab.connectComponents()
        # Main tab connectors
        self.saveProjectAs.clicked.connect(self.saveModelAsAction)
        self.saveProject.clicked.connect(self.saveModel)
        self.openProject.clicked.connect(self.loadModelAction)
        self.langEn.clicked.connect(self.switchLangEn)
        self.langFr.clicked.connect(self.switchLangFr)
        self.aboutButton.clicked.connect(self.openHelpDialog)
        sys.excepthook = self.bioDispHook
        
    # Initialize or re-initialize global variables.
    def initializeGlobals(self):
        pass  
        
    def initLog(self):
        utils.print_func = self.txtLog.append
        
        # Switch language to english.
    def switchLang(self,lang):
        utils.debug("switchLang " + str(lang))
        plugin_dir = os.path.dirname(__file__)
        lang_path = os.path.join(plugin_dir,'i18n','Meff_' + lang + '.qm')
        #self.langEn.setChecked(True)
        #self.langFr.setChecked(False)
        if os.path.exists(lang_path):
            self.translator = QTranslator()
            self.translator.load(lang_path)
            if qVersion() > '4.3.3':
                utils.debug("Installing translator")
                QCoreApplication.installTranslator(self.translator)
            else:
                utils.internal_error("Unexpected qVersion : " + str(qVersion()))
        else:
            utils.warn("No translation file : " + str(en_path))
        self.retranslateUi(self)
        utils.curr_language = lang
        self.connectors["Tabs"].loadHelpFile()
        
    def switchLangEn(self):
        self.switchLang("en")
        
    def switchLangFr(self):
        self.switchLang("fr")
        
    def openHelpDialog(self):
        utils.debug("openHelpDialog")
        about_dlg = MeffAboutDialog(self)
        about_dlg.show()
        
    
    # Recompute self.parsers in case they have been reloaded
    def recomputeParsers(self):
        self.parsers = [params.params,self.landuseConnector]
        
        # Return XML string describing project
    def toXML(self):
        xmlStr = "<MeffConfig>\n"
        for parser in self.parsers:
            xmlStr += parser.toXML() + "\n"
        xmlStr += "</MeffConfig>\n"
        utils.debug("Final xml : \n" + xmlStr)
        return xmlStr

    # Save project to 'fname'
    def saveModelAs(self,fname):
        self.recomputeParsers()
        xmlStr = self.toXML()
        params.params.projectFile = fname
        utils.writeFile(fname,xmlStr)
        utils.info("Meff model saved into file '" + fname + "'")
        
    def saveModelAsAction(self):
        fname = utils.saveFileDialog(parent=self,msg="Sauvegarder le projet sous",filter="*.xml")
        if fname:
            self.saveModelAs(fname)
        
    # Save project to projectFile if existing
    def saveModel(self):
        fname = params.params.projectFile
        utils.checkFileExists(fname,"Project ")
        self.saveModelAs(fname)
   
    # Load project from 'fname' if existing
    def loadModel(self,fname):
        utils.debug("loadModel " + str(fname))
        utils.checkFileExists(fname)
        config_parsing.setConfigParsers(self.parsers)
        params.params.projectFile = fname
        config_parsing.parseConfig(fname)
        utils.info("Meff model loaded from file '" + fname + "'")
        
    def loadModelAction(self):
        fname = utils.openFileDialog(parent=self,msg="Ouvrir le projet",filter="*.xml")
        if fname:
            self.loadModel(fname)