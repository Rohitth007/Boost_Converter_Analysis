#! /usr/bin/env python

import sys
import math
from . import circuit_exceptions as CktEx
from . import network_reader as NwRdr
from django.forms.models import model_to_dict
from .models import SimulationCase, SimulationCaseForm, CircuitSchematics
from .models import CircuitSchematicsForm, CircuitComponents
from . import models

class Resistor:
    """
    Resistor class. Contains functions to initiliaze
    the resistor according to name tag, unique cell position,
    update system matrix on each iteration.
    """

    def __init__(self, res_index, res_pos, res_tag, nw_input):
        """
        Constructor to initialize value.
        Also, takes in the identifiers -
        index (serial number), cell position and tag.
        """
        self.type = "Resistor"
        self.number = res_index
        self.pos_3D = res_pos
        self.sheet = NwRdr.csv_tuple(res_pos)[0]
        self.pos = NwRdr.csv_element_2D(NwRdr.csv_tuple(res_pos)[1:])
        self.sheet_name = nw_input[self.sheet] + ".csv"
        self.tag = res_tag
        self.has_voltage = "no"
        self.is_meter = "no"
        self.has_control = "no"
        self.resistor = 100.0
        self.voltage = 0.0
        self.current = 0.0

        return

    def display(self):
        """
        Displays info about the component.
        """
        print("Resistor is {}={} located at {} in sheet {}".format(
            self.tag, self.resistor, self.pos, self.sheet_name
        ))

        return

    def ask_values(self, x_list, ckt_mat, sys_branch):
        """
        Writes the values needed to the spreadsheet.
        """
        res_params = ["Resistor"]
        res_params.append(self.tag)
        res_params.append(self.pos)
        res_params.append(self.resistor)
        x_list.append(res_params)

        return

    def export_values_to_csv(self):
        """
        Writes the values needed to the spreadsheet.
        """
        res_params = ["Resistor"]
        res_params.append(self.tag)
        res_params.append(self.pos)
        res_params.append(self.resistor)

        return res_params

    def get_values(self, x_list, ckt_mat):
        """
        Takes the parameter from the spreadsheet.
        """
        self.resistor = float(x_list[0])

        return

    def determine_branch(self, sys_branches):
        """
        Determines which branch the component is found in.
        """
        for c1 in range(len(sys_branches)):
            if NwRdr.csv_tuple(self.pos_3D) in sys_branches[c1]:
                self.component_branch_pos = c1

        return

    def transfer_to_sys(self, sys_loops, mat_e, mat_a, mat_b, mat_u, source_list):
        """
        The matrix A in E.dx/dt=Ax+Bu will be updated by the
        resistor value.
        """
        for c1 in range(len(sys_loops)):
            for c2 in range(c1, len(sys_loops)):
                # Updating the elements depending
                # on the sense of the loops (aiding or opposing)
                for c3 in range(len(sys_loops[c1][c2])):
                    # Check is resistor position is there in the loop.
                    if NwRdr.csv_tuple(self.pos) in sys_loops[c1][c2][c3]:
                        # Add resistor if branch is in forward direction
                        if sys_loops[c1][c2][c3][-1]=="forward":
                            mat_a.data[c1][c2] += self.resistor
                        else:
                            # Else subtract if branch is in reverse direction
                            mat_a.data[c1][c2] -= self.resistor
                        # Because the matrices are symmetric
                        mat_a.data[c2][c1] = mat_a.data[c1][c2]

        return

    def transfer_to_branch(self, sys_branch, source_list,  mat_u):
        """
        The value of the resistor is transferred to the branch
        parameter in the branch where the resistor appears.
        """
        if NwRdr.csv_tuple(self.pos_3D) in sys_branch:
            sys_branch[-1][0][0] += self.resistor

        return

    def generate_val(self, source_lst, mat_e, mat_a, mat_b, mat_u, t, dt):
        pass

    def update_val(self, sys_loop_map, lbyr_ratio, mat_e, mat_a, mat_b, state_vec, mat_u, sys_branches, sys_events):
        pass

    def pre_determine_state(self, br_currents, sys_branches, sys_events):
        pass

    def determine_state(self, br_currents, sys_branches, sys_events):
        pass

    def retrieve_db_model(self, sim_para_model):
        """
        This function returns the model instance object.
        """
        check_ckt = sim_para_model.circuitschematics_set.\
                    filter(ckt_file_name=self.sheet_name)
        try:
            # Within the file, check if a database entry exists
            # with the component tag.
            check_resistor = check_ckt[0].resistor_set.\
                    filter(comp_tag=self.tag)
        except:
            return None
        else:
            if check_resistor and len(check_resistor)==1:
                return check_resistor[0]

    def init_db_values(self, sim_para_model, ckt_file_list, branch_map):
        """
        This function creates a new database entry for a component or
        updates an existing database entry from the component class data.
        """
        comp_found = False
        # Search for the file from component sheet name
        check_ckt = sim_para_model.circuitschematics_set.\
                    filter(ckt_file_name=self.sheet_name)
        try:
            # Within the file, check if a database entry exists
            # with the component tag.
            check_resistor = check_ckt[0].resistor_set.\
                    filter(comp_tag=self.tag)
        except:
            comp_found = False
        else:
            if check_resistor and len(check_resistor)==1:
                comp_found = True
                old_resistor = check_resistor[0]
                old_resistor.comp_number = self.number
                old_resistor.comp_pos_3D = self.pos_3D
                old_resistor.comp_pos = self.pos
                old_resistor.comp_sheet = self.sheet
                old_resistor.save()
                check_ckt[0].save()
            # Delete excessive components if any
            if check_resistor and len(check_resistor)>1:
                comp_found = True
                for c1 in range(len(check_resistor)-1, 0, -1):
                    check_resistor[c1].delete()
                    check_ckt[0].save()

        # Create a new component if not found.
        if not comp_found:
            new_resistor = models.Resistor()
            new_resistor.comp_resistor = self.resistor
            new_resistor.comp_number = self.number
            new_resistor.comp_pos_3D = self.pos_3D
            new_resistor.comp_pos = self.pos
            new_resistor.comp_sheet = self.sheet
            new_resistor.sheet_name = self.sheet_name.split(".csv")[0]
            new_resistor.comp_tag = self.tag
            ckt_file_item = ckt_file_list.filter(ckt_file_name=self.sheet_name)
            new_resistor.comp_ckt = ckt_file_item[0]
            new_resistor.save()
        sim_para_model.save()

        return

    def create_form_values(self, sim_para_model, ckt_file_list, branch_map):
        """
        This function creates a new database entry for a component or
        updates an existing database entry from the component class data.
        """
        comp_found = False
        # Search for the file from component sheet name
        check_ckt = sim_para_model.circuitschematics_set.\
                    filter(ckt_file_name=self.sheet_name)
        try:
            # Within the file, check if a database entry exists
            # with the component tag.
            check_resistor = check_ckt[0].resistor_set.\
                    filter(comp_tag=self.tag)
        except:
            comp_found = False
        else:
            if check_resistor and len(check_resistor)==1:
                comp_found = True
                old_resistor = check_resistor[0]
                old_resistor.comp_resistor = self.resistor
                old_resistor.comp_number = self.number
                old_resistor.comp_pos_3D = self.pos_3D
                old_resistor.comp_pos = self.pos
                old_resistor.comp_sheet = self.sheet
                old_resistor.save()
                check_ckt[0].save()
            # Delete excessive components if any
            if check_resistor and len(check_resistor)>1:
                comp_found = True
                for c1 in range(len(check_resistor)-1, 0, -1):
                    check_resistor[c1].delete()
                    check_ckt[0].save()

        # Create a new component if not found.
        if not comp_found:
            new_resistor = models.Resistor()
            new_resistor.comp_resistor = self.resistor
            new_resistor.comp_number = self.number
            new_resistor.comp_pos_3D = self.pos_3D
            new_resistor.comp_pos = self.pos
            new_resistor.comp_sheet = self.sheet
            new_resistor.sheet_name = self.sheet_name.split(".csv")[0]
            new_resistor.comp_tag = self.tag
            ckt_file_item = ckt_file_list.filter(ckt_file_name=self.sheet_name)
            new_resistor.comp_ckt = ckt_file_item[0]
            new_resistor.save()
        sim_para_model.save()

        return

    def list_existing_components(self, ckt_file):
        """
        Check if the model of the circuit file contains
        the associated database entry for the component.
        Returns an empty list if not found.
        """
        try:
            check_resistor = ckt_file.resistor_set.all().\
                        filter(comp_tag=self.tag)
        except:
            comp_list = []
        else:
            if check_resistor and len(check_resistor)==1:
                comp_list = check_resistor[0]
            else:
                comp_list = []
        return comp_list

    def comp_as_a_dict(self, ckt_file):
        """
        Returns information about a component as a list
        that can be displayed in a webpage.
        """
        try:
            check_resistor = ckt_file.resistor_set.all().\
                        filter(comp_tag=self.tag)
        except:
            comp_list = []
        else:
            if check_resistor and len(check_resistor)==1:
                comp_list = []
                comp_list.append(["Component type", check_resistor[0].comp_type])
                comp_list.append(["Component name", check_resistor[0].comp_tag])
                comp_list.append(["Component position", check_resistor[0].comp_pos])
                comp_list.append(["Resistor value", check_resistor[0].comp_resistor])
            else:
                comp_list = []
        return comp_list

    def comp_as_a_form(self, ckt_file):
        """
        Returns a populated form for a component.
        """
        try:
            check_resistor = ckt_file.resistor_set.all().\
                        filter(comp_tag=self.tag)
        except:
            return []
        else:
            if check_resistor and len(check_resistor)==1:
                # comp_list = models.ResistorForm(instance=check_resistor[0])
                return [models.ResistorForm, check_resistor[0]]
            else:
                return []
        # return comp_list

    def save_to_db(self, ckt_file):
        """
        Saves object data to database.
        """
        try:
            check_resistor = ckt_file.resistor_set.all().\
                        filter(comp_tag=self.tag)
        except:
            return
        else:
            if check_resistor and len(check_resistor)==1:
                old_resistor = check_resistor[0]
                old_resistor.comp_resistor = self.resistor
                old_resistor.save()
                ckt_file.save()
            else:
                return

    def update_form_data(self, request, comp_model, branch_map):
        """
        Extracts data from a form and saves it to the database.
        """
        received_form = models.ResistorForm(request.POST)
        if received_form.is_valid():
            received_data = received_form.cleaned_data
            comp_model.comp_resistor = received_data["comp_resistor"]
            comp_model.save()
            form_status = []
        else:
            form_status = [received_form, ]
        return form_status

    def pre_run_check(self, ckt_file_item, branch_map):
        pass

    def assign_parameters(self, ckt_file_list):
        """
        Transfers data from the database to the component clas
        objects for the simulation.
        """
        for ckt_file_item in ckt_file_list:
            try:
                check_resistor = ckt_file_item.resistor_set.all().\
                        filter(comp_tag=self.tag)
            except:
                pass
            else:
                if check_resistor and len(check_resistor)==1:
                    comp_model = check_resistor[0]
                    self.resistor = comp_model.comp_resistor
        return


class Variable_Resistor:
    """
    Variable Resistor class. Similar to the class
    above except that the resistance value is a
    control input.
    """

    def __init__(self, res_index, res_pos, res_tag, nw_input):
        """
        Constructor to initialize value.
        Also, takes in the identifiers -
        index (serial number), cell position and tag.
        """
        self.type = "VariableResistor"
        self.number = res_index
        self.pos_3D = res_pos
        self.sheet = NwRdr.csv_tuple(res_pos)[0]
        self.pos = NwRdr.csv_element_2D(NwRdr.csv_tuple(res_pos)[1:])
        self.tag = res_tag
        self.sheet_name = nw_input[self.sheet] + ".csv"
        self.has_voltage = "no"
        self.is_meter = "no"
        self.has_control = "yes"
        self.control_tag=["Resistance"]
        self.control_values=[100.0]
        self.resistor = 100.0
        self.voltage = 0.0
        self.current = 0.0
        self.component_branch_pos = 0

        return

    def display(self):
        """
        Displays info about the component.
        """
        print("Variable Resistor is {}={} located at {} in sheet {}".format(
            self.tag, self.resistor, self.pos, self.sheet_name
        ))

        return

    def ask_values(self, x_list, ckt_mat, sys_branch):
        """
        Writes the values needed to the spreadsheet.
        """
        resistor_params = ["VariableResistor"]
        resistor_params.append(self.tag)
        resistor_params.append(self.pos)
        resistor_params.append("Initial resistance = %s" %str(self.resistor))
        resistor_params.append("Name of control signal = %s" %self.control_tag[0])
        x_list.append(resistor_params)

        return

    def export_values_to_csv(self):
        """
        Writes the values needed to the spreadsheet.
        """
        resistor_params = ["VariableResistor"]
        resistor_params.append(self.tag)
        resistor_params.append(self.pos)
        resistor_params.append("Initial resistance = %s" %str(self.resistor))
        resistor_params.append("Name of control signal = %s" %self.control_tag[0])

        return resistor_params

    def get_values(self, x_list, ckt_mat):
        """ Takes the parameter from the spreadsheet."""
        self.resistor = float(x_list[0].split("=")[1])
        self.control_values[0] = self.resistor
        self.control_tag[0] = x_list[1].split("=")[1]
        while self.control_tag[0][0] == " ":
            self.control_tag[0] = self.control_tag[0][1:]

        while self.control_tag[0][-1] == " ":
            self.control_tag[0] = self.control_tag[0][:-1]

        return

    def determine_branch(self, sys_branches):
        """
        Determines which branch the component is found in.
        """
        for c1 in range(len(sys_branches)):
            if NwRdr.csv_tuple(self.pos_3D) in sys_branches[c1]:
                self.component_branch_pos = c1

        return

    def transfer_to_sys(self, sys_loops, mat_e, mat_a, mat_b, mat_u, source_list):
        """
        The matrix A in E.dx/dt=Ax+Bu will be updated by the
        resistor value.
        """
        for c1 in range(len(sys_loops)):
            for c2 in range(c1, len(sys_loops)):
                # Updating the elements depending
                # on the sense of the loops (aiding or opposing)
                for c3 in range(len(sys_loops[c1][c2])):
                    # Check is resistor position is there in the loop.
                    if NwRdr.csv_tuple(self.pos) in sys_loops[c1][c2][c3]:
                        # Add resistor if branch is in forward direction
                        if sys_loops[c1][c2][c3][-1]=="forward":
                            mat_a.data[c1][c2] += self.resistor
                        else:
                            # Else subtract if branch is in reverse direction
                            mat_a.data[c1][c2] -= self.resistor
                        # Because the matrices are symmetric
                        mat_a.data[c2][c1] = mat_a.data[c1][c2]
        return

    def transfer_to_branch(self, sys_branch, source_list,  mat_u):
        """
        The value of the resistor is transferred to the branch
        parameter in the branch where the resistor appears.
        """
        if NwRdr.csv_tuple(self.pos_3D) in sys_branch:
            sys_branch[-1][0][0] += self.resistor

        return

    def generate_val(self, source_lst, mat_e, mat_a, mat_b, mat_u, t, dt):
        pass

    def update_val(self, sys_loop_map, lbyr_ratio, mat_e, mat_a, mat_b, state_vec, mat_u, sys_branches, sys_events):
        """
        The control input is pass on as the resistance value.
        """
        if not self.control_values[0]==self.resistor:
            sys_events[self.component_branch_pos] = "hard"
            self.resistor = self.control_values[0]

        return

    def pre_determine_state(self, br_currents, sys_branches, sys_events):
        pass

    def determine_state(self, br_currents, sys_branches, sys_events):
        pass

    def retrieve_db_model(self, sim_para_model):
        """
        This function returns the model instance object.
        """
        check_ckt = sim_para_model.circuitschematics_set.\
                    filter(ckt_file_name=self.sheet_name)
        try:
            check_resistor = check_ckt[0].variableresistor_set.\
                    filter(comp_tag=self.tag)
        except:
            return None
        else:
            if check_resistor and len(check_resistor)==1:
                return check_resistor[0]

    def init_db_values(self, sim_para_model, ckt_file_list, branch_map):
        """
        This function creates a new database entry for a component or
        updates an existing database entry from the component class data.
        """
        comp_found = False
        check_ckt = sim_para_model.circuitschematics_set.\
                    filter(ckt_file_name=self.sheet_name)
        try:
            check_resistor = check_ckt[0].variableresistor_set.\
                    filter(comp_tag=self.tag)
        except:
            comp_found = False
        else:
            if check_resistor and len(check_resistor)==1:
                comp_found = True
                old_resistor = check_resistor[0]
                old_resistor.comp_number = self.number
                old_resistor.comp_pos_3D = self.pos_3D
                old_resistor.comp_pos = self.pos
                old_resistor.comp_sheet = self.sheet
                old_resistor.save()
                check_ckt[0].save()
            if check_resistor and len(check_resistor)>1:
                comp_found = True
                for c1 in range(len(check_resistor)-1, 0, -1):
                    check_resistor[c1].delete()
                    check_ckt[0].save()

        if not comp_found:
            new_resistor = models.VariableResistor()
            new_resistor.comp_resistor = self.resistor
            new_resistor.comp_number = self.number
            new_resistor.comp_pos_3D = self.pos_3D
            new_resistor.comp_pos = self.pos
            new_resistor.comp_sheet = self.sheet
            new_resistor.sheet_name = self.sheet_name.split(".csv")[0]
            new_resistor.comp_tag = self.tag
            ckt_file_item = ckt_file_list.filter(ckt_file_name=self.sheet_name)
            new_resistor.comp_ckt = ckt_file_item[0]
            new_resistor.save()
        sim_para_model.save()

        return

    def create_form_values(self, sim_para_model, ckt_file_list, branch_map):
        """
        This function creates a new database entry for a component or
        updates an existing database entry from the component class data.
        """
        comp_found = False
        check_ckt = sim_para_model.circuitschematics_set.\
                    filter(ckt_file_name=self.sheet_name)
        try:
            check_resistor = check_ckt[0].variableresistor_set.\
                    filter(comp_tag=self.tag)
        except:
            comp_found = False
        else:
            if check_resistor and len(check_resistor)==1:
                comp_found = True
                old_resistor = check_resistor[0]
                old_resistor.comp_resistor = self.resistor
                old_resistor.comp_number = self.number
                old_resistor.comp_pos_3D = self.pos_3D
                old_resistor.comp_pos = self.pos
                old_resistor.comp_sheet = self.sheet
                old_resistor.comp_control_tag = self.control_tag[0]
                old_resistor.save()
                check_ckt[0].save()
            if check_resistor and len(check_resistor)>1:
                comp_found = True
                for c1 in range(len(check_resistor)-1, 0, -1):
                    check_resistor[c1].delete()
                    check_ckt[0].save()

        if not comp_found:
            new_resistor = models.VariableResistor()
            new_resistor.comp_resistor = self.resistor
            new_resistor.comp_number = self.number
            new_resistor.comp_pos_3D = self.pos_3D
            new_resistor.comp_pos = self.pos
            new_resistor.comp_sheet = self.sheet
            new_resistor.sheet_name = self.sheet_name.split(".csv")[0]
            new_resistor.comp_tag = self.tag
            ckt_file_item = ckt_file_list.filter(ckt_file_name=self.sheet_name)
            new_resistor.comp_ckt = ckt_file_item[0]
            new_resistor.save()
        sim_para_model.save()

        return

    def list_existing_components(self, ckt_file):
        """
        Check if the model of the circuit file contains
        the associated database entry for the component.
        Returns an empty list if not found.
        """
        try:
            check_resistor = ckt_file.variableresistor_set.all().\
                        filter(comp_tag=self.tag)
        except:
            comp_list = []
        else:
            if check_resistor and len(check_resistor)==1:
                comp_list = check_resistor[0]
            else:
                comp_list = []
        return comp_list

    def comp_as_a_dict(self, ckt_file):
        """
        Returns information about a component as a list
        that can be displayed in a webpage.
        """
        try:
            check_resistor = ckt_file.variableresistor_set.all().\
                        filter(comp_tag=self.tag)
        except:
            comp_list = []
        else:
            if check_resistor and len(check_resistor)==1:
                comp_list = []
                comp_list.append(["Component type", check_resistor[0].comp_type])
                comp_list.append(["Component name", check_resistor[0].comp_tag])
                comp_list.append(["Component position", check_resistor[0].comp_pos])
                comp_list.append(["Control name", check_resistor[0].comp_control_tag])
                comp_list.append(["Initial resistor value", check_resistor[0].comp_resistor])
            else:
                comp_list = []
        return comp_list

    def comp_as_a_form(self, ckt_file):
        """
        Returns a populated form for a component.
        """
        try:
            check_resistor = ckt_file.variableresistor_set.all().\
                        filter(comp_tag=self.tag)
        except:
            return []
        else:
            if check_resistor and len(check_resistor)==1:
                # comp_list = models.VariableResistorForm(instance=check_resistor[0])
                return [models.VariableResistorForm, check_resistor[0]]
            else:
                return []
                # comp_list = []
        # return comp_list

    def save_to_db(self, ckt_file):
        """
        Saves object data to database.
        """
        try:
            check_resistor = ckt_file.variableresistor_set.all().\
                        filter(comp_tag=self.tag)
        except:
            return
        else:
            if check_resistor and len(check_resistor)==1:
                old_resistor = check_resistor[0]
                old_resistor.comp_resistor = self.resistor
                old_resistor.comp_control_tag = self.control_tag[0]
                old_resistor.save()
                ckt_file.save()
                return
            else:
                return

    def update_form_data(self, request, comp_model, branch_map):
        """
        Extracts data from a form and saves it to the database.
        """
        received_form = models.VariableResistorForm(request.POST)
        if received_form.is_valid():
            received_data = received_form.cleaned_data
            comp_model.comp_control_tag = received_data["comp_control_tag"]
            comp_model.comp_resistor = received_data["comp_resistor"]
            comp_model.save()
            form_status = []
        else:
            form_status = [received_form, ]
        return form_status

    def pre_run_check(self, ckt_file_item, branch_map):
        pass

    def assign_parameters(self, ckt_file_list):
        """
        Transfers data from the database to the component clas
        objects for the simulation.
        """
        for ckt_file_item in ckt_file_list:
            try:
                check_resistor = ckt_file_item.variableresistor_set.all().\
                        filter(comp_tag=self.tag)
            except:
                pass
            else:
                if check_resistor and len(check_resistor)==1:
                    comp_model = check_resistor[0]
                    self.resistor = comp_model.comp_resistor
                    self.control_tag=[comp_model.comp_control_tag, ]
                    self.control_values=[comp_model.comp_resistor, ]
                    self.resistor = comp_model.comp_resistor
        return


class Inductor:
    """
    Inductor class. Contains functions to initiliaze
    the resistor according to name tag, unique cell position,
    update system matrix on each iteration.
    """

    def __init__(self, ind_index, ind_pos, ind_tag, nw_input):
        """
        Constructor to initialize value.
        Also, takes in the identifiers -
        index (serial number), cell position and tag.
        """
        self.type = "Inductor"
        self.number = ind_index
        self.pos_3D = ind_pos
        self.sheet = NwRdr.csv_tuple(ind_pos)[0]
        self.pos = NwRdr.csv_element_2D(NwRdr.csv_tuple(ind_pos)[1:])
        self.tag = ind_tag
        self.sheet_name = nw_input[self.sheet] + ".csv"
        self.has_voltage = "no"
        self.is_meter = "no"
        self.has_control = "no"
        self.inductor = 0.001
        self.voltage = 0.0
        self.current = 0.0
        self.polrty = [-1, -1]

        return

    def display(self):
        """
        Displays info about the component.
        """
        print("Inductor is {}={} located at {} in sheet {}".format(
            self.tag, self.inductor, self.pos, self.sheet_name
        ))

        return

    def ask_values(self, x_list, ckt_mat, sys_branch):
        """
        Writes the values needed to the spreadsheet.
        """
        ind_params = ["Inductor"]
        ind_params.append(self.tag)
        ind_params.append(self.pos)
        ind_params.append(self.inductor)
        # Looking for a default value of polarity
        # in the neighbouring cells
        # The polarity is for simulator use only. So not added into ind_params.
        # The polarity is in the direction of current
        # Just like an ammeter.
        self.ind_elem = NwRdr.csv_tuple_2D(self.pos)
        if self.ind_elem[0]>0:
            if ckt_mat[self.sheet][self.ind_elem[0]-1][self.ind_elem[1]]:
                self.polrty = [self.ind_elem[0]-1, self.ind_elem[1]]
        if self.ind_elem[1]>0:
            if ckt_mat[self.sheet][self.ind_elem[0]][self.ind_elem[1]-1]:
                self.polrty = [self.ind_elem[0], self.ind_elem[1]-1]
        if self.ind_elem[0]<len(ckt_mat[self.sheet])-1:
            if ckt_mat[self.sheet][self.ind_elem[0]+1][self.ind_elem[1]]:
                self.polrty = [self.ind_elem[0]+1, self.ind_elem[1]]
        if self.ind_elem[1]<len(ckt_mat[self.sheet][0])-1:
            if ckt_mat[self.sheet][self.ind_elem[0]][self.ind_elem[1]+1]:
                self.polrty = [self.ind_elem[0], self.ind_elem[1]+1]

        x_list.append(ind_params)

        return

    def export_values_to_csv(self):
        """
        Writes the values needed to the spreadsheet.
        """
        ind_params = ["Inductor"]
        ind_params.append(self.tag)
        ind_params.append(self.pos)
        ind_params.append(self.inductor)

        return ind_params

    def get_values(self, x_list, ckt_mat):
        """
        Takes the parameter from the spreadsheet.
        """
        self.inductor = float(x_list[0])

        return

    def determine_branch(self, sys_branches):
        pass

    def transfer_to_sys(self, sys_loops, mat_e, mat_a, mat_b, mat_u, source_list):
        """
        The matrix E in E.dx/dt=Ax+Bu will be updated by the
        inductor value.
        """
        for c1 in range(len(sys_loops)):
            for c2 in range(c1, len(sys_loops)):
                # Updating the elements depending
                # on the sense of the loops (aiding or opposing)
                for c3 in range(len(sys_loops[c1][c2])):
                    # Check if inductor is there in loop
                    if NwRdr.csv_tuple(self.pos) in sys_loops[c1][c2][c3]:
                        # Check is branch is in same direction as loop
                        if sys_loops[c1][c2][c3][-1]=="forward":
                            mat_e.data[c1][c2] += self.inductor
                        else:
                            mat_e.data[c1][c2] -= self.inductor
                        # Because the matrices are symmetric
                        mat_e.data[c2][c1] = mat_e.data[c1][c2]
        return

    def transfer_to_branch(self, sys_branch, source_list,  mat_u):
        """
        The value of the inductor is added to the parameter of the
        branch where the inductor is found.
        """
        if NwRdr.csv_tuple(self.pos_3D) in sys_branch:
            sys_branch[-1][0][1] += self.inductor

        return

    def generate_val(self, source_lst, mat_e, mat_a, mat_b, mat_u, t, dt):
        pass

    def update_val(self, sys_loop_map, lbyr_ratio, mat_e, mat_a, mat_b, state_vec, mat_u, sys_branches, sys_events):
        pass

    def pre_determine_state(self, br_currents, sys_branches, sys_events):
        pass

    def determine_state(self, br_currents, sys_branches, sys_events):
        pass

    def retrieve_db_model(self, sim_para_model):
        """
        This function returns the model instance object.
        """
        check_ckt = sim_para_model.circuitschematics_set.\
                    filter(ckt_file_name=self.sheet_name)
        try:
            check_inductor = check_ckt[0].inductor_set.\
                    filter(comp_tag=self.tag)
        except:
            return None
        else:
            if check_inductor and len(check_inductor)==1:
                return check_inductor[0]

    def init_db_values(self, sim_para_model, ckt_file_list, branch_map):
        """
        This function creates a new database entry for a component or
        updates an existing database entry from the component class data.
        """
        comp_found = False
        check_ckt = sim_para_model.circuitschematics_set.\
                    filter(ckt_file_name=self.sheet_name)
        try:
            check_inductor = check_ckt[0].inductor_set.\
                    filter(comp_tag=self.tag)
        except:
            comp_found = False
        else:
            if check_inductor and len(check_inductor)==1:
                comp_found = True
                old_inductor = check_inductor[0]
                old_inductor.comp_number = self.number
                old_inductor.comp_pos_3D = self.pos_3D
                old_inductor.comp_pos = self.pos
                old_inductor.comp_sheet = self.sheet
                old_inductor.save()
                check_ckt[0].save()
            if check_inductor and len(check_inductor)>1:
                comp_found = True
                for c1 in range(len(check_inductor)-1, 0, -1):
                    check_inductor[c1].delete()
                    check_ckt[0].save()

        if not comp_found:
            new_inductor = models.Inductor()
            new_inductor.comp_inductor = self.inductor
            new_inductor.comp_number = self.number
            new_inductor.comp_pos_3D = self.pos_3D
            new_inductor.comp_pos = self.pos
            new_inductor.comp_sheet = self.sheet
            new_inductor.sheet_name = self.sheet_name.split(".csv")[0]
            new_inductor.comp_tag = self.tag
            ckt_file_item = ckt_file_list.filter(ckt_file_name=self.sheet_name)
            new_inductor.comp_ckt = ckt_file_item[0]
            new_inductor.save()
        sim_para_model.save()

        return

    def create_form_values(self, sim_para_model, ckt_file_list, branch_map):
        """
        This function creates a new database entry for a component or
        updates an existing database entry from the component class data.
        """
        comp_found = False
        check_ckt = sim_para_model.circuitschematics_set.\
                    filter(ckt_file_name=self.sheet_name)
        try:
            check_inductor = check_ckt[0].inductor_set.\
                    filter(comp_tag=self.tag)
        except:
            comp_found = False
        else:
            if check_inductor and len(check_inductor)==1:
                comp_found = True
                old_inductor = check_inductor[0]
                old_inductor.comp_inductor = self.inductor
                old_inductor.comp_number = self.number
                old_inductor.comp_pos_3D = self.pos_3D
                old_inductor.comp_pos = self.pos
                old_inductor.comp_sheet = self.sheet
                old_inductor.save()
                check_ckt[0].save()
            if check_inductor and len(check_inductor)>1:
                comp_found = True
                for c1 in range(len(check_inductor)-1, 0, -1):
                    check_inductor[c1].delete()
                    check_ckt[0].save()

        if not comp_found:
            new_inductor = models.Inductor()
            new_inductor.comp_inductor = self.inductor
            new_inductor.comp_number = self.number
            new_inductor.comp_pos_3D = self.pos_3D
            new_inductor.comp_pos = self.pos
            new_inductor.comp_sheet = self.sheet
            new_inductor.sheet_name = self.sheet_name.split(".csv")[0]
            new_inductor.comp_tag = self.tag
            ckt_file_item = ckt_file_list.filter(ckt_file_name=self.sheet_name)
            new_inductor.comp_ckt = ckt_file_item[0]
            new_inductor.save()
        sim_para_model.save()

        return

    def list_existing_components(self, ckt_file):
        """
        Check if the model of the circuit file contains
        the associated database entry for the component.
        Returns an empty list if not found.
        """
        try:
            check_inductor = ckt_file.inductor_set.all().\
                        filter(comp_tag=self.tag)
        except:
            comp_list = []
        else:
            if check_inductor and len(check_inductor)==1:
                comp_list = check_inductor[0]
            else:
                comp_list = []
        return comp_list

    def comp_as_a_dict(self, ckt_file):
        """
        Returns information about a component as a list
        that can be displayed in a webpage.
        """
        try:
            check_inductor = ckt_file.inductor_set.all().\
                        filter(comp_tag=self.tag)
        except:
            comp_list = []
        else:
            if check_inductor and len(check_inductor)==1:
                comp_list = []
                comp_list.append(["Component type", check_inductor[0].comp_type])
                comp_list.append(["Component name", check_inductor[0].comp_tag])
                comp_list.append(["Component position", check_inductor[0].comp_pos])
                comp_list.append(["Inductor value", check_inductor[0].comp_inductor])
            else:
                comp_list = []
        return comp_list

    def comp_as_a_form(self, ckt_file):
        """
        Returns a populated form for a component.
        """
        try:
            check_inductor = ckt_file.inductor_set.all().\
                        filter(comp_tag=self.tag)
        except:
            return []
        else:
            if check_inductor and len(check_inductor)==1:
                return [models.InductorForm, check_inductor[0]]
                # comp_list = models.InductorForm(instance=check_inductor[0])
            else:
                return []
        # return comp_list

    def save_to_db(self, ckt_file):
        """
        Returns a populated form for a component.
        """
        try:
            check_inductor = ckt_file.inductor_set.all().\
                        filter(comp_tag=self.tag)
        except:
            return
        else:
            if check_inductor and len(check_inductor)==1:
                old_inductor = check_inductor[0]
                old_inductor.comp_inductor = self.inductor
                old_inductor.save()
                ckt_file.save()
                return
            else:
                return

    def update_form_data(self, request, comp_model, branch_map):
        """
        Extracts data from a form and saves it to the database.
        """
        received_form = models.InductorForm(request.POST)
        if received_form.is_valid():
            received_data = received_form.cleaned_data
            comp_model.comp_inductor = received_data["comp_inductor"]
            comp_model.save()
            form_status = []
        else:
            form_status = [received_form, ]
        return form_status

    def pre_run_check(self, ckt_file_item, branch_map):
        pass

    def assign_parameters(self, ckt_file_list):
        """
        Transfers data from the database to the component clas
        objects for the simulation.
        """
        for ckt_file_item in ckt_file_list:
            try:
                check_inductor = ckt_file_item.inductor_set.all().\
                        filter(comp_tag=self.tag)
            except:
                pass
            else:
                if check_inductor and len(check_inductor)==1:
                    comp_model = check_inductor[0]
                    self.inductor = comp_model.comp_inductor
        return


