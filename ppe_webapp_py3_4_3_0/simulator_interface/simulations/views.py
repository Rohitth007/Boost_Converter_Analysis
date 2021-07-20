import sys
import django
django.setup()
from django.shortcuts import render
from django.http import HttpResponse
from django.forms.models import model_to_dict
from django.views import View
from django.views.generic.base import TemplateView, RedirectView
from django.views.generic.edit import FormView
from .models import SimulationCase, SimulationCaseForm, CircuitSchematics
from .models import CircuitSchematicsForm, CircuitComponents
from . import models
import os
from . import network_reader as NwRdr
from . import circuit_elements as CktElem
from . import solver as Slv
from . import matrix
import multiprocessing
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as Matpyplot
from .circuit_solver import prepare_simulation_objects, simulation_iterations


# This is a dicitonary that contains the simulation function
# objects. This way, the server knows when a process is running
# and it can be terminated. The status of the process does not
# change when moving between URLs.
simulation_iteration_collection = {}



# Create your views here.


def index(request):
    return render(request, "index.html")


class SimulationData:
    """
    This class is a parent class to most other class views.
    It extracts a simulation model, reads the circuit files,
    processes circuits and checks for errors.
    """
    def get_sim_model(self):
        """
        Gets the simulation model instance from the
        GET request parameters.
        """
        if 'id' in self.kwargs:
            self.sim_id = int(self.kwargs['id'])
            self.sim_para_model = SimulationCase.objects.get(id=self.sim_id)
        else:
            self.sim_para_model = None
        return

    def get_circuit_files(self):
        """
        Get all the circuit schematics in a simulation model.
        """
        try:
            self.sim_para_model
        except:
            self.get_sim_model()
        if self.sim_para_model:
            self.ckt_file_list = self.sim_para_model.circuitschematics_set.all()
        else:
            self.ckt_file_list = None
        return

    def get_circuit_read_errors(self):
        """
        Check if any of the circuit schematics cannot be read.
        """
        self.ckt_read_errors = []
        self.ckt_errors = -1
        if self.ckt_file_list:
            for ckt_file_item in self.ckt_file_list:
                ckt_full_path = os.path.join(os.sep, \
                                            self.sim_para_model.sim_working_directory, \
                                            ckt_file_item.ckt_file_name)
                # Try to read the file.
                try:
                    check_ckt_file = open(ckt_full_path, "r")
                # If can't be read, it means file doesn't exist in the working directory.
                except:
                    self.ckt_read_errors.append('Circuit spreadsheet could not be read. \
Make sure it is in same directory as working directory above')
                    self.ckt_errors = 1
                else:
                    self.ckt_read_errors.append('')
        return

    def process_circuit_schematics(self):
        """
        This function also reads circuit schematics and
        generates component objects. It checks for network errors.
        """
        try:
            self.sim_para_model
        except:
            self.get_sim_model()

        self.get_circuit_files()
        self.nw_input = []
        self.conn_ckt_mat = []
        if self.ckt_file_list:
            for ckt_file_item in self.ckt_file_list:
                self.nw_input.append(ckt_file_item.ckt_file_name.split(".csv")[0])
                full_file_path = os.path.join(os.sep, \
                                            self.sim_para_model.sim_working_directory, \
                                            ckt_file_item.ckt_file_name)
                ckt_file_object = open(full_file_path, "r")
                # Read the circuit into conn_ckt_mat
                # Also performs a scrubbing of circuit spreadsheet
                self.conn_ckt_mat.append(NwRdr.csv_reader(ckt_file_object))

        # Making a list of the type of components in the
        # circuit.
        self.components_found, self.component_objects, self.ckt_error_list = \
                NwRdr.determine_circuit_components(self.conn_ckt_mat, self.nw_input)

        if not self.ckt_error_list:
            # Make lists of nodes and branches in the circuit.
            self.node_list, self.branch_map, self.node_branch_errors = \
                        NwRdr.determine_nodes_branches(self.conn_ckt_mat, self.nw_input)

            if self.node_branch_errors:
                self.ckt_error_list.extend(self.node_branch_errors)
        return

    def update_db_parameters(self):
        """
        Checks if the components in the circuit schematics
        exist in the database. If they do, their positions
        are updated. If they are new, database entries are
        created.
        """
        try:
            self.sim_para_model
        except:
            self.get_sim_model()
        try:
            self.components_found
        except:
            self.process_circuit_schematics()
        all_components = self.sim_para_model.circuitcomponents_set.all()
        for comp_types in self.components_found.keys():
            # Take every type of component found
            # item -> resistor, inductor etc
            for c1 in range(len(self.components_found[comp_types])):
                # Each component type will be occurring
                # multiple times. Iterate through every find.
                # The list corresponding to each component is
                # the unique cell position in the spreadsheet
                check_comp_exists = all_components.filter(comp_type=comp_types).\
                        filter(comp_tag=self.components_found[comp_types][c1][1])
                if check_comp_exists and len(check_comp_exists)==1:
                    old_comp_object = check_comp_exists[0]
                    old_comp_object.comp_number = c1 + 1
                    old_comp_object.comp_pos_3D = self.components_found[comp_types][c1][0]
                    old_comp_object.comp_pos = NwRdr.csv_element_2D(\
                                        NwRdr.csv_tuple(self.components_found[comp_types][c1][0])[1:])
                    sheet_number = NwRdr.csv_tuple(self.components_found[comp_types][c1][0])[0]
                    old_comp_object.comp_sheet = sheet_number
                    old_comp_object.sheet_name = self.nw_input[sheet_number] + ".csv"
                    old_comp_object.sim_case = self.sim_para_model
                    old_comp_object.save()
                    self.sim_para_model.save()
                else:
                    new_comp_object = CircuitComponents()
                    new_comp_object.comp_type = comp_types
                    new_comp_object.comp_number = c1 + 1
                    new_comp_object.comp_pos_3D = self.components_found[comp_types][c1][0]
                    new_comp_object.comp_pos = NwRdr.csv_element_2D(\
                                        NwRdr.csv_tuple(self.components_found[comp_types][c1][0])[1:])
                    sheet_number = NwRdr.csv_tuple(self.components_found[comp_types][c1][0])[0]
                    new_comp_object.comp_sheet = sheet_number
                    new_comp_object.sheet_name = self.nw_input[sheet_number] + ".csv"
                    new_comp_object.comp_tag = self.components_found[comp_types][c1][1]
                    new_comp_object.sim_case = self.sim_para_model
                    new_comp_object.save()
                    self.sim_para_model.save()

        for comp_items in self.component_objects.keys():
            self.component_objects[comp_items].init_db_values(
                self.sim_para_model,
                self.ckt_file_list,
                self.branch_map
            )

        # Generate a table of meters that can be used when designing
        # control interfaces.
        try:
            self.meter_list = self.sim_para_model.metercomponents_set.all()
        except:
            self.meter_list = []

        for comp_items in self.component_objects.keys():
            if self.component_objects[comp_items].is_meter=="yes":
                meter_found = False
                if self.meter_list:
                    check_meter = self.meter_list.\
                            filter(comp_type=self.component_objects[comp_items].type).\
                            filter(comp_tag=self.component_objects[comp_items].tag)
                    if check_meter and len(check_meter)==1:
                        old_meter_item = check_meter[0]
                        old_meter_item.ckt_file_name = \
                                self.component_objects[comp_items].sheet_name
                        old_meter_item.comp_pos_3D = \
                                self.component_objects[comp_items].pos_3D
                        old_meter_item.save()
                        self.sim_para_model.save()
                        meter_found = True
                    else:
                        meter_found = False
                if not meter_found:
                    new_meter_item = models.MeterComponents()
                    new_meter_item.comp_type = self.component_objects[comp_items].type
                    new_meter_item.comp_tag = self.component_objects[comp_items].tag
                    new_meter_item.comp_pos_3D = self.component_objects[comp_items].pos_3D
                    new_meter_item.ckt_file_name = self.component_objects[comp_items].sheet_name
                    new_meter_item.comp_name = self.component_objects[comp_items].type + \
                            "_" + self.component_objects[comp_items].tag
                    new_meter_item.sim_case = self.sim_para_model
                    new_meter_item.save()
                    self.sim_para_model.save()

        # Remove meters that have been deleted from the circuit
        for meter_item in self.sim_para_model.metercomponents_set.all():
            if meter_item.comp_pos_3D not in self.component_objects.keys():
                meter_item.delete()
                self.sim_para_model.save()

        # Generate a table of control components from circuit components
        # that can be used for designing control interfaces.
        try:
            self.control_comp_list = self.sim_para_model.controllablecomponents_set.all()
        except:
            self.control_comp_list = []

        for comp_items in self.component_objects.keys():
            if self.component_objects[comp_items].has_control=="yes":
                controllable_comp_found = False
                if self.control_comp_list:
                    check_control_comp = self.control_comp_list.\
                            filter(comp_type=self.component_objects[comp_items].type).\
                            filter(comp_tag=self.component_objects[comp_items].tag)
                    if check_control_comp and len(check_control_comp)==1:
                        old_control_item = check_control_comp[0]
                        old_control_item.ckt_file_name = \
                                self.component_objects[comp_items].sheet_name
                        old_control_item.comp_pos_3D = \
                                self.component_objects[comp_items].pos_3D
                        old_control_item.save()
                        self.sim_para_model.save()
                        controllable_comp_found = True
                    else:
                        controllable_comp_found = False
                if not controllable_comp_found:
                    new_control_item = models.ControllableComponents()
                    new_control_item.comp_type = self.component_objects[comp_items].type
                    new_control_item.comp_tag = self.component_objects[comp_items].tag
                    new_control_item.comp_pos_3D = self.component_objects[comp_items].pos_3D
                    new_control_item.ckt_file_name = self.component_objects[comp_items].sheet_name
                    new_control_item.comp_name = self.component_objects[comp_items].type + \
                            "_" + self.component_objects[comp_items].tag
                    new_control_item.control_tag = self.component_objects[comp_items].control_tag
                    new_control_item.sim_case = self.sim_para_model
                    new_control_item.save()
                    self.sim_para_model.save()

        # Delete any database entries that are no longer in the circuit.
        for c2 in range(len(all_components)-1, -1, -1):
            comp_exist = all_components[c2]
            comp_found = False
            c1 = 0
            if comp_exist.comp_type in self.components_found.keys():
                while c1<len(self.components_found[comp_exist.comp_type]) and comp_found==False:
                    if self.components_found[comp_exist.comp_type][c1][1]==comp_exist.comp_tag:
                        comp_found = True
                    c1 += 1

            if comp_found==False:
                comp_exist.delete()
                self.sim_para_model.save()
        return

    def get_plot_data(self):
        """
        Generate the list of plots.
        """
        return [
            self.sim_para_model.circuitplot_set.all(),
            self.sim_para_model.plotlines_set.all()
        ]



