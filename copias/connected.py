import vtk

def extract_surfaces(input_file):
    # Ler o arquivo de entrada
    reader = vtk.vtkPolyDataReader()
    reader.SetFileName(input_file)
    reader.Update()

    # Aplicar o filtro de conectividade
    connectivity_filter = vtk.vtkConnectivityFilter()
    connectivity_filter.SetInputConnection(reader.GetOutputPort())
    connectivity_filter.SetExtractionModeToAllRegions()  # Identificar todas as regiões conectadas
    connectivity_filter.ColorRegionsOn()  # Marca cada região com um ID único
    connectivity_filter.Update()

    # Obter o número de regiões conectadas
    num_regions = connectivity_filter.GetNumberOfExtractedRegions()
    print(f"Número de superfícies separadas encontradas: {num_regions}")

    # Armazenar as superfícies separadas como objetos vtkPolyData
    surfaces = []
    for region_id in range(num_regions):
        # Configurar o filtro para extrair apenas a região atual
        region_filter = vtk.vtkThreshold()
        region_filter.SetInputConnection(connectivity_filter.GetOutputPort())
        region_filter.SetInputArrayToProcess(0, 0, 0, vtk.vtkDataObject.FIELD_ASSOCIATION_CELLS, "RegionId")
        region_filter.ThresholdBetween(region_id, region_id)  # Filtra a região específica
        region_filter.Update()

        # Converter células para dados de superfície
        geometry_filter = vtk.vtkGeometryFilter()
        geometry_filter.SetInputConnection(region_filter.GetOutputPort())
        geometry_filter.Update()

        # Adicionar a superfície à lista
        surfaces.append(geometry_filter.GetOutput())

    return surfaces



# Exemplo de uso no script de booleanas
def main():
    input_vtk_file = "Patient_1_scar.vtk"  # Substitua pelo seu arquivo de entrada

    # Extrair as superfícies conectadas
    surfaces = extract_surfaces(input_vtk_file)

    # Usar as superfícies em operações booleanas
    # if len(surfaces) >= 2:
    #     surface1 = surfaces[0]
    #     surface2 = surfaces[1]

    #     booleanOperation = vtk.vtkBooleanOperationPolyDataFilter()
    #     booleanOperation.SetOperationToDifference()  # Escolha: Union, Intersection ou Difference
    #     booleanOperation.SetInputData(0, surface1)
    #     booleanOperation.SetInputData(1, surface2)
    #     booleanOperation.Update()

    #     # Renderizar a saída ou salvar o resultado
    #     result = booleanOperation.GetOutput()

    #     writer = vtk.vtkSTLWriter()
    #     writer.SetFileName("resultado_booleano.stl")
    #     writer.SetInputData(result)
    #     writer.Write()

    #     print("Operação booleana concluída e resultado salvo.")

    # else:
    #     print("Não há superfícies suficientes para realizar a operação booleana.")


if __name__ == "__main__":
    main()