class Variable_Inductor:
    """
    Inductor class. Contains functions to initiliaze
    the resistor according to name tag, unique cell position,
    update system matrix on each iteration.
    """

    def __init__(self, ind_index, ind_pos, ind_tag, nw_input):
        """
        Constructor to initialize value.
        Also, takes in the identifiers -
        index (serial number), cell position and tag.
        """
        self.type = "VariableInductor"
        self.number = ind_index
        self.pos_3D = ind_pos
        self.sheet = NwRdr.csv_tuple(ind_pos)[0]
        self.pos = NwRdr.csv_element_2D(NwRdr.csv_tuple(ind_pos)[1:])
        self.tag = ind_tag
        self.sheet_name = nw_input[self.sheet] + ".csv"
        self.has_voltage = "no"
        self.is_meter = "no"
        self.has_control = "yes"
        self.control_tag=["Inductance"]
        self.control_values=[0.001]
        self.inductor = 0.001
        self.voltage = 0.0
        self.current = 0.0
        self.polrty = [-1, -1]

        return

    def display(self):
        """
        Displays info about the component.
        """
        print("VariableInductor is {}={} located at {} in sheet {}".format(
            self.tag, self.inductor, self.pos, self.sheet_name
        ))

        return

    def ask_values(self, x_list, ckt_mat, sys_branch):
        """
        Writes the values needed to the spreadsheet.
        """
        ind_params = ["VariableInductor"]
        ind_params.append(self.tag)
        ind_params.append(self.pos)
        ind_params.append("Initial inductance = %s"%str(self.inductor))
        ind_params.append("Name of control signal = %s" %self.control_tag[0])
        # Looking for a default value of polarity
        # in the neighbouring cells
        # The polarity is for simulator use only. So not added into ind_params.
        # The polarity is in the direction of current
        # Just like an ammeter.
        self.ind_elem = NwRdr.csv_tuple_2D(self.pos)
        if self.ind_elem[0]>0:
            if ckt_mat[self.sheet][self.ind_elem[0]-1][self.ind_elem[1]]:
                self.polrty = [self.ind_elem[0]-1, self.ind_elem[1]]
        if self.ind_elem[1]>0:
            if ckt_mat[self.sheet][self.ind_elem[0]][self.ind_elem[1]-1]:
                self.polrty = [self.ind_elem[0], self.ind_elem[1]-1]
        if self.ind_elem[0]<len(ckt_mat[self.sheet])-1:
            if ckt_mat[self.sheet][self.ind_elem[0]+1][self.ind_elem[1]]:
                self.polrty = [self.ind_elem[0]+1, self.ind_elem[1]]
        if self.ind_elem[1]<len(ckt_mat[self.sheet][0])-1:
            if ckt_mat[self.sheet][self.ind_elem[0]][self.ind_elem[1]+1]:
                self.polrty = [self.ind_elem[0], self.ind_elem[1]+1]

        x_list.append(ind_params)

        return

    def export_values_to_csv(self):
        """
        Writes the values needed to the spreadsheet.
        """
        ind_params = ["VariableInductor"]
        ind_params.append(self.tag)
        ind_params.append(self.pos)
        ind_params.append("Initial inductance = %s"%str(self.inductor))

        return ind_params

    def get_values(self, x_list, ckt_mat):
        """
        Takes the parameter from the spreadsheet.
        """
        self.inductor = float(x_list[0].split("=")[1])
        self.control_values[0] = self.inductor
        self.control_tag[0] = x_list[1].split("=")[1]
        while self.control_tag[0][0] == " ":
            self.control_tag[0] = self.control_tag[0][1:]

        while self.control_tag[0][-1] == " ":
            self.control_tag[0] = self.control_tag[0][:-1]

        return

    def determine_branch(self, sys_branches):
        """
        Determines which branch the component is found in.
        """
        for c1 in range(len(sys_branches)):
            if NwRdr.csv_tuple(self.pos_3D) in sys_branches[c1]:
                self.component_branch_pos = c1

        return

    def transfer_to_sys(self, sys_loops, mat_e, mat_a, mat_b, mat_u, source_list):
        """
        The matrix E in E.dx/dt=Ax+Bu will be updated by the
        inductor value.
        """
        for c1 in range(len(sys_loops)):
            for c2 in range(c1, len(sys_loops)):
                # Updating the elements depending
                # on the sense of the loops (aiding or opposing)
                for c3 in range(len(sys_loops[c1][c2])):
                    # Check if inductor is there in loop
                    if NwRdr.csv_tuple(self.pos) in sys_loops[c1][c2][c3]:
                        # Check is branch is in same direction as loop
                        if sys_loops[c1][c2][c3][-1]=="forward":
                            mat_e.data[c1][c2] += self.inductor
                        else:
                            mat_e.data[c1][c2] -= self.inductor
                        # Because the matrices are symmetric
                        mat_e.data[c2][c1] = mat_e.data[c1][c2]
        return

    def transfer_to_branch(self, sys_branch, source_list,  mat_u):
        """
        The value of the inductor is added to the parameter of the
        branch where the inductor is found.
        """
        if NwRdr.csv_tuple(self.pos_3D) in sys_branch:
            sys_branch[-1][0][1] += self.inductor

        return

    def generate_val(self, source_lst, mat_e, mat_a, mat_b, mat_u, t, dt):
        pass

    def update_val(self, sys_loop_map, lbyr_ratio, mat_e, mat_a, mat_b, state_vec, mat_u, sys_branches, sys_events):
        """
        The control input is pass on as the resistance value.
        """
        if not self.control_values[0]==self.inductor:
            sys_events[self.component_branch_pos] = "hard"
            self.inductor = self.control_values[0]

        return

    def pre_determine_state(self, br_currents, sys_branches, sys_events):
        pass

    def determine_state(self, br_currents, sys_branches, sys_events):
        pass

    def retrieve_db_model(self, sim_para_model):
        """
        This function returns the model instance object.
        """
        check_ckt = sim_para_model.circuitschematics_set.\
                    filter(ckt_file_name=self.sheet_name)
        try:
            check_inductor = check_ckt[0].variableinductor_set.\
                    filter(comp_tag=self.tag)
        except:
            return None
        else:
            if check_inductor and len(check_inductor)==1:
                return check_inductor[0]

    def init_db_values(self, sim_para_model, ckt_file_list, branch_map):
        """
        This function creates a new database entry for a component or
        updates an existing database entry from the component class data.
        """
        comp_found = False
        check_ckt = sim_para_model.circuitschematics_set.\
                    filter(ckt_file_name=self.sheet_name)
        try:
            check_inductor = check_ckt[0].variableinductor_set.\
                    filter(comp_tag=self.tag)
        except:
            comp_found = False
        else:
            if check_inductor and len(check_inductor)==1:
                comp_found = True
                old_inductor = check_inductor[0]
                old_inductor.comp_number = self.number
                old_inductor.comp_pos_3D = self.pos_3D
                old_inductor.comp_pos = self.pos
                old_inductor.comp_sheet = self.sheet
                old_inductor.save()
                check_ckt[0].save()
            if check_inductor and len(check_inductor)>1:
                comp_found = True
                for c1 in range(len(check_inductor)-1, 0, -1):
                    check_inductor[c1].delete()
                    check_ckt[0].save()

        if not comp_found:
            new_inductor = models.VariableInductor()
            new_inductor.comp_inductor = self.inductor
            new_inductor.comp_number = self.number
            new_inductor.comp_pos_3D = self.pos_3D
            new_inductor.comp_pos = self.pos
            new_inductor.comp_sheet = self.sheet
            new_inductor.sheet_name = self.sheet_name.split(".csv")[0]
            new_inductor.comp_tag = self.tag
            ckt_file_item = ckt_file_list.filter(ckt_file_name=self.sheet_name)
            new_inductor.comp_ckt = ckt_file_item[0]
            new_inductor.save()
        sim_para_model.save()

        return

    def create_form_values(self, sim_para_model, ckt_file_list, branch_map):
        """
        This function creates a new database entry for a component or
        updates an existing database entry from the component class data.
        """
        comp_found = False
        check_ckt = sim_para_model.circuitschematics_set.\
                    filter(ckt_file_name=self.sheet_name)
        try:
            check_inductor = check_ckt[0].variableinductor_set.\
                    filter(comp_tag=self.tag)
        except:
            comp_found = False
        else:
            if check_inductor and len(check_inductor)==1:
                comp_found = True
                old_inductor = check_inductor[0]
                old_inductor.comp_inductor = self.inductor
                old_inductor.comp_number = self.number
                old_inductor.comp_pos_3D = self.pos_3D
                old_inductor.comp_pos = self.pos
                old_inductor.comp_sheet = self.sheet
                old_inductor.comp_control_tag = self.control_tag[0]
                old_inductor.save()
                check_ckt[0].save()
            if check_inductor and len(check_inductor)>1:
                comp_found = True
                for c1 in range(len(check_inductor)-1, 0, -1):
                    check_inductor[c1].delete()
                    check_ckt[0].save()

        if not comp_found:
            new_inductor = models.VariableInductor()
            new_inductor.comp_inductor = self.inductor
            new_inductor.comp_number = self.number
            new_inductor.comp_pos_3D = self.pos_3D
            new_inductor.comp_pos = self.pos
            new_inductor.comp_sheet = self.sheet
            new_inductor.sheet_name = self.sheet_name.split(".csv")[0]
            new_inductor.comp_tag = self.tag
            ckt_file_item = ckt_file_list.filter(ckt_file_name=self.sheet_name)
            new_inductor.comp_ckt = ckt_file_item[0]
            new_inductor.save()
        sim_para_model.save()

        return

    def list_existing_components(self, ckt_file):
        """
        Check if the model of the circuit file contains
        the associated database entry for the component.
        Returns an empty list if not found.
        """
        try:
            check_inductor = ckt_file.variableinductor_set.all().\
                        filter(comp_tag=self.tag)
        except:
            comp_list = []
        else:
            if check_inductor and len(check_inductor)==1:
                comp_list = check_inductor[0]
            else:
                comp_list = []
        return comp_list

    def comp_as_a_dict(self, ckt_file):
        """
        Returns information about a component as a list
        that can be displayed in a webpage.
        """
        try:
            check_inductor = ckt_file.variableinductor_set.all().\
                        filter(comp_tag=self.tag)
        except:
            comp_list = []
        else:
            if check_inductor and len(check_inductor)==1:
                comp_list = []
                comp_list.append(["Component type", check_inductor[0].comp_type])
                comp_list.append(["Component name", check_inductor[0].comp_tag])
                comp_list.append(["Component position", check_inductor[0].comp_pos])
                comp_list.append(["Control name", check_inductor[0].comp_control_tag])
                comp_list.append(["Initial inductor value", check_inductor[0].comp_inductor])
            else:
                comp_list = []
        return comp_list

    def comp_as_a_form(self, ckt_file):
        """
        Returns a populated form for a component.
        """
        try:
            check_inductor = ckt_file.variableinductor_set.all().\
                        filter(comp_tag=self.tag)
        except:
            return []
        else:
            if check_inductor and len(check_inductor)==1:
                return [models.VariableInductorForm, check_inductor[0]]
                # comp_list = models.VariableInductorForm(instance=check_inductor[0])
            else:
                return []
        # return comp_list

    def save_to_db(self, ckt_file):
        """
        Returns a populated form for a component.
        """
        try:
            check_inductor = ckt_file.variableinductor_set.all().\
                        filter(comp_tag=self.tag)
        except:
            return
        else:
            if check_inductor and len(check_inductor)==1:
                old_inductor = check_inductor[0]
                old_inductor.comp_inductor = self.inductor
                old_inductor.comp_control_tag = self.control_tag[0]
                old_inductor.save()
                ckt_file.save()
                return
            else:
                return

    def update_form_data(self, request, comp_model, branch_map):
        """
        Extracts data from a form and saves it to the database.
        """
        received_form = models.VariableInductorForm(request.POST)
        if received_form.is_valid():
            received_data = received_form.cleaned_data
            comp_model.comp_control_tag = received_data["comp_control_tag"]
            comp_model.comp_inductor = received_data["comp_inductor"]
            comp_model.save()
            form_status = []
        else:
            form_status = [received_form, ]
        return form_status

    def pre_run_check(self, ckt_file_item, branch_map):
        pass

    def assign_parameters(self, ckt_file_list):
        """
        Transfers data from the database to the component clas
        objects for the simulation.
        """
        for ckt_file_item in ckt_file_list:
            try:
                check_inductor = ckt_file_item.variableinductor_set.all().\
                        filter(comp_tag=self.tag)
            except:
                pass
            else:
                if check_inductor and len(check_inductor)==1:
                    comp_model = check_inductor[0]
                    self.inductor = comp_model.comp_inductor
                    self.control_tag=[comp_model.comp_control_tag,]
                    self.control_values=[comp_model.comp_inductor,]
        return


class Capacitor:
    """
    Capacitor class. Contains functions to initiliaze
    the resistor according to name tag, unique cell position,
    update system matrix on each iteration.
    """

    def __init__(self, cap_index, cap_pos, cap_tag, nw_input):
        """
        Constructor to initialize value.
        Also, takes in the identifiers -
        index (serial number), cell position and tag.
        """
        self.type = "Capacitor"
        self.number = cap_index
        self.pos_3D = cap_pos
        self.sheet = NwRdr.csv_tuple(cap_pos)[0]
        self.pos = NwRdr.csv_element_2D(NwRdr.csv_tuple(cap_pos)[1:])
        self.tag = cap_tag
        self.sheet_name = nw_input[self.sheet] + ".csv"
        self.has_voltage = "yes"
        self.is_meter = "no"
        self.has_control = "no"
        self.capacitor = 10.0e-6
        self.current = 0.0
        self.voltage = 0.0
        self.v_dbydt = 0.0
        self.polrty_3D = [-1, -1, -1]
        self.polrty = [-1, -1]
        self.polrty_3D = [-1, -1, -1]
        self.component_banch_pos = 0
        self.component_branch_dir = 1.0

        return

    def display(self):
        """
        Displays info about the component.
        """
        print("Capacitor is {}={} located at {} with positive polarity towards {} in sheet {}".format(
            self.tag, self.capacitor, self.pos, NwRdr.csv_element_2D(self.polrty), self.sheet_name
        ))

        return

    def get_polarity(self, ckt_mat, sys_branch):
        if self.polrty==[-1, -1]:
            # Looking for a default value of polarity
            # in the neighbouring cells

            if self.cap_elem[0]>0:
                if ckt_mat[self.sheet][self.cap_elem[0]-1][self.cap_elem[1]]:
                    self.polrty = [self.cap_elem[0]-1, self.cap_elem[1]]
            if self.cap_elem[1]>0:
                if ckt_mat[self.sheet][self.cap_elem[0]][self.cap_elem[1]-1]:
                    self.polrty = [self.cap_elem[0], self.cap_elem[1]-1]
            if self.cap_elem[0]<len(ckt_mat[self.sheet])-1:
                if ckt_mat[self.sheet][self.cap_elem[0]+1][self.cap_elem[1]]:
                    self.polrty = [self.cap_elem[0]+1, self.cap_elem[1]]
            if self.cap_elem[1]<len(ckt_mat[self.sheet][0])-1:
                if ckt_mat[self.sheet][self.cap_elem[0]][self.cap_elem[1]+1]:
                    self.polrty = [self.cap_elem[0], self.cap_elem[1]+1]
        else:
            for c1 in range(len(sys_branch)):
                if [self.sheet, self.cap_elem[0], self.cap_elem[1]] in sys_branch[c1]:
                    if not [self.sheet, self.polrty[0], self.polrty[1]] in sys_branch[c1]:
                        print()
                        print("!"*50)
                        print("ERROR!!! Capacitor polarity should be in the same branch as the capacitor. \
Check source at {} in sheet {}".format(self.pos, self.sheet_name))
                        print("!"*50)
                        print()
                        raise CktEx.PolarityError

        self.polrty_3D = [self.sheet, self.polrty[0], self.polrty[1]]

        return

    def ask_values(self, x_list, ckt_mat, sys_branch):
        """
        Writes the values needed to the spreadsheet.
        """
        cap_params = ["Capacitor"]
        cap_params.append(self.tag)
        cap_params.append(self.pos)
        cap_params.append(self.capacitor)

        self.cap_elem = NwRdr.csv_tuple_2D(self.pos)
        self.get_polarity(ckt_mat, sys_branch)

        cap_params.append("Positive polarity towards (cell) = %s" %NwRdr.csv_element_2D(self.polrty))

        x_list.append(cap_params)

        return

    def export_values_to_csv(self):
        """
        Writes the values needed to the spreadsheet.
        """
        cap_params = ["Capacitor"]
        cap_params.append(self.tag)
        cap_params.append(self.pos)
        cap_params.append(self.capacitor)
        cap_params.append("Positive polarity towards (cell) = %s" %NwRdr.csv_element_2D(self.polrty))

        return cap_params

    def get_values(self, x_list, ckt_mat):
        """
        Takes the parameter from the spreadsheet.
        """
        self.capacitor = float(x_list[0])
        cap_polrty = x_list[1].split("=")[1]

        # Convert the human readable form of cell
        # to [row, column] form
        while cap_polrty[0]==" ":
            cap_polrty = cap_polrty[1:]

        self.polrty = NwRdr.csv_tuple_2D(cap_polrty)
        self.polrty_3D = [self.sheet, self.polrty[0], self.polrty[1]]

        if not ckt_mat[self.sheet][self.polrty[0]][self.polrty[1]]:
            print("Polarity incorrect or changed. Branch does not exist at {} in sheet {}".format(
                NwRdr.csv_element(self.polrty). self.sheet_name
            ))
            print()
            raise CktEx.PolarityError

        return

    def determine_branch(self, sys_branches):
        """
        Determines which branch the component is found in.
        """
        for c1 in range(len(sys_branches)):
            if NwRdr.csv_tuple(self.pos_3D) in sys_branches[c1]:
                self.component_branch_pos = c1
                if sys_branches[c1].index(self.polrty_3D)<sys_branches[c1].index(NwRdr.csv_tuple(self.pos_3D)):
                    self.component_branch_dir = 1.0
                else:
                    self.component_branch_dir = -1.0

        return

    def transfer_to_sys(self, sys_loops, mat_e, mat_a, mat_b, mat_u, source_list):
        """
        The matrix B in E.dx/dt=Ax+Bu will be updated by the
        polarity of the capacitor.
        """
        for c1 in range(len(sys_loops)):
            for c2 in range(len(sys_loops[c1][c1])):
                if NwRdr.csv_tuple(self.pos) in sys_loops[c1][c1][c2]:
                    # If the positive polarity appears before the capacitor position
                    # it means as per KVL, we are moving from +ve to -ve
                    # and so the capacitor voltage will be taken negative
                    if sys_loops[c1][c1][c2].index(self.polrty)<sys_loops[c1][c1][c2].index(NwRdr.csv_tuple(self.pos)):
                        if sys_loops[c1][c1][c2][-1]=="forward":
                            mat_b.data[c1][source_list.index(self.pos)] = -1.0
                        else:
                            mat_b.data[c1][source_list.index(self.pos)] = 1.0
                    else:
                        if sys_loops[c1][c1][c2][-1]=="forward":
                            mat_b.data[c1][source_list.index(self.pos)] = 1.0
                        else:
                            mat_b.data[c1][source_list.index(self.pos)] = -1.0
        return

    def transfer_to_branch(self, sys_branch, source_list,  mat_u):
        """
        Transfers parameters to system branch if capacitor
        exists in the branch.
        """
        if NwRdr.csv_tuple(self.pos_3D) in sys_branch:
            if sys_branch.index(self.polrty_3D)<sys_branch.index(NwRdr.csv_tuple(self.pos_3D)):
                sys_branch[-1][1][source_list.index(self.pos_3D)] = -1.0
            else:
                sys_branch[-1][1][source_list.index(self.pos_3D)] = 1.0
        return

    def generate_val(self, source_lst, mat_e, mat_a, mat_b, mat_u, t, dt):
        """
        The capacitor voltage is updated in the matrix u in
        E.dx/dt=Ax+Bu .
        """
        self.v_dbydt = self.current/self.capacitor

        self.voltage += self.v_dbydt*dt
        mat_u.data[source_lst.index(self.pos_3D)][0] = self.voltage
        self.op_value = self.voltage

        return

    def update_val_old(self, sys_loop_map, lbyr_ratio, mat_e, mat_a, mat_b, state_vec, mat_u, sys_branches, sys_events):
        """
        The capacitor current is calculated as a result of the KVL.
        """
        for c1 in range(len(sys_branches)):
            if NwRdr.csv_tuple(self.pos) in sys_branches[c1]:
                branch_pos = c1

        if sys_branches[branch_pos].index(self.polrty)<sys_branches[branch_pos].index(NwRdr.csv_tuple(self.pos)):
            self.current = sys_branches[branch_pos][-1][2]
        else:
            self.current = -sys_branches[branch_pos][-1][2]

        return

    def update_val(self, sys_loop_map, lbyr_ratio, mat_e, mat_a, mat_b, state_vec, mat_u, sys_branches, sys_events):
        """
        The capacitor current is calculated as a result of the KVL.
        """
        self.current = self.component_branch_dir*sys_branches[self.component_branch_pos][-1][2]
        return

    def pre_determine_state(self, br_currents, sys_branches, sys_events):
        pass

    def determine_state(self, br_currents, sys_branches, sys_events):
        pass

    def retrieve_db_model(self, sim_para_model):
        """
        This function returns the model instance object.
        """
        check_ckt = sim_para_model.circuitschematics_set.\
                filter(ckt_file_name=self.sheet_name)
        try:
            check_capacitor = check_ckt[0].capacitor_set.\
                    filter(comp_tag=self.tag)
        except:
            return None
        else:
            if check_capacitor and len(check_capacitor)==1:
                return check_capacitor[0]

    def determine_polarity(self, branch_map, capacitor_obj):
        """
        Determines polarity of a database object.
        """
        for c1 in range(len(branch_map)):
            for c2 in range(c1+1, len(branch_map)):
                for c3 in range(len(branch_map[c1][c2])):
                    if NwRdr.csv_tuple(self.pos_3D) in branch_map[c1][c2][c3]:
                        pos_in_branch = branch_map[c1][c2][c3].\
                                index(NwRdr.csv_tuple(self.pos_3D))
                        prev_element = branch_map[c1][c2][c3][pos_in_branch-1]
                        capacitor_obj.comp_polarity_3D = NwRdr.csv_element(prev_element)
                        capacitor_obj.comp_polarity = \
                                NwRdr.csv_element_2D(prev_element[1:])
        return

    def init_db_values(self, sim_para_model, ckt_file_list, branch_map):
        """
        This function creates a new database entry for a component or
        updates an existing database entry from the component class data.
        But only the positional data.
        """
        comp_found = False
        check_ckt = sim_para_model.circuitschematics_set.\
                filter(ckt_file_name=self.sheet_name)
        try:
            check_capacitor = check_ckt[0].capacitor_set.\
                    filter(comp_tag=self.tag)
        except:
            comp_found = False
        else:
            if check_capacitor and len(check_capacitor)==1:
                comp_found = True
                old_capacitor = check_capacitor[0]
                if not (self.polrty==[-1, -1]):
                    old_capacitor.comp_polarity = NwRdr.csv_element_2D(self.polrty)
                if not (self.polrty_3D==[-1, -1, -1]):
                    old_capacitor.comp_polarity_3D = NwRdr.csv_element(self.polrty_3D)
                if old_capacitor.comp_polarity_3D:
                    cap_old_polarity = NwRdr.csv_tuple(old_capacitor.comp_polarity_3D)
                    cap_new_polarity = NwRdr.csv_tuple(self.pos_3D)
                    cap_old_polarity[0] = cap_new_polarity[0]
                    old_capacitor.comp_polarity_3D = NwRdr.csv_element(cap_old_polarity)
                else:
                    self.determine_polarity(branch_map, old_capacitor)
                old_capacitor.comp_number = self.number
                old_capacitor.comp_pos_3D = self.pos_3D
                old_capacitor.comp_pos = self.pos
                old_capacitor.comp_sheet = self.sheet
                old_capacitor.save()
                check_ckt[0].save()
            if check_capacitor and len(check_capacitor)==1:
                comp_found = True
                for c1 in range(len(check_capacitor)-1, 0, -1):
                    check_capacitor[c1].delete()
                    check_ckt[0].save()

        if not comp_found:
            new_capacitor = models.Capacitor()
            new_capacitor.comp_capacitor = self.capacitor
            if not (self.polrty==[-1, -1]):
                new_capacitor.comp_polarity = NwRdr.csv_element_2D(self.polrty)
            if not (self.polrty_3D==[-1, -1, -1]):
                new_capacitor.comp_polarity_3D = NwRdr.csv_element(self.polrty_3D)
            new_capacitor.comp_number = self.number
            new_capacitor.comp_pos_3D = self.pos_3D
            new_capacitor.comp_pos = self.pos
            new_capacitor.comp_sheet = self.sheet
            new_capacitor.sheet_name = self.sheet_name.split(".csv")[0]
            new_capacitor.comp_tag = self.tag
            self.determine_polarity(branch_map, new_capacitor)
            ckt_file_item = ckt_file_list.filter(ckt_file_name=self.sheet_name)
            new_capacitor.comp_ckt = ckt_file_item[0]
            new_capacitor.save()
        sim_para_model.save()

        return

    def create_form_values(self, sim_para_model, ckt_file_list, branch_map):
        """
        This function creates a new database entry for a component or
        updates an existing database entry from the component class data.
        """
        comp_found = False
        check_ckt = sim_para_model.circuitschematics_set.\
                filter(ckt_file_name=self.sheet_name)
        try:
            check_capacitor = check_ckt[0].capacitor_set.\
                    filter(comp_tag=self.tag)
        except:
            comp_found = False
        else:
            if check_capacitor and len(check_capacitor)==1:
                comp_found = True
                old_capacitor = check_capacitor[0]
                old_capacitor.comp_capacitor = self.capacitor
                if not (self.polrty==[-1, -1]):
                    old_capacitor.comp_polarity = NwRdr.csv_element_2D(self.polrty)
                if not (self.polrty_3D==[-1, -1, -1]):
                    old_capacitor.comp_polarity_3D = NwRdr.csv_element(self.polrty_3D)
                old_capacitor.comp_number = self.number
                old_capacitor.comp_pos_3D = self.pos_3D
                old_capacitor.comp_pos = self.pos
                old_capacitor.comp_sheet = self.sheet
                old_capacitor.save()
                check_ckt[0].save()
            if check_capacitor and len(check_capacitor)==1:
                comp_found = True
                for c1 in range(len(check_capacitor)-1, 0, -1):
                    check_capacitor[c1].delete()
                    check_ckt[0].save()

        if not comp_found:
            new_capacitor = models.Capacitor()
            new_capacitor.comp_capacitor = self.capacitor
            if not (self.polrty==[-1, -1]):
                new_capacitor.comp_polarity = NwRdr.csv_element_2D(self.polrty)
            if not (self.polrty_3D==[-1, -1, -1]):
                new_capacitor.comp_polarity_3D = NwRdr.csv_element(self.polrty_3D)
            new_capacitor.comp_number = self.number
            new_capacitor.comp_pos_3D = self.pos_3D
            new_capacitor.comp_pos = self.pos
            new_capacitor.comp_sheet = self.sheet
            new_capacitor.sheet_name = self.sheet_name.split(".csv")[0]
            new_capacitor.comp_tag = self.tag
            self.determine_polarity(branch_map, new_capacitor)
            ckt_file_item = ckt_file_list.filter(ckt_file_name=self.sheet_name)
            new_capacitor.comp_ckt = ckt_file_item[0]
            new_capacitor.save()
        sim_para_model.save()

        return

    def list_existing_components(self, ckt_file):
        """
        Check if the model of the circuit file contains
        the associated database entry for the component.
        Returns an empty list if not found.
        """
        try:
            check_capacitor = ckt_file.capacitor_set.all().\
                        filter(comp_tag=self.tag)
        except:
            comp_list = []
        else:
            if check_capacitor and len(check_capacitor)==1:
                comp_list = check_capacitor[0]
            else:
                comp_list = []
        return comp_list

    def comp_as_a_dict(self, ckt_file):
        """
        Returns information about a component as a list
        that can be displayed in a webpage.
        """
        try:
            check_capacitor = ckt_file.capacitor_set.all().\
                        filter(comp_tag=self.tag)
        except:
            comp_list = []
        else:
            if check_capacitor and len(check_capacitor)==1:
                comp_list = []
                comp_list.append(["Component type", check_capacitor[0].comp_type])
                comp_list.append(["Component name", check_capacitor[0].comp_tag])
                comp_list.append(["Component position", check_capacitor[0].comp_pos])
                comp_list.append(["Capacitor value", check_capacitor[0].comp_capacitor])
                comp_list.append(["Positive polarity", check_capacitor[0].comp_polarity])
            else:
                comp_list = []
        return comp_list

    def comp_as_a_form(self, ckt_file):
        """
        Returns a populated form for a component.
        """
        try:
            check_capacitor = ckt_file.capacitor_set.all().\
                        filter(comp_tag=self.tag)
        except:
            return []
        else:
            if check_capacitor and len(check_capacitor)==1:
                return [models.CapacitorForm, check_capacitor[0]]
                # comp_list = models.CapacitorForm(instance=check_capacitor[0])
            else:
                return []
        # return comp_list

    def save_to_db(self, ckt_file):
        """
        Returns a populated form for a component.
        """
        try:
            check_capacitor = ckt_file.capacitor_set.all().\
                        filter(comp_tag=self.tag)
        except:
            return
        else:
            if check_capacitor and len(check_capacitor)==1:
                old_capacitor = check_capacitor[0]
                old_capacitor.comp_capacitor = self.capacitor
                if not (self.polrty==[-1, -1]):
                    old_capacitor.comp_polarity = NwRdr.csv_element_2D(self.polrty)
                if not (self.polrty_3D==[-1, -1, -1]):
                    old_capacitor.comp_polarity_3D = NwRdr.csv_element(self.polrty_3D)
                old_capacitor.save()
                ckt_file.save()
                return
            else:
                return

    def update_form_data(self, request, comp_model, branch_map):
        """
        Extracts data from a form and saves it to the database.
        """
        received_form = models.CapacitorForm(request.POST)
        if received_form.is_valid():
            received_data = received_form.cleaned_data
            comp_model.comp_capacitor = received_data["comp_capacitor"]
            new_polarity = received_data["comp_polarity"]
            comp_model.comp_polarity = new_polarity
            new_polarity_3D = [comp_model.comp_sheet, ]
            new_polarity_3D.extend(NwRdr.csv_tuple_2D(new_polarity))
            current_pos = NwRdr.csv_tuple(comp_model.comp_pos_3D)
            for c1 in range(len(branch_map)):
                for c2 in range(c1+1, len(branch_map[c1])):
                    for c3 in range(len(branch_map[c1][c2])):
                        if current_pos in branch_map[c1][c2][c3]:
                            if new_polarity_3D not in branch_map[c1][c2][c3]:
                                received_form.add_error("comp_polarity", \
                                    "Polarity has to be an element on same branch as capacitor.")
                                form_status = [received_form, ]
                            elif new_polarity_3D==current_pos:
                                received_form.add_error("comp_polarity", \
                                    "Polarity can't be the same element as the component.")
                                form_status = [received_form, ]
                            else:
                                comp_model.comp_polarity_3D = NwRdr.csv_element(new_polarity_3D)
                                comp_model.save()
                                form_status = []
        else:
            form_status = [received_form, ]
        return form_status

    def pre_run_check(self, ckt_file_item, branch_map):
        """
        This function checks for errors primarily in polarity.
        """
        comp_errors = []
        try:
            check_capacitor = ckt_file_item.capacitor_set.all().\
                        filter(comp_tag=self.tag)
        except:
            pass
        else:
            if check_capacitor and len(check_capacitor)==1:
                comp_item = check_capacitor[0]
                current_pos = NwRdr.csv_tuple(comp_item.comp_pos_3D)
                current_polarity = NwRdr.csv_tuple(comp_item.comp_polarity_3D)
                for c1 in range(len(branch_map)):
                    for c2 in range(c1+1, len(branch_map[c1])):
                        for c3 in range(len(branch_map[c1][c2])):
                            if current_pos in branch_map[c1][c2][c3]:
                                if current_polarity not in branch_map[c1][c2][c3]:
                                    print(current_pos, current_polarity)
                                    comp_errors.append("Polarity has to be an element on \
                                        same branch as capacitor. Check Capacitor_" + self.tag)
                                elif current_pos==current_polarity:
                                    comp_errors.append("Polarity can't be the same element \
                                        as the component. Check Capacitor_" + self.tag)
        return comp_errors

    def assign_parameters(self, ckt_file_list):
        """
        Transfers data from the database to the component clas
        objects for the simulation.
        """
        for ckt_file_item in ckt_file_list:
            try:
                check_capacitor = ckt_file_item.capacitor_set.all().\
                        filter(comp_tag=self.tag)
            except:
                pass
            else:
                if check_capacitor and len(check_capacitor)==1:
                    comp_model = check_capacitor[0]
                    self.capacitor = comp_model.comp_capacitor
                    self.polrty = NwRdr.csv_tuple_2D(comp_model.comp_polarity)
                    self.polrty_3D = NwRdr.csv_tuple(comp_model.comp_polarity_3D)
        return