class NewSimulation(FormView, SimulationData):
    """
    This class creates a new simulation model instance.
    """
    template_name = 'edit_simulation.html'
    form_class = SimulationCaseForm
    success_url = '/edit-simulation/'

    def get_initial(self):
        initial = super().get_initial()
        self.get_sim_model()
        if self.sim_para_model:
            initial = model_to_dict(self.sim_para_model)
        return initial

    def form_valid(self, form):
        self.get_sim_model()
        if self.sim_para_model:
            new_simulation_form = SimulationCaseForm(self.request.POST or None, instance=self.sim_para_model)
        else:
            new_simulation_form = SimulationCaseForm(self.request.POST)
        new_simulation_case = new_simulation_form.save()
        self.success_url += str(new_simulation_case.id) + '/'
        return super().form_valid(form)


class EditSimulation(TemplateView, SimulationData):
    """
    This class lists the simulation parameters.
    """
    template_name = 'edit_simulation.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.get_sim_model()
        context['simulation'] = self.sim_para_model
        return context


class BrowseSimulation(TemplateView, SimulationData):
    """
    This class lists all the features in a simulation -
    adding circuits, editing parameters, adding control,
    and viewing the output.
    """
    template_name = 'new_simulation.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.get_sim_model()
        if self.sim_para_model:
            context['sim_id'] = self.sim_id
        return context


class AddCktSchematic(FormView, SimulationData):
    """
    This class creates and saves a form that saves
    a circuit schematic spreadsheet.
    """
    template_name = 'edit_circuit_schematic.html'
    form_class = CircuitSchematicsForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.get_sim_model()
        self.get_circuit_files()
        self.get_circuit_read_errors()
        ckt_schematic_form = zip(self.ckt_file_list, self.ckt_read_errors)

        context['sim_id'] = self.sim_id
        context['ckt_schematic_form'] = ckt_schematic_form
        context['ckt_errors'] = self.ckt_errors
        return context

    def form_valid(self, form):
        try:
            self.sim_id
        except:
            self.get_sim_model()
        self.success_url = '/add-ckt-schematic/' + str(self.sim_id) + '/'

        # Check the new circuit file for the same errors.

        received_ckt_file_form = CircuitSchematicsForm(self.request.POST)
        received_ckt_file = received_ckt_file_form.save(commit=False)
        received_ckt_file.ckt_file_name = self.request.POST['ckt_file_path']
        # ckt_file_path in request.POST contains the circuit file name because no
        # upload takes place and only file name is obtained.

        # Add the circuit file to the working directory path
        ckt_full_path = os.path.join(os.sep, \
                                self.sim_para_model.sim_working_directory, \
                                received_ckt_file.ckt_file_name)
        # Try to read the file.
        try:
            check_ckt_file = open(ckt_full_path, "r")
        # If can't be read, it means file doesn't exist in the working directory.
        except:
            form = CircuitSchematicsForm(self.request.POST)
            if form.is_valid():
                form.add_error('ckt_file_descrip', \
'Circuit spreadsheet could not be read. Make sure it is in same directory as working directory above')
            return super().form_invalid(form)

        # If it can be read, it could be a genuine file in which case save it.
        # Or else, it may not be a .csv file, in which case raise an error.
        else:
            if len(received_ckt_file.ckt_file_name.split("."))>1 and \
                    received_ckt_file.ckt_file_name.split(".")[-1]=="csv":
                repeated_circuit = False
                for other_ckt_files in self.sim_para_model.circuitschematics_set.all():
                    if received_ckt_file.ckt_file_name==other_ckt_files.ckt_file_name:
                        repeated_circuit = True
                if repeated_circuit:
                    form = CircuitSchematicsForm(self.request.POST)
                    form.add_error('ckt_file_descrip', \
                                    'Circuit schematic has already been added.')
                    return super().form_invalid(form)
                else:
                    received_ckt_file.ckt_sim_case = self.sim_para_model
                    received_ckt_file.save()
                    self.sim_para_model.save()
            else:
                form = CircuitSchematicsForm(self.request.POST)
                form.add_error('ckt_file_descrip', \
                                'Circuit schematic must be a .csv file.')
                return super().form_invalid(form)

        return super().form_valid(form)


class RemoveCktSchematic(RedirectView, SimulationData):
    """
    This class deletes a circuit schematic from a
    simulation model.
    """

    def get_redirect_url(self, *args, **kwargs):
        self.get_sim_model()
        ckt_id = int(self.kwargs['ckt_id'])
        ckt_obj = self.sim_para_model.circuitschematics_set.get(id=ckt_id)
        ckt_obj.delete()
        self.sim_para_model.save()
        self.url = '/add-ckt-schematic/' + str(self.sim_id) + '/'
        return super().get_redirect_url(*args, **kwargs)


class ProcessCktSchematics(TemplateView, SimulationData):
    """
    This class processes all the circuit schematics in a
    simulation model. It checks for errors in reading the
    circuit files or network and connectivity errors in the
    circuits.
    """
    template_name = "edit_circuit_schematic.html"

    def get_context_data(self, *args, **kwargs):
        error_codes = []
        self.get_sim_model()
        self.get_circuit_files()
        self.get_circuit_read_errors()
        self.process_circuit_schematics()
        if not self.ckt_error_list:
            self.update_db_parameters()
        ckt_schematic_form = zip(self.ckt_file_list, self.ckt_read_errors)

        # If no errors are generated from this processing, the user
        # can edit the parameters of the circuits.
        if not self.ckt_error_list:
            # sim_state = 3
            ckt_errors = 0
        else:
            ckt_errors = 1

        context = super().get_context_data(**kwargs)
        context['sim_id'] = self.sim_id
        context['ckt_schematic_form'] = ckt_schematic_form
        context['ckt_errors'] = ckt_errors
        context['ckt_error_list'] = self.ckt_error_list
        return context


