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

def connected_superficies(file):
    colors = vtkNamedColors()

    # Aplicar o filtro de conectividade
    connectivity_filter = vtk.vtkConnectivityFilter()
    connectivity_filter.SetInputData(file)
    connectivity_filter.SetExtractionModeToAllRegions()  # Identificar todas as regiões conectadas
    connectivity_filter.ColorRegionsOn()  # Marca cada região com um ID único
    connectivity_filter.Update()
    # num_regions = connectivity_filter.GetNumberOfExtractedRegions()

    return connectivity_filter

def scalar_transform(file, center, scale):
    center = file.GetCenter()
    print(f"{file.GetCenter()=}")
    transform = vtkTransform()
    transform.Translate(center)
    transform.Scale(scale, scale, scale)
    # transform.Translate(-center[0], -center[1], -center[2])
    transform.Translate(-center[0], -center[1], -center[2])

    # Adicionar o filtro de transformação
    transformFilter = vtkTransformPolyDataFilter()
    transformFilter.SetTransform(transform) 
    transformFilter.SetInputData(file)     
    transformFilter.Update()

    
    transformed = transformFilter.GetOutput()  

    print(f"{transformed.GetCenter()=}")

    return transformed, transform

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

    return booleanOperation.GetOutput()

def invert_transform(transform, boolean):
    # Criar uma transformação inversa
    inverseTransform = vtkTransform()
    inverseTransform.DeepCopy(transform)
    inverseTransform.Inverse()

    # Aplicar a transformação inversa a um PolyData
    inverseTransformFilter = vtkTransformPolyDataFilter()
    inverseTransformFilter.SetTransform(inverseTransform)
    inverseTransformFilter.SetInputData(boolean)
    inverseTransformFilter.Update()

    # Retornar a saída corrigida do filtro
    return inverseTransformFilter.GetOutput()

def WriteStl(output_data, filename):
    print(f"Salvando scar_processed em formato stl com o nome {filename}")
    Stlwriter = vtkSTLWriter()
    Stlwriter.SetFileName(filename)
    Stlwriter.SetInputData(output_data)
    Stlwriter.Write()
    print(f"Resultado salvo em {filename}")

def append_filter(scar_processed_list):
    appendFilter = vtkAppendFilter()

    for scar in scar_processed_list:
        appendFilter.AddInputData(scar)
    appendFilter.Update()
    return appendFilter.GetOutput()

def convert_to_polydata(unstructured_grid):
    geometry_filter = vtkGeometryFilter()
    geometry_filter.SetInputData(unstructured_grid)
    geometry_filter.Update()
    return geometry_filter.GetOutput()

def WriteVtk(output_data, filename):
    print(f"Salvando arquivo em formato vtk com o nome {filename}")
    
    if isinstance(output_data, vtk.vtkPolyData):
        writer = vtk.vtkPolyDataWriter()
    elif isinstance(output_data, vtk.vtkUnstructuredGrid):
        writer = vtk.vtkUnstructuredGridWriter()
    else:
        raise ValueError("Tipo de dado não suportado para salvar como .vtk")
    
    writer.SetFileName(filename)
    writer.SetInputData(output_data)
    writer.Write()
    print(f"Resultado salvo em {filename}")

def visualizer(scar_poly, hear_poly, name):
    print("Renderizando modelos")
    colors = vtkNamedColors()
    
    # Mapper para o modelo de fibrose
    scar_mapper = vtkDataSetMapper()
    scar_mapper.SetInputData(scar_poly)
    scar_mapper.Update()

    scar_actor = vtkActor()
    scar_actor.GetProperty().SetOpacity(0.75)
    scar_actor.SetMapper(scar_mapper)

    # Mapper para o modelo de coração
    heart_mapper = vtkDataSetMapper()
    heart_mapper.SetInputData(hear_poly)
    heart_mapper.Update()

    heart_actor = vtkActor()
    heart_actor.SetMapper(heart_mapper)

    # Criando o renderer e adicionando os atores
    renderer = vtkRenderer()
    renderer.AddActor(scar_actor)
    renderer.AddActor(heart_actor)

    # Configurando a janela de renderização
    renWindow = vtkRenderWindow()
    renWindow.AddRenderer(renderer)
    
    iren = vtkRenderWindowInteractor()
    iren.SetRenderWindow(renWindow)
    
    # Inicializando o interator e renderizando a cena
    iren.Initialize()
    renWindow.Render()
    renWindow.SetWindowName(name)

    # Definindo a cor de fundo e o zoom da câmera
    renderer.SetBackground(colors.GetColor3d('deep_ochre'))
    renderer.GetActiveCamera().Zoom(0.9)
    
    # Renderizando a cena
    renWindow.Render()
    iren.Start()

