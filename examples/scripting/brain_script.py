import os
import sys

try:
    import vistrails
except:
    #try to append vistrails source dir relative to examples/scripting
    this_dir = os.path.split(__file__)[0]
    sys.path.append(os.path.join(this_dir, '../..'))
    import vistrails

from vistrails.core.application import init as vt_init
from vistrails.core.api import Package, get_api

#init vistrails
vt_app = vt_init()
vt_app.new_vistrail()
api = get_api()

urlpkg = 'org.vistrails.vistrails.url'
vtkpkg = 'edu.utah.sci.vistrails.vtk'

url = Package(urlpkg)
vtk = Package(vtkpkg)

#start with download file module
dlFA = url.DownloadFile()
dlFA.url = \
    'http://www.vistrails.org/download/download.php?type=DATA&id=gktbhFA.vtk'

#add and connect vtkDataSetReader
dataFA = api.add_and_connect_module(vtkpkg, 'vtkDataSetReader', 'SetFile',
                                    dlFA, 'file')

#add contour filter
contour = api.add_and_connect_module(vtkpkg, 'vtkContourFilter',
                                     'SetInputConnection0',
                                     dataFA, 'GetOutputPort0')
contour.SetValue = (0, 0.6)

#add normals, stripper, and probe filter
normals = api.add_and_connect_module(vtkpkg, 'vtkPolyDataNormals',
                                     'SetInputConnection0',
                                     contour, 'GetOutputPort0')
normals.SetFeatureAngle = 60.0

stripper = api.add_and_connect_module(vtkpkg, 'vtkStripper',
                                      'SetInputConnection0',
                                      normals, 'GetOutputPort0')

probe = api.add_and_connect_module(vtkpkg, 'vtkProbeFilter',
                                   'SetInputConnection0',
                                   stripper, 'GetOutputPort0')

#build other branch in reverse
colors = api.add_and_connect_module(vtkpkg, 'vtkImageMapToColors',
                                    'GetOutputPort0',
                                    probe, 'SetInputConnection1', True)
colors.SetOutputFormatToRGBA = True

lookup = api.add_and_connect_module(vtkpkg, 'vtkLookupTable', 'Instance',
                                    colors, 'SetLookupTable', True)
lookup.SetHueRange = (0.0, 0.8)
lookup.SetSaturationRange = (0.3, 0.7)
lookup.SetValueRange = (1.0, 1.0)

dataL123 = api.add_and_connect_module(vtkpkg, 'vtkDataSetReader',
                                      'GetOutputPort0',
                                      colors, 'SetInputConnection0', True)

dlL123 = api.add_and_connect_module(urlpkg, 'DownloadFile', 'file',
                                      dataL123, 'SetFile', True)

dlL123.url = \
    'http://www.vistrails.org/download/download.php?type=DATA&id=gktbhL123.vtk'

#finish bottom section
mapper = api.add_and_connect_module(vtkpkg, 'vtkPolyDataMapper',
                                    'SetInputConnection0',
                                    probe, 'GetOutputPort0')
mapper.ScalarVisibilityOn = True

actor = api.add_and_connect_module(vtkpkg, 'vtkActor', 'SetMapper',
                                   mapper, 'Instance')

prop = api.add_and_connect_module(vtkpkg, 'vtkProperty', 'Instance',
                                  actor, 'SetProperty', True)
prop.SetDiffuseColor = (1.0, 0.49, 0.25)
prop.SetOpacity = 0.7
prop.SetSpecular = 0.3
prop.SetSpecularPower = 2.0

renderer = api.add_and_connect_module(vtkpkg, 'vtkRenderer', 'AddActor',
                                      actor, 'Instance')

# Thought this used to work. Right now fails to convert to color when executed
#renderer.SetBackgroundWidget = 'white'

camera = api.add_and_connect_module(vtkpkg, 'vtkCamera', 'Instance',
                                    renderer, 'SetActiveCamera', True)
camera.SetFocalPoint = (15.666, 40.421, 39.991)
camera.SetPosition = (207.961, 34.197, 129.680)
camera.SetViewUp = (0.029, 1.0, 0.008)


cell = api.add_and_connect_module(vtkpkg, 'VTKCell', 'AddRenderer',
                                  renderer, 'Instance')

#write to file
api.save_vistrail('brain_from_script.vt')