class EditCktParameters(TemplateView, SimulationData):
    """
    This class edits the circuits in a simulation. Adding
    and removing circuits.
    """
    template_name = 'main_circuit_components.html'

    def get_context_data(self, *args, **kwargs):
        self.get_sim_model()
        self.get_circuit_files()

        ckt_error_list = []

        context = super().get_context_data(*args, **kwargs)
        context['sim_id'] = self.sim_id
        context['ckt_schematics_update'] = self.ckt_file_list
        context['ckt_error_list'] = ckt_error_list

        return context


class EditSchematicParameters(TemplateView, SimulationData):
    """
    Lists the parameters of the components in the circuit files.
    """
    template_name = 'edit_circuit_parameters.html'

    def get_context_data(self, *args, **kwargs):
        self.get_sim_model()
        self.get_circuit_files()
        self.process_circuit_schematics()
        if 'ckt_id' in self.kwargs:
            ckt_id = int(self.kwargs['ckt_id'])
        ckt_file = CircuitSchematics.objects.get(id=ckt_id)
        ckt_file_name = ckt_file.ckt_file_name
        all_comps_in_ckt = self.sim_para_model.circuitcomponents_set.filter(\
                sheet_name=ckt_file_name
        )
        for comp_item in all_comps_in_ckt:
            self.component_objects[comp_item.comp_pos_3D].assign_parameters(self.ckt_file_list)
        ckt_component_list = []

        # for comp_items in self.component_objects.keys():
        for comp_items in all_comps_in_ckt:
            # To list the components that have the same sheet
            # as the circuit file name.
            if self.component_objects[comp_items.comp_pos_3D].sheet_name== \
                    ckt_file_name:
                # Checks if a database entry has been created for
                # the component and updates if necessary.
                self.component_objects[comp_items.comp_pos_3D].\
                        create_form_values(
                            self.sim_para_model,
                            self.ckt_file_list,
                            self.branch_map
                        )

                comp_info = self.component_objects[comp_items.comp_pos_3D].\
                        comp_as_a_dict(ckt_file)
                comp_model = self.component_objects[comp_items.comp_pos_3D].\
                        list_existing_components(ckt_file)
                if comp_info:
                    # The 1 below means list the component
                    # with the object comp_info
                    # comp_form_data.append(1)
                    ckt_component_list.append([comp_info, comp_model, 1])

        context = super().get_context_data(*args, **kwargs)
        context['sim_id'] = self.sim_id
        context['ckt_id'] = ckt_id
        context['ckt_component_list'] = ckt_component_list
        context['ckt_errors'] = self.ckt_error_list
        return context


class EditComponentParameters(FormView, SimulationData):
    """
    Creates and saves a form for component parameters.
    """
    template_name = 'edit_circuit_parameters.html'

    def comp_data(self, *args, **kwargs):
        if 'ckt_id' in self.kwargs:
            ckt_id = int(self.kwargs['ckt_id'])
        if 'comp_pos_3D' in self.kwargs:
            comp_pos_3D = self.kwargs['comp_pos_3D']
        ckt_file = CircuitSchematics.objects.get(id=ckt_id)
        # The request contains the sim ID and the component position.
        # Check all the circuit schematics if the component
        # exists in the circuit.
        for ckt_file_item in self.ckt_file_list:
            recd_comp_item = self.component_objects[comp_pos_3D].\
                        list_existing_components(ckt_file_item)
            if recd_comp_item:
                break
        return [ckt_file, recd_comp_item, self.component_objects[comp_pos_3D]]

    def get_form_class(self, *args, **kwargs):
        form_class = super().get_form_class(*args, **kwargs)
        self.get_sim_model()
        self.get_circuit_files()
        self.process_circuit_schematics()
        ckt_file, recd_comp_item, recd_comp_object =  self.comp_data()
        recd_ckt_item = recd_comp_item.comp_ckt
        comp_form = recd_comp_object.comp_as_a_form(recd_ckt_item)
        self.initial = model_to_dict(comp_form[1])
        form_class = comp_form[0]
        return form_class

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        self.process_circuit_schematics()
        ckt_file, recd_comp_item, recd_comp_object =  self.comp_data()

        recd_ckt_item = recd_comp_item.comp_ckt
        comp_model_list = []
        comp_form_data = []
        if not self.ckt_error_list:
            for comp_items in self.component_objects.keys():
                if self.component_objects[comp_items].sheet_name== \
                        recd_ckt_item.ckt_file_name:
                    comp_info = self.component_objects[comp_items].\
                            comp_as_a_dict(recd_ckt_item)
                    comp_model = self.component_objects[comp_items].\
                            list_existing_components(recd_ckt_item)
                    if comp_info:
                        # If the component is the one to edited
                        # add 0 for a form, or else 1 to list it.
                        if comp_model==recd_comp_item:
                            comp_form_data = [comp_info, comp_model, 0]
                        else:
                            comp_model_list.append([comp_info, comp_model, 1])

        ckt_component_list = [comp_form_data]
        ckt_component_list.extend(comp_model_list)

        context['ckt_component_list'] = ckt_component_list
        context['sim_id'] = self.sim_id
        context['ckt_id'] = ckt_file.id
        context['ckt_errors'] = self.ckt_error_list
        return context

    def form_valid(self, form):
        self.process_circuit_schematics()
        ckt_file, recd_comp_item, recd_comp_object =  self.comp_data()
        recd_comp_object.update_form_data(
                            self.request,
                            recd_comp_item,
                            self.branch_map)
        self.sim_para_model.save()
        self.success_url = '/edit-schematic-parameters/' + str(self.sim_id) + '/' + \
                            str(ckt_file.id) + '/'
        return super().form_valid(form)


class ImportCktParameters(RedirectView, SimulationData):
    """
    This class imports circuit parameters from a spreadsheet.
    """
    def get_redirect_url(self, *args, **kwargs):
        self.get_sim_model()
        self.process_circuit_schematics()
        ckt_id = int(self.kwargs['ckt_id'])

        import_ckt_filename = self.request.POST.get('import_ckt_para')
        import_ckt_path = os.path.join(os.sep, \
                                    self.sim_para_model.sim_working_directory, \
                                    import_ckt_filename)
        import_csv_values = open(import_ckt_path, 'r')
        import_params = NwRdr.reading_params(import_csv_values)
        import_csv_values.close()

        ckt_obj = self.sim_para_model.circuitschematics_set.get(id=ckt_id)
        ckt_schematic_obj = CircuitSchematics.objects.get(id=ckt_id)
        ckt_schematic_complist = self.sim_para_model.circuitcomponents_set.filter(
                                    sheet_name=ckt_schematic_obj.ckt_file_name
                                )

        possible_comp_list = []
        for param_index in range(len(import_params)):
            import_params[param_index][0] = import_params[param_index][0].strip()
            import_params[param_index][1] = import_params[param_index][1].strip()
            import_params[param_index][2] = import_params[param_index][2].strip()
            comp_query = self.sim_para_model.circuitcomponents_set\
                                .filter(
                                    comp_type=import_params[param_index][0].lower(),
                                    comp_tag=import_params[param_index][1]
                                )
            if comp_query:
                possible_comp_list.append(comp_query[0])
            else:
                possible_comp_list.append([])

        for ckt_schematic_compitem in ckt_schematic_complist:
            comp_upload_found = False
            for param_index, possible_comp_item in enumerate(possible_comp_list):
                if possible_comp_item:
                    if (ckt_schematic_compitem.comp_pos_3D==possible_comp_item.comp_pos_3D):
                        comp_upload_found = True
                        break

            if comp_upload_found:
                self.component_objects[ckt_schematic_compitem.comp_pos_3D].get_values(
                        import_params[param_index][3:],
                        self.conn_ckt_mat
                    )
            else:
                self.component_objects[ckt_schematic_compitem.comp_pos_3D].assign_parameters(self.ckt_file_list)
            self.component_objects[ckt_schematic_compitem.comp_pos_3D].save_to_db(ckt_obj)

        self.sim_para_model.save()
        self.url = '/edit-schematic-parameters/' + str(self.sim_id) + '/' + str(ckt_id) + '/'
        return super().get_redirect_url(*args, **kwargs)