# def smoothPoly(poly,num_iter = 15,rlx_factor=0.1):
#     '''
#     http://www.vtk.org/doc/nightly/html/classvtkSmoothPolyDataFilter.html
#     '''
#     smoothFilter = vtk.vtkSmoothPolyDataFilter()
#     smoothFilter.SetInputData(poly)
#     smoothFilter.SetNumberOfIterations(num_iter)
#     smoothFilter.SetRelaxationFactor(rlx_factor)
#     smoothFilter.FeatureEdgeSmoothingOff()
#     #smoothFilter.FeatureEdgeSmoothingOn()
#     smoothFilter.BoundarySmoothingOff()
#     #smoothFilter.BoundarySmoothingOff()
#     smoothFilter.Update()
#     return smoothFilter.GetOutput()


fn1, fn2 = get_program_parameters()
file_name = f"{os.path.splitext(fn1)[0]}_processed.stl"
file_name_vtk = f"{os.path.splitext(fn1)[0]}_processed.vtk"
sup_scale = 1.1
inf_scale = 0.9
scar_poly, center_scar = clean_and_triangulate(ReadPolyData(fn1))
print(f"{center_scar=}")
heart_poly, center_heart = clean_and_triangulate(ReadPolyData(fn2))

visualizer(scar_poly, heart_poly, "Entrada inicial")