class Voltage_Source:
    """
    Voltage Source class. Contains functions to initiliaze
    the resistor according to name tag, unique cell position,
    update system matrix on each iteration.
    """

    def __init__(self, volt_index, volt_pos, volt_tag, nw_input):
        """
        Constructor to initialize value.
        Also, takes in the identifiers -
        index (serial number), cell position and tag.
        """
        self.type = "VoltageSource"
        self.number = volt_index
        self.pos_3D = volt_pos
        self.sheet = NwRdr.csv_tuple(volt_pos)[0]
        self.pos = NwRdr.csv_element_2D(NwRdr.csv_tuple(volt_pos)[1:])
        self.tag = volt_tag
        self.sheet_name = nw_input[self.sheet] + ".csv"
        self.has_voltage = "yes"
        self.is_meter = "no"
        self.has_control = "no"
        self.v_peak = 120.0
        self.v_freq = 60.0
        self.v_phase = 0.0
        self.v_offset = 0.0
        self.voltage = 0.0
        self.current = 0.0
        self.op_value = 0.0
        self.polrty = [-1, -1]
        self.polrty_3D = [-1, -1, -1]

        return

    def display(self):
        """
        Displays info about the component.
        """
        print("Voltage Source is {} of %f V(peak), {} Hz(frequency), {} (degrees phase shift) and {} dc offset \
with positive polarity towards {} in sheet {}".format(
            self.tag, self.v_peak, self.v_freq, self.v_phase, self.v_offset, self.pos, \
            NwRdr.csv_element_2D(self.polrty), self.sheet_name
        ))

        return

    def get_polarity(self, ckt_mat, sys_branch):

        if self.polrty==[-1, -1]:
            # Looking for a default value of polarity
            # in the neighbouring cells

            if self.volt_elem[0]>0:
                if ckt_mat[self.sheet][self.volt_elem[0]-1][self.volt_elem[1]]:
                    self.polrty = [self.volt_elem[0]-1, self.volt_elem[1]]
            if self.volt_elem[1]>0:
                if ckt_mat[self.sheet][self.volt_elem[0]][self.volt_elem[1]-1]:
                    self.polrty = [self.volt_elem[0], self.volt_elem[1]-1]
            if self.volt_elem[0]<len(ckt_mat[self.sheet])-1:
                if ckt_mat[self.sheet][self.volt_elem[0]+1][self.volt_elem[1]]:
                    self.polrty = [self.volt_elem[0]+1, self.volt_elem[1]]
            if self.volt_elem[1]<len(ckt_mat[self.sheet][0])-1:
                if ckt_mat[self.sheet][self.volt_elem[0]][self.volt_elem[1]+1]:
                    self.polrty = [self.volt_elem[0], self.volt_elem[1]+1]
        else:
            for c1 in range(len(sys_branch)):
                if [self.sheet, self.volt_elem[0], self.volt_elem[1]] in sys_branch[c1]:
                    if not [self.sheet, self.polrty[0], self.polrty[1]] in sys_branch[c1]:
                        print()
                        print("!"*50)
                        print("ERROR!!! Voltage source polarity should be in the same branch as the voltage source. \
Check source at {} in sheet {}".format(self.pos, self.sheet_name))
                        print("!"*50)
                        print()

        self.polrty_3D = [self.sheet, self.polrty[0], self.polrty[1]]

        return

    def ask_values(self, x_list, ckt_mat, sys_branch):
        """
        Writes the values needed to the spreadsheet.
        """
        volt_params = ["VoltageSource"]
        volt_params.append(self.tag)
        volt_params.append(self.pos)
        volt_params.append("Peak (Volts) = %f" %self.v_peak)
        volt_params.append("Frequency (Hertz) = %f" %self.v_freq)
        volt_params.append("Phase (degrees) = %f" %self.v_phase)
        volt_params.append("Dc offset = %f" %self.v_offset)

        self.volt_elem = NwRdr.csv_tuple_2D(self.pos)
        self.get_polarity(ckt_mat, sys_branch)

        volt_params.append("Positive polarity towards (cell) = %s" %NwRdr.csv_element_2D(self.polrty))
        x_list.append(volt_params)

        return

    def export_values_to_csv(self):
        """
        Writes the values needed to the spreadsheet.
        """
        volt_params = ["VoltageSource"]
        volt_params.append(self.tag)
        volt_params.append(self.pos)
        volt_params.append("Peak (Volts) = %f" %self.v_peak)
        volt_params.append("Frequency (Hertz) = %f" %self.v_freq)
        volt_params.append("Phase (degrees) = %f" %self.v_phase)
        volt_params.append("Dc offset = %f" %self.v_offset)
        volt_params.append("Positive polarity towards (cell) = %s" %NwRdr.csv_element_2D(self.polrty))

        return volt_params

    def get_values(self, x_list, ckt_mat):
        """
        Takes the parameter from the spreadsheet.
        """
        self.v_peak = float(x_list[0].split("=")[1])
        self.v_freq = float(x_list[1].split("=")[1])
        self.v_phase = float(x_list[2].split("=")[1])
        self.v_offset = float(x_list[3].split("=")[1])
        volt_polrty = x_list[4].split("=")[1]

        # Convert the human readable form of cell
        # to [row, column] form
        while volt_polrty[0]==" ":
            volt_polrty = volt_polrty[1:]

        self.polrty = NwRdr.csv_tuple_2D(volt_polrty)
        self.polrty_3D = [self.sheet, self.polrty[0], self.polrty[1]]

        if not ckt_mat[self.sheet][self.polrty[0]][self.polrty[1]]:
            print("Polarity incorrect. Branch does not exist at {} in sheet {}".format(
                NwRdr.csv_element(self.polrty), self.sheet_name
            ))

        return

    def determine_branch(self, sys_branches):
        """
        Determines which branch the component is found in.
        """
        for c1 in range(len(sys_branches)):
            if NwRdr.csv_tuple(self.pos_3D) in sys_branches[c1]:
                self.component_branch_pos = c1

        return

    def transfer_to_sys(self, sys_loops, mat_e, mat_a, mat_b, mat_u, source_list):
        """
        The matrix B in E.dx/dt=Ax+Bu will be updated by the
        polarity of the voltage source.
        """
        for c1 in range(len(sys_loops)):
            for c2 in range(len(sys_loops[c1][c1])):
                if NwRdr.csv_tuple(self.pos) in sys_loops[c1][c1][c2]:
                    # If the positive polarity appears before the voltage position
                    # it means as per KVL, we are moving from +ve to -ve
                    # and so the voltage will be taken negative
                    if sys_loops[c1][c1][c2].index(self.polrty)<sys_loops[c1][c1][c2].index(NwRdr.csv_tuple(self.pos)):
                        if sys_loops[c1][c1][c2][-1]=="forward":
                            mat_b.data[c1][source_list.index(self.pos)] = -1.0
                        else:
                            mat_b.data[c1][source_list.index(self.pos)] = 1.0
                    else:
                        if sys_loops[c1][c1][c2][-1]=="forward":
                            mat_b.data[c1][source_list.index(self.pos)] = 1.0
                        else:
                            mat_b.data[c1][source_list.index(self.pos)] = -1.0
        return

    def transfer_to_branch(self, sys_branch, source_list,  mat_u):
        """
        Transfers parameters to system branch if voltage
        source exists in the branch.
        """
        if NwRdr.csv_tuple(self.pos_3D) in sys_branch:
            if sys_branch.index(self.polrty_3D)<sys_branch.index(NwRdr.csv_tuple(self.pos_3D)):
                sys_branch[-1][1][source_list.index(self.pos_3D)] = -1.0
            else:
                sys_branch[-1][1][source_list.index(self.pos_3D)] = 1.0

    def generate_val(self, source_lst, mat_e, mat_a, mat_b, mat_u, t, dt):
        """
        The source voltage is updated in the matrix u in
        E.dx/dt=Ax+Bu .
        """
        self.voltage = self.v_peak*math.sin(2*math.pi*self.v_freq*t + self.v_phase*math.pi/180.0) + self.v_offset
        mat_u.data[source_lst.index(self.pos_3D)][0] = self.voltage
        self.op_value = self.voltage

    def update_val(self, sys_loop_map, lbyr_ratio, mat_e, mat_a, mat_b, state_vec, mat_u, sys_branches, sys_events):
        pass

    def pre_determine_state(self, br_currents, sys_branches, sys_events):
        pass

    def determine_state(self, br_currents, sys_branches, sys_events):
        pass

    def retrieve_db_model(self, sim_para_model):
        """
        This function returns the model instance object.
        """
        check_ckt = sim_para_model.circuitschematics_set.\
                    filter(ckt_file_name=self.sheet_name)
        try:
            check_voltagesource = check_ckt[0].voltage_source_set.\
                    filter(comp_tag=self.tag)
        except:
            return None
        else:
            if check_voltagesource and len(check_voltagesource)==1:
                return check_voltagesource[0]

    def determine_polarity(self, branch_map, voltagesource_obj):
        """
        Determines polarity of a database element.
        """
        for c1 in range(len(branch_map)):
            for c2 in range(c1+1, len(branch_map)):
                for c3 in range(len(branch_map[c1][c2])):
                    if NwRdr.csv_tuple(self.pos_3D) in branch_map[c1][c2][c3]:
                        pos_in_branch = branch_map[c1][c2][c3].\
                                index(NwRdr.csv_tuple(self.pos_3D))
                        prev_element = branch_map[c1][c2][c3][pos_in_branch-1]
                        voltagesource_obj.comp_polarity_3D = NwRdr.csv_element(prev_element)
                        voltagesource_obj.comp_polarity = \
                                NwRdr.csv_element_2D(prev_element[1:])
        return

    def init_db_values(self, sim_para_model, ckt_file_list, branch_map):
        """
        This function creates a new database entry for a component or
        updates an existing database entry from the component class data.
        """
        comp_found = False
        check_ckt = sim_para_model.circuitschematics_set.\
                    filter(ckt_file_name=self.sheet_name)
        try:
            check_voltagesource = check_ckt[0].voltage_source_set.\
                    filter(comp_tag=self.tag)
        except:
            comp_found = False
        else:
            if check_voltagesource and len(check_voltagesource)==1:
                comp_found = True
                old_voltagesource = check_voltagesource[0]
                if not (self.polrty==[-1, -1]):
                    old_voltagesource.comp_polarity = NwRdr.csv_element_2D(self.polrty)
                if not (self.polrty_3D==[-1, -1, -1]):
                    old_voltagesource.comp_polarity_3D = NwRdr.csv_element(self.polrty_3D)
                if old_voltagesource.comp_polarity_3D:
                    voltagesource_old_polarity = NwRdr.csv_tuple(old_voltagesource.comp_polarity_3D)
                    voltagesource_new_polarity = NwRdr.csv_tuple(self.pos_3D)
                    voltagesource_old_polarity[0] = voltagesource_new_polarity[0]
                    old_voltagesource.comp_polarity_3D = NwRdr.csv_element(voltagesource_old_polarity)
                else:
                    self.determine_polarity(branch_map, old_voltagesource)
                old_voltagesource.comp_number = self.number
                old_voltagesource.comp_pos_3D = self.pos_3D
                old_voltagesource.comp_pos = self.pos
                old_voltagesource.comp_sheet = self.sheet
                old_voltagesource.save()
                check_ckt[0].save()
            if check_voltagesource and len(check_voltagesource)>1:
                comp_found = True
                for c1 in range(len(check_voltagesource)-1, 0, -1):
                    check_voltagesource[c1].delete()
                    check_ckt[0].save()

        if not comp_found:
            new_voltagesource = models.Voltage_Source()
            new_voltagesource.comp_volt_peak = self.v_peak
            new_voltagesource.comp_volt_freq = self.v_freq
            new_voltagesource.comp_volt_phase = self.v_phase
            new_voltagesource.comp_volt_offset = self.v_offset
            if not (self.polrty==[-1, -1]):
                new_voltagesource.comp_polarity = NwRdr.csv_element_2D(self.polrty)
            if not (self.polrty_3D==[-1, -1, -1]):
                new_voltagesource.comp_polarity_3D = NwRdr.csv_element(self.polrty_3D)
            new_voltagesource.comp_number = self.number
            new_voltagesource.comp_pos_3D = self.pos_3D
            new_voltagesource.comp_pos = self.pos
            new_voltagesource.comp_sheet = self.sheet
            new_voltagesource.sheet_name = self.sheet_name.split(".csv")[0]
            new_voltagesource.comp_tag = self.tag
            new_voltagesource.comp_volt_peak = self.v_peak
            new_voltagesource.comp_volt_freq = self.v_freq
            new_voltagesource.comp_volt_phase = self.v_phase
            new_voltagesource.comp_volt_offset = self.v_offset
            self.determine_polarity(branch_map, new_voltagesource)
            ckt_file_item = ckt_file_list.filter(ckt_file_name=self.sheet_name)
            new_voltagesource.comp_ckt = ckt_file_item[0]
            new_voltagesource.save()
        sim_para_model.save()

        return

    def create_form_values(self, sim_para_model, ckt_file_list, branch_map):
        """
        This function creates a new database entry for a component or
        updates an existing database entry from the component class data.
        """
        comp_found = False
        check_ckt = sim_para_model.circuitschematics_set.\
                    filter(ckt_file_name=self.sheet_name)
        try:
            check_voltagesource = check_ckt[0].voltage_source_set.\
                    filter(comp_tag=self.tag)
        except:
            comp_found = False
        else:
            if check_voltagesource and len(check_voltagesource)==1:
                comp_found = True
                old_voltagesource = check_voltagesource[0]
                old_voltagesource.comp_volt_peak = self.v_peak
                old_voltagesource.comp_volt_freq = self.v_freq
                old_voltagesource.comp_volt_phase = self.v_phase
                old_voltagesource.comp_volt_offset = self.v_offset
                if not (self.polrty==[-1, -1]):
                    old_voltagesource.comp_polarity = NwRdr.csv_element_2D(self.polrty)
                if not (self.polrty_3D==[-1, -1, -1]):
                    old_voltagesource.comp_polarity_3D = NwRdr.csv_element(self.polrty_3D)
                old_voltagesource.comp_number = self.number
                old_voltagesource.comp_pos_3D = self.pos_3D
                old_voltagesource.comp_pos = self.pos
                old_voltagesource.comp_sheet = self.sheet
                old_voltagesource.save()
                check_ckt[0].save()
            if check_voltagesource and len(check_voltagesource)>1:
                comp_found = True
                for c1 in range(len(check_voltagesource)-1, 0, -1):
                    check_voltagesource[c1].delete()
                    check_ckt[0].save()

        if not comp_found:
            new_voltagesource = models.Voltage_Source()
            new_voltagesource.comp_volt_peak = self.v_peak
            new_voltagesource.comp_volt_freq = self.v_freq
            new_voltagesource.comp_volt_phase = self.v_phase
            new_voltagesource.comp_volt_offset = self.v_offset
            if not (self.polrty==[-1, -1]):
                new_voltagesource.comp_polarity = NwRdr.csv_element_2D(self.polrty)
            if not (self.polrty_3D==[-1, -1, -1]):
                new_voltagesource.comp_polarity_3D = NwRdr.csv_element(self.polrty_3D)
            new_voltagesource.comp_number = self.number
            new_voltagesource.comp_pos_3D = self.pos_3D
            new_voltagesource.comp_pos = self.pos
            new_voltagesource.comp_sheet = self.sheet
            new_voltagesource.sheet_name = self.sheet_name.split(".csv")[0]
            new_voltagesource.comp_tag = self.tag
            new_voltagesource.comp_volt_peak = self.v_peak
            new_voltagesource.comp_volt_freq = self.v_freq
            new_voltagesource.comp_volt_phase = self.v_phase
            new_voltagesource.comp_volt_offset = self.v_offset
            self.determine_polarity(branch_map, new_voltagesource)
            ckt_file_item = ckt_file_list.filter(ckt_file_name=self.sheet_name)
            new_voltagesource.comp_ckt = ckt_file_item[0]
            new_voltagesource.save()
        sim_para_model.save()

        return

    def list_existing_components(self, ckt_file):
        """
        Check if the model of the circuit file contains
        the associated database entry for the component.
        Returns an empty list if not found.
        """
        try:
            check_voltagesource = ckt_file.voltage_source_set.all().\
                        filter(comp_tag=self.tag)
        except:
            comp_list = []
        else:
            if check_voltagesource and len(check_voltagesource)==1:
                comp_list = check_voltagesource[0]
            else:
                comp_list = []
        return comp_list

    def comp_as_a_dict(self, ckt_file):
        """
        Returns information about a component as a list
        that can be displayed in a webpage.
        """
        try:
            check_voltagesource = ckt_file.voltage_source_set.all().\
                        filter(comp_tag=self.tag)
        except:
            comp_list = []
        else:
            if check_voltagesource and len(check_voltagesource)==1:
                comp_list = []
                comp_list.append(["Component type", check_voltagesource[0].comp_type])
                comp_list.append(["Component name", check_voltagesource[0].comp_tag])
                comp_list.append(["Component position", check_voltagesource[0].comp_pos])
                comp_list.append(["Peak value", check_voltagesource[0].comp_volt_peak])
                comp_list.append(["Frequency", check_voltagesource[0].comp_volt_freq])
                comp_list.append(["Phase angle", check_voltagesource[0].comp_volt_phase])
                comp_list.append(["Dc offset", check_voltagesource[0].comp_volt_offset])
                comp_list.append(["Positive polarity", check_voltagesource[0].comp_polarity])
            else:
                comp_list = []
        return comp_list

    def comp_as_a_form(self, ckt_file):
        """
        Returns a populated form for a component.
        """
        try:
            check_voltagesource = ckt_file.voltage_source_set.all().\
                        filter(comp_tag=self.tag)
        except:
            return []
        else:
            if check_voltagesource and len(check_voltagesource)==1:
                return [models.Voltage_SourceForm, check_voltagesource[0]]
                # comp_list = models.Voltage_SourceForm(instance=check_voltagesource[0])
            else:
                return []
        # return comp_list

    def save_to_db(self, ckt_file):
        """
        Returns a populated form for a component.
        """
        try:
            check_voltagesource = ckt_file.voltage_source_set.all().\
                        filter(comp_tag=self.tag)
        except:
            return
        else:
            if check_voltagesource and len(check_voltagesource)==1:
                old_voltagesource = check_voltagesource[0]
                old_voltagesource.comp_volt_peak = self.v_peak
                old_voltagesource.comp_volt_freq = self.v_freq
                old_voltagesource.comp_volt_phase = self.v_phase
                old_voltagesource.comp_volt_offset = self.v_offset
                if not (self.polrty==[-1, -1]):
                    old_voltagesource.comp_polarity = NwRdr.csv_element_2D(self.polrty)
                if not (self.polrty_3D==[-1, -1, -1]):
                    old_voltagesource.comp_polarity_3D = NwRdr.csv_element(self.polrty_3D)
                old_voltagesource.save()
                ckt_file.save()
                return
            else:
                return

    def update_form_data(self, request, comp_model, branch_map):
        """
        Extracts data from a form and saves it to the database.
        """
        received_form = models.Voltage_SourceForm(request.POST)
        if received_form.is_valid():
            received_data = received_form.cleaned_data
            comp_model.comp_volt_peak = received_data["comp_volt_peak"]
            comp_model.comp_volt_freq = received_data["comp_volt_freq"]
            comp_model.comp_volt_phase = received_data["comp_volt_phase"]
            comp_model.comp_volt_offset = received_data["comp_volt_offset"]
            new_polarity = received_data["comp_polarity"]
            comp_model.comp_polarity = new_polarity
            new_polarity_3D = [comp_model.comp_sheet, ]
            new_polarity_3D.extend(NwRdr.csv_tuple_2D(new_polarity))
            current_pos = NwRdr.csv_tuple(comp_model.comp_pos_3D)
            for c1 in range(len(branch_map)):
                for c2 in range(c1+1, len(branch_map[c1])):
                    for c3 in range(len(branch_map[c1][c2])):
                        if current_pos in branch_map[c1][c2][c3]:
                            if new_polarity_3D not in branch_map[c1][c2][c3]:
                                received_form.add_error("comp_polarity", \
                                    "Polarity has to be an element on same branch as voltage source.")
                                form_status = [received_form, ]
                            elif current_pos==new_polarity_3D:
                                received_form.add_error("comp_polarity", \
                                    "Polarity can't be the same element as the component.")
                                form_status = [received_form, ]
                            else:
                                comp_model.comp_polarity_3D = NwRdr.csv_element(new_polarity_3D)
                                comp_model.save()
                                form_status = []
        else:
            form_status = [received_form, ]
        return form_status

    def pre_run_check(self, ckt_file_item, branch_map):
        """
        This function checks for errors primarily in polarity.
        """
        comp_errors = []
        try:
            check_voltage_source = ckt_file_item.voltage_source_set.all().\
                        filter(comp_tag=self.tag)
        except:
            pass
        else:
            if check_voltage_source and len(check_voltage_source)==1:
                comp_item = check_voltage_source[0]
                current_pos = NwRdr.csv_tuple(comp_item.comp_pos_3D)
                current_polarity = NwRdr.csv_tuple(comp_item.comp_polarity_3D)
                for c1 in range(len(branch_map)):
                    for c2 in range(c1+1, len(branch_map[c1])):
                        for c3 in range(len(branch_map[c1][c2])):
                            if current_pos in branch_map[c1][c2][c3]:
                                if current_polarity not in branch_map[c1][c2][c3]:
                                    comp_errors.append("Polarity has to be an element on \
                                        same branch as voltage source. Check VoltageSource_" + self.tag)
                                elif current_pos==current_polarity:
                                    comp_errors.append("Polarity can't be the same element \
                                        as the component. Check VoltageSource_" + self.tag)
        return comp_errors

    def assign_parameters(self, ckt_file_list):
        """
        Transfers data from the database to the component clas
        objects for the simulation.
        """
        for ckt_file_item in ckt_file_list:
            try:
                check_voltage_source = ckt_file_item.voltage_source_set.all().\
                        filter(comp_tag=self.tag)
            except:
                pass
            else:
                if check_voltage_source and len(check_voltage_source)==1:
                    comp_model = check_voltage_source[0]
                    self.polrty = NwRdr.csv_tuple_2D(comp_model.comp_polarity)
                    self.polrty_3D = NwRdr.csv_tuple(comp_model.comp_polarity_3D)
                    self.v_peak = comp_model.comp_volt_peak
                    self.v_freq = comp_model.comp_volt_freq
                    self.v_phase = comp_model.comp_volt_phase
                    self.v_offset = comp_model.comp_volt_offset
        return