class ExportCktParameters(EditSchematicParameters):
    """
    This class exports the parameters of the components in a
    circuit to a spreadsheet with _params.csv appended.
    """

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        if 'ckt_id' in self.kwargs:
            ckt_id = int(self.kwargs['ckt_id'])
        ckt_file = self.sim_para_model.circuitschematics_set.get(id=ckt_id)

        params_for_csv = []
        for comp_key, comp_value in self.component_objects.items():
            comp_obj = CircuitComponents.objects.filter(
                comp_pos_3D=comp_key,
                sim_case=self.sim_para_model
            )[0]
            if (comp_obj.sheet_name==ckt_file.ckt_file_name):
                params_for_csv.append(self.component_objects[comp_key].export_values_to_csv())

        ckt_param_path = os.path.join(os.sep, \
                            self.sim_para_model.sim_working_directory, \
                            ckt_file.ckt_file_name.split('.')[0]+'_params.csv')
        try:
            param_file_obj = open(ckt_param_path, 'w')
        except:
            error_message = 'Cannot create spreadsheet. Make sure file with that name is not open already.'
        else:
            error_message = None
            for param_item in params_for_csv:
                for row_index in range(len(param_item)):
                    param_file_obj.write(str(param_item[row_index]))
                    if (row_index==len(param_item)-1):
                        param_file_obj.write('\n')
                    else:
                        param_file_obj.write(',')
        context['error_message'] = error_message
        return context


class AddControlFiles(FormView, SimulationData):
    """
    Creates and saves a form to add control files
    to the simulation.
    """

    template_name = 'add_control_files.html'
    form_class = models.ControlFileForm

    def get_context_data(self, *args, **kwargs):
        self.get_sim_model()
        control_files = self.sim_para_model.controlfile_set.all()
        control_error_list = []
        control_errors = -1
        # List the existing control files.
        for control_file_item in control_files:
            # This converts a model to a dictionary. The purpose is
            # to create a bound form from a model which is not
            # possible with only instance. Only with a bound form
            # can there be the is_valid method and add_error.
            control_item_dict = model_to_dict(control_file_item)
            control_full_path = os.path.join(os.sep, \
                                        self.sim_para_model.sim_working_directory, \
                                        control_file_item.control_file_name)

            # Try to read the file.
            try:
                check_control_file = open(control_full_path, "r")
                control_error_list.append('')
            # If can't be read, it means file doesn't exist in the working directory.
            except:
                control_error_list.append('Control file could not be read. Make sure it is in same directory as working directory above')
                control_errors = 1
        control_file_list = list(zip(control_files, control_error_list))

        context = super().get_context_data(*args, **kwargs)
        context['sim_id'] = self.sim_id
        context['control_file_list'] = control_file_list
        context['control_errors'] = control_errors
        context['control_error_list'] = control_error_list
        return context

    def form_valid(self, form):
        try:
            self.sim_id
        except:
            self.get_sim_model()
        control_file_name = self.request.POST.get('control_file')

        control_full_path = os.path.join(os.sep, \
                                self.sim_para_model.sim_working_directory, \
                                control_file_name)
        # Try to read the file.
        try:
            check_control_file = open(control_full_path, "r")
        # If can't be read, it means file doesn't exist in the working directory.
        except:
            form.add_error('control_file_descrip', \
                                    'Control file could not be read. \
Make sure it is in same directory as working directory above')
            return super().form_invalid(form)

        # If it can be read, it could be a genuine file in which case save it.
        # Or else, it may not be a .py file, in which case raise an error.
        else:
            if len(control_file_name.split("."))>1 and \
                    control_file_name.split(".")[-1]=="py":
                repeated_circuit = False
                for other_control_files in self.sim_para_model.controlfile_set.all():
                    if control_file_name==other_control_files.control_file_name:
                        repeated_circuit = True
                if repeated_circuit:
                    form.add_error('control_file_descrip', \
                                    'Control file has already been added.')
                    return super().form_invalid(form)
                else:
                    new_control_file = models.ControlFileForm(self.request.POST)
                    control_file = new_control_file.save(commit=False)
                    control_file.control_file_name = control_file_name
                    control_file.sim_case = self.sim_para_model
                    control_file.save()
                    self.sim_para_model.save()
            else:
                form.add_error('control_file_descrip', \
                                'Control file must be a .py file.')
                return super().form_invalid(form)

        self.success_url = '/edit-control-files/' + str(self.sim_id) + '/'
        return super().form_valid(form)


class RemoveControlFile(RedirectView, SimulationData):
    """
    This class removes control files from a simulation.
    """
    def get_redirect_url(self, *args, **kwargs):
        self.get_sim_model()
        if 'control_id' in self.kwargs:
            control_id = int(self.kwargs['control_id'])
        control_file = self.sim_para_model.controlfile_set.get(id=control_id)
        check_varstore = self.sim_para_model.controlvariablestorage_set.all()
        varstore_list = self.sim_para_model.controlvariablestorage_set.filter(
            control_file_name=control_file.control_file_name
        )
        for count in range(len(varstore_list)-1, -1, -1):
            varstore_list[count].delete()
        control_file.delete()
        self.sim_para_model.save()
        self.url = '/edit-control-files/' + str(self.sim_id) + '/'
        return super().get_redirect_url(*args, **kwargs)


class ListControlVariables(SimulationData):
    """
    This super class extracts all the control files and
    the special variables and their parameters.
    """
    def get_control_file(self):
        if 'control_id' in self.kwargs:
            self.control_id = int(self.kwargs['control_id'])

        self.config_control_file = models.ControlFile.objects.get(\
                id=self.control_id)
        return

    def get_control_variables(self, *args, **kwargs):
        self.get_sim_model()
        self.get_control_file()
        try:
            control_input_list = \
                    self.config_control_file.controlinputs_set.all()
        except:
            control_input_list = []
        if control_input_list:
            input_component_list = [input_item for input_item in control_input_list]
        else:
            input_component_list = []
        try:
            control_output_list = \
                    self.config_control_file.controloutputs_set.all()
        except:
            control_output_list = []
        if control_output_list:
            output_component_list = [output_item for output_item in control_output_list]
        else:
            output_component_list = []
        try:
            control_staticvar_list = \
                    self.config_control_file.controlstaticvariable_set.all()
        except:
            control_staticvar_list = []
        if control_staticvar_list:
            staticvar_component_list = [staticvar_item for staticvar_item in control_staticvar_list]
        else:
            staticvar_component_list = []
        try:
            control_timeevent_list = \
                    self.config_control_file.controltimeevent_set.all()
        except:
            control_timeevent_list = []
        if control_timeevent_list:
            timeevent_component_list = [timeevent_item for timeevent_item in control_timeevent_list]
        else:
            timeevent_component_list = []
        try:
            control_varstore_list = \
                    self.sim_para_model.controlvariablestorage_set.all().\
                    filter(control_file_name=self.config_control_file.control_file_name)
        except:
            control_varstore_list = []
        if control_varstore_list:
            varstore_component_list = [varstore_item for varstore_item in control_varstore_list]
        else:
            varstore_component_list = []
        return [
            input_component_list,
            output_component_list,
            staticvar_component_list,
            timeevent_component_list,
            varstore_component_list,
        ]

    def get_control_context(self, *args, **kwargs):
        control_component_list = self.get_control_variables(*args, **kwargs)
        control_context = {}
        control_context['sim_id'] = self.sim_id
        control_context['control_id'] = self.control_id
        control_context['control_component_list'] = control_component_list
        return control_context


class ConfigureControlFile(TemplateView, ListControlVariables):
    """
    This class lists the control variables in a control file.
    """
    template_name = 'config_control_files.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        control_context = self.get_control_context(*args, **kwargs)
        context.update(control_context)
        return context


class AddControlInput(FormView, ListControlVariables):
    """
    This class creates and saves a form to add a control
    input to the control file.
    """
    template_name = 'config_control_files.html'
    form_class = models.ControlInputsForm

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        control_context = self.get_control_context(*args, **kwargs)
        context.update(control_context)
        context['form_type'] = 1
        # Choosing inputs means the list of meters in a simulation case
        # is needed as a drop down box.
        try:
            meter_list = self.sim_para_model.metercomponents_set.all()
        except:
            meter_list = []
        context['meter_list'] = meter_list
        return context

    def form_valid(self, form):
        self.get_control_file()
        self.get_sim_model()
        received_input_form = models.ControlInputsForm(self.request.POST)
        new_control_input = received_input_form.save(commit=False)
        new_control_input.input_variable_name = \
                new_control_input.input_variable_name.strip()
        new_control_input.input_source = self.request.POST["input_source"]
        new_control_input.control_file = self.config_control_file
        new_control_input.save()
        self.config_control_file.save()
        self.sim_para_model.save()
        self.success_url = '/configure-control-file/' + str(self.sim_id) + \
                '/' + str(self.control_id) + '/'
        return super().form_valid(form)


