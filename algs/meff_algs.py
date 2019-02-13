# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Meff
                                 A QGIS plugin
 Computes ecological continuities based on environments permeability
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2018-04-12
        git sha              : $Format:%H$
        copyright            : (C) 2018 by IRSTEA
        email                : mathieu.chailloux@irstea.fr
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

from PyQt5.QtCore import QCoreApplication, QVariant
from qgis.core import QgsProcessing, QgsProcessingAlgorithm, QgsProcessingException
from qgis.core import (QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterExpression,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingProvider,
                       QgsProcessingParameterMultipleLayers,
                       QgsProcessingUtils,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterMatrix,
                       QgsProcessingParameterBoolean,
                       QgsProcessingParameterCrs,
                       QgsProcessingParameterVectorDestination,
                       QgsProcessingParameterFile,
                       QgsProperty,
                       QgsWkbTypes)
from qgis.core import QgsField, QgsFields, QgsFeature, QgsFeatureSink

import processing
import xml.etree.ElementTree as ET

from ..shared import utils, qgsTreatments, qgsUtils
from ..steps import params

class MeffAlgorithmsProvider(QgsProcessingProvider):

    def __init__(self):
        self.alglist = [PrepareLanduseAlgorithm(),
                        PrepareFragmentationAlgorithm(),
                        ApplyFragmentationAlgorithm(),
                        ReportingIntersection(),
                        EffectiveMeshSizeAlgorithm()]
        for a in self.alglist:
            a.initAlgorithm()
        super().__init__()
        
    def unload(self):
        pass
        
    def id(self):
        return "Meff"
        
    def name(self):
        return "Meff"
        
    def longName(self):
        return self.name()
        
    def loadAlgorithms(self):
        for a in self.alglist:
            self.addAlgorithm(a)
            
            
class PrepareLanduseAlgorithm(QgsProcessingAlgorithm):

    INPUT = "INPUT"
    CLIP_LAYER = "CLIP_LAYER"
    SELECT_EXPR = "SELECT_EXPR"
    OUTPUT = "OUTPUT"

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)
        
    def createInstance(self):
        return PrepareLanduseAlgorithm()
        
    def name(self):
        return "prepareLanduse"
        
    def displayName(self):
        return self.tr("1 - Prepare land use data")
        
    def shortHelpString(self):
        return self.tr("TODO")

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                self.tr("Input layer"),
                [QgsProcessing.TypeVectorAnyGeometry]))
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.CLIP_LAYER,
                description=self.tr("Clip layer"),
                types=[QgsProcessing.TypeVectorPolygon],
                optional=True))
        self.addParameter(
            QgsProcessingParameterExpression(
                self.SELECT_EXPR,
                self.tr("Selection expression"),
                "",
                self.INPUT))
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr("Output layer")))
                
    def processAlgorithm(self,parameters,context,feedback):
        # Dummy function to enable running an alg inside an alg
        # def no_post_process(alg, context, feedback):
            # pass
        input = self.parameterAsVectorLayer(parameters,self.INPUT,context)
        feedback.pushInfo("input = " + str(input))
        if input is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))
        feedback.pushDebugInfo("input ok")
        clip_layer = self.parameterAsVectorLayer(parameters,self.CLIP_LAYER,context)
        expr = self.parameterAsExpression(parameters,self.SELECT_EXPR,context)
        select_layer = QgsProcessingUtils.generateTempFilename("select.gpkg")
        feedback.pushDebugInfo("select_layer = " + str(select_layer))
        if clip_layer is None:
            clipped = input
        else:
            clipped_path = QgsProcessingUtils.generateTempFilename('landuseClipped.gpkg')
            qgsTreatments.applyVectorClip(input,clip_layer,clipped_path,context,feedback)
            clipped = qgsUtils.loadVectorLayer(clipped_path)
            utils.debug("clipped  = " + str(clipped))
            #clipped = clipped_path
        selected_path = QgsProcessingUtils.generateTempFilename('landuseSelection.gpkg')
        qgsTreatments.selectGeomByExpression(clipped,expr,selected_path,'landuseSelection')
        #selected = qgsUtils.loadVectorLayer(selected_path)
        #selected = qgsTreatments.extractByExpression(
        #    clipped,expr,'memory:',
        #    context=context,feedback=feedback)
        feedback.pushDebugInfo("selected = " + str(selected_path))
        output = parameters[self.OUTPUT]
        dissolved = qgsTreatments.dissolveLayer(selected_path,output,context=context,feedback=feedback)
        dissolved = None
        return {self.OUTPUT : dissolved}
        
        
