import bpy
from . import Renderer, assignTags
from util import zeroVector
from util.osm import parseNumber


class BaseNodeRenderer(Renderer):
    
    def __init__(self, app):
        self.app = app
    
    def preRender(self, element):
        if not element.l.parentLocation:
            element.l.parentLocation = zeroVector()
    
    def renderNode(self, node, osm):
        tags = node.tags
        layer = node.l
        
        coords = node.getData(osm)
        
        # calculate z-coordinate of the object
        z = parseNumber(tags["min_height"], 0.) if "min_height" in tags else 0.
        if self.app.terrain:
            terrainOffset = self.app.terrain.project(coords)
            if terrainOffset is None:
                # the point is outside of the terrain
                return
            z += terrainOffset[2]
        
        self.obj = self.createBlenderObject(
            self.getName(node),
            (coords[0], coords[1], z),
            layer.getParent(),
            layer.id
        )
        
    def postRender(self, element):
        if self.obj:
            # assign OSM tags to the blender object
            assignTags(self.obj, element.tags)

    @classmethod
    def createBlenderObject(self, name, location, parent, sourceName):
        if sourceName in bpy.data.objects:
            obj = bpy.data.objects.new(name, bpy.data.objects[sourceName].data)
            if location:
                obj.location = location
            bpy.context.scene.objects.link(obj)
            if parent:
                # perform parenting
                obj.parent = parent
            return obj