class DeleteControlInput(RedirectView, ListControlVariables):
    """
    This class deletes a control input from a control file.
    """
    def get_redirect_url(self, *args, **kwargs):
        self.get_sim_model()
        self.get_control_file()
        if 'input_id' in self.kwargs:
            input_id = int(self.kwargs['input_id'])
        control_input = models.ControlInputs.objects.get(id=input_id)
        control_input.delete()
        self.config_control_file.save()
        self.sim_para_model.save()
        self.url = '/configure-control-file/' + str(self.sim_id) + \
                '/' + str(self.control_id) + '/'
        return super().get_redirect_url(*args, **kwargs)


class AddControlOutput(FormView, ListControlVariables):
    """
    This class creates and saves a form to add outputs to
    a control file.
    """
    template_name = 'config_control_files.html'
    form_class = models.ControlOutputsForm

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        control_context = self.get_control_context(*args, **kwargs)
        context.update(control_context)
        context['form_type'] = 2
        # Choosing inputs means the list of meters in a simulation case
        # is needed as a drop down box.
        try:
            control_model_list = self.sim_para_model.controllablecomponents_set.all()
        except:
            control_model_list = []

        controlmodel_name_list = []
        for control_model_item in control_model_list:
            controlmodel_name_list.append(control_model_item)
        context['control_model_list'] = controlmodel_name_list
        return context

    def form_valid(self, form):
        self.get_control_file()
        self.get_sim_model()
        received_output_form = self.form_class(self.request.POST)
        new_control_output = received_output_form.save(commit=False)
        new_control_output.output_variable_name = \
                new_control_output.output_variable_name.strip()
        new_control_output.output_target = self.request.POST["output_target"]
        new_control_output.control_file = self.config_control_file
        new_control_output.save()
        self.config_control_file.save()
        self.sim_para_model.save()
        self.success_url = '/configure-control-file/' + str(self.sim_id) + \
                '/' + str(self.control_id) + '/'
        return super().form_valid(form)


class DeleteControlOutput(RedirectView, ListControlVariables):
    """
    This class deletes an output from a control file.
    """
    def get_redirect_url(self, *args, **kwargs):
        self.get_sim_model()
        self.get_control_file()
        if 'output_id' in self.kwargs:
            input_id = int(self.kwargs['output_id'])
        control_output = models.ControlOutputs.objects.get(id=input_id)
        control_output.delete()
        self.config_control_file.save()
        self.sim_para_model.save()
        self.url = '/configure-control-file/' + str(self.sim_id) + \
                '/' + str(self.control_id) + '/'
        return super().get_redirect_url(*args, **kwargs)


class AddControlStaticVar(FormView, ListControlVariables):
    """
    This class creates and saves a form for static variables
    in a control file.
    """
    template_name = 'config_control_files.html'
    form_class = models.ControlStaticVariableForm

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        control_context = self.get_control_context(*args, **kwargs)
        context.update(control_context)
        context['form_type'] = 3
        return context

    def form_valid(self, form):
        self.get_control_file()
        self.get_sim_model()

        received_staticvar_form = self.form_class(self.request.POST)
        new_control_staticvar = received_staticvar_form.save(commit=False)
        new_control_staticvar.static_variable_name = new_control_staticvar.static_variable_name.strip()
        new_control_staticvar.control_file = self.config_control_file
        new_control_staticvar.save()
        self.config_control_file.save()
        self.sim_para_model.save()
        self.success_url = '/configure-control-file/' + str(self.sim_id) + \
                '/' + str(self.control_id) + '/'
        return super().form_valid(form)


class DeleteControlStaticVar(RedirectView, ListControlVariables):
    """
    This class deletes a static variable from a control file.
    """
    def get_redirect_url(self, *args, **kwargs):
        self.get_sim_model()
        self.get_control_file()
        if 'staticvar_id' in self.kwargs:
            staticvar_id = int(self.kwargs['staticvar_id'])
        control_staticvar = models.ControlStaticVariable.objects.get(id=staticvar_id)
        control_staticvar.delete()
        self.config_control_file.save()
        self.sim_para_model.save()
        self.url = '/configure-control-file/' + str(self.sim_id) + \
                '/' + str(self.control_id) + '/'
        return super().get_redirect_url(*args, **kwargs)


class AddControlTimeEvent(FormView, ListControlVariables):
    """
    This class creates and saves a form to add time events
    to a control file.
    """
    template_name = 'config_control_files.html'
    form_class = models.ControlTimeEventForm

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        control_context = self.get_control_context(*args, **kwargs)
        context.update(control_context)
        context['form_type'] = 4
        return context

    def form_valid(self, form):
        self.get_control_file()
        self.get_sim_model()

        received_timeevent_form = self.form_class(self.request.POST)
        new_control_timeevent = received_timeevent_form.save(commit=False)
        new_control_timeevent.time_event_name = new_control_timeevent.time_event_name.strip()
        new_control_timeevent.control_file = self.config_control_file
        new_control_timeevent.save()
        self.config_control_file.save()
        self.sim_para_model.save()
        self.success_url = '/configure-control-file/' + str(self.sim_id) + \
                '/' + str(self.control_id) + '/'
        return super().form_valid(form)


class DeleteControlTimeEvent(RedirectView, ListControlVariables):
    """
    This class deletes a time event from a control file.
    """
    def get_redirect_url(self, *args, **kwargs):
        self.get_sim_model()
        self.get_control_file()
        if 'timeevent_id' in self.kwargs:
            timeevent_id = int(self.kwargs['timeevent_id'])
        control_timeevent = models.ControlTimeEvent.objects.get(id=timeevent_id)
        control_timeevent.delete()
        self.config_control_file.save()
        self.sim_para_model.save()
        self.url = '/configure-control-file/' + str(self.sim_id) + \
                '/' + str(self.control_id) + '/'
        return super().get_redirect_url(*args, **kwargs)


class AddControlVarStore(FormView, ListControlVariables):
    """
    This class creates and saves a variable storage element
    to a simulation model.
    """
    template_name = 'config_control_files.html'
    form_class = models.ControlVariableStorageForm

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        control_context = self.get_control_context(*args, **kwargs)
        context.update(control_context)
        context['form_type'] = 5
        return context

    def form_valid(self, form):
        self.get_control_file()
        self.get_sim_model()

        received_varstore_form = self.form_class(self.request.POST)
        new_control_varstore = received_varstore_form.save(commit=False)
        new_control_varstore.variable_storage_name = new_control_varstore.variable_storage_name.strip()
        new_control_varstore.control_file_name = self.config_control_file.control_file_name
        new_control_varstore.sim_case = self.sim_para_model
        new_control_varstore.save()
        # self.config_control_file.save()
        self.sim_para_model.save()
        self.success_url = '/configure-control-file/' + str(self.sim_id) + \
                '/' + str(self.control_id) + '/'
        return super().form_valid(form)


class DeleteControlVarStore(RedirectView, ListControlVariables):
    """
    This class deletes a variable storage element from a simulation.
    """
    def get_redirect_url(self, *args, **kwargs):
        self.get_sim_model()
        self.get_control_file()
        if 'varstore_id' in self.kwargs:
            varstore_id = int(self.kwargs['varstore_id'])
        control_varstore = models.ControlVariableStorage.objects.get(id=varstore_id)
        control_varstore.delete()
        self.config_control_file.save()
        self.sim_para_model.save()
        self.url = '/configure-control-file/' + str(self.sim_id) + \
                '/' + str(self.control_id) + '/'
        return super().get_redirect_url(*args, **kwargs)