if intersection(scar_poly, heart_poly):
    print("Uma ou mais intersecção encontradas!\n")
    scar_connected_filter = connected_superficies(scar_poly)
    num_regions = scar_connected_filter.GetNumberOfExtractedRegions()
    print(f"Número de superfícies separadas encontradas: {num_regions}\n")
    
    if num_regions > 1:
        regions = []
        scar_processed_list = []
        for region_id in range(num_regions):
            scar_connected_filter.SetExtractionModeToSpecifiedRegions()
            scar_connected_filter.AddSpecifiedRegion(region_id)
            scar_connected_filter.Update()

            region_polydata = vtk.vtkPolyData()
            region_polydata.ShallowCopy(scar_connected_filter.GetOutput())
            regions.append(region_polydata)

            scar_connected_filter.DeleteSpecifiedRegion(region_id)

            print(f"{regions=}")
        
        n_superficie = 1
        for region in regions:

            print(f"Processando a superficie{n_superficie}")

            if intersection(region, heart_poly):

                print(f"Encontrada intersecção na {n_superficie}° superficie, aplicando escala superior")
                scar_poly, center_region = clean_and_triangulate(region)
                
                print(f"{center_region=}")
                print(f"{scar_poly.GetCenter()=}")
                print(f"{scar_poly.GetCenter()=}")
                print(f"{scar_poly.GetCenter()=}")
                print(f"{scar_poly.GetCenter()=}")
                print(f"{scar_poly.GetCenter()=}")
                print(f"{scar_poly.GetCenter()=}")
                print(f"{scar_poly.GetCenter()=}")

                visualizer(scar_poly, heart_poly, f"Entrada {n_superficie} sendo tratada nesse momento")

                scar_poly_transformed, transform = scalar_transform(scar_poly,center_region, sup_scale)
                print(f"{scar_poly_transformed.GetCenter()=}")
                
                
                print(f"Centro original da superfície: {center_region=}")
                bounds = scar_poly_transformed.GetBounds()
                new_center = [
                    (bounds[0] + bounds[1]) / 2.0,
                    (bounds[2] + bounds[3]) / 2.0,
                    (bounds[4] + bounds[5]) / 2.0
                ]
                print(f"Centro após transformação: {new_center=}")

                visualizer(scar_poly_transformed, scar_poly, f"Entrada {n_superficie} comparada com base")
                

                pre_scar_bool = bool_operation(scar_poly_transformed, heart_poly, "Intersection")

                visualizer(pre_scar_bool, heart_poly, f"Entrada {n_superficie} após o booleano")

                pre_scar_bool = invert_transform(transform, pre_scar_bool)

                visualizer(pre_scar_bool, heart_poly, f"Entrada {n_superficie} após o booleano invertido")

                if intersection(pre_scar_bool, heart_poly):
                    print(f"Encontrada intersecção na {n_superficie}° superficie, aplicando escala inferior")
                    scar_poly_transformed, transform = scalar_transform(pre_scar_bool, center_scar, inf_scale)
                    visualizer(scar_poly_transformed, heart_poly, f"Entrada {n_superficie} transformada final")
                    scar_processed = bool_operation(pre_scar_bool, heart_poly, "Intersection")
                    visualizer(scar_poly_transformed, heart_poly, f"Entrada {n_superficie} booleano final")
                    scar_processed = invert_transform(transform, pre_scar_bool)
                    visualizer(scar_poly_transformed, heart_poly, f"Entrada {n_superficie} booleano final invertido")
                    print(f"Salvando a regiao {n_superficie} em scar_processed")
                else:
                    print(f"Salvando a regiao {n_superficie} em scar_processed")
                    # pre_scar_bool = bool_operation(pre_scar_bool, region, "Intersection")
                    # visualizer(pre_scar_bool, pre_scar_bool, f"Entrada {n_superficie} final")
                    scar_processed = pre_scar_bool
                    visualizer(scar_processed, heart_poly, f"Entrada {n_superficie} final")
            else:
                print(f"Salvando a superficie {n_superficie} em scar_processed")
                scar_processed = region
                visualizer(scar_processed, heart_poly, f"Entrada {n_superficie} final")
            
            print(f"Salvando a superficie {n_superficie} em scar_processed_list")
            scar_processed_list.append(scar_processed)
            n_superficie += 1
        
        print(f"Usando o append_filter para juntar scar_processed_list em scar_processed")
        scar_processed = append_filter(scar_processed_list)
        visualizer(scar_processed, heart_poly, f"Entrada {n_superficie} após append")
        print(f"Filtro aplicado com sucesso e salvo em scar_processed")
        print(f"Salvando scar_processed em stl")

        print(f"{scar_processed=}")
        
        if isinstance(scar_processed, vtk.vtkUnstructuredGrid):
            scar_processed = convert_to_polydata(scar_processed)

        scar_processed, center = clean_and_triangulate(scar_processed)
        # scar_processed = smoothPoly(scar_processed)
        WriteStl(scar_processed, file_name)
        WriteVtk(scar_processed, file_name_vtk)    
    else:
        print(f"Encontrada intersecção na fibrose... aplicando escala superior")
        scar_poly_transformed, transform = scalar_transform(scar_poly, center_scar, sup_scale)
        visualizer(scar_poly_transformed, heart_poly, f"Entrada inicial transformada")

        pre_scar_bool = bool_operation(scar_poly_transformed, heart_poly, "Intersection")
        visualizer(pre_scar_bool, heart_poly, f"Entrada inicial booleana")
        pre_scar_bool = invert_transform(transform, pre_scar_bool)
        visualizer(pre_scar_bool, heart_poly, f"Entrada inicial invertida")

        if intersection(pre_scar_bool, heart_poly):
            print(f"Encontrada intersecção na fibrose... aplicando escala inferior")
            scar_poly_transformed, transform = scalar_transform(scar_poly, center_scar, inf_scale)
            visualizer(scar_poly_transformed, heart_poly, f"Entrada final transformada")
            scar_processed = bool_operation(pre_scar_bool, heart_poly, "Intersection")
            visualizer(scar_processed, heart_poly, f"Entrada final booleano")
            scar_processed = invert_transform(transform, scar_processed)
            visualizer(scar_processed, heart_poly, f"Entrada final booleano")

            if intersection(scar_processed, heart_poly):
                print("Ainda há intersecções após o processo, aumente a escala da transformação superior e/ou inferior")
            else:
                print(f"Mais nenhuma intersecção encontrada, salvando o resultado booleano em scar_processed")
        else:
            print(f"Mais nenhuma intersecção encontrada, salvando o resultado booleano em scar_processed")
            scar_processed = pre_scar_bool
            visualizer(scar_processed, heart_poly, f"final")
        if isinstance(scar_processed, vtk.vtkUnstructuredGrid):
            scar_processed = convert_to_polydata(scar_processed)

        scar_processed, center = clean_and_triangulate(scar_processed)
        # scar_processed = smoothPoly(scar_processed)
        WriteStl(scar_processed, file_name)
        WriteVtk(scar_processed, file_name_vtk)     
else:

    os.system("Nenhuma intersecção encontrada, salvando arquivo como: {}".format(file_name))
    scar_processed = scar_poly
    visualizer(scar_processed, heart_poly, f"final")

    # if isinstance(scar_processed, vtk.vtkUnstructuredGrid):
        # scar_processed = convert_to_polydata(scar_processed)
    # scar_processed = smoothPoly(scar_processed)
    scar_processed, center = clean_and_triangulate(scar_processed)
    WriteStl(scar_processed, file_name)
    WriteVtk(scar_processed, file_name_vtk)