class PrepareFragmentationAlgorithm(QgsProcessingAlgorithm):

    INPUT = "INPUT"
    CLIP_LAYER = "CLIP_LAYER"
    SELECT_EXPR = "SELECT_EXPR"
    BUFFER = "BUFFER_EXPR"
    OUTPUT = "OUTPUT"
    
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)
        
    def createInstance(self):
        return PrepareFragmentationAlgorithm()
        
    def name(self):
        return "prepareFragm"
        
    def displayName(self):
        return self.tr("2.1 - Prepare Fragmentation")
        
    def shortHelpString(self):
        return self.tr("This algorithm prepares a fragmentation layer by applying clip, selection and buffer")

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                description=self.tr("Input layer"),
                types=[QgsProcessing.TypeVectorLine]))
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.CLIP_LAYER,
                description=self.tr("Clip layer"),
                types=[QgsProcessing.TypeVectorPolygon],
                optional=True))
        self.addParameter(
            QgsProcessingParameterExpression(
                self.SELECT_EXPR,
                description=self.tr("Selection expression"),
                parentLayerParameterName=self.INPUT,
                optional=True))
        self.addParameter(
            QgsProcessingParameterExpression(
                self.BUFFER,
                description=self.tr("Buffer expression"),
                parentLayerParameterName=self.INPUT,
                optional=True))
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                description=self.tr("Output layer")))
                
    def processAlgorithm(self,parameters,context,feedback):
        # Parameters
        feedback.pushDebugInfo("parameters = " + str(parameters))
        input = self.parameterAsVectorLayer(parameters,self.INPUT,context)
        if input is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))
        clip = self.parameterAsVectorLayer(parameters,self.CLIP_LAYER,context)
        clip_flag = (clip is None)
        select_expr = self.parameterAsExpression(parameters,self.SELECT_EXPR,context)
        #feedback.pushDebugInfo("select_expr : " + str(select_expr))
        #feedback.pushDebugInfo("select_expr type : " + str(type(select_expr)))
        buffer_expr = self.parameterAsExpression(parameters,self.BUFFER,context)
        #buffer_expr = ""
        #feedback.pushDebugInfo("buffer_expr : " + str(buffer_expr))
        #if buffer_expr == "" and input.geometryType() != QgsWkbTypes.PolygonGeometry:
        #    raise QgsProcessingException("Empty buffer with non-polygon layer")
        output = parameters[self.OUTPUT]
        if clip is None:
            clipped = input
        else:
            clipped_path = QgsProcessingUtils.generateTempFilename('fragmClipped.gpkg')
            qgsTreatments.applyVectorClip(input,clip,clipped_path,context,feedback)
            clipped = qgsUtils.loadVectorLayer(clipped_path)
        if select_expr == "":
            selected = clipped
        else:
            selected_path = QgsProcessingUtils.generateTempFilename('tmp.gpkg')
            qgsTreatments.selectGeomByExpression(clipped,select_expr,selected_path,'tmp')
            #selected = qgsUtils.loadVectorLayer(selected_path)
            selected = selected_path
            #selected = qgsTreatments.extractByExpression(clipped,select_expr,'memory:',context,feedback)
        if buffer_expr == "":
            buffered = selected
        else:
            buffer_expr_prep = QgsProperty.fromExpression(buffer_expr)
            buffered = qgsTreatments.applyBufferFromExpr(selected,buffer_expr_prep,output,context,feedback)
        #buffered = qgsTreatments.applyBufferFromExpr(selected,parameters[self.BUFFER],output,context,feedback)
        if buffered == input:
            buffered = qgsUtils.pathOfLayer(buffered)
        return {self.OUTPUT : buffered}
        

        