class ImportControlParameters(RedirectView, ListControlVariables):
    """
    This class imports the parameters for special variables for
    a control file from a descriptor spreadsheet.
    """
    def get_redirect_url(self, *args, **kwargs):
        self.get_sim_model()
        self.process_circuit_schematics()
        self.get_control_file()

        control_file_name = self.request.POST.get('import_control_para')
        control_full_path = os.path.join(os.sep, \
                            self.sim_para_model.sim_working_directory, \
                            control_file_name)

        NwRdr.extract_control_descriptor(self.component_objects, self.components_found, \
                        control_file_name, control_full_path, \
                        self.sim_para_model, self.control_id
                    )

        self.url = '/configure-control-file/' + str(self.sim_id) + \
                    '/' + str(self.control_id) + '/'
        return super().get_redirect_url(*args, **kwargs)


class ExportControlParameters(TemplateView, ListControlVariables):
    """
    This class exports the parameters of special variables in a
    control file to a speadsheet with _desc.csv appended.
    """
    template_name = 'config_control_files.html'

    def get_context_data(self, *args, **kwargs):
        self.get_sim_model()
        self.get_control_file()
        self.process_circuit_schematics()
        self.get_circuit_files()
        self.url = '/configure-control-file/' + str(self.sim_id) + \
                    '/' + str(self.control_id) + '/'
        context = super().get_context_data(*args, **kwargs)
        control_context = self.get_control_context()
        context.update(control_context)

        control_file_name = self.config_control_file.control_file_name
        control_file_name = control_file_name.split('.')[0] + '_desc.csv'
        control_full_path = os.path.join(os.sep, \
                            self.sim_para_model.sim_working_directory, \
                            control_file_name)

        for comp_items in self.component_objects.keys():
            self.component_objects[comp_items].assign_parameters(self.ckt_file_list)

        # If the file is already open, it can't be created.
        # So send an error message asking to close the file.
        try:
            control_desc_handles = open(control_full_path,"w")
        except:
            context['error_message'] = 'Cannot create file. Make sure file with same name is not open.'
            return context
        try:
            control_inputs = self.config_control_file.controlinputs_set.all()
        except:
            control_inputs = []
        try:
            control_outputs = self.config_control_file.controloutputs_set.all()
        except:
            control_outputs = []
        try:
            control_static_vars = self.config_control_file.controlstaticvariable_set.all()
        except:
            control_static_vars = []
        try:
            control_time_events = self.config_control_file.controltimeevent_set.all()
        except:
            control_time_events = []
        try:
            control_var_store = self.sim_para_model.controlvariablestorage_set.filter(
                    control_file_name=control_file_name.split('_desc')[0]+'.py')
        except:
            control_var_store = []

        for input_items in control_inputs:
            control_desc_handles.write("Input")
            control_desc_handles.write(", ")
            # Default input is the first available meter.
            control_desc_handles.write("Element name in circuit spreadsheet = {inp_src}".\
                                format(inp_src=input_items.input_source))
            control_desc_handles.write(", ")
            # Default name of the meter in the control code is the
            # meter name_meter tag.
            control_desc_handles.write("Desired variable name in control code = {inp_var}".\
                                format(inp_var=input_items.input_variable_name))
            control_desc_handles.write(", ")
            control_desc_handles.write("\n")

        for output_items in control_outputs:
            comp_items_of_type = self.components_found[output_items.output_target.split('_')[0].lower()]
            for comp_item in comp_items_of_type:
                if (comp_item[1]==output_items.output_target.split('_')[-1]):
                    comp_control_tag = self.component_objects[comp_item[0]].control_tag[0]
            control_desc_handles.write("Output")
            control_desc_handles.write(", ")
            control_desc_handles.write("Element name in circuit spreadsheet = {var_name}".\
                        format(var_name=output_items.output_target))
            control_desc_handles.write(", ")
            control_desc_handles.write("Control tag defined in parameters spreadsheet = {control_tag}".\
                        format(control_tag=comp_control_tag))
            control_desc_handles.write(", ")
            control_desc_handles.write("Desired variable name in control code = {control_name}".\
                        format(control_name=output_items.output_variable_name))
            control_desc_handles.write(", ")
            control_desc_handles.write("Initial output value = {var_val}".\
                        format(var_val=output_items.output_initial_value))
            control_desc_handles.write(", ")
            control_desc_handles.write("\n")

        for statvar_items in control_static_vars:
            control_desc_handles.write("StaticVariable")
            control_desc_handles.write(", ")
            control_desc_handles.write("Desired variable name in control code = {var_name}".\
                        format(var_name=statvar_items.static_variable_name))
            control_desc_handles.write(", ")
            control_desc_handles.write("Initial value of variable = {var_val}".\
                        format(var_val=str(statvar_items.static_initial_value)))
            control_desc_handles.write(", ")
            control_desc_handles.write("\n")

        for tevent_items in control_time_events:
            control_desc_handles.write("TimeEvent")
            control_desc_handles.write(", ")
            control_desc_handles.write("Desired variable name in control code = {var_name}".\
                        format(var_name=tevent_items.time_event_name))
            control_desc_handles.write(", ")
            control_desc_handles.write("First time event = {var_val}".\
                        format(var_val=str(tevent_items.initial_time_value)))
            control_desc_handles.write(", ")
            control_desc_handles.write("\n")

        for varstore_items in control_var_store:
            control_desc_handles.write("VariableStorage")
            control_desc_handles.write(", ")
            control_desc_handles.write("Desired variable name in control code = {var_name}".\
                        format(var_name=varstore_items.variable_storage_name))
            control_desc_handles.write(", ")
            control_desc_handles.write("Initial value of variable = {var_val}".\
                        format(var_val=varstore_items.storage_initial_value))
            control_desc_handles.write(", ")
            if (varstore_items.storage_status=='Y'):
                control_desc_handles.write("Plot variable in output file = yes")
            else:
                control_desc_handles.write("Plot variable in output file = no")
            control_desc_handles.write(", ")
            control_desc_handles.write("\n")

        return context


class ViewOutputPage(TemplateView, SimulationData):
    """
    This class lists the output page of the simulation.
    """
    template_name = 'output_interface.html'

    def get_context_data(self, *args, **kwargs):
        self.get_sim_model()
        self.get_circuit_files()
        self.get_circuit_read_errors()
        ckt_error_list = [error for error in self.ckt_read_errors if error]
        if not ckt_error_list:
            self.process_circuit_schematics()
        ckt_error_list.extend(self.ckt_error_list)
        if not self.ckt_error_list:
            circuit_analysis_components = [self.node_list, self.branch_map]
        else:
            circuit_analysis_components = []

        if not ckt_error_list:
            for ckt_file_item in self.ckt_file_list:
                for comp_keys in self.component_objects.keys():
                    comp_error = self.component_objects[comp_keys].\
                        pre_run_check(ckt_file_item, circuit_analysis_components[1])
                    if comp_error:
                        ckt_error_list.extend(comp_error)

        # Checks if the simulation is running by
        # checking is the simulation case id exists in the
        # simulation iteration dictionary. As long as the simulation
        # runs, the stop button will be displayed.
        # if not ckt_error_list:
        if "sim"+str(self.sim_para_model.id) in simulation_iteration_collection.keys():
            run_state = 1
        else:
            run_state = 0

        # Lists the plots already designed.
        plot_list, plotlines_list = self.get_plot_data()

        context = super().get_context_data(*args, **kwargs)
        context['sim_id'] = self.sim_id
        context['run_state'] = run_state
        context['ckt_error_list'] = ckt_error_list
        context['plot_list'] = plot_list
        context['plotlines_list'] = plotlines_list
        return context


