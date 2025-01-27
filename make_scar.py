import vtk
from vtkmodules.vtkFiltersSources import vtkSphereSource

def sphere_source_points():
    sphere_source = vtkSphereSource()
    sphere_source.SetCenter(0, 0, 0)
    sphere_source.SetPhiResolution(21)
    sphere_source.SetThetaResolution(21)
    sphere_source.Update()
    poly_data = sphere_source.GetOutput()

    return poly_data.GetPoints()


poly_data = vtk.vtkPolyData()
poly_data.SetPoints(sphere_source_points())

surf = vtk.vtkSurfaceReconstructionFilter()
surf.SetInputData(poly_data)

cf = vtk.vtkContourFilter()
cf.SetInputConnection(surf.GetOutputPort())
cf.SetValue(0, 0.0)

reverse = vtk.vtkReverseSense()
reverse.SetInputConnection(cf.GetOutputPort())
reverse.ReverseCellsOn()
reverse.ReverseNormalsOn()

mapper = vtk.vtkPolyDataMapper()
mapper.SetInputConnection(reverse.GetOutputPort())
mapper.ScalarVisibilityOff()

colors = vtk.vtkNamedColors()
surfaceActor = vtk.vtkActor()
surfaceActor.SetMapper(mapper);
surfaceActor.GetProperty().SetDiffuseColor(colors.GetColor3d("Tomato"))
surfaceActor.GetProperty().SetSpecularColor(colors.GetColor3d("Seashell"))
surfaceActor.GetProperty().SetSpecular(.4)
surfaceActor.GetProperty().SetSpecularPower(50)

render = vtk.vtkRenderer()
renderWindow = vtk.vtkRenderWindow()
renderWindow.AddRenderer(render)
renderWindow.SetSize(640, 480)

interactor = vtk.vtkRenderWindowInteractor()
interactor.SetRenderWindow(renderWindow)

render.AddActor(surfaceActor)
render.SetBackground(colors.GetColor3d("Burlywood"))

renderWindow.SetWindowName("SurfaceFromUnorganizedPoints")
renderWindow.Render()
interactor.Start()
# print(f"{poly_data}")
