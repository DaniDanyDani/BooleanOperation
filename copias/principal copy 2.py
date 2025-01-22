# Imports ------------------------------------------
import os, argparse, sys, vtk
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
    parser.add_argument('fn2', nargs='?', default=None, help='Patient_1_surf.vtk')

    args = parser.parse_args()
    return args.fn1, args.fn2


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

def connected_superficies(file):
    colors = vtkNamedColors()
    if not isinstance(file, vtk.vtkPolyData):
        raise TypeError("A entrada deve ser do tipo vtkPolyData.")
    if file.GetNumberOfCells() == 0:
        raise ValueError("O arquivo não possui células conectadas.")


    # Aplicar o filtro de conectividade
    connectivity_filter = vtk.vtkConnectivityFilter()
    connectivity_filter.SetInputData(file)
    connectivity_filter.SetExtractionModeToAllRegions()  # Identificar todas as regiões conectadas
    connectivity_filter.ColorRegionsOn()  # Marca cada região com um ID único
    connectivity_filter.Update()

    # Obter o número de regiões conectadas
    num_regions = connectivity_filter.GetNumberOfExtractedRegions()
    print(f"Número de superfícies separadas encontradas: {num_regions}")

    regions = []

    for region_id in range(num_regions):
        # Configure o filtro para extrair uma região específica
        connectivity_filter.SetExtractionModeToSpecifiedRegions()
        connectivity_filter.AddSpecifiedRegion(region_id)
        connectivity_filter.Update()
        
        # Obtenha a região extraída e adicione à lista
        region_polydata = vtk.vtkPolyData()
        region_polydata.ShallowCopy(connectivity_filter.GetOutput())
        regions.append(region_polydata)
        
        # Limpar a região especificada para a próxima iteração
        connectivity_filter.DeleteSpecifiedRegion(region_id)

    # Visualize
    mapper = vtkDataSetMapper()
    mapper.SetInputConnection(connectivity_filter.GetOutputPort())
    mapper.Update()

    actor = vtkActor()
    actor.SetMapper(mapper)

    renderer = vtkRenderer()
    renderer.AddActor(actor)

    renWindow = vtkRenderWindow()
    renWindow.AddRenderer(renderer)
    iren = vtkRenderWindowInteractor()
    iren.SetRenderWindow(renWindow)
    iren.Initialize()
    iren.Start()
    renWindow = vtkRenderWindow()
    renWindow.AddRenderer(renderer)
    iren = vtkRenderWindowInteractor()
    iren.SetRenderWindow(renWindow)

    iren.Initialize()
    renWindow.Render()
    renWindow.SetWindowName('ConnectivityFilter')
    renderer.SetBackground(colors.GetColor3d('deep_ochre'))
    renderer.GetActiveCamera().Zoom(0.9)
    renWindow.Render()
    iren.Start()

    return regions
    # return num_regions, connectivity_filter


def clean_and_triangulate(poly_data):
    triangle_filter = vtkTriangleFilter()
    triangle_filter.SetInputData(poly_data)
    clean_filter = vtkCleanPolyData()
    clean_filter.SetInputConnection(triangle_filter.GetOutputPort())
    clean_filter.Update()
    return clean_filter.GetOutput()

def intersection(input1, input2):

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
    return True if has_intersection else False

def scalar_transform(file, scale):
    bounds = file.GetBounds()
    center = [
        (bounds[0] + bounds[1]) / 2,  # (xmin + xmax) / 2
        (bounds[2] + bounds[3]) / 2,  # (ymin + ymax) / 2
        (bounds[4] + bounds[5]) / 2   # (zmin + zmax) / 2
    ]

    transform = vtkTransform()

    transform.Translate(center)
    transform.Scale(scale, scale, scale)
    transform.Translate(-center[0], -center[1], -center[2])

    # Adicionar o filtro de transformação
    transformFilter = vtkTransformPolyDataFilter()
    transformFilter.SetTransform(transform) 
    transformFilter.SetInputData(file)     
    transformFilter.Update()                  
    transformed = transformFilter.GetOutput()  

    return transformed, transform