class RunSimulationPage(TemplateView, ListControlVariables):
    """
    This class runs the circuit simulation in the background
    and returns back to the output page.
    """
    template_name = 'output_interface.html'

    def get_context_data(self, *args, **kwargs):
        self.get_sim_model()
        self.get_circuit_files()
        self.process_circuit_schematics()

        # Update the component object parameters from the database.
        if not self.ckt_error_list:
            for comp_keys in self.component_objects.keys():
                self.component_objects[comp_keys].\
                    assign_parameters(self.ckt_file_list)

        # A last check for component errors particularly in polarity.
        if not self.ckt_error_list:
            for ckt_file_item in self.ckt_file_list:
                for comp_keys in self.component_objects.keys():
                    comp_error = self.component_objects[comp_keys].\
                        pre_run_check(ckt_file_item, self.branch_map)
                    if comp_error:
                        ckt_error_list.extend(comp_error)

        # Generate a list of all the data objects needed for the
        # simulation process.
        if not self.ckt_error_list:
            synthesized_ckt_comps = prepare_simulation_objects(
                        self.sim_para_model, \
                        [self.components_found, self.component_objects], \
                        [self.node_list, self.branch_map], \
                        self.conn_ckt_mat)

            # When the run button is clicked, any updates in the
            # ciircuit in the form of new meters or variablestorage
            # elements will be calculated so that they can be plotted.
            meter_list = synthesized_ckt_comps["meter_list"]
            # Check all the entries in the plotlines data base. This is
            # a collection of all the data entries in the output data file.
            # First check the meters. If not a single meter is found, create
            # an default model with the first meter in the list.
            try:
                all_circuit_plotlines = self.sim_para_model.plotlines_set.all()
            except:
                new_plotline = models.PlotLines()
                new_plotline.line_name = \
                                self.component_objects[meter_list[0]].type + "_" + \
                                        self.component_objects[meter_list[0]].tag
                new_plotline.line_type = "M"
                new_plotline.line_pos = 1
                new_plotline.sim_case = self.sim_para_model
                new_plotline.save()
                self.sim_para_model.save()

            # If a meter exists in the table, update the details
            # especially the column position in the output data file.
            # If it doesn't exist, create a new entry.
            for meter_item in meter_list:
                meter_waveform = \
                        self.component_objects[meter_item].type + "_" + \
                        self.component_objects[meter_item].tag
                check_plotline = \
                        all_circuit_plotlines.filter(line_type="M").\
                        filter(line_name=meter_waveform)

                if check_plotline and len(check_plotline)==1:
                    old_plotline = check_plotline[0]
                    old_plotline.line_pos = meter_list.index(meter_item) + 1
                    old_plotline.save()
                    self.sim_para_model.save()
                else:
                    new_plotline = models.PlotLines()
                    new_plotline.line_name = \
                            self.component_objects[meter_item].type + "_" + \
                            self.component_objects[meter_item].tag
                    new_plotline.line_type = "M"
                    new_plotline.line_pos = meter_list.index(meter_item) + 1
                    new_plotline.sim_case = self.sim_para_model
                    new_plotline.save()
                    self.sim_para_model.save()

            # Delete extra meters that don't exist.
            meter_circuit_plotlines = self.sim_para_model.plotlines_set.\
                            filter(line_type="M")
            for c1 in range(len(meter_circuit_plotlines)-1, -1, -1):
                meter_extra = True
                for c2 in range(len(meter_list)):
                    meter_plot_name = self.component_objects[meter_list[c2]].type + \
                            "_" + self.component_objects[meter_list[c2]].tag
                    if meter_circuit_plotlines[c1].line_name==meter_plot_name:
                        meter_extra = False
                if meter_extra:
                    meter_circuit_plotlines[c1].delete()
                    self.sim_para_model.save()

            # Do the same for variable storage elements from
            # the plotted variable list.
            plotted_variable_list = synthesized_ckt_comps["plotted_variable_list"]
            for varstore_item in plotted_variable_list:
                check_plotline = \
                        all_circuit_plotlines.filter(line_type="V").\
                        filter(line_name=varstore_item)

                if check_plotline and len(check_plotline)==1:
                    old_plotline = check_plotline[0]
                    old_plotline.line_pos = len(meter_list) + \
                            plotted_variable_list.index(varstore_item) + 1
                    old_plotline.save()
                    self.sim_para_model.save()
                else:
                    new_plotline = models.PlotLines()
                    new_plotline.line_name = varstore_item
                    new_plotline.line_type = "V"
                    new_plotline.line_pos = len(meter_list) + \
                            plotted_variable_list.index(varstore_item) + 1
                    new_plotline.sim_case = self.sim_para_model
                    new_plotline.save()
                    self.sim_para_model.save()

            # Delete extra variable storage elements that don't exist.
            varstore_plotlines = self.sim_para_model.plotlines_set.\
                            filter(line_type="V")
            for c1 in range(len(varstore_plotlines)-1, -1, -1):
                varstore_extra = True
                for c2 in range(len(plotted_variable_list)):
                    if varstore_plotlines[c1].line_name==\
                            plotted_variable_list[c2]:
                        varstore_extra = False
                if varstore_extra:
                    varstore_plotlines[c1].delete()
                    self.sim_para_model.save()

            # Check whether every branch has a resistance.
            components_in_branch = synthesized_ckt_comps["components_in_branch"]
            comp_types_with_resistance = ["Resistor", \
                        "Voltmeter", \
                        "Diode", \
                        "Switch", \
                        "Thyristor", \
                        "VariableResistor"]
            for branch_check in components_in_branch:
                resistor_found = False
                for branch_comps in branch_check:
                    if self.component_objects[branch_comps].type in \
                                comp_types_with_resistance:
                        resistor_found = True
                if not resistor_found:
                    branch_error = "Branch with "
                    for branch_comps in branch_check:
                        branch_error += self.component_objects[branch_comps].type + \
                                "_" + self.component_objects[branch_comps].tag
                        if len(branch_check)>1:
                            branch_error += ", "
                    branch_error += " does not have a resistor."
                    self.ckt_error_list.append(branch_error)

        # run_state = int(self.kwargs['run_state'])
        # If no errors have been detected so far, the simulation can
        # be started. The simulation starts as a process and runs
        # in the background independently. The object containing the
        # process is stored in the dictionary simulation_iterations
        # to keep track of the simulations being executed.
        if not self.ckt_error_list:
            if "sim"+str(self.sim_para_model.id) not in simulation_iteration_collection.keys():
                simulator_loop = multiprocessing.Process(target=simulation_iterations, \
                        kwargs={'sim_id':self.sim_id, \
                            'synthesized_ckt_comps':synthesized_ckt_comps, })
                simulator_loop.start()
                simulation_iteration_collection["sim"+str(self.sim_para_model.id)] = \
                        simulator_loop
            run_state = 1
        else:
            run_state = 0

        # Display the plots already designed.
        plot_list, plotlines_list = self.get_plot_data()

        context = super().get_context_data(*args, **kwargs)
        context['sim_id'] = self.sim_id
        context['run_state'] = run_state
        context['ckt_error_list'] = self.ckt_error_list
        context['plot_list'] = plot_list
        context['plotlines_list'] = plotlines_list
        return context


class StopSimulationPage(TemplateView, ListControlVariables):
    """
    This class stops the simulation and returns to the output page.
    """
    template_name = 'output_interface.html'

    def get_context_data(self, *args, **kwargs):
        self.get_sim_model()
        if "sim"+str(self.sim_para_model.id) in simulation_iteration_collection.keys():
            simulator_loop = \
                    simulation_iteration_collection["sim"+str(self.sim_para_model.id)]
            simulator_loop.terminate()
            del simulation_iteration_collection["sim"+str(self.sim_para_model.id)]

        ckt_error_list = []
        # This is the stopped state.
        run_state = 2

        # List of plots.
        plot_list, plotlines_list = self.get_plot_data()

        context = super().get_context_data(*args, **kwargs)
        context['sim_id'] = self.sim_id
        context['run_state'] = run_state
        context['ckt_error_list'] = ckt_error_list
        context['plot_list'] = plot_list
        context['plotlines_list'] = plotlines_list
        return context


class AddPlot(FormView, SimulationData):
    """
    This class creates and saves a form for creating a circuit plot.
    """
    template_name = 'output_interface.html'
    form_class = models.CircuitPlotForm

    def get_context_data(self, *args, **kwargs):
        self.get_sim_model()

        # Check if the simulation is running.
        if "sim"+str(self.sim_para_model.id) in simulation_iteration_collection.keys():
            run_state = 1
        else:
            run_state = 0

        # Generate the list of plots.
        plot_list, plotlines_list = self.get_plot_data()
        ckt_error_list = []

        context = super().get_context_data(*args, **kwargs)
        context['sim_id'] = self.sim_id
        context['run_state'] = run_state
        context['ckt_error_list'] = ckt_error_list
        context['plot_list'] = plot_list
        context['plotlines_list'] = plotlines_list
        context['form_type'] = 1
        return context

    def form_valid(self, form):
        self.get_sim_model()
        new_plot_form = self.form_class(self.request.POST)
        new_plot = new_plot_form.save(commit=False)
        new_plot.sim_case = self.sim_para_model
        new_plot.save()
        self.success_url = '/add-waveform/' + str(self.sim_id) + \
                            '/' + str(new_plot.id) + '/'
        return super().form_valid(form)