class Ammeter:
    """
    Ammeter class. Contains functions to initiliaze
    the resistor according to name tag, unique cell position,
    update system matrix on each iteration.
    """

    def __init__(self, amm_index, amm_pos, amm_tag, nw_input):
        """
        Constructor to initialize value.
        Also, takes in the identifiers -
        index (serial number), cell position and tag.
        """
        self.type = "Ammeter"
        self.number = amm_index
        self.pos_3D = amm_pos
        self.sheet = NwRdr.csv_tuple(amm_pos)[0]
        self.pos = NwRdr.csv_element_2D(NwRdr.csv_tuple(amm_pos)[1:])
        self.tag = amm_tag
        self.sheet_name = nw_input[self.sheet] + ".csv"
        self.has_voltage = "no"
        self.is_meter = "yes"
        self.has_control = "no"
        self.current = 0.0
        self.op_value = 0.0
        self.polrty = [-1, -1]
        self.polrty_3D = [-1, -1, -1]
        self.component_branch_pos = 0
        self.component_branch_dir = 1.0

        return

    def display(self):
        """
        Displays info about the component.
        """
        print("Ammeter is {} located at {} with positive polarity towards {} in sheet {}".format(
            self.tag, self.pos, NwRdr.csv_element_2D(self.polrty), self.sheet_name
        ))

        return

    def get_polarity(self, ckt_mat, sys_branch):
        if self.polrty==[-1, -1]:
            # Looking for a default value of polarity
            # in the neighbouring cells

            if self.amm_elem[0]>0:
                if ckt_mat[self.sheet][self.amm_elem[0]-1][self.amm_elem[1]]:
                    self.polrty = [self.amm_elem[0]-1, self.amm_elem[1]]
            if self.amm_elem[1]>0:
                if ckt_mat[self.sheet][self.amm_elem[0]][self.amm_elem[1]-1]:
                    self.polrty = [self.amm_elem[0], self.amm_elem[1]-1]
            if self.amm_elem[0]<len(ckt_mat[self.sheet])-1:
                if ckt_mat[self.sheet][self.amm_elem[0]+1][self.amm_elem[1]]:
                    self.polrty = [self.amm_elem[0]+1, self.amm_elem[1]]
            if self.amm_elem[1]<len(ckt_mat[self.sheet][0])-1:
                if ckt_mat[self.sheet][self.amm_elem[0]][self.amm_elem[1]+1]:
                    self.polrty = [self.amm_elem[0], self.amm_elem[1]+1]

        else:
            for c1 in range(len(sys_branch)):
                if [self.sheet, self.amm_elem[0], self.amm_elem[1]] in sys_branch[c1]:
                    if not [self.sheet, self.polrty[0], self.polrty[1]] in sys_branch[c1]:
                        print()
                        print("!"*50)
                        print("ERROR!!! Ammeter polarity should be in the same branch as ammeter. \
Check ammeter at {} in sheet {}".format(self.pos, self.sheet_name))
                        print("!"*50)
                        print()
                        raise CktEx.PolarityError

        self.polrty_3D = [self.sheet, self.polrty[0], self.polrty[1]]

        return

    def ask_values(self, x_list, ckt_mat, sys_branch):
        """
        Writes the values needed to the spreadsheet.
        """
        amm_params = ["Ammeter"]
        amm_params.append(self.tag)
        amm_params.append(self.pos)

        self.amm_elem = NwRdr.csv_tuple_2D(self.pos)
        self.get_polarity(ckt_mat, sys_branch)

        amm_params.append("Positive polarity towards (cell) = %s" %NwRdr.csv_element_2D(self.polrty))
        x_list.append(amm_params)

        return

    def export_values_to_csv(self):
        """
        Writes the values needed to the spreadsheet.
        """
        amm_params = ["Ammeter"]
        amm_params.append(self.tag)
        amm_params.append(self.pos)
        amm_params.append("Positive polarity towards (cell) = %s" %NwRdr.csv_element_2D(self.polrty))

        return amm_params

    def get_values(self, x_list, ckt_mat):
        """
        Takes the parameter from the spreadsheet.
        """
        amm_polrty = x_list[0].split("=")[1]

        # Convert the human readable form of cell
        # to [row, column] form
        while amm_polrty[0]==" ":
            amm_polrty = amm_polrty[1:]

        self.polrty = NwRdr.csv_tuple_2D(amm_polrty)
        self.polrty_3D = [self.sheet, self.polrty[0], self.polrty[1]]

        if not ckt_mat[self.sheet][self.polrty[0]][self.polrty[1]]:
            print("Polarity incorrect or changed. Branch does not exist at {}".format(
                NwRdr.csv_element_2D(self.polrty)
            ))
            raise CktEx.PolarityError

        return

    def determine_branch(self, sys_branches):
        """
        Determines which branch the component is found in.
        """
        for c1 in range(len(sys_branches)):
            if NwRdr.csv_tuple(self.pos_3D) in sys_branches[c1]:
                self.component_branch_pos = c1
                if sys_branches[c1].index(self.polrty_3D)>sys_branches[c1].index(NwRdr.csv_tuple(self.pos_3D)):
                    self.component_branch_dir = 1.0
                else:
                    self.component_branch_dir = -1.0

        return

    def transfer_to_sys(self, sys_loops, mat_e, mat_a, mat_b, mat_u, source_list):
        pass

    def transfer_to_branch(self, sys_branch, source_list,  mat_u):
        pass

    def generate_val(self, source_lst, mat_e, mat_a, mat_b, mat_u, t, dt):
        pass

    def update_val_old(self, sys_loop_map, lbyr_ratio, mat_e, mat_a, mat_b, state_vec, mat_u, sys_branches, sys_events):
        """
        The ammeter current is calculated as a result of the KVL.
        """
        for c1 in range(len(sys_branches)):
            if NwRdr.csv_tuple(self.pos) in sys_branches[c1]:
                branch_pos = c1

        if sys_branches[branch_pos].index(self.polrty)>sys_branches[branch_pos].index(NwRdr.csv_tuple(self.pos)):
            self.current = sys_branches[branch_pos][-1][2]
        else:
            self.current = -sys_branches[branch_pos][-1][2]

        # Since it is a meter, this is its output value
        self.op_value = self.current

        return

    def update_val(self, sys_loop_map, lbyr_ratio, mat_e, mat_a, mat_b, state_vec, mat_u, sys_branches, sys_events):
        """
        The ammeter current is calculated as a result of the KVL.
        """
        self.current = self.component_branch_dir*sys_branches[self.component_branch_pos][-1][2]
        # Since it is a meter, this is its output value
        self.op_value = self.current
        return

    def pre_determine_state(self, br_currents, sys_branches, sys_events):
        pass

    def determine_state(self, br_currents, sys_branches, sys_events):
        pass

    def retrieve_db_model(self, sim_para_model):
        """
        This function returns the model instance object.
        """
        check_ckt = sim_para_model.circuitschematics_set.\
                    filter(ckt_file_name=self.sheet_name)
        try:
            check_ammeter = check_ckt[0].ammeter_set.\
                    filter(comp_tag=self.tag)
        except:
            return None
        else:
            if check_ammeter and len(check_ammeter)==1:
                return check_ammeter[0]

    def determine_polarity(self, branch_map, ammeter_obj):
        """
        Determines polarity of a database object.
        """
        for c1 in range(len(branch_map)):
            for c2 in range(c1+1, len(branch_map)):
                for c3 in range(len(branch_map[c1][c2])):
                    if NwRdr.csv_tuple(self.pos_3D) in branch_map[c1][c2][c3]:
                        pos_in_branch = branch_map[c1][c2][c3].\
                                index(NwRdr.csv_tuple(self.pos_3D))
                        prev_element = branch_map[c1][c2][c3][pos_in_branch-1]
                        ammeter_obj.comp_polarity_3D = NwRdr.csv_element(prev_element)
                        ammeter_obj.comp_polarity = \
                                NwRdr.csv_element_2D(prev_element[1:])
        return

    def init_db_values(self, sim_para_model, ckt_file_list, branch_map):
        """
        This function creates a new database entry for a component or
        updates an existing database entry from the component class data.
        """
        comp_found = False
        check_ckt = sim_para_model.circuitschematics_set.\
                    filter(ckt_file_name=self.sheet_name)
        try:
            check_ammeter = check_ckt[0].ammeter_set.\
                    filter(comp_tag=self.tag)
        except:
            comp_found = False
        else:
            if check_ammeter and len(check_ammeter)==1:
                comp_found = True
                old_ammeter = check_ammeter[0]
                if not (self.polrty==[-1, -1]):
                    old_ammeter.comp_polarity = NwRdr.csv_element_2D(self.polrty)
                if not (self.polrty_3D==[-1, -1, -1]):
                    old_ammeter.comp_polarity_3D = NwRdr.csv_element(self.polrty_3D)
                if old_ammeter.comp_polarity_3D:
                    ammeter_old_polarity = NwRdr.csv_tuple(old_ammeter.comp_polarity_3D)
                    ammeter_new_polarity = NwRdr.csv_tuple(self.pos_3D)
                    ammeter_old_polarity[0] = ammeter_new_polarity[0]
                    old_ammeter.comp_polarity_3D = NwRdr.csv_element(ammeter_old_polarity)
                else:
                    self.determine_polarity(branch_map, old_ammeter)
                old_ammeter.comp_number = self.number
                old_ammeter.comp_pos_3D = self.pos_3D
                old_ammeter.comp_pos = self.pos
                old_ammeter.comp_sheet = self.sheet
                old_ammeter.save()
                check_ckt[0].save()
            if check_ammeter and len(check_ammeter)>1:
                comp_found = True
                for c1 in range(len(check_ammeter)-1, 0, -1):
                    check_ammeter[c1].delete()
                    check_ckt[0].save()

        if not comp_found:
            new_ammeter = models.Ammeter()
            if not (self.polrty==[-1, -1]):
                new_ammeter.comp_polarity = NwRdr.csv_element_2D(self.polrty)
            if not (self.polrty_3D==[-1, -1, -1]):
                new_ammeter.comp_polarity_3D = NwRdr.csv_element(self.polrty_3D)
            new_ammeter.comp_number = self.number
            new_ammeter.comp_pos_3D = self.pos_3D
            new_ammeter.comp_pos = self.pos
            new_ammeter.comp_sheet = self.sheet
            new_ammeter.sheet_name = self.sheet_name.split(".csv")[0]
            new_ammeter.comp_tag = self.tag
            self.determine_polarity(branch_map, new_ammeter)
            ckt_file_item = ckt_file_list.filter(ckt_file_name=self.sheet_name)
            new_ammeter.comp_ckt = ckt_file_item[0]
            new_ammeter.save()
        sim_para_model.save()

        return

    def create_form_values(self, sim_para_model, ckt_file_list, branch_map):
        """
        This function creates a new database entry for a component or
        updates an existing database entry from the component class data.
        """
        comp_found = False
        check_ckt = sim_para_model.circuitschematics_set.\
                    filter(ckt_file_name=self.sheet_name)
        try:
            check_ammeter = check_ckt[0].ammeter_set.\
                    filter(comp_tag=self.tag)
        except:
            comp_found = False
        else:
            if check_ammeter and len(check_ammeter)==1:
                comp_found = True
                old_ammeter = check_ammeter[0]
                if not (self.polrty==[-1, -1]):
                    old_ammeter.comp_polarity = NwRdr.csv_element_2D(self.polrty)
                if not (self.polrty_3D==[-1, -1, -1]):
                    old_ammeter.comp_polarity_3D = NwRdr.csv_element(self.polrty_3D)
                old_ammeter.comp_number = self.number
                old_ammeter.comp_pos_3D = self.pos_3D
                old_ammeter.comp_pos = self.pos
                old_ammeter.comp_sheet = self.sheet
                old_ammeter.save()
                check_ckt[0].save()
            if check_ammeter and len(check_ammeter)>1:
                comp_found = True
                for c1 in range(len(check_ammeter)-1, 0, -1):
                    check_ammeter[c1].delete()
                    check_ckt[0].save()

        if not comp_found:
            new_ammeter = models.Ammeter()
            if not (self.polrty==[-1, -1]):
                new_ammeter.comp_polarity = NwRdr.csv_element_2D(self.polrty)
            if not (self.polrty_3D==[-1, -1, -1]):
                new_ammeter.comp_polarity_3D = NwRdr.csv_element(self.polrty_3D)
            new_ammeter.comp_number = self.number
            new_ammeter.comp_pos_3D = self.pos_3D
            new_ammeter.comp_pos = self.pos
            new_ammeter.comp_sheet = self.sheet
            new_ammeter.sheet_name = self.sheet_name.split(".csv")[0]
            new_ammeter.comp_tag = self.tag
            self.determine_polarity(branch_map, new_ammeter)
            ckt_file_item = ckt_file_list.filter(ckt_file_name=self.sheet_name)
            new_ammeter.comp_ckt = ckt_file_item[0]
            new_ammeter.save()
        sim_para_model.save()

        return

    def list_existing_components(self, ckt_file):
        """
        Check if the model of the circuit file contains
        the associated database entry for the component.
        Returns an empty list if not found.
        """
        try:
            check_ammeter = ckt_file.ammeter_set.all().\
                        filter(comp_tag=self.tag)
        except:
            comp_list = []
        else:
            if check_ammeter and len(check_ammeter)==1:
                comp_list = check_ammeter[0]
            else:
                comp_list = []
        return comp_list

    def comp_as_a_dict(self, ckt_file):
        """
        Returns information about a component as a list
        that can be displayed in a webpage.
        """
        try:
            check_ammeter = ckt_file.ammeter_set.all().\
                        filter(comp_tag=self.tag)
        except:
            comp_list = []
        else:
            if check_ammeter and len(check_ammeter)==1:
                comp_list = []
                comp_list.append(["Component type", check_ammeter[0].comp_type])
                comp_list.append(["Component name", check_ammeter[0].comp_tag])
                comp_list.append(["Component position", check_ammeter[0].comp_pos])
                comp_list.append(["Positive direction of current", \
                        check_ammeter[0].comp_polarity])
            else:
                comp_list = []
        return comp_list

    def comp_as_a_form(self, ckt_file):
        """
        Returns a populated form for a component.
        """
        try:
            check_ammeter = ckt_file.ammeter_set.all().\
                        filter(comp_tag=self.tag)
        except:
            return []
        else:
            if check_ammeter and len(check_ammeter)==1:
                return [models.AmmeterForm, check_ammeter[0]]
                # comp_list = models.AmmeterForm(instance=check_ammeter[0])
            else:
                return []
        # return comp_list

    def save_to_db(self, ckt_file):
        """
        Returns a populated form for a component.
        """
        try:
            check_ammeter = ckt_file.ammeter_set.all().\
                        filter(comp_tag=self.tag)
        except:
            return
        else:
            if check_ammeter and len(check_ammeter)==1:
                old_ammeter = check_ammeter[0]
                if not (self.polrty==[-1, -1]):
                    old_ammeter.comp_polarity = NwRdr.csv_element_2D(self.polrty)
                if not (self.polrty_3D==[-1, -1, -1]):
                    old_ammeter.comp_polarity_3D = NwRdr.csv_element(self.polrty_3D)
                old_ammeter.save()
                ckt_file.save()
                return
            else:
                return

    def update_form_data(self, request, comp_model, branch_map):
        """
        Extracts data from a form and saves it to the database.
        """
        received_form = models.AmmeterForm(request.POST)
        if received_form.is_valid():
            received_data = received_form.cleaned_data
            new_polarity = received_data["comp_polarity"]
            comp_model.comp_polarity = new_polarity
            new_polarity_3D = [comp_model.comp_sheet, ]
            new_polarity_3D.extend(NwRdr.csv_tuple_2D(new_polarity))
            comp_model.comp_polarity_3D = NwRdr.csv_element(new_polarity_3D)
            current_pos = NwRdr.csv_tuple(comp_model.comp_pos_3D)
            for c1 in range(len(branch_map)):
                for c2 in range(c1+1, len(branch_map[c1])):
                    for c3 in range(len(branch_map[c1][c2])):
                        if current_pos in branch_map[c1][c2][c3]:
                            if new_polarity_3D not in branch_map[c1][c2][c3]:
                                received_form.add_error("comp_polarity", \
                                    "Polarity has to be an element on same branch as ammeter.")
                                form_status = [received_form, ]
                            elif current_pos==new_polarity_3D:
                                received_form.add_error("comp_polarity", \
                                    "Polarity can't be the same element as the component.")
                                form_status = [received_form, ]
                            else:
                                comp_model.comp_polarity_3D = NwRdr.csv_element(new_polarity_3D)
                                comp_model.save()
                                form_status = []
        return form_status

    def pre_run_check(self, ckt_file_item, branch_map):
        """
        This function checks for errors primarily in polarity.
        """
        comp_errors = []
        try:
            check_ammeter = ckt_file_item.ammeter_set.all().\
                        filter(comp_tag=self.tag)
        except:
            pass
        else:
            if check_ammeter and len(check_ammeter)==1:
                comp_item = check_ammeter[0]
                current_pos = NwRdr.csv_tuple(comp_item.comp_pos_3D)
                current_polarity = NwRdr.csv_tuple(comp_item.comp_polarity_3D)
                for c1 in range(len(branch_map)):
                    for c2 in range(c1+1, len(branch_map[c1])):
                        for c3 in range(len(branch_map[c1][c2])):
                            if current_pos in branch_map[c1][c2][c3]:
                                if current_polarity not in branch_map[c1][c2][c3]:
                                    comp_errors.append("Polarity has to be an element on \
                                        same branch as ammeter. Check Ammeter_" + self.tag)
                                elif current_pos==current_polarity:
                                    comp_errors.append("Polarity can't be the same element \
                                        as the component. Check Ammeter_" + self.tag)
        return comp_errors

    def assign_parameters(self, ckt_file_list):
        """
        Transfers data from the database to the component clas
        objects for the simulation.
        """
        for ckt_file_item in ckt_file_list:
            try:
                check_ammeter = ckt_file_item.ammeter_set.all().\
                        filter(comp_tag=self.tag)
            except:
                pass
            else:
                if check_ammeter and len(check_ammeter)==1:
                    comp_model = check_ammeter[0]
                    self.polrty = NwRdr.csv_tuple_2D(comp_model.comp_polarity)
                    self.polrty_3D = NwRdr.csv_tuple(comp_model.comp_polarity_3D)
        return


class Voltmeter:
    """
    Voltmeter class. Contains functions to initiliaze
    the resistor according to name tag, unique cell position,
    update system matrix on each iteration.
    """

    def __init__(self, vm_index, vm_pos, vm_tag, nw_input):
        """
        Constructor to initialize value.
        Also, takes in the identifiers -
        index (serial number), cell position and tag.
        """
        self.type = "Voltmeter"
        self.number = vm_index
        self.pos_3D = vm_pos
        self.sheet = NwRdr.csv_tuple(vm_pos)[0]
        self.pos = NwRdr.csv_element_2D(NwRdr.csv_tuple(vm_pos)[1:])
        self.tag = vm_tag
        self.sheet_name = nw_input[self.sheet] + ".csv"
        self.has_voltage = "no"
        self.is_meter = "yes"
        self.has_control = "no"
        self.vm_level = 120.0
        self.current = 0.0
        self.voltage = 0.0
        self.op_value = 0.0
        self.polrty = [-1, -1]
        self.polrty_3D = [-1, -1, -1]
        self.component_branch_pos = 0
        self.component_branch_dir = 1.0

        return

    def display(self):
        """
        Displays info about the component.
        """
        print("Voltmeter is {} located at {} with positive polarity towards {} in sheet".format(
            self.tag, self.pos, NwRdr.csv_element_2D(self.polrty), self.sheet_name
        ))

        return

    def get_polarity(self, ckt_mat, sys_branch):
        if self.polrty==[-1, -1]:
            # Looking for a default value of polarity
            # in the neighbouring cells

            if self.vm_elem[0]>0:
                if ckt_mat[self.sheet][self.vm_elem[0]-1][self.vm_elem[1]]:
                    self.polrty = [self.vm_elem[0]-1, self.vm_elem[1]]
            if self.vm_elem[1]>0:
                if ckt_mat[self.sheet][self.vm_elem[0]][self.vm_elem[1]-1]:
                    self.polrty = [self.vm_elem[0], self.vm_elem[1]-1]
            if self.vm_elem[0]<len(ckt_mat[self.sheet])-1:
                if ckt_mat[self.sheet][self.vm_elem[0]+1][self.vm_elem[1]]:
                    self.polrty = [self.vm_elem[0]+1, self.vm_elem[1]]
            if self.vm_elem[1]<len(ckt_mat[self.sheet][0])-1:
                if ckt_mat[self.sheet][self.vm_elem[0]][self.vm_elem[1]+1]:
                    self.polrty = [self.vm_elem[0], self.vm_elem[1]+1]
        else:
            for c1 in range(len(sys_branch)):
                if [self.sheet, self.vm_elem[0], self.vm_elem[1]] in sys_branch[c1]:
                    if not [self.sheet, self.polrty[0], self.polrty[1]] in sys_branch[c1]:
                        print()
                        print("!"*50)
                        print("ERROR!!! Voltmeter polarity should be in the same branch as voltmeter. \
Check voltmeter at {} in sheet {}".format(self.pos, self.sheet_name))
                        print( "!"*50)
                        print()
                        raise CktEx.PolarityError

        self.polrty_3D = [self.sheet, self.polrty[0], self.polrty[1]]

        return

    def ask_values(self, x_list, ckt_mat, sys_branch):
        """
        Writes the values needed to the spreadsheet.
        """
        vm_params = ["Voltmeter"]
        vm_params.append(self.tag)
        vm_params.append(self.pos)
        vm_params.append("Rated voltage level to be measured = %s" %self.vm_level)

        self.vm_elem = NwRdr.csv_tuple_2D(self.pos)
        self.get_polarity(ckt_mat, sys_branch)

        vm_params.append("Positive polarity towards (cell) = %s" %NwRdr.csv_element_2D(self.polrty))
        x_list.append(vm_params)

        return

    def export_values_to_csv(self):
        """
        Writes the values needed to the spreadsheet.
        """
        vm_params = ["Voltmeter"]
        vm_params.append(self.tag)
        vm_params.append(self.pos)
        vm_params.append("Rated voltage level to be measured = %s" %self.vm_level)
        vm_params.append("Positive polarity towards (cell) = %s" %NwRdr.csv_element_2D(self.polrty))

        return vm_params

    def get_values(self, x_list, ckt_mat):
        """
        Takes the parameter from the spreadsheet.
        """
        self.vm_level = float(x_list[0].split("=")[1])
        # Choosing 1 micro Amp as the leakage current that
        # is drawn by the voltmeter.
        self.resistor = self.vm_level/1.0e-6
        vm_polrty = x_list[1].split("=")[1]

        # Convert the human readable form of cell
        # to [row, column] form
        while vm_polrty[0]==" ":
            vm_polrty = vm_polrty[1:]

        self.polrty = NwRdr.csv_tuple_2D(vm_polrty)
        self.polrty_3D = [self.sheet, self.polrty[0], self.polrty[1]]

        if not ckt_mat[self.sheet][self.polrty[0]][self.polrty[1]]:
            print("Polarity incorrect or changed. Branch does not exist at {} in sheet {}".format(
                NwRdr.csv_element(self.polrty), self.sheet_name)
            )
            raise CktEx.PolarityError

        return

    def determine_branch(self, sys_branches):
        """
        Determines which branch the component is found in.
        """
        for c1 in range(len(sys_branches)):
            if NwRdr.csv_tuple(self.pos_3D) in sys_branches[c1]:
                self.component_branch_pos = c1
                if sys_branches[c1].index(self.polrty_3D)<sys_branches[c1].index(NwRdr.csv_tuple(self.pos_3D)):
                    self.component_branch_dir = 1.0
                else:
                    self.component_branch_dir = -1.0

        return

    def transfer_to_sys(self, sys_loops, mat_e, mat_a, mat_b, mat_u, source_list):
        """
        The matrix A in E.dx/dt=Ax+Bu will be updated by the
        resistor value.
        """
        for c1 in range(len(sys_loops)):
            for c2 in range(c1, len(sys_loops)):
                # Updating the elements depending
                # on the sense of the loops (aiding or opposing)
                for c3 in range(len(sys_loops[c1][c2])):
                    # Check if voltmeter position is there in the loop.
                    if NwRdr.csv_tuple(self.pos) in sys_loops[c1][c2][c3]:
                        # Add voltmeter resistor if branch is in forward direction
                        if sys_loops[c1][c2][c3][-1]=="forward":
                            mat_a.data[c1][c2] += self.resistor
                        else:
                            # Else subtract if branch is in reverse direction
                            mat_a.data[c1][c2] -= self.resistor
                        # Because the matrices are symmetric
                        mat_a.data[c2][c1] = mat_a.data[c1][c2]

        return

    def transfer_to_branch(self, sys_branch, source_list,  mat_u):
        """
        Update the resistor info of the voltmeter
        to the branch list.
        """
        if NwRdr.csv_tuple(self.pos_3D) in sys_branch:
            sys_branch[-1][0][0] += self.resistor

        return

    def generate_val(self, source_lst, mat_e, mat_a, mat_b, mat_u, t, dt):
        pass

    def update_val_old(self, sys_loop_map, lbyr_ratio, mat_e, mat_a, mat_b, state_vec, mat_u, sys_branches, sys_events):
        """
        The voltmeter current is calculated as a result of the KVL.
        """
        for c1 in range(len(sys_branches)):
            if NwRdr.csv_tuple(self.pos) in sys_branches[c1]:
                branch_pos = c1

        if sys_branches[branch_pos].index(self.polrty)<sys_branches[branch_pos].index(NwRdr.csv_tuple(self.pos)):
            self.current = sys_branches[branch_pos][-1][2]
        else:
            self.current = -sys_branches[branch_pos][-1][2]

        # Since it is a meter, this is its output value
        self.voltage = self.resistor*self.current
        self.op_value = self.voltage

        return

    def update_val(self, sys_loop_map, lbyr_ratio, mat_e, mat_a, mat_b, state_vec, mat_u, sys_branches, sys_events):
        """
        The voltmeter current is calculated as a result of the KVL.
        """
        self.current = self.component_branch_dir*sys_branches[self.component_branch_pos][-1][2]

        # Since it is a meter, this is its output value
        self.voltage = self.resistor*self.current
        self.op_value = self.voltage

        return

    def pre_determine_state(self, br_currents, sys_branches, sys_events):
        pass

    def determine_state(self, br_currents, sys_branches, sys_events):
        pass

    def retrieve_db_model(self, sim_para_model):
        """
        This function returns the model instance object.
        """
        check_ckt = sim_para_model.circuitschematics_set.\
                    filter(ckt_file_name=self.sheet_name)
        try:
            check_voltmeter = check_ckt[0].voltmeter_set.\
                    filter(comp_tag=self.tag)
        except:
            return None
        else:
            if check_voltmeter and len(check_voltmeter)==1:
                return check_voltmeter[0]

    def determine_polarity(self, branch_map, voltmeter_obj):
        """
        This function determines polarity of a new database object.
        """
        for c1 in range(len(branch_map)):
            for c2 in range(c1+1, len(branch_map)):
                for c3 in range(len(branch_map[c1][c2])):
                    if NwRdr.csv_tuple(self.pos_3D) in branch_map[c1][c2][c3]:
                        pos_in_branch = branch_map[c1][c2][c3].\
                                index(NwRdr.csv_tuple(self.pos_3D))
                        prev_element = branch_map[c1][c2][c3][pos_in_branch-1]
                        voltmeter_obj.comp_polarity_3D = NwRdr.csv_element(prev_element)
                        voltmeter_obj.comp_polarity = \
                                NwRdr.csv_element_2D(prev_element[1:])
        return

    def init_db_values(self, sim_para_model, ckt_file_list, branch_map):
        """
        This function creates a new database entry for a component or
        updates an existing database entry from the component class data.
        """
        comp_found = False
        check_ckt = sim_para_model.circuitschematics_set.\
                    filter(ckt_file_name=self.sheet_name)
        try:
            check_voltmeter = check_ckt[0].voltmeter_set.\
                    filter(comp_tag=self.tag)
        except:
            comp_found = False
        else:
            if check_voltmeter and len(check_voltmeter)==1:
                comp_found = True
                old_voltmeter = check_voltmeter[0]
                if not (self.polrty==[-1, -1]):
                    old_voltmeter.comp_polarity = NwRdr.csv_element_2D(self.polrty)
                if not (self.polrty_3D==[-1, -1, -1]):
                    old_voltmeter.comp_polarity_3D = NwRdr.csv_element(self.polrty_3D)
                if old_voltmeter.comp_polarity_3D:
                    voltmeter_old_polarity = NwRdr.csv_tuple(old_voltmeter.comp_polarity_3D)
                    voltmeter_new_polarity = NwRdr.csv_tuple(self.pos_3D)
                    voltmeter_old_polarity[0] = voltmeter_new_polarity[0]
                    old_voltmeter.comp_polarity_3D = NwRdr.csv_element(voltmeter_old_polarity)
                else:
                    self.determine_polarity(branch_map, old_voltmeter)
                old_voltmeter.comp_number = self.number
                old_voltmeter.comp_pos_3D = self.pos_3D
                old_voltmeter.comp_pos = self.pos
                old_voltmeter.comp_sheet = self.sheet
                old_voltmeter.save()
                check_ckt[0].save()
            if check_voltmeter and len(check_voltmeter)>1:
                comp_found = True
                for c1 in range(len(check_voltmeter)-1, 0, -1):
                    check_voltmeter[c1].delete()
                    check_ckt[0].save()

        if not comp_found:
            new_voltmeter = models.Voltmeter()
            if not (self.polrty==[-1, -1]):
                new_voltmeter.comp_polarity = NwRdr.csv_element_2D(self.polrty)
            if not (self.polrty_3D==[-1, -1, -1]):
                new_voltmeter.comp_polarity_3D = NwRdr.csv_element(self.polrty_3D)
            new_voltmeter.comp_number = self.number
            new_voltmeter.comp_pos_3D = self.pos_3D
            new_voltmeter.comp_pos = self.pos
            new_voltmeter.comp_sheet = self.sheet
            new_voltmeter.sheet_name = self.sheet_name.split(".csv")[0]
            new_voltmeter.comp_tag = self.tag
            new_voltmeter.comp_volt_level = self.vm_level
            self.determine_polarity(branch_map, new_voltmeter)
            ckt_file_item = ckt_file_list.filter(ckt_file_name=self.sheet_name)
            new_voltmeter.comp_ckt = ckt_file_item[0]
            new_voltmeter.save()
        sim_para_model.save()

        return

    def create_form_values(self, sim_para_model, ckt_file_list, branch_map):
        """
        This function creates a new database entry for a component or
        updates an existing database entry from the component class data.
        """
        comp_found = False
        check_ckt = sim_para_model.circuitschematics_set.\
                    filter(ckt_file_name=self.sheet_name)
        try:
            check_voltmeter = check_ckt[0].voltmeter_set.\
                    filter(comp_tag=self.tag)
        except:
            comp_found = False
        else:
            if check_voltmeter and len(check_voltmeter)==1:
                comp_found = True
                old_voltmeter = check_voltmeter[0]
                old_voltmeter.comp_volt_level = self.vm_level
                if not (self.polrty==[-1, -1]):
                    old_voltmeter.comp_polarity = NwRdr.csv_element_2D(self.polrty)
                if not (self.polrty_3D==[-1, -1, -1]):
                    old_voltmeter.comp_polarity_3D = NwRdr.csv_element(self.polrty_3D)
                old_voltmeter.comp_number = self.number
                old_voltmeter.comp_pos_3D = self.pos_3D
                old_voltmeter.comp_pos = self.pos
                old_voltmeter.comp_sheet = self.sheet
                old_voltmeter.save()
                check_ckt[0].save()
            if check_voltmeter and len(check_voltmeter)>1:
                comp_found = True
                for c1 in range(len(check_voltmeter)-1, 0, -1):
                    check_voltmeter[c1].delete()
                    check_ckt[0].save()

        if not comp_found:
            new_voltmeter = models.Voltmeter()
            if not (self.polrty==[-1, -1]):
                new_voltmeter.comp_polarity = NwRdr.csv_element_2D(self.polrty)
            if not (self.polrty_3D==[-1, -1, -1]):
                new_voltmeter.comp_polarity_3D = NwRdr.csv_element(self.polrty_3D)
            new_voltmeter.comp_number = self.number
            new_voltmeter.comp_pos_3D = self.pos_3D
            new_voltmeter.comp_pos = self.pos
            new_voltmeter.comp_sheet = self.sheet
            new_voltmeter.sheet_name = self.sheet_name.split(".csv")[0]
            new_voltmeter.comp_tag = self.tag
            new_voltmeter.comp_volt_level = self.vm_level
            self.determine_polarity(branch_map, new_voltmeter)
            ckt_file_item = ckt_file_list.filter(ckt_file_name=self.sheet_name)
            new_voltmeter.comp_ckt = ckt_file_item[0]
            new_voltmeter.save()
        sim_para_model.save()

        return

    def list_existing_components(self, ckt_file):
        """
        Check if the model of the circuit file contains
        the associated database entry for the component.
        Returns an empty list if not found.
        """
        try:
            check_voltmeter = ckt_file.voltmeter_set.all().\
                        filter(comp_tag=self.tag)
        except:
            comp_list = []
        else:
            if check_voltmeter and len(check_voltmeter)==1:
                comp_list = check_voltmeter[0]
            else:
                comp_list = []
        return comp_list

    def comp_as_a_dict(self, ckt_file):
        """
        Returns information about a component as a list
        that can be displayed in a webpage.
        """
        try:
            check_voltmeter = ckt_file.voltmeter_set.all().\
                        filter(comp_tag=self.tag)
        except:
            comp_list = []
        else:
            if check_voltmeter and len(check_voltmeter)==1:
                comp_list = []
                comp_list.append(["Component type", check_voltmeter[0].comp_type])
                comp_list.append(["Component name", check_voltmeter[0].comp_tag])
                comp_list.append(["Component position", check_voltmeter[0].comp_pos])
                comp_list.append(["Voltage level", check_voltmeter[0].comp_volt_level])
                comp_list.append(["Positive direction of voltage", \
                        check_voltmeter[0].comp_polarity])
            else:
                comp_list = []
        return comp_list

    def comp_as_a_form(self, ckt_file):
        """
        Returns a populated form for a component.
        """
        try:
            check_voltmeter = ckt_file.voltmeter_set.all().\
                        filter(comp_tag=self.tag)
        except:
            return []
        else:
            if check_voltmeter and len(check_voltmeter)==1:
                return [models.VoltmeterForm, check_voltmeter[0]]
                # comp_list = models.VoltmeterForm(instance=check_voltmeter[0])
            else:
                return []
        # return comp_list

    def save_to_db(self, ckt_file):
        """
        Returns a populated form for a component.
        """
        try:
            check_voltmeter = ckt_file.voltmeter_set.all().\
                        filter(comp_tag=self.tag)
        except:
            return
        else:
            if check_voltmeter and len(check_voltmeter)==1:
                old_voltmeter = check_voltmeter[0]
                old_voltmeter.comp_volt_level = self.vm_level
                if not (self.polrty==[-1, -1]):
                    old_voltmeter.comp_polarity = NwRdr.csv_element_2D(self.polrty)
                if not (self.polrty_3D==[-1, -1, -1]):
                    old_voltmeter.comp_polarity_3D = NwRdr.csv_element(self.polrty_3D)
                old_voltmeter.save()
                ckt_file.save()
                return
            else:
                return

    def update_form_data(self, request, comp_model, branch_map):
        """
        Extracts data from a form and saves it to the database.
        """
        received_form = models.VoltmeterForm(request.POST)
        if received_form.is_valid():
            received_data = received_form.cleaned_data
            comp_model.comp_volt_level = received_data["comp_volt_level"]
            new_polarity = received_data["comp_polarity"]
            comp_model.comp_polarity = new_polarity
            new_polarity_3D = [comp_model.comp_sheet, ]
            new_polarity_3D.extend(NwRdr.csv_tuple_2D(new_polarity))
            comp_model.comp_polarity_3D = NwRdr.csv_element(new_polarity_3D)
            current_pos = NwRdr.csv_tuple(comp_model.comp_pos_3D)
            for c1 in range(len(branch_map)):
                for c2 in range(c1+1, len(branch_map[c1])):
                    for c3 in range(len(branch_map[c1][c2])):
                        if current_pos in branch_map[c1][c2][c3]:
                            if new_polarity_3D not in branch_map[c1][c2][c3]:
                                received_form.add_error("comp_polarity", \
                                    "Polarity has to be an element on same branch as voltmeter.")
                                form_status = [received_form, ]
                            elif current_pos==new_polarity_3D:
                                received_form.add_error("comp_polarity", \
                                    "Polarity can't be the same element as the component.")
                                form_status = [received_form, ]
                            else:
                                comp_model.comp_polarity_3D = NwRdr.csv_element(new_polarity_3D)
                                comp_model.save()
                                form_status = []
        else:
            form_status = [received_form, ]
        return form_status

    def pre_run_check(self, ckt_file_item, branch_map):
        """
        This function checks for errors primarily in polarity.
        """
        comp_errors = []
        try:
            check_voltmeter = ckt_file_item.voltmeter_set.all().\
                        filter(comp_tag=self.tag)
        except:
            pass
        else:
            if check_voltmeter and len(check_voltmeter)==1:
                comp_item = check_voltmeter[0]
                current_pos = NwRdr.csv_tuple(comp_item.comp_pos_3D)
                current_polarity = NwRdr.csv_tuple(comp_item.comp_polarity_3D)
                for c1 in range(len(branch_map)):
                    for c2 in range(c1+1, len(branch_map[c1])):
                        for c3 in range(len(branch_map[c1][c2])):
                            if current_pos in branch_map[c1][c2][c3]:
                                if current_polarity not in branch_map[c1][c2][c3]:
                                    comp_errors.append("Polarity has to be an element on \
                                        same branch as voltmeter. Check Voltmeter_" + self.tag)
                                elif current_pos==current_polarity:
                                    comp_errors.append("Polarity can't be the same element \
                                        as the component. Check Voltmeter_" + self.tag)
        return comp_errors

    def assign_parameters(self, ckt_file_list):
        """
        Transfers data from the database to the component clas
        objects for the simulation.
        """
        for ckt_file_item in ckt_file_list:
            try:
                check_voltmeter = ckt_file_item.voltmeter_set.all().\
                        filter(comp_tag=self.tag)
            except:
                pass
            else:
                if check_voltmeter and len(check_voltmeter)==1:
                    comp_model = check_voltmeter[0]
                    self.polrty = NwRdr.csv_tuple_2D(comp_model.comp_polarity)
                    self.polrty_3D = NwRdr.csv_tuple(comp_model.comp_polarity_3D)
                    self.vm_level = comp_model.comp_volt_level
                    self.resistor = self.vm_level/1.0e-6
        return


