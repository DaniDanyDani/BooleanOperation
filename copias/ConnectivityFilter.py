#!/usr/bin/env python







import os
import argparse
import sys

# VTK Módulos necessários
import vtkmodules.vtkInteractionStyle
import vtkmodules.vtkRenderingOpenGL2
from vtkmodules.vtkCommonColor import vtkNamedColors
from vtkmodules.vtkFiltersCore import (
    vtkAppendFilter,
    vtkConnectivityFilter,
    vtkDelaunay3D,
    vtkCleanPolyData,
    vtkTriangleFilter
)
from vtkmodules.vtkFiltersGeneral import (
    vtkBooleanOperationPolyDataFilter,
    vtkTransformPolyDataFilter
)
from vtkmodules.vtkFiltersSources import vtkSphereSource
from vtkmodules.vtkIOGeometry import (
    vtkSTLReader,
    vtkSTLWriter,
    vtkBYUReader,
    vtkOBJReader
)
from vtkmodules.vtkIOLegacy import (
    vtkPolyDataReader,
    vtkPolyDataWriter
)
from vtkmodules.vtkIOPLY import vtkPLYReader
from vtkmodules.vtkIOXML import vtkXMLPolyDataReader
from vtkmodules.vtkCommonTransforms import vtkTransform




def get_program_parameters():
    import argparse
    description = ''
    epilogue = '''

    '''
    parser = argparse.ArgumentParser(description=description, epilog=epilogue,
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('fn1', nargs='?', default=None, help='The polydata source file name,e.g. Grey_Nurse_Shark.stl.')

    args = parser.parse_args()

    return args.fn1

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

def main():
    colors = vtkNamedColors()

    file = ReadPolyData(get_program_parameters())

    connectivityFilter = vtkConnectivityFilter()
    connectivityFilter.SetInputData(file)
    connectivityFilter.SetExtractionModeToAllRegions()
    connectivityFilter.ColorRegionsOn()
    connectivityFilter.Update()




if __name__ == '__main__':
    main()