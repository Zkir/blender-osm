import os
import bpy
from . import Roof
from renderer import Renderer
from util.blender import loadMeshFromFile


class RoofMesh(Roof):
    """
    A class to deal with buildings or building part
    with roof meshes loaded from a .blend library file
    """
    
    defaultHeight = 5.
    
    def __init__(self, mesh):
        """
        Args:
            mesh (str): Name of the mesh in the .blend library file <self.assetPath>
        """
        super().__init__()
        self.mesh = mesh
    
    def make(self, bldgMaxHeight, roofMinHeight, bldgMinHeight, osm):
        polygon = self.polygon
        
        if not bldgMinHeight is None:
            # Create sides for the prism with the height <roofMinHeight - bldgMinHeight>,
            # that is based on the <polygon>
            polygon.sidesPrism(roofMinHeight, self.wallIndices)
        
        c = polygon.center
        # location of the Blender mesh for the roof
        self.location = (c.x, c.y, roofMinHeight)
        
        return True
    
    def render(self, r):
        polygon = self.polygon
        op = r.op
        
        # create building walls
        super().render(r)
        
        # Now deal with the roof
        # Use the Blender mesh loaded before or load it from the .blend file
        # with the path defined by <op.assetPath> and <self.assetPath>
        # <self.assetPath> is set in the parent class <Roof>
        mesh = bpy.data.meshes.get(self.mesh)\
            if self.mesh in bpy.data.meshes else\
            loadMeshFromFile(os.path.join(op.assetPath, self.assetPath), self.mesh)
        if not mesh.materials:
            # create an empty slot for a Blender material
            mesh.materials.append(None)
        # create a Blender object to host <mesh>
        o = bpy.data.objects.new(self.mesh, mesh)
        o.location = self.location
        o.scale = (
            ( max(v.x for v in polygon.verts) - min(v.x for v in polygon.verts) )/2.,
            ( max(v.y for v in polygon.verts) - min(v.y for v in polygon.verts) )/2.,
            self.h
        )
        bpy.context.scene.objects.link(o)
        # perform Blender parenting
        o.parent = r.obj
        # link Blender material to the Blender object <o> instead of <o.data>
        slot = o.material_slots[0]
        slot.link = 'OBJECT'
        slot.material = r.getRoofMaterial(self.element)
        # add Blender object <o> for joining with Blender object <r.obj>
        Renderer.addForJoin(o, r.obj)