class Current_Source:
    """
    Current source class. Contains functions to initiliaze
    the resistor according to name tag, unique cell position,
    update system matrix on each iteration.
    """

    def __init__(self, cs_index, cs_pos, cs_tag, nw_input):
        """
        Constructor to initialize value.
        Also, takes in the identifiers -
        index (serial number), cell position and tag.
        """
        self.type = "CurrentSource"
        self.number = cs_index
        self.pos_3D = cs_pos
        self.sheet = NwRdr.csv_tuple(cs_pos)[0]
        self.pos = NwRdr.csv_element_2D(NwRdr.csv_tuple(cs_pos)[1:])
        self.tag = cs_tag
        self.sheet_name = nw_input[self.sheet] + ".csv"
        self.has_voltage = "yes"
        self.is_meter = "no"
        self.has_control = "no"
        self.cs_peak = 5.0
        self.cs_freq = 60.0
        self.cs_phase = 0.0
        self.cs_level = 120.0
        self.resistor = 1.0
        self.current = 0.0
        self.voltage = 0.0
        self.op_value = 0.0
        self.polrty=[-1, -1]
        self.polrty_3D = [-1, -1, -1]
        self.component_banch_pos = 0
        self.component_branch_dir = 1.0

        return

    def display(self):
        """
        Displays info about the component.
        """
        print("Current Source is {} of {} A (peak), {} Hz(frequency) and {} (degrees phase shift) \
located at {} with positive polarity towards {} in sheet {}".format(
            self.tag, self.cs_peak, self.cs_freq, self.cs_phase, self.pos, \
            NwRdr.csv_element(self.polrty), self.sheet_name
        ))

        return

    def get_polarity(self, ckt_mat, sys_branch):
        if self.polrty==[-1, -1]:
            # Looking for a default value of polarity
            # in the neighbouring cells

            if self.cs_elem[0]>0:
                if ckt_mat[self.sheet][self.cs_elem[0]-1][self.cs_elem[1]]:
                    self.polrty = [self.cs_elem[0]-1, self.cs_elem[1]]
            if self.cs_elem[1]>0:
                if ckt_mat[self.sheet][self.cs_elem[0]][self.cs_elem[1]-1]:
                    self.polrty = [self.cs_elem[0], self.cs_elem[1]-1]
            if self.cs_elem[0]<len(ckt_mat[self.sheet])-1:
                if ckt_mat[self.sheet][self.cs_elem[0]+1][self.cs_elem[1]]:
                    self.polrty = [self.cs_elem[0]+1, self.cs_elem[1]]
            if self.cs_elem[1]<len(ckt_mat[self.sheet][0])-1:
                if ckt_mat[self.sheet][self.cs_elem[0]][self.cs_elem[1]+1]:
                    self.polrty = [self.cs_elem[0], self.cs_elem[1]+1]
        else:
            for c1 in range(len(sys_branch)):
                if NwRdr.csv_tuple(self.pos_3D) in sys_branch[c1]:
                    if not self.polrty in sys_branch[c1]:
                        print()
                        print("!"*50)
                        print("ERROR!!! Current source polarity should be in the same branch as the current source. \
Check source at {} in sheet {}".format(self.pos, self.sheet_name))
                        print("!"*50)
                        print()
                        raise CktEx.PolarityError

        self.polrty_3D = [self.sheet, self.polrty[0], self.polrty[1]]

        return

    def ask_values(self, x_list, ckt_mat, sys_branch):
        """
        Writes the values needed to the spreadsheet.
        """
        cs_params = ["CurrentSource"]
        cs_params.append(self.tag)
        cs_params.append(self.pos)
        cs_params.append("Peak (Amps) = %f" %self.cs_peak)
        cs_params.append("Frequency (Hertz) = %f" %self.cs_freq)
        cs_params.append("Phase (degrees) = %f" %self.cs_phase)

        self.cs_elem = NwRdr.csv_tuple_2D(self.pos)
        self.get_polarity(ckt_mat, sys_branch)

        cs_params.append("Positive polarity towards (cell) = %s" %NwRdr.csv_element_2D(self.polrty))
        x_list.append(cs_params)

        return

    def export_values_to_csv(self):
        """
        Writes the values needed to the spreadsheet.
        """
        cs_params = ["CurrentSource"]
        cs_params.append(self.tag)
        cs_params.append(self.pos)
        cs_params.append("Peak (Amps) = %f" %self.cs_peak)
        cs_params.append("Frequency (Hertz) = %f" %self.cs_freq)
        cs_params.append("Phase (degrees) = %f" %self.cs_phase)
        cs_params.append("Positive polarity towards (cell) = %s" %NwRdr.csv_element_2D(self.polrty))

        return cs_params

    def get_values(self, x_list, ckt_mat):
        """ Takes the parameter from the spreadsheet."""
        self.cs_peak = float(x_list[0].split("=")[1])
        self.cs_freq = float(x_list[1].split("=")[1])
        self.cs_phase = float(x_list[2].split("=")[1])
        curr_polrty = x_list[3].split("=")[1]

        # Convert the human readable form of cell
        # to [row, column] form
        while curr_polrty[0]==" ":
            curr_polrty = curr_polrty[1:]

        self.polrty = NwRdr.csv_tuple_2D(curr_polrty)
        self.polrty_3D = [self.sheet, self.polrty[0], self.polrty[1]]

        if not ckt_mat[self.sheet][self.polrty[0]][self.polrty[1]]:
            print("Polarity incorrect. Branch does not exist at {} in sheet {}".format(
                NwRdr.csv_element_2D(self.polrty), self.sheet_name)
            )
            raise CktEx.PolarityError

        return

    def determine_branch(self, sys_branches):
        """
        Determines which branch the component is found in.
        """
        for c1 in range(len(sys_branches)):
            if NwRdr.csv_tuple(self.pos_3D) in sys_branches[c1]:
                self.component_branch_pos = c1
                if sys_branches[c1].index(self.polrty_3D)<sys_branches[c1].index(NwRdr.csv_tuple(self.pos_3D)):
                    self.component_branch_dir = 1.0
                else:
                    self.component_branch_dir = -1.0
        return

    def transfer_to_sys(self, sys_loops, mat_e, mat_a, mat_b, mat_u, source_list):
        """
        The matrix A in E.dx/dt=Ax+Bu will be updated by the
        resistor value of the current source.
        """
        for c1 in range(len(sys_loops)):
            for c2 in range(c1, len(sys_loops)):
                # Updating the elements depending
                # on the sense of the loops (aiding or opposing)
                for c3 in range(len(sys_loops[c1][c2])):
                    # Check if current source position is there in the loop.
                    if NwRdr.csv_tuple(self.pos) in sys_loops[c1][c2][c3]:
                        # Add current source series resistor
                        # if branch is in forward direction
                        if sys_loops[c1][c2][c3][-1]=="forward":
                            mat_a.data[c1][c2] += self.resistor
                        else:
                            # Else subtract if branch is in reverse direction
                            mat_a.data[c1][c2] -= self.resistor
                        # Because the matrices are symmetric
                        mat_a.data[c2][c1] = mat_a.data[c1][c2]

                        # If the positive polarity appears before the voltage position
                        # it means as per KVL, we are moving from +ve to -ve
                        # and so the voltage will be taken negative
                        if sys_loops[c1][c1][c2].index(self.polrty)<sys_loops[c1][c1][c2].index(NwRdr.csv_tuple(self.pos)):
                            if sys_loops[c1][c1][c2][-1]=="forward":
                                mat_b.data[c1][source_list.index(self.pos)] = -1.0
                            else:
                                mat_b.data[c1][source_list.index(self.pos)] = 1.0
                        else:
                            if sys_loops[c1][c1][c2][-1]=="forward":
                                mat_b.data[c1][source_list.index(self.pos)] = 1.0
                            else:
                                mat_b.data[c1][source_list.index(self.pos)] = -1.0
        return

    def transfer_to_branch(self, sys_branch, source_list, mat_u):
        """
        Update the resistor info of the current source
        to the branch list
        """
        if NwRdr.csv_tuple(self.pos_3D) in sys_branch:
            sys_branch[-1][0][0] += self.resistor

        if NwRdr.csv_tuple(self.pos_3D) in sys_branch:
            if sys_branch.index(self.polrty_3D)<sys_branch.index(NwRdr.csv_tuple(self.pos_3D)):
                sys_branch[-1][1][source_list.index(self.pos_3D)] = -1.0
            else:
                sys_branch[-1][1][source_list.index(self.pos_3D)] = 1.0

        return

    def generate_val(self, source_lst, mat_e, mat_a, mat_b, mat_u, t, dt):
        """
        The source current is updated in the matrix u in
        E.dx/dt=Ax+Bu. The matrix E has a row set to zero. The
        matrix B has the diagonal element in the row set to 1,
        others set to zero.
        """
        # Updating the current source value
        self.current = self.cs_peak*math.sin(2*math.pi*self.cs_freq*t+self.cs_phase)

        # The value passed to the input matrix is
        # the voltage calculated
        mat_u.data[source_lst.index(self.pos_3D)][0] = self.voltage

        # The output value of the source will the current
        # even though it is actually modelled as a
        # voltage source with a series resistance.
        self.op_value = self.current

        return

    def update_val_old(self, sys_loop_map, lbyr_ratio, mat_e, mat_a, mat_b, state_vec, mat_u, sys_branches, sys_events):
        """
        This function calculates the actual current in
        the current source branch. With this, the branch voltage is
        found with respect to the existing voltage source. The branch
        voltage is then used to calculate the new voltage source value.
        """
        # Local variable to calculate the branch
        # current from all loops that contain
        # the current source branch.
        act_current = 0.0

        for c1 in range(len(sys_branches)):
            if NwRdr.csv_tuple(self.pos) in sys_branches[c1]:
                branch_pos = c1

        if sys_branches[branch_pos].index(self.polrty)<sys_branches[branch_pos].index(NwRdr.csv_tuple(self.pos)):
            act_current = sys_branches[branch_pos][-1][2]
        else:
            act_current = -sys_branches[branch_pos][-1][2]

        # The branch voltage is the KVL with the
        # existing voltage source and the branch current
        branch_voltage = self.voltage+act_current*self.resistor
        # The new source voltage will be the branch voltage
        # in addition to the desired value of current.
        self.voltage = branch_voltage+self.current*self.resistor

        return

    def update_val(self, sys_loop_map, lbyr_ratio, mat_e, mat_a, mat_b, state_vec, mat_u, sys_branches, sys_events):
        """
        This function calculates the actual current in
        the current source branch. With this, the branch voltage is
        found with respect to the existing voltage source. The branch
        voltage is then used to calculate the new voltage source value.
        """
        # Local variable to calculate the branch
        # current from all loops that contain
        # the current source branch.
        act_current = 0.0
        act_current = self.component_branch_dir*sys_branches[self.component_branch_pos][-1][2]

        # The branch voltage is the KVL with the
        # existing voltage source and the branch current
        branch_voltage = self.voltage+act_current*self.resistor
        # The new source voltage will be the branch voltage
        # in addition to the desired value of current.
        self.voltage = branch_voltage+self.current*self.resistor

        return

    def pre_determine_state(self, br_currents, sys_branches, sys_events):
        pass

    def determine_state(self, br_currents, sys_branches, sys_events):
        pass

    def create_form_values(self, sim_id, branch_map):
        pass


class Controlled_Voltage_Source:
    """
    Controlled Voltage Source class. Takes the instantaneous
    voltage as input from the user file.self.get_polarity(ckt_mat, sys_branch)
    """

    def __init__(self, volt_index, volt_pos, volt_tag, nw_input):
        """
        Constructor to initialize value.
        Also, takes in the identifiers -
        index (serial number), cell position and tag.
        """
        self.type = "ControlledVoltageSource"
        self.number = volt_index
        self.pos_3D = volt_pos
        self.sheet = NwRdr.csv_tuple(volt_pos)[0]
        self.pos = NwRdr.csv_element_2D(NwRdr.csv_tuple(volt_pos)[1:])
        self.tag = volt_tag
        self.sheet_name = nw_input[self.sheet] + ".csv"
        self.has_voltage = "yes"
        self.is_meter = "no"
        self.has_control = "yes"
        self.voltage = 0.0
        self.current = 0.0
        self.op_value = 0.0
        self.polrty = [-1, -1]
        self.polrty_3D = [-1, -1, -1]
        self.control_tag = ["Control"]
        self.control_values = [0.0]

        return

    def display(self):
        """
        Displays info about the component.
        """
        print("Controlled Voltage Source is {} located at {} with positive polarity towards {} in sheet {}".format(
            self.tag, self.pos, NwRdr.csv_element_2D(self.polrty), self.sheet_name
        ))

        return

    def get_polarity(self, ckt_mat, sys_branch):
        if self.polrty==[-1, -1]:
            # Looking for a default value of polarity
            # in the neighbouring cells

            if self.volt_elem[0]>0:
                if ckt_mat[self.sheet][self.volt_elem[0]-1][self.volt_elem[1]]:
                    self.polrty = [self.volt_elem[0]-1, self.volt_elem[1]]
            if self.volt_elem[1]>0:
                if ckt_mat[self.sheet][self.volt_elem[0]][self.volt_elem[1]-1]:
                    self.polrty = [self.volt_elem[0], self.volt_elem[1]-1]
            if self.volt_elem[0]<len(ckt_mat[self.sheet])-1:
                if ckt_mat[self.sheet][self.volt_elem[0]+1][self.volt_elem[1]]:
                    self.polrty = [self.volt_elem[0]+1, self.volt_elem[1]]
            if self.volt_elem[1]<len(ckt_mat[self.sheet][0])-1:
                if ckt_mat[self.sheet][self.volt_elem[0]][self.volt_elem[1]+1]:
                    self.polrty = [self.volt_elem[0], self.volt_elem[1]+1]

        else:

            for c1 in range(len(sys_branch)):
                if NwRdr.csv_tuple(self.pos_3D) in sys_branch[c1]:
                    if not [self.sheet, self.polrty[0], self.polrty[1]]  in sys_branch[c1]:
                        print()
                        print("!"*50)
                        print("ERROR!!! Voltage source polarity should be in the same branch as the voltage source. \
Check source at {} in sheet {}".format(self.pos, self.sheet_name))
                        print("!"*50)
                        print()
                        raise CktEx.PolarityError

        self.polrty_3D = [self.sheet, self.polrty[0], self.polrty[1]]

        return

    def ask_values(self, x_list, ckt_mat, sys_branch):
        """
        Writes the values needed to the spreadsheet.
        """
        volt_params = ["ControlledVoltageSource"]
        volt_params.append(self.tag)
        volt_params.append(self.pos)

        self.volt_elem = NwRdr.csv_tuple_2D(self.pos)
        self.get_polarity(ckt_mat, sys_branch)

        volt_params.append("Positive polarity towards (cell) = %s" %NwRdr.csv_element_2D(self.polrty))
        volt_params.append("Name of control signal = %s" %self.control_tag[0])
        x_list.append(volt_params)

        return

    def export_values_to_csv(self):
        """
        Writes the values needed to the spreadsheet.
        """
        volt_params = ["ControlledVoltageSource"]
        volt_params.append(self.tag)
        volt_params.append(self.pos)
        volt_params.append("Positive polarity towards (cell) = %s" %NwRdr.csv_element_2D(self.polrty))
        volt_params.append("Name of control signal = %s" %self.control_tag[0])

        return volt_params

    def get_values(self, x_list, ckt_mat):
        """ Takes the parameter from the spreadsheet."""
        volt_polrty = x_list[0].split("=")[1]

        # Convert the human readable form of cell
        # to [row, column] form
        while volt_polrty[0]==" ":
            volt_polrty = volt_polrty[1:]

        self.polrty = NwRdr.csv_tuple_2D(volt_polrty)
        self.polrty_3D = [self.sheet, self.polrty[0], self.polrty[1]]

        if not ckt_mat[self.sheet][self.polrty[0]][self.polrty[1]]:
            print("Polarity incorrect. Branch does not exist at {} in sheet {}".format(
                NwRdr.csv_element_2D(self.polrty), self.sheet_name)
            )
            raise CktEx.PolarityError

        self.control_tag[0] = x_list[1].split("=")[1]
        while self.control_tag[0][0]==" ":
            self.control_tag[0] = self.control_tag[0][1:]

        return

    def determine_branch(self, sys_branches):
        pass

    def transfer_to_sys(self, sys_loops, mat_e, mat_a, mat_b, mat_u, source_list):
        """
        The matrix B in E.dx/dt=Ax+Bu will be updated by the
        polarity of the voltage source.
        """
        for c1 in range(len(sys_loops)):
            for c2 in range(len(sys_loops[c1][c1])):
                if NwRdr.csv_tuple(self.pos) in sys_loops[c1][c1][c2]:
                    # If the positive polarity appears before the voltage position
                    # it means as per KVL, we are moving from +ve to -ve
                    # and so the voltage will be taken negative
                    if sys_loops[c1][c1][c2].index(self.polrty)<sys_loops[c1][c1][c2].index(NwRdr.csv_tuple(self.pos)):
                        if sys_loops[c1][c1][c2][-1]=="forward":
                            mat_b.data[c1][source_list.index(self.pos)] = -1.0
                        else:
                            mat_b.data[c1][source_list.index(self.pos)] = 1.0
                    else:
                        if sys_loops[c1][c1][c2][-1]=="forward":
                            mat_b.data[c1][source_list.index(self.pos)] = 1.0
                        else:
                            mat_b.data[c1][source_list.index(self.pos)] = -1.0

        return

    def transfer_to_branch(self, sys_branch, source_list, mat_u):
        """
        Transfers parameters to system branch if voltage
        source exists in the branch.
        """
        if NwRdr.csv_tuple(self.pos_3D) in sys_branch:
            if sys_branch.index(self.polrty_3D)<sys_branch.index(NwRdr.csv_tuple(self.pos_3D)):
                sys_branch[-1][1][source_list.index(self.pos_3D)] = -1.0
            else:
                sys_branch[-1][1][source_list.index(self.pos_3D)] = 1.0

        return

    def generate_val(self, source_lst, mat_e, mat_a, mat_b, mat_u, t, dt):
        """
        The source voltage is updated in the matrix u in
        E.dx/dt=Ax+Bu.
        """
        mat_u.data[source_lst.index(self.pos_3D)][0] = self.control_values[0]
        self.op_value = self.control_values[0]

        return

    def update_val(self, sys_loop_map, lbyr_ratio, mat_e, mat_a, mat_b, state_vec, mat_u, sys_branches, sys_events):
        pass

    def pre_determine_state(self, br_currents, sys_branches, sys_events):
        pass

    def determine_state(self, br_currents, sys_branches, sys_events):
        pass

    def retrieve_db_model(self, sim_para_model):
        """
        This function returns the model instance object.
        """
        check_ckt = sim_para_model.circuitschematics_set.\
                    filter(ckt_file_name=self.sheet_name)
        try:
            check_contvoltsource = check_ckt[0].controlled_voltage_source_set.\
                    filter(comp_tag=self.tag)
        except:
            return None
        else:
            if check_contvoltsource and len(check_contvoltsource)==1:
                return check_contvoltsource[0]

    def determine_polarity(self, branch_map, voltagesource_obj):
        """
        Determines polatity of a new database object.
        """
        for c1 in range(len(branch_map)):
            for c2 in range(c1+1, len(branch_map)):
                for c3 in range(len(branch_map[c1][c2])):
                    if NwRdr.csv_tuple(self.pos_3D) in branch_map[c1][c2][c3]:
                        pos_in_branch = branch_map[c1][c2][c3].\
                                index(NwRdr.csv_tuple(self.pos_3D))
                        prev_element = branch_map[c1][c2][c3][pos_in_branch-1]
                        voltagesource_obj.comp_polarity_3D = NwRdr.csv_element(prev_element)
                        voltagesource_obj.comp_polarity = \
                                NwRdr.csv_element_2D(prev_element[1:])
        return

    def init_db_values(self, sim_para_model, ckt_file_list, branch_map):
        """
        This function creates a new database entry for a component or
        updates an existing database entry from the component class data.
        """
        comp_found = False
        check_ckt = sim_para_model.circuitschematics_set.\
                    filter(ckt_file_name=self.sheet_name)
        try:
            check_contvoltsource = check_ckt[0].controlled_voltage_source_set.\
                    filter(comp_tag=self.tag)
        except:
            comp_found = False
        else:
            if check_contvoltsource and len(check_contvoltsource)==1:
                comp_found = True
                old_contvoltsource = check_contvoltsource[0]
                if not (self.polrty==[-1, -1]):
                    old_contvoltsource.comp_polarity = NwRdr.csv_element_2D(self.polrty)
                if not (self.polrty_3D==[-1, -1, -1]):
                    old_contvoltsource.comp_polarity_3D = NwRdr.csv_element(self.polrty_3D)
                if old_contvoltsource.comp_polarity_3D:
                    contvoltsource_old_polarity = NwRdr.csv_tuple(old_contvoltsource.comp_polarity_3D)
                    contvoltsource_new_polarity = NwRdr.csv_tuple(self.pos_3D)
                    contvoltsource_old_polarity[0] = contvoltsource_new_polarity[0]
                    old_contvoltsource.comp_polarity_3D = NwRdr.csv_element(contvoltsource_old_polarity)
                else:
                    self.determine_polarity(branch_map, old_contvoltsource)
                old_contvoltsource.comp_number = self.number
                old_contvoltsource.comp_pos_3D = self.pos_3D
                old_contvoltsource.comp_pos = self.pos
                old_contvoltsource.comp_sheet = self.sheet
                old_contvoltsource.save()
                check_ckt[0].save()
            if check_contvoltsource and len(check_contvoltsource)>1:
                comp_found = True
                for c1 in range(len(check_contvoltsource)-1, 0, -1):
                    check_contvoltsource[c1].delete()
                    check_ckt[0].save()

        if not comp_found:
            new_contvoltsource = models.Controlled_Voltage_Source()
            if not (self.polrty==[-1, -1]):
                new_contvoltsource.comp_polarity = NwRdr.csv_element_2D(self.polrty)
            if not (self.polrty_3D==[-1, -1, -1]):
                new_contvoltsource.comp_polarity_3D = NwRdr.csv_element(self.polrty_3D)
            new_contvoltsource.comp_number = self.number
            new_contvoltsource.comp_pos_3D = self.pos_3D
            new_contvoltsource.comp_pos = self.pos
            new_contvoltsource.comp_sheet = self.sheet
            new_contvoltsource.sheet_name = self.sheet_name.split(".csv")[0]
            new_contvoltsource.comp_tag = self.tag
            self.determine_polarity(branch_map, new_contvoltsource)
            ckt_file_item = ckt_file_list.filter(ckt_file_name=self.sheet_name)
            new_contvoltsource.comp_ckt = ckt_file_item[0]
            new_contvoltsource.save()
        sim_para_model.save()

        return

    def create_form_values(self, sim_para_model, ckt_file_list, branch_map):
        """
        This function creates a new database entry for a component or
        updates an existing database entry from the component class data.
        """
        comp_found = False
        check_ckt = sim_para_model.circuitschematics_set.\
                    filter(ckt_file_name=self.sheet_name)
        try:
            check_contvoltsource = check_ckt[0].controlled_voltage_source_set.\
                    filter(comp_tag=self.tag)
        except:
            comp_found = False
        else:
            if check_contvoltsource and len(check_contvoltsource)==1:
                comp_found = True
                old_contvoltsource = check_contvoltsource[0]
                if not (self.polrty==[-1, -1]):
                    old_contvoltsource.comp_polarity = NwRdr.csv_element_2D(self.polrty)
                if not (self.polrty_3D==[-1, -1, -1]):
                    old_contvoltsource.comp_polarity_3D = NwRdr.csv_element(self.polrty_3D)
                old_contvoltsource.comp_number = self.number
                old_contvoltsource.comp_pos_3D = self.pos_3D
                old_contvoltsource.comp_pos = self.pos
                old_contvoltsource.comp_sheet = self.sheet
                old_contvoltsource.comp_control_tag = self.control_tag[0]
                old_contvoltsource.save()
                check_ckt[0].save()
            if check_contvoltsource and len(check_contvoltsource)>1:
                comp_found = True
                for c1 in range(len(check_contvoltsource)-1, 0, -1):
                    check_contvoltsource[c1].delete()
                    check_ckt[0].save()

        if not comp_found:
            new_contvoltsource = models.Controlled_Voltage_Source()
            if not (self.polrty==[-1, -1]):
                new_contvoltsource.comp_polarity = NwRdr.csv_element_2D(self.polrty)
            if not (self.polrty_3D==[-1, -1, -1]):
                new_contvoltsource.comp_polarity_3D = NwRdr.csv_element(self.polrty_3D)
            new_contvoltsource.comp_number = self.number
            new_contvoltsource.comp_pos_3D = self.pos_3D
            new_contvoltsource.comp_pos = self.pos
            new_contvoltsource.comp_sheet = self.sheet
            new_contvoltsource.sheet_name = self.sheet_name.split(".csv")[0]
            new_contvoltsource.comp_tag = self.tag
            self.determine_polarity(branch_map, new_contvoltsource)
            ckt_file_item = ckt_file_list.filter(ckt_file_name=self.sheet_name)
            new_contvoltsource.comp_ckt = ckt_file_item[0]
            new_contvoltsource.save()
        sim_para_model.save()

        return

    def list_existing_components(self, ckt_file):
        """
        Check if the model of the circuit file contains
        the associated database entry for the component.
        Returns an empty list if not found.
        """
        try:
            check_voltagesource = ckt_file.controlled_voltage_source_set.all().\
                        filter(comp_tag=self.tag)
        except:
            comp_list = []
        else:
            if check_voltagesource and len(check_voltagesource)==1:
                comp_list = check_voltagesource[0]
            else:
                comp_list = []
        return comp_list

    def comp_as_a_dict(self, ckt_file):
        """
        Returns information about a component as a list
        that can be displayed in a webpage.
        """
        try:
            check_voltagesource = ckt_file.controlled_voltage_source_set.all().\
                        filter(comp_tag=self.tag)
        except:
            comp_list = []
        else:
            if check_voltagesource and len(check_voltagesource)==1:
                comp_list = []
                comp_list.append(["Component type", check_voltagesource[0].comp_type])
                comp_list.append(["Component name", check_voltagesource[0].comp_tag])
                comp_list.append(["Component position", check_voltagesource[0].comp_pos])
                comp_list.append(["Control name", check_voltagesource[0].comp_control_tag])
                comp_list.append(["Positive polarity", check_voltagesource[0].comp_polarity])
                comp_list.append(["Initial voltage", check_voltagesource[0].comp_voltage])
            else:
                comp_list = []
        return comp_list

    def comp_as_a_form(self, ckt_file):
        """
        Returns a populated form for a component.
        """
        try:
            check_voltagesource = ckt_file.controlled_voltage_source_set.all().\
                        filter(comp_tag=self.tag)
        except:
            return []
        else:
            if check_voltagesource and len(check_voltagesource)==1:
                return [models.Controlled_Voltage_SourceForm, check_voltagesource[0]]
                # comp_list = models.Controlled_Voltage_SourceForm(instance=check_voltagesource[0])
            else:
                return []
        # return comp_list

    def save_to_db(self, ckt_file):
        """
        Returns a populated form for a component.
        """
        try:
            check_voltagesource = ckt_file.controlled_voltage_source_set.all().\
                        filter(comp_tag=self.tag)
        except:
            return
        else:
            if check_voltagesource and len(check_voltagesource)==1:
                old_contvoltsource = check_voltagesource[0]
                if not (self.polrty==[-1, -1]):
                    old_contvoltsource.comp_polarity = NwRdr.csv_element_2D(self.polrty)
                if not (self.polrty_3D==[-1, -1, -1]):
                    old_contvoltsource.comp_polarity_3D = NwRdr.csv_element(self.polrty_3D)
                old_contvoltsource.comp_control_tag = self.control_tag[0]
                old_contvoltsource.save()
                ckt_file.save()
                return
            else:
                return

    def update_form_data(self, request, comp_model, branch_map):
        """
        Extracts data from a form and saves it to the database.
        """
        received_form = models.Controlled_Voltage_SourceForm(request.POST)
        if received_form.is_valid():
            received_data = received_form.cleaned_data
            comp_model.comp_control_tag = received_data["comp_control_tag"]
            comp_model.comp_voltage = received_data["comp_voltage"]
            new_polarity = received_data["comp_polarity"]
            comp_model.comp_polarity = new_polarity
            new_polarity_3D = [comp_model.comp_sheet, ]
            new_polarity_3D.extend(NwRdr.csv_tuple_2D(new_polarity))
            current_pos = NwRdr.csv_tuple(comp_model.comp_pos_3D)
            for c1 in range(len(branch_map)):
                for c2 in range(c1+1, len(branch_map[c1])):
                    for c3 in range(len(branch_map[c1][c2])):
                        if current_pos in branch_map[c1][c2][c3]:
                            if new_polarity_3D not in branch_map[c1][c2][c3]:
                                received_form.add_error("comp_polarity", \
                                    "Polarity has to be an element on same branch as voltage source.")
                                form_status = [received_form, ]
                            elif current_pos==new_polarity_3D:
                                received_form.add_error("comp_polarity", \
                                    "Polarity can't be the same element as the component.")
                                form_status = [received_form, ]
                            else:
                                comp_model.comp_polarity_3D = NwRdr.csv_element(new_polarity_3D)
                                comp_model.save()
                                form_status = []
        else:
            form_status = [received_form, ]
        return form_status

    def pre_run_check(self, ckt_file_item, branch_map):
        """
        This function checks for errors primarily in polarity.
        """
        comp_errors = []
        try:
            check_voltage_source = ckt_file_item.controlled_voltage_source_set.all().\
                        filter(comp_tag=self.tag)
        except:
            pass
        else:
            if check_voltage_source and len(check_voltage_source)==1:
                comp_item = check_voltage_source[0]
                current_pos = NwRdr.csv_tuple(comp_item.comp_pos_3D)
                current_polarity = NwRdr.csv_tuple(comp_item.comp_polarity_3D)
                for c1 in range(len(branch_map)):
                    for c2 in range(c1+1, len(branch_map[c1])):
                        for c3 in range(len(branch_map[c1][c2])):
                            if current_pos in branch_map[c1][c2][c3]:
                                if current_polarity not in branch_map[c1][c2][c3]:
                                    comp_errors.append("Polarity has to be an element on \
                                        same branch as voltage source. Check ControlledVoltageSource_" + self.tag)
                                elif current_pos==current_polarity:
                                    comp_errors.append("Polarity can't be the same element \
                                        as the component. Check ControlledVoltageSource_" + self.tag)
        return comp_errors

    def assign_parameters(self, ckt_file_list):
        """
        Transfers data from the database to the component clas
        objects for the simulation.
        """
        for ckt_file_item in ckt_file_list:
            try:
                check_voltage_source = ckt_file_item.controlled_voltage_source_set.all().\
                        filter(comp_tag=self.tag)
            except:
                pass
            else:
                if check_voltage_source and len(check_voltage_source)==1:
                    comp_model = check_voltage_source[0]
                    self.polrty = NwRdr.csv_tuple_2D(comp_model.comp_polarity)
                    self.polrty_3D = NwRdr.csv_tuple(comp_model.comp_polarity_3D)
                    self.control_tag = [comp_model.comp_control_tag, ]
                    self.control_values = [comp_model.comp_voltage, ]
                    self.voltage = comp_model.comp_voltage
        return


