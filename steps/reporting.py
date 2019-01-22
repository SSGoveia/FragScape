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

from qgis.core import QgsMapLayerProxyModel, QgsField, QgsFeature, QgsProcessingFeedback
from qgis.gui import QgsFileWidget
from PyQt5.QtCore import QVariant
from processing import QgsProcessingUtils

from ..shared import utils, abstract_model, qgsUtils, progress, qgsTreatments
from ..algs import meff_algs
from . import params, fragm

class ReportingModel(abstract_model.DictModel):

    # Configuration slots
    REPORTING = "reporting_layer"
    OUTPUT = "output"

    def __init__(self,fsModel):
        self.parser_name = "Reporting"
        self.fsModel = fsModel
        self.layer = None
        self.outLayer = None
        self.init_fields = ["meff"]
        self.fields = self.init_fields
        super().__init__(self,self.fields)
        #super().__init__(self,self.fields)
                
    def setOutLayer(self,layer):
        self.outLayer = layer
        
    def getOutLayer(self):
        if self.outLayer:
            return self.fsModel.getOrigPath(self.outLayer)
        else:
            return QgsProcessingUtils.generateTempFilename("reportingResults.gpkg")
        
    def mkIntersectionLayer(self):
        pass
        
    def getIntersectionLayerPath(self):
        return self.fsModel.mkOutputFile("reportingIntersection.gpkg")
        
    def getReportingResultsLayerPath(self):
        return self.fsModel.mkOutputFile("reportingResults.gpkg")
        
    # def createIntersectionLayer(self):
        # path = self.getIntersectionLayerPath()
        # qgsUtils.removeVectorLayer(path)
        # landuseFragmPath = self.fsModel.fragmModel.getFinalLayer()
        # landuseFragmlayer = qgsUtils.loadVectorLayer(landuseFragmPath)
        # layer = qgsUtils.createLayerFromExisting(landuseFragmlayer,"reportingIntersection")
        # patch_id_field = QgsField("patch_id", QVariant.Int)
        # report_id_field = QgsField("report_id", QVariant.Int)
        # area = QgsField("area", QVariant.Double)
        # report_area = QgsField("report_area", QVariant.Double)
        # fields = [patch_id_field,report_id_field,area,report_area]
        # layer.dataProvider().addAttributes(fields)
        # layer.updateFields()
        # print("fieldnames = " + str(layer.fields().names()))
        # return layer
        
    # def computeIntersections(self):
        # progress.progressFeedback.setSubText("Intersection with reporting units")
        # landuseFragmPath = self.fsModel.fragmModel.getFinalLayer()
        # landuseFragmlayer = qgsUtils.loadVectorLayer(landuseFragmPath)
        # reporting_layer = self.layer
        # intersection_layer = self.createIntersectionLayer()
        # print("fieldnames = " + str(intersection_layer.fields().names()))
        # intersection_fields = intersection_layer.fields()
        # utils.debug("fields = " + str(intersection_layer.fields().names()))
        # landuse_fragm_feats = landuseFragmlayer.getFeatures()
        # report_feats = reporting_layer.getFeatures()
        # for f in landuseFragmlayer.getFeatures():
            # f_geom = f.geometry()
            # f_area = f_geom.area()
            # patches_area_sum = 0
            # for report_feat in  reporting_layer.getFeatures():
                # report_geom = report_feat.geometry()
                # report_area = report_geom.area()
                # if f_geom.intersects(report_geom):
                    # intersection = f_geom.intersection(report_geom)
                    # intersection_area = intersection.area()
                    # f_area2 = pow(f_area,2)
                    # intersection_area2 = pow(intersection_area,2)
                    # f_area_cbc = intersection_area * (f_area - intersection_area)
                    # patches_area_sum += f_area_cbc
                    # new_f = QgsFeature(intersection_fields)
                    # new_f["patch_id"] = f.id()
                    # new_f["report_id"] = report_feat.id()
                    # new_f["area"] = f_area
                    # new_f["report_area"] = intersection_area
                    # new_f.setGeometry(f_geom)
                    # res = intersection_layer.dataProvider().addFeature(new_f)
                    # if not res:
                        # internal_error("addFeature failed")
                    # intersection_layer.updateExtents()
            # coh = patches_area_sum / f_area
            # utils.debug("coh = " + str(coh))
        # intersection_path = self.getIntersectionLayerPath()
        # qgsUtils.writeVectorLayer(intersection_layer,intersection_path)
        # qgsUtils.loadVectorLayer(intersection_path,loadProject=True)
        
    # def computeResults(self):
        # progress.progressFeedback.setSubText("Results layer creation")
        # intersection_path = self.getIntersectionLayerPath()
        # utils.checkFileExists(intersection_path)
        # intersection_layer = qgsUtils.loadVectorLayer(intersection_path)
        # reporting_layer = self.layer
        # results_path = self.getOutLayer()
        # qgsUtils.removeVectorLayer(results_path)
        # results_layer = qgsUtils.createLayerFromExisting(reporting_layer,results_path)
        # report_id_field = QgsField("report_id", QVariant.Int)
        # nb_patches_field = QgsField("nb_patches", QVariant.Int)
        # area_field = QgsField("area_sq", QVariant.Double)
        # area_cbc_field = QgsField("area_cbc", QVariant.Double)
        # meff_cbc = QgsField("meff_cbc", QVariant.Double)
        # meff_no_cbc = QgsField("meff_no_cbc", QVariant.Double)
        # fields = [report_id_field,nb_patches_field,area_field,area_cbc_field,meff_no_cbc,meff_cbc]
        # results_layer.dataProvider().addAttributes(fields)
        # results_layer.updateFields()
        # total_area = 0
        # report_feats = reporting_layer.getFeatures()
        # for report_feat in report_feats:
            # report_geom = report_feat.geometry()
            # report_area = report_geom.area()
            # if report_area == 0:
                # break
            # new_f = QgsFeature(results_layer.fields())
            # new_f.setGeometry(report_geom)
            # new_f["report_id"] = report_feat["fid"]
            # new_f["nb_patches"] = 0
            # new_f["area_sq"] = 0
            # new_f["area_cbc"] = 0
            # intersecting_feats = [f for f in intersection_layer.getFeatures() if f["report_id"] == report_feat["fid"]]
            # report_sum_area = 0
            # for inter_feat in intersecting_feats:
                # new_f["nb_patches"] += 1
                # new_f["area_sq"] += pow(inter_feat["area"],2)
                # new_f["area_cbc"] += inter_feat["area"] * inter_feat["report_area"]
            # new_f["meff_cbc"] = new_f["area_cbc"] / report_area
            # new_f["meff_no_cbc"] = new_f["area_sq"] / report_area
            # res = results_layer.dataProvider().addFeature(new_f)
            # if not res:
                # internal_error("addFeature failed")
            # results_layer.updateExtents()
        # qgsUtils.writeVectorLayer(results_layer,results_path)
        # qgsUtils.loadVectorLayer(results_path,loadProject=True)
                
    # def runReportingOld(self):
        # progress.progressFeedback.beginSection("Meff results computation")
        # self.computeIntersections()
        # self.computeResults()
        # progress.progressFeedback.endSection()
        
    def runReporting(self):
        reportingMsg = "Reporting layer computation"
        progress.progressFeedback.beginSection(reportingMsg)
        landuseFragmPath = self.fsModel.fragmModel.getFinalLayer()
        results_path = self.getOutLayer()
        parameters = { meff_algs.EffectiveMeshSizeAlgorithm.INPUT : landuseFragmPath,
                       meff_algs.EffectiveMeshSizeAlgorithm.REPORTING : qgsUtils.pathOfLayer(self.layer),
                       meff_algs.EffectiveMeshSizeAlgorithm.CBC_MODE : False,
                       meff_algs.EffectiveMeshSizeAlgorithm.OUTPUT : results_path }
        res = qgsTreatments.applyProcessingAlg(
            "Meff","effectiveMeshSize",parameters,
            context=None,feedback=progress.progressFeedback)
        qgsUtils.loadVectorLayer(res,loadProject=True)
        progress.progressFeedback.endSection()
        
        
    def toXML(self,indent=" "):
        if not self.layer:
            utils.warn("No reporting layer selected")
            return ""
        layerRelPath = self.fsModel.normalizePath(qgsUtils.pathOfLayer(self.layer))
        modelParams = { "layer" : layerRelPath }
        if self.outLayer:
            modelParams["outLayer"] = self.fsModel.normalizePath(self.outLayer)
        xmlStr = super().toXML(indent,modelParams)
        return xmlStr
        
    def fromXMLAttribs(self,attribs):
        if self.REPORTING in attribs:
            self.layer = self.fsModel.getOrigPath(attribs[self.REPORTING])
        if self.OUTPUT in attribs:
            self.model.setOutLayer(attribs[self.OUTPUT])
        
    def fromXMLRoot(self,root):
        self.fromXMLAttribs(root.attrib)
        
