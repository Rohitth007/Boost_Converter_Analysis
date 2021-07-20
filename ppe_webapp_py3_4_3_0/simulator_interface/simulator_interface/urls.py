"""simulator_interface URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf.urls import url
from django.urls import include, path, re_path
from django.contrib import admin
from simulations import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='homepage'),
    path('edit-simulation/<int:id>/', views.EditSimulation.as_view(), name='edit-simulation'),
    path('browse-simulation/<int:id>/', views.BrowseSimulation.as_view(), name='browse-simulation'),
    path('new-simulation/<int:id>/', views.NewSimulation.as_view(), name='change-simulation'),
    path('add-ckt-schematic/<int:id>/', views.AddCktSchematic.as_view(), name='add-ckt-schematic'),
    path('remove-ckt-schematic/<int:id>/<int:ckt_id>/', views.RemoveCktSchematic.as_view(), name='remove-ckt-schematic'),
    path('process-ckt-schematics/<int:id>/', views.ProcessCktSchematics.as_view(), name='process-ckt-schematics'),
    path('edit-ckt-parameters/<int:id>/', views.EditCktParameters.as_view(), name='edit-ckt-parameters'),
    path('edit-schematic-parameters/<int:id>/<int:ckt_id>/', views.EditSchematicParameters.as_view(), name='edit-schematic-parameters'),
    path('edit-comp-parameters/<int:id>/<int:ckt_id>/<str:comp_pos_3D>/', views.EditComponentParameters.as_view(), name='edit-comp-parameters'),
    path('import-ckt-parameters/<int:id>/<int:ckt_id>/', views.ImportCktParameters.as_view(), name='import-ckt-parameters'),
    path('export-ckt-parameters/<int:id>/<int:ckt_id>/', views.ExportCktParameters.as_view(), name='export-ckt-parameters'),
    path('edit-control-files/<int:id>/', views.AddControlFiles.as_view(), name='edit-control-files'),
    path('remove-control-file/<int:id>/<int:control_id>/', views.RemoveControlFile.as_view(), name='remove-control-file'),
    path('configure-control-file/<int:id>/<int:control_id>/', views.ConfigureControlFile.as_view(), name='configure-control-file'),
    path('add-control-input/<int:id>/<int:control_id>/', views.AddControlInput.as_view(), name='add-control-input'),
    path('delete-control-input/<int:id>/<int:control_id>/<int:input_id>/', views.DeleteControlInput.as_view(), name='delete-control-input'),
    path('add-control-output/<int:id>/<int:control_id>/', views.AddControlOutput.as_view(), name='add-control-output'),
    path('delete-control-output/<int:id>/<int:control_id>/<int:output_id>/', views.DeleteControlOutput.as_view(), name='delete-control-output'),
    path('add-control-staticvar/<int:id>/<int:control_id>/', views.AddControlStaticVar.as_view(), name='add-control-staticvar'),
    path('delete-control-staticvar/<int:id>/<int:control_id>/<int:staticvar_id>/', views.DeleteControlStaticVar.as_view(), name='delete-control-staticvar'),
    path('add-control-timeevent/<int:id>/<int:control_id>/', views.AddControlTimeEvent.as_view(), name='add-control-timeevent'),
    path('delete-control-timeevent/<int:id>/<int:control_id>/<int:timeevent_id>/', views.DeleteControlTimeEvent.as_view(), name='delete-control-timeevent'),
    path('add-control-varstore/<int:id>/<int:control_id>/', views.AddControlVarStore.as_view(), name='add-control-varstore'),
    path('delete-control-varstore/<int:id>/<int:control_id>/<int:varstore_id>/', views.DeleteControlVarStore.as_view(), name='delete-control-varstore'),
    path('import-control-parameters/<int:id>/<int:control_id>/', views.ImportControlParameters.as_view(), name='import-control-parameters'),
    path('export-control-parameters/<int:id>/<int:control_id>/', views.ExportControlParameters.as_view(), name='export-control-parameters'),
    path('view-output-page/<int:id>/', views.ViewOutputPage.as_view(), name='view-output-page'),
    path('run-simulation-page/<int:id>/', views.RunSimulationPage.as_view(), name='run-simulation-page'),
    path('stop-simulation-page/<int:id>/', views.StopSimulationPage.as_view(), name='stop-simulation-page'),
    path('add-plot/<int:id>/', views.AddPlot.as_view(), name='add-plot'),
    path('add-waveform/<int:id>/<int:plot_id>/', views.AddWaveform.as_view(), name='add-waveform'),
    path('delete-plot/<int:id>/<int:plot_id>/', views.DeletePlot.as_view(), name='delete-plot'),
    path('save-plot/<int:id>/', views.SavePlot.as_view(), name='save-plot'),
    path('generate-plot/<int:id>/<int:plot_id>/', views.GeneratePlot.as_view(), name='generate-plot'),
    path('load-simulation/<int:id>/', views.LoadSimulation.as_view(), name='load-simulation'),
    path('new-simulation/', views.NewSimulation.as_view(), name='new-simulation'),
    path('simulation-library/', views.simulation_library, name='simulation-library'),
    path('documentation/', views.doc_ppe, name='ppe-docs'),
    path('contact/', views.contact_ppe, name='ppe-contact'),
]