class Diode:
    """
    Diode class. Contains functions to initiliaze
    the diode according to name tag, unique cell position,
    update system matrix on each iteration.
    """

    def __init__(self, diode_index, diode_pos, diode_tag, nw_input):
        """
        Constructor to initialize value.
        Also, takes in the identifiers -
        index (serial number), cell position and tag.
        """
        self.type = "Diode"
        self.number = diode_index
        self.pos_3D = diode_pos
        self.sheet = NwRdr.csv_tuple(diode_pos)[0]
        self.pos = NwRdr.csv_element_2D(NwRdr.csv_tuple(diode_pos)[1:])
        self.tag = diode_tag
        self.sheet_name = nw_input[self.sheet] + ".csv"
        self.has_voltage = "yes"
        self.is_meter = "no"
        self.has_control = "no"
        self.diode_level = 120.0
        self.current = 0.0
        self.voltage = 0.0
        self.polrty = [-1, -1]
        self.polrty_3D = [-1, -1, -1]
        self.resistor_on = 0.01
        self.status = "off"
        self.component_banch_pos = 0
        self.component_branch_dir = 1.0

        return

    def display(self):
        """
        Displays info about the component.
        """
        print("Diode is {} located at {} with cathode polarity towards {} in sheet {}".format(
            self.tag, self.pos, NwRdr.csv_element_2D(self.polrty), self.sheet_name
        ))

        return

    def get_polarity(self, ckt_mat, sys_branch):
        if self.polrty==[-1, -1]:
            # Looking for a default value of polarity
            # in the neighbouring cells

            if self.diode_elem[0]>0:
                if ckt_mat[self.sheet][self.diode_elem[0]-1][self.diode_elem[1]]:
                    self.polrty = [self.diode_elem[0]-1, self.diode_elem[1]]
            if self.diode_elem[1]>0:
                if ckt_mat[self.sheet][self.diode_elem[0]][self.diode_elem[1]-1]:
                    self.polrty = [self.diode_elem[0], self.diode_elem[1]-1]
            if self.diode_elem[0]<len(ckt_mat[self.sheet])-1:
                if ckt_mat[self.sheet][self.diode_elem[0]+1][self.diode_elem[1]]:
                    self.polrty = [self.diode_elem[0]+1, self.diode_elem[1]]
            if self.diode_elem[1]<len(ckt_mat[self.sheet][0])-1:
                if ckt_mat[self.sheet][self.diode_elem[0]][self.diode_elem[1]+1]:
                    self.polrty = [self.diode_elem[0], self.diode_elem[1]+1]
        else:
            for c1 in range(len(sys_branch)):
                if [self.sheet, self.diode_elem[0], self.diode_elem[1]] in sys_branch[c1]:
                    if not [self.sheet, self.polrty[0], self.polrty[1]] in sys_branch[c1]:
                        print()
                        print("!"*50)
                        print("ERROR!!! Diode polarity should be in the same branch as the diode. \
Check diode at {} in sheet {}".format(self.pos, self.sheet_name))
                        print("!"*50)
                        print()
                        raise CktEx.PolarityError

        self.polrty_3D = [self.sheet, self.polrty[0], self.polrty[1]]

        return

    def ask_values(self, x_list, ckt_mat, sys_branch):
        """
        Writes the values needed to the spreadsheet.
        """
        diode_params = ["Diode"]
        diode_params.append(self.tag)
        diode_params.append(self.pos)
        diode_params.append("Voltage level (V) = %f" %self.diode_level)

        self.diode_elem = NwRdr.csv_tuple_2D(self.pos)
        self.get_polarity(ckt_mat, sys_branch)

        diode_params.append("Cathode polarity towards (cell) = %s" %NwRdr.csv_element_2D(self.polrty))
        x_list.append(diode_params)

        return

    def export_values_to_csv(self):
        """
        Writes the values needed to the spreadsheet.
        """
        diode_params = ["Diode"]
        diode_params.append(self.tag)
        diode_params.append(self.pos)
        diode_params.append("Voltage level (V) = %f" %self.diode_level)
        diode_params.append("Cathode polarity towards (cell) = %s" %NwRdr.csv_element_2D(self.polrty))

        return diode_params

    def get_values(self, x_list, ckt_mat):
        """
        Takes the parameter from the spreadsheet.
        """
        self.diode_level = float(x_list[0].split("=")[1])
        # Choosing 1 micro Amp as the leakage current that
        # is drawn by the diode in off state.
        self.resistor_off = self.diode_level/1.0e-6
        self.resistor = self.resistor_off

        diode_polrty = x_list[1].split("=")[1]

        # Convert the human readable form of cell
        # to [row, column] form
        while diode_polrty[0]==" ":
            diode_polrty = diode_polrty[1:]

        self.polrty = NwRdr.csv_tuple_2D(diode_polrty)
        self.polrty_3D = [self.sheet, self.polrty[0], self.polrty[1]]

        if not ckt_mat[self.sheet][self.polrty[0]][self.polrty[1]]:
            print("Polarity incorrect. Branch does not exist at {} in sheet {}".format(
                NwRdr.csv_element_2D(self.polrty), self.sheet_name)
            )
            raise CktEx.PolarityError

        return

    def determine_branch(self, sys_branches):
        """
        Determines which branch the component is found in.
        """
        for c1 in range(len(sys_branches)):
            if NwRdr.csv_tuple(self.pos_3D) in sys_branches[c1]:
                self.component_branch_pos = c1
                if sys_branches[c1].index(self.polrty_3D)>sys_branches[c1].index(NwRdr.csv_tuple(self.pos_3D)):
                    self.component_branch_dir = 1.0
                else:
                    self.component_branch_dir = -1.0

        return

    def transfer_to_sys(self, sys_loops, mat_e, mat_a, mat_b, mat_u, source_list):
        """
        The matrix A in E.dx/dt=Ax+Bu will be updated by the
        resistor value of the diode.
        """
        for c1 in range(len(sys_loops)):
            for c2 in range(c1, len(sys_loops)):
                # Updating the elements depending
                # on the sense of the loops (aiding or opposing)
                for c3 in range(len(sys_loops[c1][c2])):
                    # Check if current source position is there in the loop.
                    if NwRdr.csv_tuple(self.pos) in sys_loops[c1][c2][c3]:
                        # Add current source series resistor
                        # if branch is in forward direction
                        if sys_loops[c1][c2][c3][-1]=="forward":
                            mat_a.data[c1][c2] += self.resistor
                        else:
                            # Else subtract if branch is in reverse direction
                            mat_a.data[c1][c2] -= self.resistor
                        # Because the matrices are symmetric
                        mat_a.data[c2][c1] = mat_a.data[c1][c2]

                        # If the positive polarity appears before the voltage position
                        # it means as per KVL, we are moving from +ve to -ve
                        # and so the voltage will be taken negative
                        if sys_loops[c1][c1][c2].index(self.polrty)>sys_loops[c1][c1][c2].index(NwRdr.csv_tuple(self.pos)):
                            if sys_loops[c1][c1][c2][-1]=="forward":
                                mat_b.data[c1][source_list.index(self.pos)] = -1.0
                            else:
                                mat_b.data[c1][source_list.index(self.pos)] = 1.0
                        else:
                            if sys_loops[c1][c1][c2][-1]=="forward":
                                mat_b.data[c1][source_list.index(self.pos)] = 1.0
                            else:
                                mat_b.data[c1][source_list.index(self.pos)] = -1.0

        return

    def transfer_to_branch(self, sys_branch, source_list,  mat_u):
        """
        Update the resistor info of the diode
        to the branch list.
        """
        if NwRdr.csv_tuple(self.pos_3D) in sys_branch:
            sys_branch[-1][0][0] += self.resistor

        # For the diode forward voltage drop.
        if NwRdr.csv_tuple(self.pos_3D) in sys_branch:
            if sys_branch.index(self.polrty_3D)>sys_branch.index(NwRdr.csv_tuple(self.pos_3D)):
                sys_branch[-1][1][source_list.index(self.pos_3D)] = 0.0
            else:
                sys_branch[-1][1][source_list.index(self.pos_3D)] = 0.0

        if self.status=="on":
            mat_u.data[source_list.index(self.pos_3D)][0] = 0.0
            self.voltage = 0.0
        else:
            mat_u.data[source_list.index(self.pos_3D)][0] = 0.0
            self.voltage = 0.0

        return

    def generate_val(self, source_lst, mat_e, mat_a, mat_b, mat_u, t, dt):
        """
        The diode forward drop voltage is updated
        in the matrix u in E.dx/dt=Ax+Bu.
        """
        if self.status=="on":
            mat_u.data[source_lst.index(self.pos_3D)][0] = 0.0
            self.voltage = 0.0
        else:
            mat_u.data[source_lst.index(self.pos_3D)][0] = 0.0
            self.voltage = 0.0

        return

    def update_val_old(self, sys_loop_map, lbyr_ratio, mat_e, mat_a, mat_b, state_vec, mat_u, sys_branches, sys_events):
        """
        This function calculates the actual current in the
        diode branch. With this, the branch voltage is found
        with respect to the existing diode resistance. The diode
        voltage is then used to decide the turn on condition.
        """
        for c1 in range(len(sys_branches)):
            if NwRdr.csv_tuple(self.pos) in sys_branches[c1]:
                branch_pos = c1

        if sys_branches[branch_pos].index(self.polrty)>sys_branches[branch_pos].index(NwRdr.csv_tuple(self.pos)):
            self.current = sys_branches[branch_pos][-1][2]
        else:
            self.current = -sys_branches[branch_pos][-1][2]

        self.voltage = self.current*self.resistor

        # Diode will turn on when it is forward biased
        # and it was previously off.
        if self.status=="off" and self.voltage>1.0:
            sys_events[branch_pos] = "hard"
            self.status = "on"

        # Diode will turn off only when current becomes
        # negative.
        if self.status=="on" and self.current<0.0:
            sys_events[branch_pos] = "yes"
            self.status = "off"

        if self.status=="off":
            self.resistor = self.resistor_off
        else:
            self.resistor = self.resistor_on

        return

    def update_val(self, sys_loop_map, lbyr_ratio, mat_e, mat_a, mat_b, state_vec, mat_u, sys_branches, sys_events):
        """
        This function calculates the actual current in the
        diode branch. With this, the branch voltage is found
        with respect to the existing diode resistance. The diode
        voltage is then used to decide the turn on condition.
        """
        self.current = self.component_branch_dir*sys_branches[self.component_branch_pos][-1][2]
        self.voltage = self.current*self.resistor

        # Diode will turn on when it is forward biased
        # and it was previously off.
        if self.status=="off" and self.voltage>1.0:
            sys_events[self.component_branch_pos] = "hard"
            self.status = "on"

        # Diode will turn off only when current becomes
        # negative.
        if self.status=="on" and self.current<0.0:
            sys_events[self.component_branch_pos] = "yes"
            self.status = "off"

        if self.status=="off":
            self.resistor = self.resistor_off
        else:
            self.resistor = self.resistor_on

        return

    def determine_state_old(self, br_currents, sys_branches, sys_events):
        """
        Determines the state of the diode following an event
        where the continuity of current through an inductor is
        about to be broken.
        """
        # Mark the position of the diode in the branches list
        for c1 in range(len(sys_branches)):
            if NwRdr.csv_tuple(self.pos) in sys_branches[c1]:
                branch_pos = c1

        # Since branch current direction is by default considered
        # positive when flowing away from the starting node
        # If the branch current is negative, with the diode cathode
        # closer towards the starting node, current direction is
        # positive
        if br_currents[branch_pos]*self.resistor<-1.0:
            if sys_branches[branch_pos].index(self.polrty)<sys_branches[branch_pos].index(NwRdr.csv_tuple(self.pos)):
                if self.status=="off":
                    sys_events[branch_pos] = "yes"
                    self.status = "on"

        # If current direction is reverse, diode can never conduct
        if br_currents[branch_pos]<0.0:
            if sys_branches[branch_pos].index(self.polrty)>sys_branches[branch_pos].index(NwRdr.csv_tuple(self.pos)):
                if self.status=="on":
                    sys_events[branch_pos] = "yes"
                    self.status = "off"

        if br_currents[branch_pos]*self.resistor>1.0:
            if sys_branches[branch_pos].index(self.polrty)>sys_branches[branch_pos].index(NwRdr.csv_tuple(self.pos)):
                if self.status=="off":
                    sys_events[branch_pos] = "yes"
                    self.status = "on"

        if br_currents[branch_pos]>0.0:
            if sys_branches[branch_pos].index(self.polrty)<sys_branches[branch_pos].index(NwRdr.csv_tuple(self.pos)):
                if self.status=="on":
                    sys_events[branch_pos] = "yes"
                    self.status = "off"

        # Update the value of resistance
        if self.status=="off":
            self.resistor = self.resistor_off
        else:
            self.resistor = self.resistor_on

        return

    def pre_determine_state(self, br_currents, sys_branches, sys_events):
        """
        Determines the state of the diode following an event
        where the continuity of current through an inductor is
        about to be broken.
        """
        # Since branch current direction is by default considered
        # positive when flowing away from the starting node
        # If the branch current is negative, with the diode cathode
        # closer towards the starting node, current direction is
        # positive
        if br_currents[self.component_branch_pos]*self.component_branch_dir*self.resistor>1.0:
            if self.status=="off":
                sys_events[self.component_branch_pos] = "yes"
                self.status = "on"

        # If current direction is reverse, diode can never conduct
        if br_currents[self.component_branch_pos]*self.component_branch_dir<0.0:
            if self.status=="on":
                sys_events[self.component_branch_pos] = "yes"
                self.status = "off"

        # Update the value of resistance
        if self.status=="off":
            self.resistor = self.resistor_off
        else:
            self.resistor = self.resistor_on

        return

    def determine_state(self, br_currents, sys_branches, sys_events):
        """
        Determines the state of the diode following an event
        where the continuity of current through an inductor is
        about to be broken.
        """
        # Since branch current direction is by default considered
        # positive when flowing away from the starting node
        # If the branch current is negative, with the diode cathode
        # closer towards the starting node, current direction is
        # positive
        if br_currents[self.component_branch_pos]*self.component_branch_dir*self.resistor>1.0:
            if self.status=="off":
                sys_events[self.component_branch_pos] = "yes"
                self.status = "on"

        # If current direction is reverse, diode can never conduct
        if br_currents[self.component_branch_pos]*self.component_branch_dir<0.0:
            if self.status=="on":
                sys_events[self.component_branch_pos] = "yes"
                self.status = "off"

        # Update the value of resistance
        if self.status=="off":
            self.resistor = self.resistor_off
        else:
            self.resistor = self.resistor_on

        return

    def retrieve_db_model(self, sim_para_model):
        """
        This function returns the model instance object.
        """
        check_ckt = sim_para_model.circuitschematics_set.\
                    filter(ckt_file_name=self.sheet_name)
        try:
            check_diode = check_ckt[0].diode_set.\
                    filter(comp_tag=self.tag)
        except:
            return None
        else:
            if check_diode and len(check_diode)==1:
                return check_diode[0]

    def determine_polarity(self, branch_map, diode_obj):
        """
        Determine polarity of a database object.
        """
        for c1 in range(len(branch_map)):
            for c2 in range(c1+1, len(branch_map)):
                for c3 in range(len(branch_map[c1][c2])):
                    if NwRdr.csv_tuple(self.pos_3D) in branch_map[c1][c2][c3]:
                        pos_in_branch = branch_map[c1][c2][c3].\
                                index(NwRdr.csv_tuple(self.pos_3D))
                        prev_element = branch_map[c1][c2][c3][pos_in_branch-1]
                        diode_obj.comp_polarity_3D = NwRdr.csv_element(prev_element)
                        diode_obj.comp_polarity = \
                                NwRdr.csv_element_2D(prev_element[1:])
        return

    def init_db_values(self, sim_para_model, ckt_file_list, branch_map):
        """
        This function creates a new database entry for a component or
        updates an existing database entry from the component class data.
        """
        comp_found = False
        check_ckt = sim_para_model.circuitschematics_set.\
                    filter(ckt_file_name=self.sheet_name)
        try:
            check_diode = check_ckt[0].diode_set.\
                    filter(comp_tag=self.tag)
        except:
            comp_found = False
        else:
            if check_diode and len(check_diode)==1:
                comp_found = True
                old_diode = check_diode[0]
                if not (self.polrty==[-1, -1]):
                    old_diode.comp_polarity = NwRdr.csv_element_2D(self.polrty)
                if not (self.polrty_3D==[-1, -1, -1]):
                    old_diode.comp_polarity_3D = NwRdr.csv_element(self.polrty_3D)
                if old_diode.comp_polarity_3D:
                    diode_old_polarity = NwRdr.csv_tuple(old_diode.comp_polarity_3D)
                    diode_new_polarity = NwRdr.csv_tuple(self.pos_3D)
                    diode_old_polarity[0] = diode_new_polarity[0]
                    old_diode.comp_polarity_3D = NwRdr.csv_element(diode_old_polarity)
                else:
                    self.determine_polarity(branch_map, old_diode)
                old_diode.comp_number = self.number
                old_diode.comp_pos_3D = self.pos_3D
                old_diode.comp_pos = self.pos
                old_diode.comp_sheet = self.sheet
                old_diode.save()
                check_ckt[0].save()
            if check_diode and len(check_diode)==1:
                comp_found = True
                for c1 in range(len(check_diode)-1, 0, -1):
                    check_diode[c1].delete()
                    check_ckt[0].save()

        if not comp_found:
            new_diode = models.Diode()
            if not (self.polrty==[-1, -1]):
                new_diode.comp_polarity = NwRdr.csv_element_2D(self.polrty)
            if not (self.polrty_3D==[-1, -1, -1]):
                new_diode.comp_polarity_3D = NwRdr.csv_element(self.polrty_3D)
            new_diode.comp_number = self.number
            new_diode.comp_pos_3D = self.pos_3D
            new_diode.comp_pos = self.pos
            new_diode.comp_sheet = self.sheet
            new_diode.sheet_name = self.sheet_name.split(".csv")[0]
            new_diode.comp_tag = self.tag
            self.determine_polarity(branch_map, new_diode)
            ckt_file_item = ckt_file_list.filter(ckt_file_name=self.sheet_name)
            new_diode.comp_ckt = ckt_file_item[0]
            new_diode.save()
        sim_para_model.save()

        return

    def create_form_values(self, sim_para_model, ckt_file_list, branch_map):
        """
        This function creates a new database entry for a component or
        updates an existing database entry from the component class data.
        """
        comp_found = False
        check_ckt = sim_para_model.circuitschematics_set.\
                    filter(ckt_file_name=self.sheet_name)
        try:
            check_diode = check_ckt[0].diode_set.\
                    filter(comp_tag=self.tag)
        except:
            comp_found = False
        else:
            if check_diode and len(check_diode)==1:
                comp_found = True
                old_diode = check_diode[0]
                if not (self.polrty==[-1, -1]):
                    old_diode.comp_polarity = NwRdr.csv_element_2D(self.polrty)
                if not (self.polrty_3D==[-1, -1, -1]):
                    old_diode.comp_polarity_3D = NwRdr.csv_element(self.polrty_3D)
                old_diode.comp_number = self.number
                old_diode.comp_volt_level = self.diode_level
                old_diode.comp_pos_3D = self.pos_3D
                old_diode.comp_pos = self.pos
                old_diode.comp_sheet = self.sheet
                old_diode.save()
                check_ckt[0].save()
            if check_diode and len(check_diode)==1:
                comp_found = True
                for c1 in range(len(check_diode)-1, 0, -1):
                    check_diode[c1].delete()
                    check_ckt[0].save()

        if not comp_found:
            new_diode = models.Diode()
            if not (self.polrty==[-1, -1]):
                new_diode.comp_polarity = NwRdr.csv_element_2D(self.polrty)
            if not (self.polrty_3D==[-1, -1, -1]):
                new_diode.comp_polarity_3D = NwRdr.csv_element(self.polrty_3D)
            new_diode.comp_number = self.number
            new_diode.comp_pos_3D = self.pos_3D
            new_diode.comp_pos = self.pos
            new_diode.comp_sheet = self.sheet
            new_diode.sheet_name = self.sheet_name.split(".csv")[0]
            new_diode.comp_tag = self.tag
            self.determine_polarity(branch_map, new_diode)
            ckt_file_item = ckt_file_list.filter(ckt_file_name=self.sheet_name)
            new_diode.comp_ckt = ckt_file_item[0]
            new_diode.save()
        sim_para_model.save()

        return

    def list_existing_components(self, ckt_file):
        """
        Check if the model of the circuit file contains
        the associated database entry for the component.
        Returns an empty list if not found.
        """
        try:
            check_diode = ckt_file.diode_set.all().\
                        filter(comp_tag=self.tag)
        except:
            comp_list = []
        else:
            if check_diode and len(check_diode)==1:
                comp_list = check_diode[0]
            else:
                comp_list = []
        return comp_list

    def comp_as_a_dict(self, ckt_file):
        """
        Returns information about a component as a list
        that can be displayed in a webpage.
        """
        try:
            check_diode = ckt_file.diode_set.all().\
                        filter(comp_tag=self.tag)
        except:
            comp_list = []
        else:
            if check_diode and len(check_diode)==1:
                comp_list = []
                comp_list.append(["Component type", check_diode[0].comp_type])
                comp_list.append(["Component name", check_diode[0].comp_tag])
                comp_list.append(["Component position", check_diode[0].comp_pos])
                comp_list.append(["Voltage level", check_diode[0].comp_volt_level])
                comp_list.append(["Direction of cathode", \
                        check_diode[0].comp_polarity])
            else:
                comp_list = []
        return comp_list

    def comp_as_a_form(self, ckt_file):
        """
        Returns a populated form for a component.
        """
        try:
            check_diode = ckt_file.diode_set.all().\
                        filter(comp_tag=self.tag)
        except:
            return []
        else:
            if check_diode and len(check_diode)==1:
                return [models.DiodeForm, check_diode[0]]
                # comp_list = models.DiodeForm(instance=check_diode[0])
            else:
                return []
        # return comp_list

    def save_to_db(self, ckt_file):
        """
        Returns a populated form for a component.
        """
        try:
            check_diode = ckt_file.diode_set.all().\
                        filter(comp_tag=self.tag)
        except:
            return
        else:
            if check_diode and len(check_diode)==1:
                old_diode = check_diode[0]
                if not (self.polrty==[-1, -1]):
                    old_diode.comp_polarity = NwRdr.csv_element_2D(self.polrty)
                if not (self.polrty_3D==[-1, -1, -1]):
                    old_diode.comp_polarity_3D = NwRdr.csv_element(self.polrty_3D)
                old_diode.comp_volt_level = self.diode_level
                old_diode.save()
                ckt_file.save()
                return
            else:
                return

    def update_form_data(self, request, comp_model, branch_map):
        """
        Extracts data from a form and saves it to the database.
        """
        received_form = models.DiodeForm(request.POST)
        if received_form.is_valid():
            received_data = received_form.cleaned_data
            comp_model.comp_volt_level = received_data["comp_volt_level"]
            new_polarity = received_data["comp_polarity"]
            comp_model.comp_polarity = new_polarity
            new_polarity_3D = [comp_model.comp_sheet, ]
            new_polarity_3D.extend(NwRdr.csv_tuple_2D(new_polarity))
            comp_model.comp_polarity_3D = NwRdr.csv_element(new_polarity_3D)
            current_pos = NwRdr.csv_tuple(comp_model.comp_pos_3D)
            for c1 in range(len(branch_map)):
                for c2 in range(c1+1, len(branch_map[c1])):
                    for c3 in range(len(branch_map[c1][c2])):
                        if current_pos in branch_map[c1][c2][c3]:
                            if new_polarity_3D not in branch_map[c1][c2][c3]:
                                received_form.add_error("comp_polarity", \
                                    "Polarity has to be an element on same branch as diode.")
                                form_status = [received_form, ]
                            elif current_pos==new_polarity_3D:
                                received_form.add_error("comp_polarity", \
                                    "Polarity can't be the same element as the component.")
                                form_status = [received_form, ]
                            else:
                                comp_model.comp_polarity_3D = NwRdr.csv_element(new_polarity_3D)
                                comp_model.save()
                                form_status = []
        else:
            form_status = [received_form, ]
        return form_status

    def pre_run_check(self, ckt_file_item, branch_map):
        """
        This function checks for errors primarily in polarity.
        """
        comp_errors = []
        try:
            check_diode = ckt_file_item.diode_set.all().\
                        filter(comp_tag=self.tag)
        except:
            pass
        else:
            if check_diode and len(check_diode)==1:
                comp_item = check_diode[0]
                current_pos = NwRdr.csv_tuple(comp_item.comp_pos_3D)
                current_polarity = NwRdr.csv_tuple(comp_item.comp_polarity_3D)
                for c1 in range(len(branch_map)):
                    for c2 in range(c1+1, len(branch_map[c1])):
                        for c3 in range(len(branch_map[c1][c2])):
                            if current_pos in branch_map[c1][c2][c3]:
                                if current_polarity not in branch_map[c1][c2][c3]:
                                    comp_errors.append("Polarity has to be an element on \
                                        same branch as diode. Check Diode_" + self.tag)
                                elif current_pos==current_polarity:
                                    comp_errors.append("Polarity can't be the same element \
                                        as the component. Check Diode_" + self.tag)
        return comp_errors

    def assign_parameters(self, ckt_file_list):
        """
        Transfers data from the database to the component clas
        objects for the simulation.
        """
        for ckt_file_item in ckt_file_list:
            try:
                check_diode = ckt_file_item.diode_set.all().\
                        filter(comp_tag=self.tag)
            except:
                pass
            else:
                if check_diode and len(check_diode)==1:
                    comp_model = check_diode[0]
                    self.polrty = NwRdr.csv_tuple_2D(comp_model.comp_polarity)
                    self.polrty_3D = NwRdr.csv_tuple(comp_model.comp_polarity_3D)
                    self.diode_level = comp_model.comp_volt_level
                    self.resistor_off = self.diode_level/1.0e-6
                    self.resistor = self.resistor_off
        return