def invert_transform(transform, boolean):
    # Criar uma transformação inversa
    inverseTransform = vtkTransform()
    inverseTransform.DeepCopy(transform)
    inverseTransform.Inverse()

    # Aplicar a transformação inversa a um PolyData
    inverseTransformFilter = vtkTransformPolyDataFilter()
    inverseTransformFilter.SetTransform(inverseTransform)
    inverseTransformFilter.SetInputConnection(boolean.GetOutputPort())
    inverseTransformFilter.Update()

    # Retornar a saída corrigida do filtro
    return inverseTransformFilter.GetOutput()


def bool_operation(scar, heart, operation="Difference"):
    print(f"Iniciando operação booleana: {operation}")

    booleanOperation = vtkBooleanOperationPolyDataFilter()

    if operation == "Difference":
        booleanOperation.SetOperationToDifference()
    elif operation == "Intersection":
        booleanOperation.SetOperationToIntersection()
    elif operation == "Union":
        booleanOperation.SetOperationToUnion()
    else:
        raise ValueError(f"Operação booleana desconhecida: {operation}")
    
    booleanOperation.SetInputData(0, scar)
    booleanOperation.SetInputData(1, heart)

    try:
        booleanOperation.Update()
    except RuntimeError as e:
        print(f"Erro durante a operação booleana: {e}")
        return None

    return booleanOperation

def WriteStl(output_data, filename):
    Stlwriter = vtkSTLWriter()
    Stlwriter.SetFileName(filename)
    Stlwriter.SetInputConnection(output_data.GetOutputPort())
    Stlwriter.Write()
    print(f"Resultado salvo em {filename}")

def handle_error(message):
    print(f"Erro: {message}")
    sys.exit(1)


def main():

    fn1, fn2 = get_program_parameters()
    if not fn1 or not fn2:
        handle_error("Os argumentos de entrada não foram fornecidos")

    try:
        scar_poly = ReadPolyData(fn1)
        heart_poly = ReadPolyData(fn2)

    except ValueError as e:
        handle_error(str(e))

    base_scar = clean_and_triangulate(scar_poly)
    base_heart = clean_and_triangulate(heart_poly)


    if intersection(base_scar, base_heart):

        regions = connected_superficies(base_scar)


        results = []
        for i, region in enumerate(regions):
            print(f"Processando região {i + 1} de {len(regions)}")
            scar_transformed, transform = scalar_transform(region, 1.2)

            bool_filter = bool_operation(scar_transformed, base_heart)
            result = invert_transform(transform, bool_filter)

            if intersection(result, base_heart):

                scar_transformed, transform = scalar_transform(result, 0.98)

                result = bool_operation(scar_transformed, base_heart)
                result = invert_transform(transform, result)
            results.append(result)
        
        final_result = vtkAppendFilter()
        for r in results:
            final_result.AddInputData(r)
        final_result.Update()

        WriteStl(final_result, "teste_1_scar.stl")
    else:
        print("Nenhuma intersecção foi encontrada entre a fibrose e o coração")

        
if __name__== "__main__":
    main()




        

        

        


        

        
    


'''

Leitura de Arquivos
principal:
    Se a fibrose possui mais de um modelo separado:
        fibroses [list] = connectivityFilter()
        n_regioes = 
    se não houver mais de uma fibrose:
        Fibroses [list] = database
        n_regioes = 1
        continua

    Se houver intersecções:

        para cada fibrose em fibroses:
            aplica a escala na fibrose
            realiza a diferença booleana da fibrose com o modelo do coração
            aplica a escala inversa no resultado final

            # OUUUUUUUUUUUUUU
            # aplica a transformação linear em cada uma com as normais das intersecções

        junta todas as fibroses em um único modelo de novo
    Se não houver intersecções:
        continua

'''