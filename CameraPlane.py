bl_info = {
    "name": "Camera Plane",
    "author": "Stijn Tas",
    "version": (0, 1),
    "blender": (2, 80, 0),
    "location": "View3D > Add > Mesh > Camera Plane",
    "description": "Adds a camera plane",
    "warning": "",
    "wiki_url": "",
    "category": "Add Mesh",
    }
    
import bpy
from bpy.types import Operator
from bpy.props import *
from bpy_extras.object_utils import AddObjectHelper, object_data_add
from math import radians, sin, cos, pi
#from mathutils import Vector

def calc_mid_2_points(pt1,pt2):
    return tuple([ (pt1[0]+pt2[0])/2 , (pt1[1]+pt2[1])/2 , (pt1[2]+pt2[2])/2 ])

def calc_intersection_2D(pt1,pt2,pt3,pt4):
    vertical=0
    if not (pt1[0]-pt2[0]): vertical=1              # first line is vertical
    if not (pt3[0]-pt4[0]): vertical=vertical+2     # second line is vertical
    
    if (vertical == 0):                             # no vertical lines
        slope1 = (pt1[1]-pt2[1])/(pt1[0]-pt2[0])
        slope2 = (pt3[1]-pt4[1])/(pt3[0]-pt4[0])
        if (slope1 == slope2):                      # parallel
            return None
        else:
            # calculate 2D intersection
            # y = slope1*(x-pt1[0])+pt1[1]
            # y = slope2*(x-pt3[0])+pt3[1]
            #
            # find x first --> x is equal in both equations on the intersection point
            # slope1*(x-pt1[0])+pt1[1]  =  slope2*(x-pt3[0])+pt3[1]
            # slope1*(x-pt1[0])  -  slope2*(x-pt3[0])  =  pt3[1]  -  pt1[1]
            # slope1*x  - slope1*pt1[0]  -  slope2*x  +  slope2*pt3[0]  =  pt3[1]  -  pt1[1]
            # slope1*x  -  slope2*x  =  pt3[1]  -  pt1[1] -  slope2*pt3[0] + slope1*pt1[0]
            # (slope1-slope2)*x  =  pt3[1]  -  pt1[1] -  slope2*pt3[0] + slope1*pt1[0]
            x = (pt3[1]-pt1[1]-slope2*pt3[0]+slope1*pt1[0]) / (slope1-slope2)
            y = slope1*(x-pt1[0])+pt1[1]
            
    if (vertical == 1):                             # first line is vertical
        slope2 = (pt3[1]-pt4[1])/(pt3[0]-pt4[0])
        x=pt1[0]
        y=slope2*(x-pt3[0])+pt3[1]
        
    if (vertical == 2):                             # second line is vertical
        slope1 = (pt1[1]-pt2[1])/(pt1[0]-pt2[0])
        x=pt3[0]
        y = slope1*(x-pt1[0])+pt1[1]
        
    if (vertical == 3):                             # parallel with two vertical lines
        return None
        
    return (x,y,0)
    

def create_mesh_data ( level, vi1, vi2, vi3, vi4, verts, faces):
    # vi = vertex index
    if level:
        # calculate vertices
        c_verts = len(verts)
        verts.append(calc_intersection_2D(verts[vi1],verts[vi3],verts[vi2],verts[vi4])) # point middle +0
        hpoint=((verts[c_verts][0]-1),verts[c_verts][1],0)
        verts.append(calc_mid_2_points(verts[vi1],verts[vi2])) # point middle upper +1
        verts.append(calc_intersection_2D(verts[vi2],verts[vi3],verts[c_verts],hpoint)) # point middle left +2
        verts.append(calc_mid_2_points(verts[vi3],verts[vi4])) # point middle botton +3
        verts.append(calc_intersection_2D(verts[vi4],verts[vi1],verts[c_verts],hpoint)) # point middle right +4
           
        # Q1
        create_mesh_data ( level-1, vi1, c_verts+1, c_verts, c_verts+4, verts, faces )
        # Q2
        create_mesh_data ( level-1, c_verts+1, vi2, c_verts+2, c_verts, verts, faces )
        # Q3
        create_mesh_data ( level-1, c_verts, c_verts+2, vi3, c_verts+3, verts, faces )
        # Q4
        create_mesh_data ( level-1, c_verts+4, c_verts, c_verts+3, vi4, verts, faces )
    else:
        faces.append((vi1, vi2, vi3, vi4))      
    return;

