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
    epilogue = '''  '''

    parser = argparse.ArgumentParser(description=description, epilog=epilogue,
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('fn1', nargs='?', default=None, help='.')
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
    return clean_filter.GetOutput()

def visualizer(scar_poly, name):
    print("\nRenderizando modelos\n")
    colors = vtkNamedColors()
    
    # Mapper para o modelo de fibrose
    scar_mapper = vtkDataSetMapper()
    scar_mapper.SetInputData(scar_poly)
    scar_mapper.Update()

    scar_actor = vtkActor()
    scar_actor.GetProperty().SetOpacity(1)
    scar_actor.SetMapper(scar_mapper)

    renderer = vtkRenderer()
    renderer.AddActor(scar_actor)

    renWindow = vtkRenderWindow()
    renWindow.AddRenderer(renderer)
    
    iren = vtkRenderWindowInteractor()
    iren.SetRenderWindow(renWindow)
    
    iren.Initialize()
    renWindow.Render()
    renWindow.SetWindowName(name)

    renderer.SetBackground(colors.GetColor3d('deep_ochre'))
    renderer.GetActiveCamera().Zoom(0.9)
    
    renWindow.Render()
    iren.Start()

def WriteStl(output_data, filename):
    print(f"Salvando scar_processed em formato stl com o nome {filename}")
    Stlwriter = vtkSTLWriter()
    Stlwriter.SetFileName(filename)
    Stlwriter.SetInputData(output_data)
    Stlwriter.Write()
    print(f"Resultado salvo em {filename}")

print(f"Pegando parâmetros, limpando e triangulando arquivo poly_data...")
fn1 = get_program_parameters()
file_name = f"{os.path.splitext(fn1)[0]}_noMain.stl"
scar_poly= clean_and_triangulate(ReadPolyData(fn1))
print(f"... Concluido\n")


idFilter = vtk.vtkGenerateIds()
idFilter.SetInputData(scar_poly)
idFilter.SetPointIds(True)
idFilter.SetCellIds(False)
idFilter.SetPointIdsArrayName("PointIds")
idFilter.SetCellIdsArrayName("CellIds")
idFilter.Update()

nonManifoldEdgesFilter = vtk.vtkFeatureEdges()
nonManifoldEdgesFilter.SetInputData(idFilter.GetOutput())
nonManifoldEdgesFilter.BoundaryEdgesOff()
nonManifoldEdgesFilter.FeatureEdgesOff()
nonManifoldEdgesFilter.ManifoldEdgesOff()
nonManifoldEdgesFilter.NonManifoldEdgesOn()
nonManifoldEdgesFilter.Update()

nonManifoldPointids = (nonManifoldEdgesFilter.GetOutput().GetPointData().GetArray("PointIds"))
nonManifoldPointids.GetNumberOfValues()

manifoldEdgesFilter = vtk.vtkFeatureEdges()
manifoldEdgesFilter.SetInputData(idFilter.GetOutput())
manifoldEdgesFilter.BoundaryEdgesOff()
manifoldEdgesFilter.FeatureEdgesOff()
manifoldEdgesFilter.ManifoldEdgesOn()
manifoldEdgesFilter.NonManifoldEdgesOff()
manifoldEdgesFilter.Update()

manifoldPointids = manifoldEdgesFilter.GetOutput().GetPointData().GetArray("PointIds")

ids = vtk.vtkIdTypeArray()
ids.SetNumberOfComponents(1)
for i in range(nonManifoldPointids.GetNumberOfValues()):
    sharedPointIDFound = True
    for j in range(manifoldPointids.GetNumberOfValues()):
        # =========================================================
        print(f"\n\nExecução: ({i},{j})\n")
        print(f"{nonManifoldPointids.GetTuple1(i)=}\n")
        print(f"{manifoldPointids.GetTuple1(j)=}")
        # =========================================================
        if int(nonManifoldPointids.GetTuple1(i)) == int(manifoldPointids.GetTuple1(j)):
            sharedPointIDFound = False
            break
    if not sharedPointIDFound:
          ids.InsertNextValue(int(nonManifoldPointids.GetTuple1(i)))

selectionNode = vtk.vtkSelectionNode()
selectionNode.SetFieldType(vtk.vtkSelectionNode.POINT)
selectionNode.SetContentType(vtk.vtkSelectionNode.INDICES)
selectionNode.SetSelectionList(ids)
selectionNode.GetProperties().Set(vtk.vtkSelectionNode.CONTAINING_CELLS(), 1)
selectionNode.GetProperties().Set(vtk.vtkSelectionNode.INVERSE(), 1)

selection = vtk.vtkSelection()
selection.AddNode(selectionNode)

extractSelection = vtk.vtkExtractSelection()
extractSelection.SetInputData(0, scar_poly)
extractSelection.SetInputData(1, selection)
extractSelection.Update()

geometryFilter = vtk.vtkGeometryFilter()
geometryFilter.SetInputData(extractSelection.GetOutput())
geometryFilter.Update()

# test if the removal of non manifold edges did work
featureEdges2 = vtk.vtkFeatureEdges()
featureEdges2.SetInputData(geometryFilter.GetOutput())
featureEdges2.BoundaryEdgesOff()
featureEdges2.FeatureEdgesOff()
featureEdges2.ManifoldEdgesOff()
featureEdges2.NonManifoldEdgesOn()
featureEdges2.Update()
featureEdges2.GetOutput().GetNumberOfPoints()

# save the model without non-manifold edges
scar_poly = geometryFilter.GetOutput()

visualizer(scar_poly, "Teste")

WriteStl(scar_poly, file_name)