class Switch:
    """
    Ideal switch class. Contains functions to initiliaze
    the switch according to name tag, unique cell position,
    update system matrix on each iteration.
    """

    def __init__(self, switch_index, switch_pos, switch_tag, nw_input):
        """
        Constructor to initialize value.
        Also, takes in the identifiers -
        index (serial number), cell position and tag.
        """
        self.type="Switch"
        self.number = switch_index
        self.pos_3D = switch_pos
        self.sheet = NwRdr.csv_tuple(switch_pos)[0]
        self.pos = NwRdr.csv_element_2D(NwRdr.csv_tuple(switch_pos)[1:])
        self.tag = switch_tag
        self.sheet_name = nw_input[self.sheet] + ".csv"
        self.has_voltage = "yes"
        self.switch_level = 120.0
        self.is_meter = "no"
        self.has_control = "yes"
        self.current = 0.0
        self.voltage = 0.0
        self.polrty = [-1, -1]
        self.polrty_3D = [-1, -1, -1]
        self.resistor_on = 0.01
        self.status = "off"
        self.control_tag = ["Control"]
        self.control_values = [0.0]
        self.component_banch_pos = 0
        self.component_branch_dir = 1.0

        return

    def display(self):
        """
        Displays info about the component.
        """
        print("Switch is {} located at {} with negative polarity towards {} in sheet {}".format(
            self.tag, self.pos, NwRdr.csv_element_2D(self.polrty), self.sheet_name
        ))

        return

    def get_polarity(self, ckt_mat, sys_branch):
        if self.polrty==[-1, -1]:
            # Looking for a default value of polarity
            # in the neighbouring cells

            if self.switch_elem[0]>0:
                if ckt_mat[self.sheet][self.switch_elem[0]-1][self.switch_elem[1]]:
                    self.polrty = [self.switch_elem[0]-1, self.switch_elem[1]]
            if self.switch_elem[1]>0:
                if ckt_mat[self.sheet][self.switch_elem[0]][self.switch_elem[1]-1]:
                    self.polrty = [self.switch_elem[0], self.switch_elem[1]-1]

            if self.switch_elem[0]<len(ckt_mat[self.sheet])-1:
                if ckt_mat[self.sheet][self.switch_elem[0]+1][self.switch_elem[1]]:
                    self.polrty = [self.switch_elem[0]+1, self.switch_elem[1]]
            if self.switch_elem[1]<len(ckt_mat[self.sheet][0])-1:
                if ckt_mat[self.sheet][self.switch_elem[0]][self.switch_elem[1]+1]:
                    self.polrty = [self.switch_elem[0], self.switch_elem[1]+1]
        else:
            for c1 in range(len(sys_branch)):
                if NwRdr.csv_tuple(self.pos_3D) in sys_branch[c1]:
                    if not [self.sheet, self.polrty[0], self.polrty[1]] in sys_branch[c1]:
                        print()
                        print("!"*50)
                        print("ERROR!!! Switch polarity should be in the same branch as the switch. \
Check switch at {} in sheet {}".format(self.pos, self.sheet_name))
                        print("!"*50)
                        print()
                        raise CktEx.PolarityError

        self.polrty_3D = [self.sheet, self.polrty[0], self.polrty[1]]

        return

    def ask_values(self, x_list, ckt_mat, sys_branch):
        """
        Writes the values needed to the spreadsheet.
        """
        switch_params = ["Switch"]
        switch_params.append(self.tag)
        switch_params.append(self.pos)
        switch_params.append("Voltage level (V) = %f" %self.switch_level)

        self.switch_elem = NwRdr.csv_tuple_2D(self.pos)
        self.get_polarity(ckt_mat, sys_branch)

        switch_params.append("Negative polarity towards (cell) = %s" %NwRdr.csv_element_2D(self.polrty))
        switch_params.append("Name of control signal = %s" %self.control_tag[0])
        x_list.append(switch_params)

        return

    def export_values_to_csv(self):
        """
        Writes the values needed to the spreadsheet.
        """
        switch_params = ["Switch"]
        switch_params.append(self.tag)
        switch_params.append(self.pos)
        switch_params.append("Voltage level (V) = %f" %self.switch_level)
        switch_params.append("Negative polarity towards (cell) = %s" %NwRdr.csv_element_2D(self.polrty))
        switch_params.append("Name of control signal = %s" %self.control_tag[0])

        return switch_params

    def get_values(self, x_list, ckt_mat):
        """ Takes the parameter from the spreadsheet."""
        self.switch_level = float(x_list[0].split("=")[1])
        # Choosing 1 micro Amp as the leakage current that
        # is drawn by the switch in off state.
        self.resistor_off = self.switch_level/1.0e-6
        self.resistor = self.resistor_off

        switch_polrty = x_list[1].split("=")[1]

        # Convert the human readable form of cell
        # to [row, column] form
        while switch_polrty[0]==" ":
            switch_polrty = switch_polrty[1:]

        self.polrty = NwRdr.csv_tuple_2D(switch_polrty)
        self.polrty_3D = [self.sheet, self.polrty[0], self.polrty[1]]

        if not ckt_mat[self.sheet][self.polrty[0]][self.polrty[1]]:
            print("Polarity incorrect. Branch does not exist at {} in sheet {}".format(
                NwRdr.csv_element(self.polrty), self.sheet_name)
            )
            raise CktEx.PolarityError

        self.control_tag[0] = x_list[2].split("=")[1]
        while self.control_tag[0][0]==" ":
            self.control_tag[0] = self.control_tag[0][1:]

        return

    def determine_branch(self, sys_branches):
        """
        Determines which branch the component is found in.
        """
        for c1 in range(len(sys_branches)):
            if NwRdr.csv_tuple(self.pos_3D) in sys_branches[c1]:
                self.component_branch_pos = c1
                if sys_branches[c1].index(self.polrty_3D)>sys_branches[c1].index(NwRdr.csv_tuple(self.pos_3D)):
                    self.component_branch_dir = 1.0
                else:
                    self.component_branch_dir = -1.0

        return

    def transfer_to_sys(self, sys_loops, mat_e, mat_a, mat_b, mat_u, source_list):
        """
        The matrix A in E.dx/dt=Ax+Bu will be updated by the
        resistor value of the switch.
        """
        for c1 in range(len(sys_loops)):
            for c2 in range(c1, len(sys_loops)):
                # Updating the elements depending
                # on the sense of the loops (aiding or opposing)
                for c3 in range(len(sys_loops[c1][c2])):
                    # Check if current source position is there in the loop.
                    if NwRdr.csv_tuple(self.pos) in sys_loops[c1][c2][c3]:
                        # Add current source series resistor
                        # if branch is in forward direction
                        if sys_loops[c1][c2][c3][-1]=="forward":
                            mat_a.data[c1][c2] += self.resistor
                        else:
                            # Else subtract if branch is in reverse direction
                            mat_a.data[c1][c2] -= self.resistor
                        # Because the matrices are symmetric
                        mat_a.data[c2][c1] = mat_a.data[c1][c2]

                        # If the positive polarity appears before the voltage position
                        # it means as per KVL, we are moving from +ve to -ve
                        # and so the voltage will be taken negative
                        if sys_loops[c1][c1][c2].index(self.polrty)>sys_loops[c1][c1][c2].index(NwRdr.csv_tuple(self.pos)):
                            if sys_loops[c1][c1][c2][-1]=="forward":
                                mat_b.data[c1][source_list.index(self.pos)] = -1.0
                            else:
                                mat_b.data[c1][source_list.index(self.pos)] = 1.0
                        else:
                            if sys_loops[c1][c1][c2][-1]=="forward":
                                mat_b.data[c1][source_list.index(self.pos)] = 1.0
                            else:
                                mat_b.data[c1][source_list.index(self.pos)] = -1.0

        return

    def transfer_to_branch(self, sys_branch, source_list,  mat_u):
        """
        Update the resistor info of the switch
        to the branch list.
        """
        if NwRdr.csv_tuple(self.pos_3D) in sys_branch:
            sys_branch[-1][0][0] += self.resistor

        # For the switch forward voltage drop.
        if NwRdr.csv_tuple(self.pos_3D) in sys_branch:
            if sys_branch.index(self.polrty_3D)>sys_branch.index(NwRdr.csv_tuple(self.pos_3D)):
                sys_branch[-1][1][source_list.index(self.pos_3D)] = 0.0
            else:
                sys_branch[-1][1][source_list.index(self.pos_3D)] = 0.0

        if self.status=="on":
            mat_u.data[source_list.index(self.pos_3D)][0] = 0.0
            self.voltage = 0.0
        else:
            mat_u.data[source_list.index(self.pos_3D)][0] = 0.0
            self.voltage = 0.0

        return

    def generate_val(self, source_lst, mat_e, mat_a, mat_b, mat_u, t, dt):
        """
        The switch forward drop voltage is updated
        in the matrix u in E.dx/dt=Ax+Bu.
        """
        # The switch does not contain voltage when on.
        if self.status=="on":
            mat_u.data[source_lst.index(self.pos_3D)][0] = 0.0
            self.voltage = 0.0
        else:
            mat_u.data[source_lst.index(self.pos_3D)][0] = 0.0
            self.voltage = 0.0

        return

    def update_val_old(self, sys_loop_map, lbyr_ratio, mat_e, mat_a, mat_b, state_vec, mat_u, sys_branches, sys_events):
        """
        This function calculates the actual current in the
        switch branch. With this, the branch voltage is found
        with respect to the existing switch resistance. The switch
        voltage is then used to decide the turn on condition.
        """
        for c1 in range(len(sys_branches)):
            if NwRdr.csv_tuple(self.pos) in sys_branches[c1]:
                branch_pos = c1

        if sys_branches[branch_pos].index(self.polrty)>sys_branches[branch_pos].index(NwRdr.csv_tuple(self.pos)):
            self.current = sys_branches[branch_pos][-1][2]
        else:
            self.current = -sys_branches[branch_pos][-1][2]

        self.voltage = self.current*self.resistor

        # Identifying the position of the switch branch
        # to generate events.
        for c1 in range(len(sys_branches)):
            if NwRdr.csv_tuple(self.pos) in sys_branches[c1]:
                branch_pos = c1

        # Switch will turn on when it is forward biased
        # and it is gated on.
        if self.control_values[0]>=1.0 and self.voltage>1.0:
            if self.status=="off":
                sys_events[branch_pos] = "hard"
                self.status = "on"

        # Switch will turn off when gated off or
        # when current becomes negative.
        # If the current becomes negative, it is a soft turn off
        if self.current<0.0:
            if self.status=="on":
                sys_events[branch_pos] = "yes"
                self.status = "off"

        # If the switch turns off due to a gate signal
        # it is a hard turn off
        if self.control_values[0]==0.0:
            if self.status=="on":
                sys_events[branch_pos] = "hard"
                self.status = "off"

        if self.status=="off":
            self.resistor = self.resistor_off
        else:
            self.resistor = self.resistor_on

        return

    def update_val(self, sys_loop_map, lbyr_ratio, mat_e, mat_a, mat_b, state_vec, mat_u, sys_branches, sys_events):
        """
        This function calculates the actual current in the
        switch branch. With this, the branch voltage is found
        with respect to the existing switch resistance. The switch
        voltage is then used to decide the turn on condition.
        """
        self.switch_elem = NwRdr.csv_tuple_2D(self.pos)
        self.current = self.component_branch_dir*sys_branches[self.component_branch_pos][-1][2]
        self.voltage = self.current*self.resistor

        # Switch will turn on when it is forward biased
        # and it is gated on.
        if self.control_values[0]>=1.0 and self.voltage>1.0:
            if self.status=="off":
                sys_events[self.component_branch_pos] = "hard"
                self.status = "on"

        # Switch will turn off when gated off or
        # when current becomes negative.
        # If the current becomes negative, it is a soft turn off
        if self.current<0.0:
            if self.status=="on":
                sys_events[self.component_branch_pos] = "yes"
                self.status = "off"

        # If the switch turns off due to a gate signal
        # it is a hard turn off
        if self.control_values[0]==0.0:
            if self.status=="on":
                sys_events[self.component_branch_pos] = "hard"
                self.status = "off"

        if self.status=="off":
            self.resistor = self.resistor_off
        else:
            self.resistor = self.resistor_on

        return

    def determine_state_old(self, br_currents, sys_branches, sys_events):
        """
        Determines the state of the switch following an event
        where the continuity of current through an inductor is
        about to be broken. This can only check if the switch should
        turn off. Turn on is only decided by the update_value method.
        """
        # Mark the position of the switch in sys_branches
        for c1 in range(len(sys_branches)):
            if NwRdr.csv_tuple(self.pos) in sys_branches[c1]:
                branch_pos = c1

        # If the current direction is reverse, switch can never conduct
        if br_currents[branch_pos]<0.0:
            if sys_branches[branch_pos].index(self.polrty)>sys_branches[branch_pos].index(NwRdr.csv_tuple(self.pos)):
                if self.status=="on":
                    sys_events[branch_pos] = "yes"
                self.status = "off"

        if br_currents[branch_pos]>0.0:
            if sys_branches[branch_pos].index(self.polrty)<sys_branches[branch_pos].index(NwRdr.csv_tuple(self.pos)):
                if self.status=="on":
                    sys_events[branch_pos] = "yes"
                self.status = "off"

        # Update the value of resistance
        if self.status=="off":
            self.resistor = self.resistor_off
        else:
            self.resistor = self.resistor_on

        return

    def pre_determine_state(self, br_currents, sys_branches, sys_events):
        """
        Determines the state of the switch following an event
        where the continuity of current through an inductor is
        about to be broken. This can only check if the switch should
        turn off. Turn on is only decided by the update_value method.
        """

        self.current = self.component_branch_dir*br_currents[self.component_branch_pos]
        self.voltage = self.current*self.resistor

        # Switch will turn on when it is forward biased
        # and it is gated on.
        if self.control_values[0]>=1.0 and self.voltage>1.0:
            if self.status=="off":
                sys_events[self.component_branch_pos] = "hard"
                self.status = "on"

        # Switch will turn off when gated off or
        # when current becomes negative.
        # If the current becomes negative, it is a soft turn off
        if self.current<0.0:
            if self.status=="on":
                sys_events[self.component_branch_pos] = "yes"
                self.status = "off"

        # If the switch turns off due to a gate signal
        # it is a hard turn off
        if self.control_values[0]==0.0:
            if self.status=="on":
                sys_events[self.component_branch_pos] = "hard"
                self.status = "off"

        if self.status=="off":
            self.resistor = self.resistor_off
        else:
            self.resistor = self.resistor_on

        return

    def determine_state(self, br_currents, sys_branches, sys_events):
        """
        Determines the state of the switch following an event
        where the continuity of current through an inductor is
        about to be broken. This can only check if the switch should
        turn off. Turn on is only decided by the update_value method.
        """
        # If the current direction is reverse, switch can never conduct
        if br_currents[self.component_branch_pos]*self.component_branch_dir<0.0:
            #if sys_branches[branch_pos].index(self.polrty)>sys_branches[branch_pos].index(NwRdr.csv_tuple(self.pos)):
            if self.status=="on":
                sys_events[self.component_branch_pos] = "yes"
            self.status = "off"

        # Update the value of resistance
        if self.status=="off":
            self.resistor = self.resistor_off
        else:
            self.resistor = self.resistor_on

        return

    def retrieve_db_model(self, sim_para_model):
        """
        This function returns the model instance object.
        """
        check_ckt = sim_para_model.circuitschematics_set.\
                    filter(ckt_file_name=self.sheet_name)
        try:
            check_switch = check_ckt[0].switch_set.\
                    filter(comp_tag=self.tag)
        except:
            return None
        else:
            if check_switch and len(check_switch)==1:
                return check_switch[0]

    def determine_polarity(self, branch_map, switch_obj):
        """
        Determines polarity of a database object
        """
        for c1 in range(len(branch_map)):
            for c2 in range(c1+1, len(branch_map)):
                for c3 in range(len(branch_map[c1][c2])):
                    if NwRdr.csv_tuple(self.pos_3D) in branch_map[c1][c2][c3]:
                        pos_in_branch = branch_map[c1][c2][c3].\
                                index(NwRdr.csv_tuple(self.pos_3D))
                        prev_element = branch_map[c1][c2][c3][pos_in_branch-1]
                        switch_obj.comp_polarity_3D = NwRdr.csv_element(prev_element)
                        switch_obj.comp_polarity = \
                                NwRdr.csv_element_2D(prev_element[1:])
        return

    def init_db_values(self, sim_para_model, ckt_file_list, branch_map):
        """
        This function creates a new database entry for a component or
        updates an existing database entry from the component class data.
        """
        comp_found = False
        check_ckt = sim_para_model.circuitschematics_set.\
                    filter(ckt_file_name=self.sheet_name)
        try:
            check_switch = check_ckt[0].switch_set.\
                    filter(comp_tag=self.tag)
        except:
            comp_found = False
        else:
            if check_switch and len(check_switch)==1:
                comp_found = True
                old_switch = check_switch[0]
                if not (self.polrty==[-1, -1]):
                    old_switch.comp_polarity = NwRdr.csv_element_2D(self.polrty)
                if not (self.polrty_3D==[-1, -1, -1]):
                    old_switch.comp_polarity_3D = NwRdr.csv_element(self.polrty_3D)
                if old_switch.comp_polarity_3D:
                    switch_old_polarity = NwRdr.csv_tuple(old_switch.comp_polarity_3D)
                    switch_new_polarity = NwRdr.csv_tuple(self.pos_3D)
                    switch_old_polarity[0] = switch_new_polarity[0]
                    old_switch.comp_polarity_3D = NwRdr.csv_element(switch_old_polarity)
                else:
                    self.determine_polarity(branch_map, old_switch)
                old_switch.comp_number = self.number
                old_switch.comp_pos_3D = self.pos_3D
                old_switch.comp_pos = self.pos
                old_switch.comp_sheet = self.sheet
                old_switch.save()
                check_ckt[0].save()
            if check_switch and len(check_switch)>1:
                comp_found = True
                for c1 in range(len(check_switch)-1, 0, -1):
                    check_switch[c1].delete()
                    check_ckt[0].save()

        if not comp_found:
            new_switch = models.Switch()
            if not (self.polrty==[-1, -1]):
                new_switch.comp_polarity = NwRdr.csv_element_2D(self.polrty)
            if not (self.polrty_3D==[-1, -1, -1]):
                new_switch.comp_polarity_3D = NwRdr.csv_element(self.polrty_3D)
            new_switch.comp_number = self.number
            new_switch.comp_pos_3D = self.pos_3D
            new_switch.comp_pos = self.pos
            new_switch.comp_sheet = self.sheet
            new_switch.sheet_name = self.sheet_name.split(".csv")[0]
            new_switch.comp_tag = self.tag
            self.determine_polarity(branch_map, new_switch)
            ckt_file_item = ckt_file_list.filter(ckt_file_name=self.sheet_name)
            new_switch.comp_ckt = ckt_file_item[0]
            new_switch.save()
        sim_para_model.save()

        return

    def create_form_values(self, sim_para_model, ckt_file_list, branch_map):
        """
        This function creates a new database entry for a component or
        updates an existing database entry from the component class data.
        """
        comp_found = False
        check_ckt = sim_para_model.circuitschematics_set.\
                    filter(ckt_file_name=self.sheet_name)
        try:
            check_switch = check_ckt[0].switch_set.\
                    filter(comp_tag=self.tag)
        except:
            comp_found = False
        else:
            if check_switch and len(check_switch)==1:
                comp_found = True
                old_switch = check_switch[0]
                if not (self.polrty==[-1, -1]):
                    old_switch.comp_polarity = NwRdr.csv_element_2D(self.polrty)
                if not (self.polrty_3D==[-1, -1, -1]):
                    old_switch.comp_polarity_3D = NwRdr.csv_element(self.polrty_3D)
                old_switch.comp_number = self.number
                old_switch.comp_pos_3D = self.pos_3D
                old_switch.comp_volt_level = self.switch_level
                old_switch.comp_pos = self.pos
                old_switch.comp_sheet = self.sheet
                old_switch.comp_control_tag = self.control_tag[0]
                old_switch.save()
                check_ckt[0].save()
            if check_switch and len(check_switch)>1:
                comp_found = True
                for c1 in range(len(check_switch)-1, 0, -1):
                    check_switch[c1].delete()
                    check_ckt[0].save()

        if not comp_found:
            new_switch = models.Switch()
            if not (self.polrty==[-1, -1]):
                new_switch.comp_polarity = NwRdr.csv_element_2D(self.polrty)
            if not (self.polrty_3D==[-1, -1, -1]):
                new_switch.comp_polarity_3D = NwRdr.csv_element(self.polrty_3D)
            new_switch.comp_number = self.number
            new_switch.comp_pos_3D = self.pos_3D
            new_switch.comp_pos = self.pos
            new_switch.comp_sheet = self.sheet
            new_switch.sheet_name = self.sheet_name.split(".csv")[0]
            new_switch.comp_tag = self.tag
            self.determine_polarity(branch_map, new_switch)
            ckt_file_item = ckt_file_list.filter(ckt_file_name=self.sheet_name)
            new_switch.comp_ckt = ckt_file_item[0]
            new_switch.save()
        sim_para_model.save()

        return

    def list_existing_components(self, ckt_file):
        """
        Check if the model of the circuit file contains
        the associated database entry for the component.
        Returns an empty list if not found.
        """
        try:
            check_switch = ckt_file.switch_set.all().\
                        filter(comp_tag=self.tag)
        except:
            comp_list = []
        else:
            if check_switch and len(check_switch)==1:
                comp_list = check_switch[0]
            else:
                comp_list = []
        return comp_list

    def comp_as_a_dict(self, ckt_file):
        """
        Returns information about a component as a list
        that can be displayed in a webpage.
        """
        try:
            check_switch = ckt_file.switch_set.all().\
                        filter(comp_tag=self.tag)
        except:
            comp_list = []
        else:
            if check_switch and len(check_switch)==1:
                comp_list = []
                comp_list.append(["Component type", check_switch[0].comp_type])
                comp_list.append(["Component name", check_switch[0].comp_tag])
                comp_list.append(["Component position", check_switch[0].comp_pos])
                comp_list.append(["Control tag", check_switch[0].comp_control_tag])
                comp_list.append(["Voltage level", check_switch[0].comp_volt_level])
                comp_list.append(["Direction of cathode", \
                        check_switch[0].comp_polarity])
            else:
                comp_list = []
        return comp_list

    def comp_as_a_form(self, ckt_file):
        """
        Returns a populated form for a component.
        """
        try:
            check_switch = ckt_file.switch_set.all().\
                        filter(comp_tag=self.tag)
        except:
            return []
        else:
            if check_switch and len(check_switch)==1:
                return [models.SwitchForm, check_switch[0]]
                # comp_list = models.SwitchForm(instance=check_switch[0])
            else:
                return []
        # return comp_list

    def save_to_db(self, ckt_file):
        """
        Returns a populated form for a component.
        """
        try:
            check_switch = ckt_file.switch_set.all().\
                        filter(comp_tag=self.tag)
        except:
            return
        else:
            if check_switch and len(check_switch)==1:
                old_switch = check_switch[0]
                if not (self.polrty==[-1, -1]):
                    old_switch.comp_polarity = NwRdr.csv_element_2D(self.polrty)
                if not (self.polrty_3D==[-1, -1, -1]):
                    old_switch.comp_polarity_3D = NwRdr.csv_element(self.polrty_3D)
                old_switch.comp_volt_level = self.switch_level
                old_switch.comp_control_tag = self.control_tag[0]
                old_switch.save()
                ckt_file.save()
                return
            else:
                return

    def update_form_data(self, request, comp_model, branch_map):
        """
        Extracts data from a form and saves it to the database.
        """
        received_form = models.SwitchForm(request.POST)
        if received_form.is_valid():
            received_data = received_form.cleaned_data
            comp_model.comp_volt_level = received_data["comp_volt_level"]
            comp_model.comp_control_tag = received_data["comp_control_tag"]
            new_polarity = received_data["comp_polarity"]
            comp_model.comp_polarity = new_polarity
            new_polarity_3D = [comp_model.comp_sheet, ]
            new_polarity_3D.extend(NwRdr.csv_tuple_2D(new_polarity))
            comp_model.comp_polarity_3D = NwRdr.csv_element(new_polarity_3D)
            current_pos = NwRdr.csv_tuple(comp_model.comp_pos_3D)
            for c1 in range(len(branch_map)):
                for c2 in range(c1+1, len(branch_map[c1])):
                    for c3 in range(len(branch_map[c1][c2])):
                        if current_pos in branch_map[c1][c2][c3]:
                            if new_polarity_3D not in branch_map[c1][c2][c3]:
                                received_form.add_error("comp_polarity", \
                                    "Polarity has to be an element on same branch as switch.")
                                form_status = [received_form, ]
                            elif current_pos==new_polarity_3D:
                                received_form.add_error("comp_polarity", \
                                    "Polarity can't be the same element as the component.")
                                form_status = [received_form, ]
                            else:
                                comp_model.comp_polarity_3D = NwRdr.csv_element(new_polarity_3D)
                                comp_model.save()
                                form_status = []
        else:
            form_status = [received_form, ]
        return form_status

    def pre_run_check(self, ckt_file_item, branch_map):
        """
        This function checks for errors primarily in polarity.
        """
        comp_errors = []
        try:
            check_switch = ckt_file_item.switch_set.all().\
                        filter(comp_tag=self.tag)
        except:
            pass
        else:
            if check_switch and len(check_switch)==1:
                comp_item = check_switch[0]
                current_pos = NwRdr.csv_tuple(comp_item.comp_pos_3D)
                current_polarity = NwRdr.csv_tuple(comp_item.comp_polarity_3D)
                for c1 in range(len(branch_map)):
                    for c2 in range(c1+1, len(branch_map[c1])):
                        for c3 in range(len(branch_map[c1][c2])):
                            if current_pos in branch_map[c1][c2][c3]:
                                if current_polarity not in branch_map[c1][c2][c3]:
                                    comp_errors.append("Polarity has to be an element on \
                                        same branch as switch. Check Switch_" + self.tag)
                                elif current_pos==current_polarity:
                                    comp_errors.append("Polarity can't be the same element \
                                        as the component. Check Switch_" + self.tag)
        return comp_errors

    def assign_parameters(self, ckt_file_list):
        """
        Transfers data from the database to the component clas
        objects for the simulation.
        """
        for ckt_file_item in ckt_file_list:
            try:
                check_switch = ckt_file_item.switch_set.all().\
                        filter(comp_tag=self.tag)
            except:
                pass
            else:
                if check_switch and len(check_switch)==1:
                    comp_model = check_switch[0]
                    self.polrty = NwRdr.csv_tuple_2D(comp_model.comp_polarity)
                    self.polrty_3D = NwRdr.csv_tuple(comp_model.comp_polarity_3D)
                    self.switch_level = comp_model.comp_volt_level
                    self.control_tag = [comp_model.comp_control_tag, ]
                    self.resistor_off = self.switch_level/1.0e-6
                    self.resistor = self.resistor_off
        return