class DeletePlot(RedirectView, SimulationData):
    """
    This class deletes a circuit plot from the simulation.
    """
    def get_redirect_url(self, *args, **kwargs):
        self.get_sim_model()
        plot_id = int(self.kwargs['plot_id'])
        ckt_plot = models.CircuitPlot.objects.get(id=plot_id)
        ckt_plot.delete()
        self.sim_para_model.save()
        self.url = '/view-output-page/' + str(self.sim_id) + '/'
        return super().get_redirect_url(*args, **kwargs)


class SavePlot(RedirectView, SimulationData):
    """
    This class completes the circuit plot editing
    and returns to the output page.
    """
    def get_redirect_url(self, *args, **kwargs):
        self.get_sim_model()
        self.url = '/view-output-page/' + str(self.sim_id) + '/'
        return super().get_redirect_url(*args, **kwargs)


class AddWaveform(FormView, SimulationData):
    """
    This class creates and saves a form for adding
    waveforms to a circuit plot.
    """
    template_name = 'output_interface.html'
    form_class = models.CircuitWaveformsForm

    def get_context_data(self, *args, **kwargs):
        # Check if the simulation is running.
        self.get_sim_model()
        if "sim"+str(self.sim_para_model.id) in simulation_iteration_collection.keys():
            run_state = 1
        else:
            run_state = 0

        # Generate the list of plots.
        plot_list, plotlines_list = self.get_plot_data()
        ckt_error_list = []

        plot_id = int(self.kwargs['plot_id'])

        context = super().get_context_data(*args, **kwargs)
        context['sim_id'] = self.sim_id
        context['run_state'] = run_state
        context['ckt_error_list'] = ckt_error_list
        context['plot_list'] = plot_list
        context['plotlines_list'] = plotlines_list
        context['new_plot'] = models.CircuitPlot.objects.get(id=plot_id)
        context['new_plot_id'] = plot_id
        context['form_type'] = 2
        return context

    def form_valid(self, form):
        self.get_sim_model()
        plot_id = int(self.kwargs['plot_id'])
        new_waveform_form = self.form_class(self.request.POST)
        new_waveform = new_waveform_form.save(commit=False)
        ckt_plot = models.CircuitPlot.objects.get(id=plot_id)
        new_waveform.circuit_plot = ckt_plot
        new_waveform.save()
        plotline_received = self.request.POST['waveform_source']
        plotline_obj = models.PlotLines.objects.filter(
            sim_case=self.sim_para_model,
            line_name=plotline_received
        )[0]
        new_waveform.waveform.add(plotline_obj)
        new_waveform.save()
        ckt_plot.save()
        self.sim_para_model.save()
        self.success_url = '/add-waveform/' + str(self.sim_id) + \
                            '/' + str(plot_id) + '/'
        return super().form_valid(form)


class GeneratePlot(RedirectView, SimulationData):
    """
    This class generates a plot.
    """
    def get_redirect_url(self, *args, **kwargs):
        self.get_sim_model()
        plot_id = int(self.kwargs['plot_id'])

        ckt_plot_item = self.sim_para_model.circuitplot_set.get(id=plot_id)

        # The plot will contain a x axis, multiple y axis
        #  and the scales of the waveforms and multiple y-labels.
        y_var_indices = []
        y_var = []
        y_var_labels = []
        y_var_scale = []
        for waveform_items in ckt_plot_item.circuitwaveforms_set.all():
            y_var_labels.append(waveform_items.waveform_legend)
            y_var_scale.append(float(waveform_items.waveform_scale))
            for waveform_plots in waveform_items.waveform.all():
                y_var_indices.append(waveform_plots.line_pos)
                y_var.append([])

        # Get the list of files to be read depending
        # on whether the output file is sliced.
        if self.sim_para_model.sim_output_slice=="Yes":
            output_file_list = []
            outputfilename = self.sim_para_model.sim_output_file.split(".")[0]
            outputfileext = self.sim_para_model.sim_output_file.split(".")[1]
            for c1 in range(1, self.sim_para_model.sim_div_number+1):
                output_file_list.append(outputfilename+str(c1))

            outputfile_path = []
            for file_item in output_file_list:
                outputfile_path.append(os.path.join(os.sep, \
                        self.sim_para_model.sim_working_directory, \
                        file_item+"."+outputfileext))
        else:
            outputfile_path = [os.path.join(os.sep, \
                self.sim_para_model.sim_working_directory, \
                self.sim_para_model.sim_output_file), ]

        # Get the x and y axis values.
        x_var = []
        for file_item in outputfile_path:
            # Try to read the file.
            try:
                outputfile = open(file_item, "r")
            except:
                pass
            else:
                for line_output in outputfile:
                    try:
                        xvalue = float(line_output.split()[0])
                    except:
                        pass
                    else:
                        x_var.append(xvalue)

                    for c1 in range(len(y_var)):
                        try:
                            yvalue = float(line_output.split()\
                                        [y_var_indices[c1]])
                        except:
                            pass
                        else:
                            y_var[c1].append(yvalue*y_var_scale[c1])

        # In case the file was in progress, some columns
        # may be smaller in which case delete the last 5 rows.
        for c1 in range(len(x_var)-1, len(x_var)-5, -1):
            try:
                del x_var[c1]
            except:
                pass

        for c1 in range(len(y_var)):
            for c2 in range(len(y_var[c1])-1, len(x_var)-1, -1):
                try:
                    del y_var[c1][c2]
                except:
                    pass

        # Extract the start time and check if it is within range
        if "start_time" in self.request.POST:
            try:
                start_time = float(self.request.POST["start_time"])
            except:
                start_time = 0.0
            else:
                if start_time<x_var[0] or start_time>x_var[-1]:
                    start_time = 0.0

        # Extract the stop time and check if it is within range
        if "stop_time" in self.request.POST:
            try:
                stop_time = float(self.request.POST["stop_time"])
            except:
                stop_time = x_var[-1]
            else:
                if stop_time<x_var[0] or stop_time>x_var[-1]:
                    stop_time = x_var[-1]

        # Extract the y lower limit
        if "ylim_lower" in self.request.POST:
            try:
                ylim_lower = float(self.request.POST["ylim_lower"])
            except:
                ylim_lower = None

        # Extract the y upper limit
        if "ylim_upper" in self.request.POST:
            try:
                ylim_upper = float(self.request.POST["ylim_upper"])
            except:
                ylim_upper = None

        # Check if stop time is greater than start time.
        if start_time > stop_time:
            start_time, stop_time = stop_time, start_time

        # Create the name of the .PNG file
        figoutputname = ""
        for c1 in ckt_plot_item.plot_title.split():
            figoutputname += c1
        figoutputname += ".png"
        # Delete the figurefile if it exists.
        figfile_path = os.path.join(os.sep, \
            self.sim_para_model.sim_working_directory, \
            figoutputname)
        try:
            os.remove(figfile_path)
        except:
            pass

        # Plot the file
        for c1 in range(len(y_var)):
            Matpyplot.plot(x_var, y_var[c1], label=y_var_labels[c1])
            Matpyplot.xlim([start_time, stop_time])
            if (ylim_lower and ylim_upper):
                Matpyplot.ylim([ylim_lower, ylim_upper])
            Matpyplot.legend()
        # Save the file.
        Matpyplot.savefig(figfile_path)
        # Matpyplot.show()
        # This is necessary to start a fresh plot the next plot.
        Matpyplot.close()

        self.url = '/view-output-page/' + str(self.sim_id) + '/'
        return super().get_redirect_url(*args, **kwargs)


class LoadSimulation(RedirectView):
    """
    This class loads a simulation by going to the
    listing simulation parameter page.
    """
    def get_redirect_url(self, *args, **kwargs):
        sim_id = int(self.kwargs['id'])
        self.url = '/edit-simulation/' + str(sim_id) + '/'
        return super().get_redirect_url(*args, **kwargs)


def simulation_library(request):
    """
    This function lists the existing simulation cases.
    """
    simulation_collection = SimulationCase.objects.all()
    return render(request,
                "list_simulation.html",
                {'simulation_collection' : simulation_collection, })


def doc_ppe(request):
    """
    This function renders the documentation page.
    """
    return render(request, "documentation.html")


def contact_ppe(request):
    """
    This function renders the contact page.
    """
    return render(request, "contact.html")