class ApplyFragmentationAlgorithm(QgsProcessingAlgorithm):

    LANDUSE = "LANDUSE"
    FRAGMENTATION = "FRAGMENTATION"
    CRS = "CRS"
    OUTPUT = "OUTPUT"

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)
        
    def createInstance(self):
        return ApplyFragmentationAlgorithm()
        
    def name(self):
        return "applyFragm"
        
    def displayName(self):
        return self.tr("2.2 - Apply fragmentation")
        
    def shortHelpString(self):
        return self.tr("This algorithm cuts a land use layer with fragmentation data")

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.LANDUSE,
                self.tr("Land use layer"),
                [QgsProcessing.TypeVectorPolygon]))
        self.addParameter(
            QgsProcessingParameterMultipleLayers(
                self.FRAGMENTATION,
                self.tr("Fragmentation layers"),
                QgsProcessing.TypeVectorPolygon))
        self.addParameter(
            QgsProcessingParameterCrs(
                self.CRS,
                description=self.tr("Output CRS"),
                defaultValue=params.defaultCrs))
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr("Output layer")))
                
    def processAlgorithm(self,parameters,context,feedback):
        feedback.pushInfo("begin")
        # Parameters
        feedback.pushInfo("parameters = " + str(parameters))
        landuse = self.parameterAsVectorLayer(parameters,self.LANDUSE,context)
        if landuse is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.LANDUSE))
        fragm_layers = self.parameterAsLayerList(parameters,self.FRAGMENTATION,context)
        #output = self.parameterAsOutputLayer(parameters,self.OUTPUT,context)
        crs = self.parameterAsCrs(parameters,self.CRS,context)
        output = parameters[self.OUTPUT]
        # Merge fragmentation layers
        fragm_path = QgsProcessingUtils.generateTempFilename("fragm.gpkg")
        fragm_layer = qgsTreatments.mergeVectorLayers(fragm_layers,crs,fragm_path)
        feedback.pushDebugInfo("fragm_layer = " + str(fragm_layer))
        if fragm_layer is None:
            raise QgsProcessingException("Fragmentation layers merge failed")
        # Apply difference
        diff_layer = qgsTreatments.applyDifference(
            landuse,fragm_layer,'memory:',
            context=context,feedback=feedback)
        if fragm_layer is None:
            raise QgsProcessingException("Difference landuse/fragmentation failed")
        # Multi to single part
        singleGeomLayer = qgsTreatments.multiToSingleGeom(
            diff_layer,output,
            context=context,feedback=feedback)
        if fragm_layer is None:
            raise QgsProcessingException("Multi to single part failed")
        feedback.pushInfo("end")
        return {self.OUTPUT : singleGeomLayer}
        
                
class ReportingIntersection(QgsProcessingAlgorithm):

    INPUT = "INPUT"
    REPORTING = "REPORTING"
    OUTPUT = "OUTPUT"
    
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)
        
    def createInstance(self):
        return ReportingIntersection()
        
    def name(self):
        return "reportingIntersection"
        
    def displayName(self):
        return self.tr("3.1 - Reporting Intersection")
        
    def shortHelpString(self):
        return self.tr("Computes intersections with each reporting unit")

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                self.tr("Input layer"),
                [QgsProcessing.TypeVectorPolygon]))
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.REPORTING,
                self.tr("Reporting layer"),
                [QgsProcessing.TypeVectorPolygon]))
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr("Output layer")))
                
    def processAlgorithm(self,parameters,context,feedback):
        feedback.pushInfo("begin")
        # Parameters
        source = self.parameterAsVectorLayer(parameters,self.INPUT,context)
        feedback.pushInfo("source = " + str(source))
        if source is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))
        reporting = self.parameterAsVectorLayer(parameters,self.REPORTING,context)
        feedback.pushInfo("reporting = " + str(reporting))
        if reporting is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.REPORTING))
        patch_id_field = QgsField("patch_id", QVariant.Int)
        report_id_field = QgsField("report_id", QVariant.Int)
        area_field = QgsField("area", QVariant.Double)
        report_area_field = QgsField("report_area", QVariant.Double)
        output_fields = QgsFields()
        output_fields.append(patch_id_field)
        output_fields.append(report_id_field)
        output_fields.append(area_field)
        output_fields.append(report_area_field)
        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            output_fields,
            reporting.wkbType(),
            reporting.sourceCrs()
        )
        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))
        # progress step
        nb_feats = source.featureCount() * reporting.featureCount()
        if nb_feats == 0:
            raise QgsProcessingException("Empty layers")
        progress_step = 100.0 / nb_feats
        curr_step = 0
        # gna gna
        for f in source.getFeatures():
            f_geom = f.geometry()
            f_area = f_geom.area()
            patches_area_sum = 0
            for report_feat in  reporting.getFeatures():
                report_geom = report_feat.geometry()
                report_area = report_geom.area()
                if f_geom.intersects(report_geom):
                    intersection = f_geom.intersection(report_geom)
                    intersection_area = intersection.area()
                    #f_area2 = pow(f_area,2)
                    #intersection_area2 = pow(intersection_area,2)
                    f_area_cbc = intersection_area * (f_area - intersection_area)
                    patches_area_sum += f_area_cbc
                    new_f = QgsFeature(output_fields)
                    new_f["patch_id"] = f.id()
                    new_f["report_id"] = report_feat.id()
                    new_f["area"] = f_area
                    new_f["report_area"] = intersection_area
                    new_f.setGeometry(f_geom)
                    sink.addFeature(new_f,QgsFeatureSink.FastInsert)
                    curr_step += 1
                    feedback.setProgress(int(curr_step * progress_step))
            #coh = patches_area_sum / f_area
            #utils.debug("coh = " + str(coh))
        return {self.OUTPUT: dest_id}

        
