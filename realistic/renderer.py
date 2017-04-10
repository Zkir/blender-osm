"""
This file is part of blender-osm (OpenStreetMap importer for Blender).
Copyright (C) 2014-2017 Vladimir Elistratov
prokitektura+support@gmail.com

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import os, math
import bpy
from renderer import Renderer
from util.blender import makeActive, loadParticlesFromFile, getBmesh


class AreaRenderer:
    
    baseAssetPath = "assets/base.blend"
    
    calculateArea = False
    
    def __init__(self):
        self.assetPath = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), self.baseAssetPath
        )
    
    def finalizeBlenderObject(self, layer, app):
        terrain = app.terrain
        obj = layer.obj
        # add modifiers, slice flat mesh
        if layer.area:
            if not terrain.envelope:
                terrain.createEnvelope()
            Renderer.addBoolenModifier(obj, terrain.envelope)
            makeActive(obj)
            bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Boolean")
            # calculate area after the BOOLEAND modifier has been applied
            if self.calculateArea:
                bm = getBmesh(obj)
                layer.surfaceArea = sum(face.calc_area() for face in bm.faces)
                bm.free()
            Renderer.slice(obj, terrain, app)
            Renderer.addShrinkwrapModifier(obj, terrain.terrain, layer.swOffset)
            bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Shrinkwrap")
            obj.select = False
        else:
            Renderer.finalizeBlenderObject(obj, layer, app)

    def renderTerrain(self, layer, terrain):
        layerId = layer.id
        obj = layer.obj
        # DYNAMIC_PAINT modifier of <terrain>
        m = terrain.modifiers[-1]
        # create a brush group
        group = bpy.data.groups.new("%s_brush" % layerId)
        # add <obj> to the brush group
        group.objects.link(obj)
        # vertex colors
        bpy.ops.dpaint.surface_slot_add()
        surface = m.canvas_settings.canvas_surfaces[-1]
        surface.name = "%s_colors" % layerId
        # create a target vertex colors layer for dynamically painted vertex colors
        colors = terrain.data.vertex_colors.new(layerId)
        AreaRenderer.prepareDynamicPaintSurface(surface, group, colors.name)
        # vertex weights
        bpy.ops.dpaint.surface_slot_add()
        surface = m.canvas_settings.canvas_surfaces[-1]
        surface.name = "%s_weights" % layerId
        surface.surface_type = 'WEIGHT'
        # create a target vertex group for dynamically painted vertex weights
        weights = terrain.vertex_groups.new(layerId)
        AreaRenderer.prepareDynamicPaintSurface(surface, group, weights.name)
    
    def renderArea(self, layer, app):
        # setup a DYNAMIC_PAINT modifier for <layer.obj> in the brush mode
        obj = layer.obj
        makeActive(obj)
        m = obj.modifiers.new("Dynamic Paint", 'DYNAMIC_PAINT')
        m.ui_type = 'BRUSH'
        bpy.ops.dpaint.type_toggle(type='BRUSH')
        brush = m.brush_settings
        brush.paint_color = (1., 1., 1.)
        brush.paint_source = 'DISTANCE'
        brush.paint_distance = 500.
        brush.use_proximity_project = True
        brush.ray_direction = 'Z_AXIS'
        brush.proximity_falloff = 'CONSTANT'
        obj.hide = True
        # deselect <obj> to ensure correct work of subsequent operators
        obj.select = False
    
    @staticmethod
    def addSubsurfModifier(terrain):
        # check if <terrain> has a SUBSURF modifier
        for m in terrain.modifiers:
            if m.type == 'SUBSURF':
                break
        else:
            # add a SUBSURF modifier
            m = terrain.modifiers.new("Subsurf", 'SUBSURF')
            m.subdivision_type = 'SIMPLE'
            m.use_subsurf_uv = False
            m.levels = 3
            m.render_levels = 3
    
    @staticmethod
    def beginDynamicPaintCanvas(terrain):
        # setup a DYNAMIC_PAINT modifier for <terrain> with canvas surfaces
        makeActive(terrain)
        terrain.modifiers.new("Dynamic Paint", 'DYNAMIC_PAINT')
        bpy.ops.dpaint.type_toggle(type='CANVAS')
        bpy.ops.dpaint.surface_slot_remove()

    @staticmethod
    def endDynamicPaintCanvas(terrain):
        # DYNAMIC_PAINT modifier of <terrain>
        m = terrain.modifiers[-1]
        # setup a DYNAMIC_PAINT modifier for <terrain> with canvas surfaces
        m.canvas_settings.canvas_surfaces[-1].show_preview = False
        m.canvas_settings.canvas_surfaces.active_index = 0
        terrain.select = False
    
    @staticmethod
    def prepareDynamicPaintSurface(surface, group, output_name_a):
        surface.use_antialiasing = True
        surface.use_drying = False
        surface.use_dry_log = False
        surface.use_dissolve_log = False
        surface.brush_group = group
        surface.output_name_a = output_name_a
        surface.output_name_b = ""


class ForestRenderer(AreaRenderer):
    
    # name for the particle settings for a forest
    particles = "forest"
    
    calculateArea = True
    
    # maximum number of Blender particles object to be displayed in the Blender 3D View
    maxDisplayCount = 10000
    
    def renderArea(self, layer, app):
        super().renderArea(layer, app)
        
        # the terrain Blender object
        terrain = app.terrain.terrain
        
        layerId = layer.id
        
        # make the Blender object for the terrain the acrive one
        if not terrain.select:
            makeActive(terrain)
        
        bpy.ops.object.particle_system_add()
        # <ps> stands for particle systems
        ps = terrain.particle_systems[-1]
        ps.name = layerId
        # name for the particle settings for a forest
        name = self.particles
        particles = bpy.data.particles.get(name)\
            if name in bpy.data.particles else\
            loadParticlesFromFile(self.assetPath, name)
        # the total number of particles
        count = math.ceil(app.treeDensity/10000*layer.surfaceArea)
        if count > self.maxDisplayCount:
            particles.draw_percentage = math.floor(self.maxDisplayCount/count*100)
        particles.count = count
        ps.vertex_group_density = layerId
        ps.settings = particles


class WaterRenderer(AreaRenderer):
    pass


class BareRockRenderer(AreaRenderer):
    pass