class ReportingConnector(abstract_model.AbstractConnector):

    
    def __init__(self,dlg,reportingModel):
        self.dlg = dlg
        self.parser_name = "Reporting"
        self.model = reportingModel
        #reportingModel = ReportingModel()
        super().__init__(reportingModel,self.dlg.resultsView)
        
    def initGui(self):
        self.dlg.reportingLayerCombo.setFilters(QgsMapLayerProxyModel.VectorLayer)
        self.dlg.reportingLayer.setFilter(qgsUtils.getVectorFilters())
        self.dlg.resultsOutLayer.setStorageMode(QgsFileWidget.SaveFile)
        self.dlg.resultsOutLayer.setFilter(qgsUtils.getVectorFilters())
        
    def connectComponents(self):
        super().connectComponents()
        self.dlg.reportingLayerCombo.layerChanged.connect(self.setLayer)
        self.dlg.reportingLayer.fileChanged.connect(self.loadLayer)
        self.dlg.resultsOutLayer.fileChanged.connect(self.model.setOutLayer)
        self.dlg.resultsRun.clicked.connect(self.model.runReporting)
        
    def setLayer(self,layer):
        utils.debug("setLayer " + str(layer.type))
        #self.dlg.reportingLayerCombo.setLayer(layer)
        self.model.layer = layer
    
    def loadLayer(self,path):
        utils.debug("loadLayer")
        loaded_layer = qgsUtils.loadVectorLayer(path,loadProject=True)
        self.dlg.reportingLayerCombo.setLayer(loaded_layer)
        self.model.layer = loaded_layer
        #self.setLayer(loaded_layer)
        
    def updateUI(self):
        if self.model.layer:
            abs_layer = qgsUtils.loadVectorLayer(self.model.layer,loadProject=True)
            self.dlg.reportingLayerCombo.setLayer(abs_layer)
        if self.model.outLayer:
            self.dlg.resultsOutLayer.setFilePath(self.model.outLayer)

    def fromXMLRoot(self,root):
        self.model.fromXMLRoot(root)
        self.updateUI()
        
    def toXML(self,indent=" "):
        return self.model.toXML()
        