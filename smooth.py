# Imports ------------------------------------------
import os, argparse, sys, vtk
from vtkmodules.vtkFiltersGeometry import vtkGeometryFilter
from vtkmodules.vtkIOLegacy import vtkPolyDataReader
from vtkmodules.vtkIOPLY import vtkPLYReader
from vtkmodules.vtkIOXML import vtkXMLPolyDataReader
from vtkmodules.vtkIOGeometry import (
    vtkBYUReader,
    vtkOBJReader,
    vtkSTLReader,
    vtkSTLWriter
)
from vtkmodules.vtkCommonColor import vtkNamedColors
from vtkmodules.vtkFiltersCore import (
    vtkCleanPolyData,
    vtkTriangleFilter,
    vtkAppendFilter,
    vtkDelaunay3D,
    vtkConnectivityFilter
)

from vtkmodules.vtkFiltersGeneral import (
    vtkBooleanOperationPolyDataFilter,
    vtkTransformPolyDataFilter)
from vtkmodules.vtkCommonTransforms import vtkTransform
from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkDataSetMapper,
    vtkRenderWindow,
    vtkRenderWindowInteractor,
    vtkRenderer
)
# ===============================


def get_program_parameters():
    description = ''
    epilogue = '''
    Exemplo de uso:
        python principal.py Patient_1_scar.vtk Patient_1_surf.vtk

    Extensões suportadas:
        .vtk, .stl, .ply, .obj, .vtp, .g
    '''

    parser = argparse.ArgumentParser(description=description, epilog=epilogue,
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('fn1', nargs='?', default=None, help='Patient_1_scar.vtk.')
    # parser.add_argument('fn2', nargs='?', default=None, help='Patient_1_surf.vtk')

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
        raise ValueError(f"Tipo de dado não reconhecido para o arquivo: {file_name}")
    return poly_data

def clean_and_triangulate(poly_data):
    triangle_filter = vtkTriangleFilter()
    triangle_filter.SetInputData(poly_data)
    clean_filter = vtkCleanPolyData()
    clean_filter.SetInputConnection(triangle_filter.GetOutputPort())
    clean_filter.Update()
    # bounds = poly_data.GetBounds()
    center = poly_data.GetCenter()
    # center = [
    #     (bounds[0] + bounds[1]) / 2,  # (xmin + xmax) / 2
    #     (bounds[2] + bounds[3]) / 2,  # (ymin + ymax) / 2
    #     (bounds[4] + bounds[5]) / 2   # (zmin + zmax) / 2
    # ]
    return clean_filter.GetOutput(), center

def smoothPoly(poly,num_iter = 30,rlx_factor=0.1):
    '''
    http://www.vtk.org/doc/nightly/html/classvtkSmoothPolyDataFilter.html
    '''
    smoothFilter = vtk.vtkSmoothPolyDataFilter()
    smoothFilter.SetInputData(poly)
    smoothFilter.SetNumberOfIterations(num_iter)
    smoothFilter.SetRelaxationFactor(rlx_factor)
    smoothFilter.FeatureEdgeSmoothingOff()
    #smoothFilter.FeatureEdgeSmoothingOn()
    smoothFilter.BoundarySmoothingOff()
    #smoothFilter.BoundarySmoothingOff()
    smoothFilter.Update()
    return smoothFilter.GetOutput()

def WriteStl(output_data, filename):
    print(f"Salvando scar_processed em formato stl com o nome {filename}")
    Stlwriter = vtkSTLWriter()
    Stlwriter.SetFileName(filename)
    Stlwriter.SetInputData(output_data)
    Stlwriter.Write()
    print(f"Resultado salvo em {filename}")


def convert_to_polydata(unstructured_grid):
    geometry_filter = vtkGeometryFilter()
    geometry_filter.SetInputData(unstructured_grid)
    geometry_filter.Update()
    return geometry_filter.GetOutput()


fn1 = get_program_parameters()
file_name = f"{os.path.splitext(fn1)[0]}_processed.stl"

scar_poly, center_scar = clean_and_triangulate(ReadPolyData(fn1))

WriteStl(scar_poly, file_name)