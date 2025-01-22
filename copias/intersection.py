import sys
from vtkmodules.vtkFiltersCore import vtkCleanPolyData, vtkTriangleFilter
from vtkmodules.vtkFiltersGeneral import vtkBooleanOperationPolyDataFilter
from vtkmodules.vtkIOGeometry import (
    vtkBYUReader,
    vtkOBJReader,
    vtkSTLReader
)
from vtkmodules.vtkIOLegacy import vtkPolyDataReader
from vtkmodules.vtkIOPLY import vtkPLYReader
from vtkmodules.vtkIOXML import vtkXMLPolyDataReader


def get_program_parameters():
    import argparse
    parser = argparse.ArgumentParser(description="Verificar interseção entre duas malhas.")
    parser.add_argument("fn1", help="Arquivo da primeira malha, e.g., malha1.stl")
    parser.add_argument("fn2", help="Arquivo da segunda malha, e.g., malha2.stl")
    args = parser.parse_args()
    return args.fn1, args.fn2


def separate_scar():
    colors = vtkNamedColors()

    file = ReadPolyData(get_program_parameters())

    connectivityFilter = vtkConnectivityFilter()
    connectivityFilter.SetInputData(file)
    connectivityFilter.SetExtractionModeToAllRegions()
    connectivityFilter.ColorRegionsOn()
    connectivityFilter.Update()


def read_poly_data(file_name):
    import os
    _, extension = os.path.splitext(file_name)
    extension = extension.lower()

    if extension == ".ply":
        reader = vtkPLYReader()
    elif extension == ".vtp":
        reader = vtkXMLPolyDataReader()
    elif extension == ".obj":
        reader = vtkOBJReader()
    elif extension == ".stl":
        reader = vtkSTLReader()
    elif extension == ".vtk":
        reader = vtkPolyDataReader()
    elif extension == ".g":
        reader = vtkBYUReader()
        reader.SetGeometryFileName(file_name)
    else:
        raise ValueError(f"Formato de arquivo não suportado: {extension}")

    reader.SetFileName(file_name)
    reader.Update()
    return reader.GetOutput()


def main():
    fn1, fn2 = get_program_parameters()

    # Ler as malhas de entrada
    input1 = read_poly_data(fn1)
    input2 = read_poly_data(fn2)

    # Limpar e triangular as malhas
    def clean_and_triangulate(poly_data):
        triangle_filter = vtkTriangleFilter()
        triangle_filter.SetInputData(poly_data)
        clean_filter = vtkCleanPolyData()
        clean_filter.SetInputConnection(triangle_filter.GetOutputPort())
        clean_filter.Update()
        return clean_filter.GetOutput()

    input1 = clean_and_triangulate(input1)
    input2 = clean_and_triangulate(input2)

    # Operação booleana de interseção
    boolean_operation = vtkBooleanOperationPolyDataFilter()
    boolean_operation.SetOperationToIntersection()
    boolean_operation.SetInputData(0, input1)
    boolean_operation.SetInputData(1, input2)
    boolean_operation.Update()

    # Verificar se há interseção
    intersection_output = boolean_operation.GetOutput()
    has_intersection = intersection_output.GetNumberOfCells() > 0

    # Retornar o resultado como um código de saída
    sys.exit(0 if has_intersection else 1)


if __name__ == "__main__":
    main()