class Thyristor:
    """
    Ideal thyristor class. Contains functions to initiliaze
    the thyristor according to name tag, unique cell position,
    update system matrix on each iteration.
    """

    def __init__(self, thyristor_index, thyristor_pos, thyristor_tag, nw_input):
        """
        Constructor to initialize value.
        Also, takes in the identifiers -
        index (serial number), cell position and tag.
        """
        self.type="Thyristor"
        self.number = thyristor_index
        self.pos_3D = thyristor_pos
        self.sheet = NwRdr.csv_tuple(thyristor_pos)[0]
        self.pos = NwRdr.csv_element_2D(NwRdr.csv_tuple(thyristor_pos)[1:])
        self.tag = thyristor_tag
        self.sheet_name = nw_input[self.sheet] + ".csv"
        self.has_voltage = "yes"
        self.thyristor_level = 120.0
        self.is_meter = "no"
        self.has_control = "yes"
        self.current = 0.0
        self.voltage = 0.0
        self.polrty = [-1, -1]
        self.polrty_3D = [-1, -1, -1]
        self.resistor_on = 0.01
        self.status = "off"
        self.control_tag = ["Control"]
        self.control_values = [0.0]
        self.component_banch_pos = 0
        self.component_branch_dir = 1.0

        return

    def display(self):
        """
        Displays info about the component.
        """
        print("Thyristor is {} located at {} with negative polarity towards {} in sheet {}".format(
            self.tag, self.pos, NwRdr.csv_element_2D(self.polrty), self.sheet_name
        ))

        return

    def get_polarity(self, ckt_mat, sys_branch):
        if self.polrty==[-1, -1]:
            # Looking for a default value of polarity
            # in the neighbouring cells

            if self.thyristor_elem[0]>0:
                if ckt_mat[self.sheet][self.thyristor_elem[0]-1][self.thyristor_elem[1]]:
                    self.polrty = [self.thyristor_elem[0]-1, self.thyristor_elem[1]]
            if self.thyristor_elem[1]>0:
                if ckt_mat[self.sheet][self.thyristor_elem[0]][self.thyristor_elem[1]-1]:
                    self.polrty = [self.thyristor_elem[0], self.thyristor_elem[1]-1]

            if self.thyristor_elem[0]<len(ckt_mat[self.sheet])-1:
                if ckt_mat[self.sheet][self.thyristor_elem[0]+1][self.thyristor_elem[1]]:
                    self.polrty = [self.thyristor_elem[0]+1, self.thyristor_elem[1]]
            if self.thyristor_elem[1]<len(ckt_mat[self.sheet][0])-1:
                if ckt_mat[self.sheet][self.thyristor_elem[0]][self.thyristor_elem[1]+1]:
                    self.polrty = [self.thyristor_elem[0], self.thyristor_elem[1]+1]
        else:
            for c1 in range(len(sys_branch)):
                if NwRdr.csv_tuple(self.pos_3D) in sys_branch[c1]:
                    if not [self.sheet, self.polrty[0], self.polrty[1]] in sys_branch[c1]:
                        print()
                        print("!"*50)
                        print("ERROR!!! Thyristor polarity should be in the same branch as the thyristor. \
Check thyristor at {} in sheet {}".format(self.pos, self.sheet_name))
                        print("!"*50)
                        print()
                        raise CktEx.PolarityError

        self.polrty_3D = [self.sheet, self.polrty[0], self.polrty[1]]

        return

    def ask_values(self, x_list, ckt_mat, sys_branch):
        """
        Writes the values needed to the spreadsheet.
        """
        thyristor_params = ["Thyristor"]
        thyristor_params.append(self.tag)
        thyristor_params.append(self.pos)
        thyristor_params.append("Voltage level (V) = %f" %self.thyristor_level)

        self.thyristor_elem = NwRdr.csv_tuple_2D(self.pos)
        self.get_polarity(ckt_mat, sys_branch)

        thyristor_params.append("Negative polarity towards (cell) = %s" %NwRdr.csv_element_2D(self.polrty))
        thyristor_params.append("Name of control signal = %s" %self.control_tag[0])
        x_list.append(thyristor_params)

        return

    def export_values_to_csv(self):
        """
        Writes the values needed to the spreadsheet.
        """
        thyristor_params = ["Thyristor"]
        thyristor_params.append(self.tag)
        thyristor_params.append(self.pos)
        thyristor_params.append("Voltage level (V) = %f" %self.thyristor_level)
        thyristor_params.append("Negative polarity towards (cell) = %s" %NwRdr.csv_element_2D(self.polrty))
        thyristor_params.append("Name of control signal = %s" %self.control_tag[0])

        return thyristor_params

    def get_values(self, x_list, ckt_mat):
        """ Takes the parameter from the spreadsheet."""
        self.thyristor_level = float(x_list[0].split("=")[1])
        # Choosing 1 micro Amp as the leakage current that
        # is drawn by the thyristor in off state.
        self.resistor_off = self.thyristor_level/1.0e-6
        self.resistor = self.resistor_off

        thyristor_polrty = x_list[1].split("=")[1]

        # Convert the human readable form of cell
        # to [row, column] form
        while thyristor_polrty[0]==" ":
            thyristor_polrty = thyristor_polrty[1:]

        self.polrty = NwRdr.csv_tuple_2D(thyristor_polrty)
        self.polrty_3D = [self.sheet, self.polrty[0], self.polrty[1]]

        if not ckt_mat[self.sheet][self.polrty[0]][self.polrty[1]]:
            print("Polarity incorrect. Branch does not exist at {} in sheet {}".format(
                NwRdr.csv_element(self.polrty), self.sheet_name)
            )
            raise CktEx.PolarityError

        self.control_tag[0] = x_list[2].split("=")[1]
        while self.control_tag[0][0]==" ":
            self.control_tag[0] = self.control_tag[0][1:]

        return

    def determine_branch(self, sys_branches):
        """
        Determines which branch the component is found in.
        """
        for c1 in range(len(sys_branches)):
            if NwRdr.csv_tuple(self.pos_3D) in sys_branches[c1]:
                self.component_branch_pos = c1
                if sys_branches[c1].index(self.polrty_3D)>sys_branches[c1].index(NwRdr.csv_tuple(self.pos_3D)):
                    self.component_branch_dir = 1.0
                else:
                    self.component_branch_dir = -1.0

        return

    def transfer_to_sys(self, sys_loops, mat_e, mat_a, mat_b, mat_u, source_list):
        """
        The matrix A in E.dx/dt=Ax+Bu will be updated by the
        resistor value of the thyristor.
        """
        for c1 in range(len(sys_loops)):
            for c2 in range(c1, len(sys_loops)):
                # Updating the elements depending
                # on the sense of the loops (aiding or opposing)
                for c3 in range(len(sys_loops[c1][c2])):
                    # Check if current source position is there in the loop.
                    if NwRdr.csv_tuple(self.pos) in sys_loops[c1][c2][c3]:
                        # Add current source series resistor
                        # if branch is in forward direction
                        if sys_loops[c1][c2][c3][-1]=="forward":
                            mat_a.data[c1][c2] += self.resistor
                        else:
                            # Else subtract if branch is in reverse direction
                            mat_a.data[c1][c2] -= self.resistor
                        # Because the matrices are symmetric
                        mat_a.data[c2][c1] = mat_a.data[c1][c2]

                        # If the positive polarity appears before the voltage position
                        # it means as per KVL, we are moving from +ve to -ve
                        # and so the voltage will be taken negative
                        if sys_loops[c1][c1][c2].index(self.polrty)>sys_loops[c1][c1][c2].index(NwRdr.csv_tuple(self.pos)):
                            if sys_loops[c1][c1][c2][-1]=="forward":
                                mat_b.data[c1][source_list.index(self.pos)] = -1.0
                            else:
                                mat_b.data[c1][source_list.index(self.pos)] = 1.0
                        else:
                            if sys_loops[c1][c1][c2][-1]=="forward":
                                mat_b.data[c1][source_list.index(self.pos)] = 1.0
                            else:
                                mat_b.data[c1][source_list.index(self.pos)] = -1.0

        return

    def transfer_to_branch(self, sys_branch, source_list,  mat_u):
        """
        Update the resistor info of the thyristor
        to the branch list.
        """
        if NwRdr.csv_tuple(self.pos_3D) in sys_branch:
            sys_branch[-1][0][0] += self.resistor

        # For the thyristor forward voltage drop.
        if NwRdr.csv_tuple(self.pos_3D) in sys_branch:
            if sys_branch.index(self.polrty_3D)>sys_branch.index(NwRdr.csv_tuple(self.pos_3D)):
                sys_branch[-1][1][source_list.index(self.pos_3D)] = 0.0
            else:
                sys_branch[-1][1][source_list.index(self.pos_3D)] = 0.0

        if self.status=="on":
            mat_u.data[source_list.index(self.pos_3D)][0] = 0.0
            self.voltage = 0.0
        else:
            mat_u.data[source_list.index(self.pos_3D)][0] = 0.0
            self.voltage = 0.0

        return

    def generate_val(self, source_lst, mat_e, mat_a, mat_b, mat_u, t, dt):
        """
        The thyristor forward drop voltage is updated
        in the matrix u in E.dx/dt=Ax+Bu.
        """
        # The thyristor does not contain voltage when on.
        if self.status=="on":
            mat_u.data[source_lst.index(self.pos_3D)][0] = 0.0
            self.voltage = 0.0
        else:
            mat_u.data[source_lst.index(self.pos_3D)][0] = 0.0
            self.voltage = 0.0

        return

    def update_val_old(self, sys_loop_map, lbyr_ratio, mat_e, mat_a, mat_b, state_vec, mat_u, sys_branches, sys_events):
        """
        This function calculates the actual current in the
        thyristor branch. With this, the branch voltage is found
        with respect to the existing thyristor resistance. The thyristor
        voltage is then used to decide the turn on condition.
        """
        for c1 in range(len(sys_branches)):
            if NwRdr.csv_tuple(self.pos) in sys_branches[c1]:
                branch_pos = c1

        if sys_branches[branch_pos].index(self.polrty)>sys_branches[branch_pos].index(NwRdr.csv_tuple(self.pos)):
            self.current = sys_branches[branch_pos][-1][2]
        else:
            self.current = -sys_branches[branch_pos][-1][2]

        self.voltage = self.current*self.resistor

        # Identifying the position of the thyristor branch
        # to generate events.
        for c1 in range(len(sys_branches)):
            if NwRdr.csv_tuple(self.pos) in sys_branches[c1]:
                branch_pos = c1

        # Thyristor will turn on when it is forward biased
        # and it is gated on.
        if self.control_values[0]>=1.0 and self.voltage>1.0:
            if self.status=="off":
                sys_events[branch_pos] = "hard"
                self.status = "on"

        # Thyristor will turn off when gated off or
        # when current becomes negative.
        # If the current becomes negative, it is a soft turn off
        if self.current<0.0:
            if self.status=="on":
                sys_events[branch_pos] = "yes"
                self.status = "off"

        # If the thyristor turns off due to a gate signal
        # it is a hard turn off
        if self.control_values[0]==0.0:
            if self.status=="on":
                sys_events[branch_pos] = "hard"
                self.status = "off"

        if self.status=="off":
            self.resistor = self.resistor_off
        else:
            self.resistor = self.resistor_on

        return

    def update_val(self, sys_loop_map, lbyr_ratio, mat_e, mat_a, mat_b, state_vec, mat_u, sys_branches, sys_events):
        """
        This function calculates the actual current in the
        thyristor branch. With this, the branch voltage is found
        with respect to the existing thyristor resistance. The thyristor
        voltage is then used to decide the turn on condition.
        """
        self.thyristor_elem = NwRdr.csv_tuple_2D(self.pos)
        self.current = self.component_branch_dir*sys_branches[self.component_branch_pos][-1][2]
        self.voltage = self.current*self.resistor

        # Thyristor will turn on when it is forward biased
        # and it is gated on.
        if self.control_values[0]>=1.0 and self.voltage>1.0:
            if self.status=="off":
                sys_events[self.component_branch_pos] = "hard"
                self.status = "on"

        # Thyristor will turn off when gated off or
        # when current becomes negative.
        # If the current becomes negative, it is a soft turn off
        if self.current<0.0:
            if self.status=="on":
                sys_events[self.component_branch_pos] = "yes"
                self.status = "off"

        if self.status=="off":
            self.resistor = self.resistor_off
        else:
            self.resistor = self.resistor_on

        return

    def determine_state_old(self, br_currents, sys_branches, sys_events):
        """
        Determines the state of the thyristor following an event
        where the continuity of current through an inductor is
        about to be broken. This can only check if the thyristor should
        turn off. Turn on is only decided by the update_value method.
        """
        # Mark the position of the thyristor in sys_branches
        for c1 in range(len(sys_branches)):
            if NwRdr.csv_tuple(self.pos) in sys_branches[c1]:
                branch_pos = c1

        # If the current direction is reverse, thyristor can never conduct
        if br_currents[branch_pos]<0.0:
            if sys_branches[branch_pos].index(self.polrty)>sys_branches[branch_pos].index(NwRdr.csv_tuple(self.pos)):
                if self.status=="on":
                    sys_events[branch_pos] = "yes"
                self.status = "off"

        if br_currents[branch_pos]>0.0:
            if sys_branches[branch_pos].index(self.polrty)<sys_branches[branch_pos].index(NwRdr.csv_tuple(self.pos)):
                if self.status=="on":
                    sys_events[branch_pos] = "yes"
                self.status = "off"

        # Update the value of resistance
        if self.status=="off":
            self.resistor = self.resistor_off
        else:
            self.resistor = self.resistor_on

        return

    def pre_determine_state(self, br_currents, sys_branches, sys_events):
        """
        Determines the state of the thyristor following an event
        where the continuity of current through an inductor is
        about to be broken. This can only check if the thyristor should
        turn off. Turn on is only decided by the update_value method.
        """

        self.current = self.component_branch_dir*br_currents[self.component_branch_pos]
        self.voltage = self.current*self.resistor

        # Thyristor will turn on when it is forward biased
        # and it is gated on.
        if self.control_values[0]>=1.0 and self.voltage>1.0:
            if self.status=="off":
                sys_events[self.component_branch_pos] = "hard"
                self.status = "on"

        # Thyristor will turn off
        # when current becomes negative.
        # If the current becomes negative, it is a soft turn off
        if self.current<0.0:
            if self.status=="on":
                sys_events[self.component_branch_pos] = "yes"
                self.status = "off"

        if self.status=="off":
            self.resistor = self.resistor_off
        else:
            self.resistor = self.resistor_on

        return

    def determine_state(self, br_currents, sys_branches, sys_events):
        """
        Determines the state of the thyristor following an event
        where the continuity of current through an inductor is
        about to be broken. This can only check if the thyristor should
        turn off. Turn on is only decided by the update_value method.
        """
        # If the current direction is reverse, thyristor can never conduct
        if br_currents[self.component_branch_pos]*self.component_branch_dir<0.0:
            #if sys_branches[branch_pos].index(self.polrty)>sys_branches[branch_pos].index(NwRdr.csv_tuple(self.pos)):
            if self.status=="on":
                sys_events[self.component_branch_pos] = "yes"
            self.status = "off"

        # Update the value of resistance
        if self.status=="off":
            self.resistor = self.resistor_off
        else:
            self.resistor = self.resistor_on

        return

    def retrieve_db_model(self, sim_para_model):
        """
        This function returns the model instance object.
        """
        check_ckt = sim_para_model.circuitschematics_set.\
                    filter(ckt_file_name=self.sheet_name)
        try:
            check_thyristor = check_ckt[0].thyristor_set.\
                    filter(comp_tag=self.tag)
        except:
            return None
        else:
            if check_thyristor and len(check_thyristor)==1:
                return check_thyristor[0]

    def determine_polarity(self, branch_map, thyristor_obj):
        """
        Determines polarity of a database object
        """
        for c1 in range(len(branch_map)):
            for c2 in range(c1+1, len(branch_map)):
                for c3 in range(len(branch_map[c1][c2])):
                    if NwRdr.csv_tuple(self.pos_3D) in branch_map[c1][c2][c3]:
                        pos_in_branch = branch_map[c1][c2][c3].\
                                index(NwRdr.csv_tuple(self.pos_3D))
                        prev_element = branch_map[c1][c2][c3][pos_in_branch-1]
                        thyristor_obj.comp_polarity_3D = NwRdr.csv_element(prev_element)
                        thyristor_obj.comp_polarity = \
                                NwRdr.csv_element_2D(prev_element[1:])
        return

    def init_db_values(self, sim_para_model, ckt_file_list, branch_map):
        """
        This function creates a new database entry for a component or
        updates an existing database entry from the component class data.
        """
        comp_found = False
        check_ckt = sim_para_model.circuitschematics_set.\
                    filter(ckt_file_name=self.sheet_name)
        try:
            check_thyristor = check_ckt[0].thyristor_set.\
                    filter(comp_tag=self.tag)
        except:
            comp_found = False
        else:
            if check_thyristor and len(check_thyristor)==1:
                comp_found = True
                old_thyristor = check_thyristor[0]
                if not (self.polrty==[-1, -1]):
                    old_thyristor.comp_polarity = NwRdr.csv_element_2D(self.polrty)
                if not (self.polrty_3D==[-1, -1, -1]):
                    old_thyristor.comp_polarity_3D = NwRdr.csv_element(self.polrty_3D)
                if old_thyristor.comp_polarity_3D:
                    thyristor_old_polarity = NwRdr.csv_tuple(old_thyristor.comp_polarity_3D)
                    thyristor_new_polarity = NwRdr.csv_tuple(self.pos_3D)
                    thyristor_old_polarity[0] = thyristor_new_polarity[0]
                    old_thyristor.comp_polarity_3D = NwRdr.csv_element(thyristor_old_polarity)
                else:
                    self.determine_polarity(branch_map, old_thyristor)
                old_thyristor.comp_number = self.number
                old_thyristor.comp_pos_3D = self.pos_3D
                old_thyristor.comp_pos = self.pos
                old_thyristor.comp_sheet = self.sheet
                old_thyristor.save()
                check_ckt[0].save()
            if check_thyristor and len(check_thyristor)>1:
                comp_found = True
                for c1 in range(len(check_thyristor)-1, 0, -1):
                    check_thyristor[c1].delete()
                    check_ckt[0].save()

        if not comp_found:
            new_thyristor = models.Thyristor()
            if not (self.polrty==[-1, -1]):
                new_thyristor.comp_polarity = NwRdr.csv_element_2D(self.polrty)
            if not (self.polrty_3D==[-1, -1, -1]):
                new_thyristor.comp_polarity_3D = NwRdr.csv_element(self.polrty_3D)
            new_thyristor.comp_number = self.number
            new_thyristor.comp_pos_3D = self.pos_3D
            new_thyristor.comp_pos = self.pos
            new_thyristor.comp_sheet = self.sheet
            new_thyristor.sheet_name = self.sheet_name.split(".csv")[0]
            new_thyristor.comp_tag = self.tag
            self.determine_polarity(branch_map, new_thyristor)
            ckt_file_item = ckt_file_list.filter(ckt_file_name=self.sheet_name)
            new_thyristor.comp_ckt = ckt_file_item[0]
            new_thyristor.save()
        sim_para_model.save()

        return

    def create_form_values(self, sim_para_model, ckt_file_list, branch_map):
        """
        This function creates a new database entry for a component or
        updates an existing database entry from the component class data.
        """
        comp_found = False
        check_ckt = sim_para_model.circuitschematics_set.\
                    filter(ckt_file_name=self.sheet_name)
        try:
            check_thyristor = check_ckt[0].thyristor_set.\
                    filter(comp_tag=self.tag)
        except:
            comp_found = False
        else:
            if check_thyristor and len(check_thyristor)==1:
                comp_found = True
                old_thyristor = check_thyristor[0]
                if not (self.polrty==[-1, -1]):
                    old_thyristor.comp_polarity = NwRdr.csv_element_2D(self.polrty)
                if not (self.polrty_3D==[-1, -1, -1]):
                    old_thyristor.comp_polarity_3D = NwRdr.csv_element(self.polrty_3D)
                old_thyristor.comp_number = self.number
                old_thyristor.comp_pos_3D = self.pos_3D
                old_thyristor.comp_volt_level = self.thyristor_level
                old_thyristor.comp_pos = self.pos
                old_thyristor.comp_sheet = self.sheet
                old_thyristor.comp_control_tag = self.control_tag[0]
                old_thyristor.save()
                check_ckt[0].save()
            if check_thyristor and len(check_thyristor)>1:
                comp_found = True
                for c1 in range(len(check_thyristor)-1, 0, -1):
                    check_thyristor[c1].delete()
                    check_ckt[0].save()

        if not comp_found:
            new_thyristor = models.Thyristor()
            if not (self.polrty==[-1, -1]):
                new_thyristor.comp_polarity = NwRdr.csv_element_2D(self.polrty)
            if not (self.polrty_3D==[-1, -1, -1]):
                new_thyristor.comp_polarity_3D = NwRdr.csv_element(self.polrty_3D)
            new_thyristor.comp_number = self.number
            new_thyristor.comp_pos_3D = self.pos_3D
            new_thyristor.comp_pos = self.pos
            new_thyristor.comp_sheet = self.sheet
            new_thyristor.sheet_name = self.sheet_name.split(".csv")[0]
            new_thyristor.comp_tag = self.tag
            self.determine_polarity(branch_map, new_thyristor)
            ckt_file_item = ckt_file_list.filter(ckt_file_name=self.sheet_name)
            new_thyristor.comp_ckt = ckt_file_item[0]
            new_thyristor.save()
        sim_para_model.save()

        return

    def list_existing_components(self, ckt_file):
        """
        Check if the model of the circuit file contains
        the associated database entry for the component.
        Returns an empty list if not found.
        """
        try:
            check_thyristor = ckt_file.thyristor_set.all().\
                        filter(comp_tag=self.tag)
        except:
            comp_list = []
        else:
            if check_thyristor and len(check_thyristor)==1:
                comp_list = check_thyristor[0]
            else:
                comp_list = []
        return comp_list

    def comp_as_a_dict(self, ckt_file):
        """
        Returns information about a component as a list
        that can be displayed in a webpage.
        """
        try:
            check_thyristor = ckt_file.thyristor_set.all().\
                        filter(comp_tag=self.tag)
        except:
            comp_list = []
        else:
            if check_thyristor and len(check_thyristor)==1:
                comp_list = []
                comp_list.append(["Component type", check_thyristor[0].comp_type])
                comp_list.append(["Component name", check_thyristor[0].comp_tag])
                comp_list.append(["Component position", check_thyristor[0].comp_pos])
                comp_list.append(["Control tag", check_thyristor[0].comp_control_tag])
                comp_list.append(["Voltage level", check_thyristor[0].comp_volt_level])
                comp_list.append(["Direction of cathode", \
                        check_thyristor[0].comp_polarity])
            else:
                comp_list = []
        return comp_list

    def comp_as_a_form(self, ckt_file):
        """
        Returns a populated form for a component.
        """
        try:
            check_thyristor = ckt_file.thyristor_set.all().\
                        filter(comp_tag=self.tag)
        except:
            return []
        else:
            if check_thyristor and len(check_thyristor)==1:
                return [models.ThyristorForm, check_thyristor[0]]
                # comp_list = models.ThyristorForm(instance=check_thyristor[0])
            else:
                return []
        # return comp_list

    def save_to_db(self, ckt_file):
        """
        Returns a populated form for a component.
        """
        try:
            check_thyristor = ckt_file.thyristor_set.all().\
                        filter(comp_tag=self.tag)
        except:
            return
        else:
            if check_thyristor and len(check_thyristor)==1:
                old_thyristor = check_thyristor[0]
                if not (self.polrty==[-1, -1]):
                    old_thyristor.comp_polarity = NwRdr.csv_element_2D(self.polrty)
                if not (self.polrty_3D==[-1, -1, -1]):
                    old_thyristor.comp_polarity_3D = NwRdr.csv_element(self.polrty_3D)
                old_thyristor.comp_volt_level = self.thyristor_level
                old_thyristor.comp_control_tag = self.control_tag[0]
                old_thyristor.save()
                ckt_file.save()
                return
            else:
                return

    def update_form_data(self, request, comp_model, branch_map):
        """
        Extracts data from a form and saves it to the database.
        """
        received_form = models.ThyristorForm(request.POST)
        if received_form.is_valid():
            received_data = received_form.cleaned_data
            comp_model.comp_volt_level = received_data["comp_volt_level"]
            comp_model.comp_control_tag = received_data["comp_control_tag"]
            new_polarity = received_data["comp_polarity"]
            comp_model.comp_polarity = new_polarity
            new_polarity_3D = [comp_model.comp_sheet, ]
            new_polarity_3D.extend(NwRdr.csv_tuple_2D(new_polarity))
            comp_model.comp_polarity_3D = NwRdr.csv_element(new_polarity_3D)
            current_pos = NwRdr.csv_tuple(comp_model.comp_pos_3D)
            for c1 in range(len(branch_map)):
                for c2 in range(c1+1, len(branch_map[c1])):
                    for c3 in range(len(branch_map[c1][c2])):
                        if current_pos in branch_map[c1][c2][c3]:
                            if new_polarity_3D not in branch_map[c1][c2][c3]:
                                received_form.add_error("comp_polarity", \
                                    "Polarity has to be an element on same branch as thyristor.")
                                form_status = [received_form, ]
                            elif current_pos==new_polarity_3D:
                                received_form.add_error("comp_polarity", \
                                    "Polarity can't be the same element as the component.")
                                form_status = [received_form, ]
                            else:
                                comp_model.comp_polarity_3D = NwRdr.csv_element(new_polarity_3D)
                                comp_model.save()
                                form_status = []
        else:
            form_status = [received_form, ]
        return form_status

    def pre_run_check(self, ckt_file_item, branch_map):
        """
        This function checks for errors primarily in polarity.
        """
        comp_errors = []
        try:
            check_thyristor = ckt_file_item.thyristor_set.all().\
                        filter(comp_tag=self.tag)
        except:
            pass
        else:
            if check_thyristor and len(check_thyristor)==1:
                comp_item = check_thyristor[0]
                current_pos = NwRdr.csv_tuple(comp_item.comp_pos_3D)
                current_polarity = NwRdr.csv_tuple(comp_item.comp_polarity_3D)
                for c1 in range(len(branch_map)):
                    for c2 in range(c1+1, len(branch_map[c1])):
                        for c3 in range(len(branch_map[c1][c2])):
                            if current_pos in branch_map[c1][c2][c3]:
                                if current_polarity not in branch_map[c1][c2][c3]:
                                    comp_errors.append("Polarity has to be an element on \
                                        same branch as thyristor. Check Thyristor_" + self.tag)
                                elif current_pos==current_polarity:
                                    comp_errors.append("Polarity can't be the same element \
                                        as the component. Check Thyristor_" + self.tag)
        return comp_errors

    def assign_parameters(self, ckt_file_list):
        """
        Transfers data from the database to the component clas
        objects for the simulation.
        """
        for ckt_file_item in ckt_file_list:
            try:
                check_thyristor = ckt_file_item.thyristor_set.all().\
                        filter(comp_tag=self.tag)
            except:
                pass
            else:
                if check_thyristor and len(check_thyristor)==1:
                    comp_model = check_thyristor[0]
                    self.polrty = NwRdr.csv_tuple_2D(comp_model.comp_polarity)
                    self.polrty_3D = NwRdr.csv_tuple(comp_model.comp_polarity_3D)
                    self.thyristor_level = comp_model.comp_volt_level
                    self.control_tag = [comp_model.comp_control_tag, ]
                    self.resistor_off = self.thyristor_level/1.0e-6
                    self.resistor = self.resistor_off
        return


nonlinear_freewheel_components = ["Switch", "Diode", "Thyristor"]

component_list = {"resistor": Resistor, "inductor": Inductor, "capacitor": Capacitor, \
        "voltagesource": Voltage_Source, "ammeter": Ammeter, "voltmeter": Voltmeter, \
        "currentsource": Current_Source, "controlledvoltagesource": Controlled_Voltage_Source, \
        "diode": Diode, "switch": Switch, "variableresistor": Variable_Resistor, \
        "variableinductor": Variable_Inductor, "thyristor": Thyristor}
