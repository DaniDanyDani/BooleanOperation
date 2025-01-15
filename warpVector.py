#!/usr/bin/env python

# noinspection PyUnresolvedReferences
import vtkmodules.vtkInteractionStyle
# noinspection PyUnresolvedReferences
from vtkmodules.vtkCommonCore import vtkDoubleArray
import vtkmodules.vtkRenderingOpenGL2
from vtkmodules.vtkCommonColor import vtkNamedColors
from vtkmodules.vtkFiltersCore import (
    vtkCleanPolyData,
    vtkTriangleFilter,
    vtkPolyDataNormals
)
from vtkmodules.vtkFiltersGeneral import (
    vtkBooleanOperationPolyDataFilter,
    vtkWarpVector
    )

from vtkmodules.vtkFiltersSources import vtkSphereSource
from vtkmodules.vtkIOGeometry import (
    vtkBYUReader,
    vtkOBJReader,
    vtkSTLReader
)
from vtkmodules.vtkIOLegacy import vtkPolyDataReader
from vtkmodules.vtkIOPLY import vtkPLYReader
from vtkmodules.vtkIOXML import vtkXMLPolyDataReader
from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkPolyDataMapper,
    vtkRenderWindow,
    vtkRenderWindowInteractor,
    vtkRenderer
)
from vtkmodules.vtkFiltersGeneral import vtkTransformPolyDataFilter
from vtkmodules.vtkCommonTransforms import vtkTransform
from vtkmodules.vtkFiltersSources import vtkSphereSource
from vtkmodules.vtkRenderingCore import vtkActor, vtkPolyDataMapper

from vtkmodules.vtkIOLegacy import vtkPolyDataWriter

#!/usr/bin/env python

# noinspection PyUnresolvedReferences
import vtkmodules.vtkInteractionStyle
# noinspection PyUnresolvedReferences
import vtkmodules.vtkRenderingOpenGL2
from vtkmodules.vtkCommonColor import vtkNamedColors
from vtkmodules.vtkFiltersSources import vtkSphereSource
from vtkmodules.vtkIOGeometry import (
    vtkSTLReader,
    vtkSTLWriter
)
from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkPolyDataMapper,
    vtkRenderWindow,
    vtkRenderWindowInteractor,
    vtkRenderer
)

def ReadPolyData(file_name):
    import os
    path, extension = os.path.splitext(file_name)
    extension = extension.lower()
    if extension == '.ply':
        reader = vtkPLYReader()
        reader.SetFileName(file_name)
        reader.Update()
        poly_data = reader.GetOutput()
    elif extension == '.vtp':
        reader = vtkXMLPolyDataReader()
        reader.SetFileName(file_name)
        reader.Update()
        poly_data = reader.GetOutput()
    elif extension == '.obj':
        reader = vtkOBJReader()
        reader.SetFileName(file_name)
        reader.Update()
        poly_data = reader.GetOutput()
    elif extension == '.stl':
        reader = vtkSTLReader()
        reader.SetFileName(file_name)
        reader.Update()
        poly_data = reader.GetOutput()
    elif extension == '.vtk':
        reader = vtkPolyDataReader()
        reader.SetFileName(file_name)
        reader.Update()
        poly_data = reader.GetOutput()
    elif extension == '.g':
        reader = vtkBYUReader()
        reader.SetGeometryFileName(file_name)
        reader.Update()
        poly_data = reader.GetOutput()
    else:
        # Return a None if the extension is unknown.
        poly_data = None
    return poly_data
# Supondo input1 (fechado) e input2 (aberto) como vtkPolyData.

def get_program_parameters():
    import argparse
    description = 'How to align two vtkPolyData\'s.'
    epilogue = '''

    '''
    parser = argparse.ArgumentParser(description=description, epilog=epilogue,
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-o', '--operation', nargs='?', default='intersection', help='The type of  ')
    parser.add_argument('fn1', nargs='?', default=None, help='The polydata source file name,e.g. Grey_Nurse_Shark.stl.')
    parser.add_argument('fn2', nargs='?', default=None, help='The polydata target file name, e.g. shark.ply.')

    args = parser.parse_args()

    return args.fn1, args.fn2

def WriteStl(polydata, filename):
    writer = vtkSTLWriter()
    writer.SetFileName(filename)
    writer.SetInputData(polydata)  # Usar SetInputData para passar o vtkPolyData diretamente
    writer.Write()
    print(f"Resultado salvo em {filename}")


fn1, fn2 = get_program_parameters()

poly1 = ReadPolyData(fn1)
tri1 = vtkTriangleFilter()
tri1.SetInputData(poly1)
clean1 = vtkCleanPolyData()
clean1.SetInputConnection(tri1.GetOutputPort())
clean1.Update()
input1 = clean1.GetOutput()

poly2 = ReadPolyData(fn2)
tri2 = vtkTriangleFilter()
tri2.SetInputData(poly2)
tri2.Update()
clean2 = vtkCleanPolyData()
clean2.SetInputConnection(tri2.GetOutputPort())
clean2.Update()
input2 = clean2.GetOutput()

# Supondo input1 (fechado) e input2 (aberto) como vtkPolyData.

# Passo 1: Detectar a interseção
booleanFilter = vtkBooleanOperationPolyDataFilter()
booleanFilter.SetOperationToIntersection()
booleanFilter.SetInputData(0, input1)
booleanFilter.SetInputData(1, input2)
booleanFilter.Update()

intersection = booleanFilter.GetOutput()

# Passo 2: Calcular as normais para a superfície do modelo fechado
normals = vtkPolyDataNormals()
normals.SetInputData(input1)
normals.ComputePointNormalsOn()
normals.Update()

# Passo 3: Associar deformação à região de interseção
warpData = vtkDoubleArray()
warpData.SetNumberOfComponents(3)
warpData.SetName("warpData")

magnitude = 1

for i in range(input1.GetNumberOfPoints()):
    point = input1.GetPoint(i)
    if intersection.FindPoint(point) != -1:  # Está na interseção
        normal = normals.GetOutput().GetPointData().GetNormals().GetTuple(i)
        warp = [normal[0] * magnitude, normal[1] * magnitude, normal[2] * magnitude]
    else:
        warp = [0.0, 0.0, 0.0]
    warpData.InsertNextTuple(warp)

input1.GetPointData().AddArray(warpData)
input1.GetPointData().SetActiveVectors(warpData.GetName())

# Passo 4: Aplicar a deformação com WarpVector
warpVector = vtkWarpVector()
warpVector.SetInputData(input1)
warpVector.Update()

# Visualizar o resultado
mapper = vtkPolyDataMapper()
mapper.SetInputConnection(warpVector.GetOutputPort())

actor = vtkActor()
actor.SetMapper(mapper)

# Salvar o modelo deformado
WriteStl(warpVector.GetOutput(), "warp.stl")