class EffectiveMeshSizeAlgorithm(QgsProcessingAlgorithm):

    # Algorithm parameters
    INPUT = "INPUT"
    REPORTING = "REPORTING"
    CRS = "CRS"
    CUT_MODE = "CUT_MODE"
    OUTPUT = "OUTPUT"
    
    OUTPUT_GLOBAL_MEFF = "GLOBAL_MEFF"
    
    # Output layer fields
    ID = "fid"
    NB_PATCHES = "nb_patches"
    REPORT_AREA = "report_area"
    INTERSECTING_AREA = "intersecting_area"
    # Main measures
    MESH_SIZE = "effective_mesh_size"
    DIVI = "landscape_division"
    SPLITTING_INDEX = "splitting_index"
    # Auxiliary measures
    COHERENCE = "coherence"
    SPLITTING_DENSITY = "splitting_density"
    NET_PRODUCT = "net_product"
    
    
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)
        
    def createInstance(self):
        return EffectiveMeshSizeAlgorithm()
        
    def name(self):
        return "effectiveMeshSize"
        
    def displayName(self):
        return self.tr("3 - Effective Mesh Size")
        
    def shortHelpString(self):
        return self.tr("Computes effective mesh size and other fragmentation indicators")

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                self.tr("Input layer"),
                [QgsProcessing.TypeVectorPolygon]))
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.REPORTING,
                self.tr("Reporting layer"),
                [QgsProcessing.TypeVectorPolygon]))
        self.addParameter(
            QgsProcessingParameterCrs(
                self.CRS,
                description=self.tr("Output CRS"),
                defaultValue=params.defaultCrs))
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.CUT_MODE,
                self.tr("Cross-boundary connection method")))
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr("Output layer")))
                
    def processAlgorithm(self,parameters,context,feedback):
        feedback.pushInfo("begin")
        # Parameters
        source = self.parameterAsVectorLayer(parameters,self.INPUT,context)
        feedback.pushInfo("source = " + str(source))
        if source is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))
        reporting = self.parameterAsVectorLayer(parameters,self.REPORTING,context)
        feedback.pushInfo("reporting = " + str(reporting))
        if reporting is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.REPORTING))
        crs = self.parameterAsCrs(parameters,self.CRS,context)
        cut_mode = self.parameterAsBool(parameters,self.CUT_MODE,context)
        # CRS reprojection
        source_crs = source.crs().authid()
        reporting_crs = reporting.crs().authid()
        feedback.pushDebugInfo("source_crs = " + str(source_crs))
        feedback.pushDebugInfo("reporting_crs = " + str(reporting_crs))
        feedback.pushDebugInfo("crs = " + str(crs.authid()))
        if source_crs != crs.authid():
            source_path = QgsProcessingUtils.generateTempFilename('source_reproject.gpkg')
            qgsTreatments.applyReprojectLayer(source,crs,source_path,context,feedback)
            source = qgsUtils.loadVectorLayer(source_path)
        if reporting_crs != crs.authid():
            reporting_path = QgsProcessingUtils.generateTempFilename('reporting_reproject.gpkg')
            qgsTreatments.applyReprojectLayer(reporting,crs,reporting_path,context,feedback)
            reporting = qgsUtils.loadVectorLayer(reporting_path)
        # Dissolved
        dissolved_path = QgsProcessingUtils.generateTempFilename('reporting_dissolved.gpkg')
        dissolved = qgsTreatments.dissolveLayer(reporting,dissolved_path,context,feedback)
        dissolved_layer = qgsUtils.loadVectorLayer(dissolved)
        dissolved_feat = None
        for f in dissolved_layer.getFeatures():
            dissolved_feat = f
        assert(dissolved_feat is not None)
        dissolved_geom = dissolved_feat.geometry()
        dissolved_area = dissolved_geom.area() / 1000
        # Output fields
        report_id_field = QgsField(self.ID, QVariant.Int)
        nb_patches_field = QgsField(self.NB_PATCHES, QVariant.Int)
        report_area_field = QgsField(self.REPORT_AREA, QVariant.Double)
        intersecting_area_field = QgsField(self.INTERSECTING_AREA, QVariant.Double)
        mesh_size_field = QgsField(self.MESH_SIZE, QVariant.Double)
        div_field = QgsField(self.DIVI, QVariant.Double)
        split_index_field = QgsField(self.SPLITTING_INDEX, QVariant.Double)
        coherence_field = QgsField(self.COHERENCE, QVariant.Double)
        split_density_field = QgsField(self.SPLITTING_DENSITY, QVariant.Double)
        net_product_field = QgsField(self.NET_PRODUCT, QVariant.Double)
        output_fields = QgsFields()
        output_fields.append(report_id_field)
        output_fields.append(nb_patches_field)
        output_fields.append(report_area_field)
        output_fields.append(intersecting_area_field)
        output_fields.append(mesh_size_field)
        output_fields.append(div_field)
        output_fields.append(split_index_field)
        output_fields.append(coherence_field)
        output_fields.append(split_density_field)
        output_fields.append(net_product_field)
        feedback.pushDebugInfo("fields =  " + str(output_fields.names()))
        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            output_fields,
            reporting.wkbType(),
            #reporting.sourceCrs()
            crs
        )
        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))
        # Algorithm
        # progress step
        nb_feats = reporting.featureCount()
        feedback.pushDebugInfo("nb_feats = " + str(nb_feats))
        if nb_feats == 0:
            raise QgsProcessingException("Empty layer")
        progress_step = 100.0 / nb_feats
        curr_step = 0
        treated_fids = set()
        # first_pass = True
        global_net_product = 0
        global_area = 0
        global_nb_feats = 0
        # gna gna
        for report_feat in reporting.getFeatures():
            report_geom = report_feat.geometry()
            report_area = report_geom.area() / 1000000
            feedback.pushDebugInfo("report_area = " + str(report_area))
            if report_area == 0:
                raise QgsProcessingException("Empty reporting area")
            else:
                feedback.pushDebugInfo("ok")
            global_area += report_area
            report_area_sq = report_area * report_area
            new_f = QgsFeature(output_fields)
            new_f.setGeometry(report_geom)
            new_f[self.ID] = report_feat.id()
            new_f[self.NB_PATCHES] = 0
            new_f[self.REPORT_AREA] = report_area
            new_f[self.NET_PRODUCT] = 0
            new_f[self.COHERENCE] = 0
            net_product = 0
            intersecting_area = 0
            for f in source.getFeatures():
                f_geom = f.geometry()
                intersects_report = f_geom.intersects(report_geom)
                if intersects_report:
                    f_area = f_geom.area() / 1000000
                    intersection = f_geom.intersection(report_geom)
                    intersection_area = intersection.area() / 1000000
                    intersecting_area += intersection_area
                    new_f[self.NB_PATCHES] += 1
                    if cut_mode:
                        net_product += intersection_area * intersection_area
                    else:
                        net_product += f_area * intersection_area
                    new_f[self.COHERENCE] += pow(f_area / report_area,2)
                    if f.id() not in treated_fids:
                        intersection = f_geom.intersection(dissolved_geom)
                        intersection_area = intersection.area() / 1000000
                        if cut_mode:
                            global_net_product += intersection_area * intersection_area
                        else:
                            global_net_product += f_area * intersection_area
                        global_nb_feats += 1
                        treated_fids.add(f.id())
            new_f[self.NET_PRODUCT] = net_product
            new_f[self.INTERSECTING_AREA] = intersecting_area
            new_f[self.COHERENCE] = net_product / report_area_sq
            new_f[self.SPLITTING_DENSITY] = report_area / net_product if net_product > 0 else 0
            new_f[self.MESH_SIZE] = net_product / report_area
            new_f[self.SPLITTING_INDEX] = report_area_sq / net_product if net_product > 0 else 0
            new_f[self.DIVI] = 1 - new_f[self.COHERENCE]
            sink.addFeature(new_f)
            curr_step += 1
            # first_pass = False
            feedback.setProgress(int(curr_step * progress_step))
        if global_area == 0:
            utils.user_error("Empty area for reporting layer")
        feedback.pushDebugInfo("global_nb_feats = " + str(global_nb_feats))
        feedback.pushDebugInfo("global_net_product = " + str(global_net_product))
        feedback.pushDebugInfo("global_area = " + str(global_area))
        global_meff = global_net_product / dissolved_area
        #global_meff = 3
        return {self.OUTPUT: dest_id, self.OUTPUT_GLOBAL_MEFF : global_meff }

        