def add_camera_plane(self, context):
    theta = (radians(180)-self.cp_Camera_FOV)/2
    start =  self.cp_Start_Clipping
    end = self.cp_End_Clipping
    
    verts = []
    verts.append((  cos(theta)*(end/sin(theta)),    end, 0))
    verts.append(( -cos(theta)*(end/sin(theta)),    end,0))
    verts.append(( -cos(theta)*(start/sin(theta)),  start, 0))
    verts.append((  cos(theta)*(start/sin(theta)),  start,0))

    edges = []

    faces = []

    # create mesh data
    create_mesh_data ( self.cp_Subdivide, 0, 1, 2, 3, verts, faces)
    mesh = bpy.data.meshes.new("CameraPlane")
    mesh.from_pydata(verts,edges,faces)
    # useful for development when the mesh may be invalid.
    # mesh.validate(verbose=True)
    mesh.update()
    
    # create object
    obj = object_data_add(context, mesh, operator=self)
    bpy.ops.object.editmode_toggle()
    bpy.ops.mesh.remove_doubles()
    bpy.ops.object.editmode_toggle()
    
    #create camera
    if self.cp_Camera_Type == "cp_Camera_Add":
        bpy.ops.object.camera_add(
            location=(self.location[0],self.location[1],self.location[2]+self.cp_Camera_Height),            
            rotation=(radians(90.0),0.0,0.0)
            )
        bpy.context.active_object.name = 'CameraPlane'
        bpy.context.active_object.data.name = 'CameraPlane'
        bpy.context.scene.camera = bpy.data.objects["CameraPlane"]
        bpy.context.object.data.angle = self.cp_Camera_FOV
        bpy.context.scene.camera = bpy.data.objects["CameraPlane"]
    
    return    


class OBJECT_OT_camera_plane(Operator, AddObjectHelper):
    """Create a new Camera Plane Mesh Object"""
    bl_idname = "mesh.camera_plane"
    bl_label = "Camera Plane"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Add plane with same camera FOV"

    # plane options
    
    cp_Subdivide : IntProperty(
            attr="cp_Subdivide",
            name="Subdivide",
            description="Total amount of subdivisions in the mesh (0-6).",
            default=3,
            min=0,
            max=6
            )             
    
    cp_Start_Clipping : FloatProperty(
            attr="cp_Start_Clipping",
            name="Start distance",
            description="Start distance of cameraplane (0,1<).",
            default=3,
            min=0.1,
            unit="LENGTH"
            ) 
            
    cp_End_Clipping : FloatProperty(
            attr="cp_End_Clipping",
            name="End distance",
            description="End distance of cameraplane (1<).",
            default=30,
            min=1,
            unit="LENGTH"
            ) 
            
    cp_Background : BoolProperty(
            attr="cpBackground",
            name="Background",
            description="Use a background at the end",
            default=False
            )

    # camera options
                
    Model_Camera_List = [
            ("cp_Camera_None", "NONE", "None"),
            ("cp_Camera_Add", "ADD", "Add camera"),
# -->       ("cp_Camera_Use", "USE", " Use camera")
            ]
            
    cp_Camera_Type : EnumProperty(
            attr="cp_Camera_Type",
            name="Camera",
            description="Specify if you want a camera",
            items= Model_Camera_List,
            default="cp_Camera_None"
            )

    cp_Camera_FOV : FloatProperty(
            attr="cp_Camera_FOV",
            name="Camera FOV",
            description="Camera Field of view (5°-160°).",
            default=radians(50.0),
            min=radians(5.0),
            max=radians(160.0),
            unit="ROTATION"         
            )
            
    cp_Camera_Height : FloatProperty(
            attr="cp_Camera_Height",
            name="Camera Height",
            description="Eye height of the camera",
            default=1.0,
            min=0,
            unit="LENGTH"
            )
            
    def draw(self, context):
        layout = self.layout
        col = layout.column()
        
        # camera plane options
        col.label(text="--- CAMERA PLANE ---")
        col.prop(self, "cp_Subdivide")
        col.prop(self, "cp_Start_Clipping")
        col.prop(self, "cp_End_Clipping")
# -->   col.prop(self, "cp_Background")
        col.separator()
        
        # camera
        col.label(text="--- CAMERA ---")
        col.prop(self,"cp_Camera_Type")
        col.prop(self, "cp_Camera_FOV")
        if self.cp_Camera_Type == "cp_Camera_None":
            pass
        elif self.cp_Camera_Type == "cp_Camera_Add":
            col.prop(self, "cp_Camera_Height")
# -->   elif self.cp_Camera_Type == "cp_Camera_Use":
# -->       col.prop(self, "cp_Camera_Height")
        col.separator()        
    
    def execute(self, context):
        add_camera_plane(self, context)

        return {'FINISHED'}


# Registration

classes = ( OBJECT_OT_camera_plane, )

def camera_plane_button(self, context):
    self.layout.operator(
        OBJECT_OT_camera_plane.bl_idname,
        text="Camera Plane",
        icon='VIEW_PERSPECTIVE')


# This allows you to right click on a button and link to the manual
def camera_plane_manual_map():
    url_manual_prefix = "http://wiki.blender.org/index.php/Doc:2.6/Manual/"
    url_manual_mapping = (
        ("bpy.ops.mesh.camera_plane", "Modeling/Objects"),
        )
    return url_manual_prefix, url_manual_mapping


def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
        
    bpy.utils.register_manual_map(camera_plane_manual_map)
    bpy.types.VIEW3D_MT_mesh_add.append(camera_plane_button)


def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)

    bpy.utils.unregister_manual_map(camera_plane_manual_map)
    bpy.types.VIEW3D_MT_mesh_add.remove(camera_plane_button)


if __name__ == "__main__":
    register()
