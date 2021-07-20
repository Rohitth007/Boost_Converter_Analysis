# Generated by Django 2.2.1 on 2021-05-26 09:17

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CircuitPlot',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('plot_title', models.CharField(default='Plot', max_length=100, verbose_name='Plot title')),
            ],
        ),
        migrations.CreateModel(
            name='CircuitSchematics',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ckt_file_path', models.FileField(blank=True, max_length=300, upload_to='', verbose_name='Circuit file path')),
                ('ckt_file_descrip', models.CharField(default='Sample circuit', max_length=100, verbose_name='Schematic description')),
                ('ckt_file_name', models.CharField(max_length=300)),
            ],
            options={
                'ordering': ['ckt_file_name'],
            },
        ),
        migrations.CreateModel(
            name='ControlFile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('control_file', models.FileField(blank=True, max_length=300, upload_to='')),
                ('control_file_name', models.CharField(max_length=300)),
                ('control_file_descrip', models.TextField(blank=True, null=True, verbose_name='Control description')),
            ],
            options={
                'ordering': ['control_file_name'],
            },
        ),
        migrations.CreateModel(
            name='SimulationCase',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sim_title', models.CharField(default='Test case', max_length=100, verbose_name='Simulation Title')),
                ('sim_descrip', models.TextField(blank=True, null=True, verbose_name='Simulation description')),
                ('sim_time_limit', models.FloatField(default=1.0, verbose_name='Time duration')),
                ('sim_time_step', models.FloatField(default=1e-06, verbose_name='Integration time step')),
                ('sim_time_data', models.FloatField(default=1e-05, verbose_name='Time step of data storage')),
                ('sim_output_file', models.CharField(default='ckt_output.dat', max_length=30, verbose_name='Output data file')),
                ('sim_output_slice', models.CharField(choices=[('Yes', 'Yes'), ('No', 'No')], default='No', max_length=3, verbose_name='Slice the output file?')),
                ('sim_div_number', models.IntegerField(default=1, verbose_name='Number of slices')),
                ('sim_working_directory', models.CharField(max_length=300, verbose_name='Directory with circuit files')),
            ],
        ),
        migrations.CreateModel(
            name='Voltmeter',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('comp_type', models.CharField(default='Voltmeter', max_length=100, verbose_name='Component type')),
                ('comp_number', models.IntegerField()),
                ('comp_pos_3D', models.CharField(max_length=50, verbose_name='Component position')),
                ('comp_pos', models.CharField(max_length=50, verbose_name='Component position')),
                ('comp_sheet', models.IntegerField()),
                ('sheet_name', models.CharField(max_length=200, verbose_name='Found in circuit schematic')),
                ('comp_tag', models.CharField(max_length=100, verbose_name='Component name')),
                ('comp_polarity_3D', models.CharField(max_length=50, verbose_name='Positive polarity towards')),
                ('comp_polarity', models.CharField(max_length=50, verbose_name='Positive polarity towards')),
                ('comp_volt_level', models.FloatField(default=120.0, verbose_name='Rated voltage level to be measured')),
                ('comp_has_voltage', models.BooleanField(default=False, max_length=5)),
                ('comp_is_meter', models.BooleanField(default=True, max_length=5)),
                ('comp_has_control', models.BooleanField(default=False, max_length=5)),
                ('comp_ckt', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='simulations.CircuitSchematics')),
            ],
        ),
        migrations.CreateModel(
            name='Voltage_Source',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('comp_type', models.CharField(default='VoltageSource', max_length=100, verbose_name='Component type')),
                ('comp_number', models.IntegerField()),
                ('comp_pos_3D', models.CharField(max_length=50, verbose_name='Component position')),
                ('comp_pos', models.CharField(max_length=50, verbose_name='Component position')),
                ('comp_sheet', models.IntegerField()),
                ('sheet_name', models.CharField(max_length=200, verbose_name='Found in circuit schematic')),
                ('comp_tag', models.CharField(max_length=100, verbose_name='Component name')),
                ('comp_polarity_3D', models.CharField(max_length=50, verbose_name='Positive polarity towards')),
                ('comp_polarity', models.CharField(max_length=50, verbose_name='Positive polarity towards')),
                ('comp_has_voltage', models.BooleanField(default=True, max_length=5)),
                ('comp_is_meter', models.BooleanField(default=False, max_length=5)),
                ('comp_has_control', models.BooleanField(default=False, max_length=5)),
                ('comp_volt_peak', models.FloatField(default=120.0, verbose_name='Peak voltage')),
                ('comp_volt_freq', models.FloatField(default=60.0, verbose_name='Voltage frequency')),
                ('comp_volt_phase', models.FloatField(default=0.0, verbose_name='Phase angle (degrees)')),
                ('comp_volt_offset', models.FloatField(default=0.0, verbose_name='Dc offset')),
                ('comp_ckt', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='simulations.CircuitSchematics')),
            ],
        ),
        migrations.CreateModel(
            name='VariableResistor',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('comp_type', models.CharField(default='VariableResistor', max_length=100, verbose_name='Component type')),
                ('comp_number', models.IntegerField()),
                ('comp_pos_3D', models.CharField(max_length=50, verbose_name='Component position')),
                ('comp_pos', models.CharField(max_length=50, verbose_name='Component position')),
                ('comp_sheet', models.IntegerField()),
                ('sheet_name', models.CharField(max_length=200, verbose_name='Found in circuit schematic')),
                ('comp_tag', models.CharField(max_length=100, verbose_name='Component name')),
                ('comp_control_tag', models.CharField(default='Resistance', max_length=50, verbose_name='Control tag')),
                ('comp_control_value', models.FloatField(default=100.0, verbose_name='Controlled resistance')),
                ('comp_has_voltage', models.BooleanField(default=False, max_length=5)),
                ('comp_is_meter', models.BooleanField(default=False, max_length=5)),
                ('comp_has_control', models.BooleanField(default=True, max_length=5)),
                ('comp_resistor', models.FloatField(default=100.0, verbose_name='Initial resistor value')),
                ('comp_ckt', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='simulations.CircuitSchematics')),
            ],
        ),
        migrations.CreateModel(
            name='VariableInductor',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('comp_type', models.CharField(default='VariableInductor', max_length=100, verbose_name='Component type')),
                ('comp_number', models.IntegerField()),
                ('comp_pos_3D', models.CharField(max_length=50, verbose_name='Component position')),
                ('comp_pos', models.CharField(max_length=50, verbose_name='Component position')),
                ('comp_sheet', models.IntegerField()),
                ('sheet_name', models.CharField(max_length=200, verbose_name='Found in circuit schematic')),
                ('comp_tag', models.CharField(max_length=100, verbose_name='Component name')),
                ('comp_control_tag', models.CharField(default='Inductance', max_length=50, verbose_name='Control tag')),
                ('comp_control_value', models.FloatField(default=0.001, verbose_name='Controlled inductance')),
                ('comp_has_voltage', models.BooleanField(default=False, max_length=5)),
                ('comp_is_meter', models.BooleanField(default=False, max_length=5)),
                ('comp_has_control', models.BooleanField(default=True, max_length=5)),
                ('comp_inductor', models.FloatField(default=0.001, verbose_name='Initial inductor value')),
                ('comp_ckt', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='simulations.CircuitSchematics')),
            ],
        ),
        migrations.CreateModel(
            name='Thyristor',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('comp_type', models.CharField(default='Thyristor', max_length=100, verbose_name='Component type')),
                ('comp_number', models.IntegerField()),
                ('comp_pos_3D', models.CharField(max_length=50, verbose_name='Component position')),
                ('comp_pos', models.CharField(max_length=50, verbose_name='Component position')),
                ('comp_sheet', models.IntegerField()),
                ('sheet_name', models.CharField(max_length=200, verbose_name='Found in circuit schematic')),
                ('comp_tag', models.CharField(max_length=100, verbose_name='Component name')),
                ('comp_polarity_3D', models.CharField(max_length=50, verbose_name='Negative polarity towards')),
                ('comp_polarity', models.CharField(max_length=50, verbose_name='Negative polarity towards')),
                ('comp_control_tag', models.CharField(default='Gate', max_length=50, verbose_name='Control tag')),
                ('comp_control_value', models.FloatField(default=0.0, verbose_name='Gate signal')),
                ('comp_volt_level', models.FloatField(default=120.0, verbose_name='Rated voltage level')),
                ('comp_has_voltage', models.BooleanField(default=True, max_length=5)),
                ('comp_is_meter', models.BooleanField(default=False, max_length=5)),
                ('comp_has_control', models.BooleanField(default=True, max_length=5)),
                ('comp_ckt', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='simulations.CircuitSchematics')),
            ],
        ),
        migrations.CreateModel(
            name='Switch',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('comp_type', models.CharField(default='Switch', max_length=100, verbose_name='Component type')),
                ('comp_number', models.IntegerField()),
                ('comp_pos_3D', models.CharField(max_length=50, verbose_name='Component position')),
                ('comp_pos', models.CharField(max_length=50, verbose_name='Component position')),
                ('comp_sheet', models.IntegerField()),
                ('sheet_name', models.CharField(max_length=200, verbose_name='Found in circuit schematic')),
                ('comp_tag', models.CharField(max_length=100, verbose_name='Component name')),
                ('comp_polarity_3D', models.CharField(max_length=50, verbose_name='Negative polarity towards')),
                ('comp_polarity', models.CharField(max_length=50, verbose_name='Negative polarity towards')),
                ('comp_control_tag', models.CharField(default='Gate', max_length=50, verbose_name='Control tag')),
                ('comp_control_value', models.FloatField(default=0.0, verbose_name='Gate signal')),
                ('comp_volt_level', models.FloatField(default=120.0, verbose_name='Rated voltage level')),
                ('comp_has_voltage', models.BooleanField(default=True, max_length=5)),
                ('comp_is_meter', models.BooleanField(default=False, max_length=5)),
                ('comp_has_control', models.BooleanField(default=True, max_length=5)),
                ('comp_ckt', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='simulations.CircuitSchematics')),
            ],
        ),
        migrations.CreateModel(
            name='Resistor',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('comp_type', models.CharField(default='Resistor', max_length=100, verbose_name='Component type')),
                ('comp_number', models.IntegerField()),
                ('comp_pos_3D', models.CharField(max_length=50, verbose_name='Component position')),
                ('comp_pos', models.CharField(max_length=50, verbose_name='Component position')),
                ('comp_sheet', models.IntegerField()),
                ('sheet_name', models.CharField(max_length=200, verbose_name='Found in circuit schematic')),
                ('comp_tag', models.CharField(max_length=100, verbose_name='Component name')),
                ('comp_has_voltage', models.BooleanField(default=False, max_length=5)),
                ('comp_is_meter', models.BooleanField(default=False, max_length=5)),
                ('comp_has_control', models.BooleanField(default=False, max_length=5)),
                ('comp_resistor', models.FloatField(default=100.0, verbose_name='Resistor value')),
                ('comp_ckt', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='simulations.CircuitSchematics')),
            ],
        ),
        migrations.CreateModel(
            name='PlotLines',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('line_name', models.CharField(max_length=50, verbose_name='Waveform source')),
                ('line_type', models.CharField(choices=[('M', 'Model'), ('V', 'VariableStorage')], default='M', max_length=1)),
                ('line_pos', models.IntegerField()),
                ('sim_case', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='simulations.SimulationCase')),
            ],
            options={
                'ordering': ['line_name'],
            },
        ),
        migrations.CreateModel(
            name='MeterComponents',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ckt_file_name', models.CharField(max_length=100)),
                ('comp_pos_3D', models.CharField(max_length=50)),
                ('comp_tag', models.CharField(max_length=100)),
                ('comp_type', models.CharField(max_length=25)),
                ('comp_name', models.CharField(max_length=100)),
                ('sim_case', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='simulations.SimulationCase')),
            ],
            options={
                'ordering': ['comp_type', 'comp_tag'],
            },
        ),
        migrations.CreateModel(
            name='Inductor',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('comp_type', models.CharField(default='Inductor', max_length=100, verbose_name='Component type')),
                ('comp_number', models.IntegerField()),
                ('comp_pos_3D', models.CharField(max_length=50, verbose_name='Component position')),
                ('comp_pos', models.CharField(max_length=50, verbose_name='Component position')),
                ('comp_sheet', models.IntegerField()),
                ('sheet_name', models.CharField(max_length=200, verbose_name='Found in circuit schematic')),
                ('comp_tag', models.CharField(max_length=100, verbose_name='Component name')),
                ('comp_has_voltage', models.BooleanField(default=False, max_length=5)),
                ('comp_is_meter', models.BooleanField(default=False, max_length=5)),
                ('comp_has_control', models.BooleanField(default=False, max_length=5)),
                ('comp_inductor', models.FloatField(default=0.001, verbose_name='Inductor value')),
                ('comp_ckt', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='simulations.CircuitSchematics')),
            ],
        ),
        migrations.CreateModel(
            name='Diode',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('comp_type', models.CharField(default='Diode', max_length=100, verbose_name='Component type')),
                ('comp_number', models.IntegerField()),
                ('comp_pos_3D', models.CharField(max_length=50, verbose_name='Component position')),
                ('comp_pos', models.CharField(max_length=50, verbose_name='Component position')),
                ('comp_sheet', models.IntegerField()),
                ('sheet_name', models.CharField(max_length=200, verbose_name='Found in circuit schematic')),
                ('comp_tag', models.CharField(max_length=100, verbose_name='Component name')),
                ('comp_polarity_3D', models.CharField(max_length=50, verbose_name='Cathode polarity towards')),
                ('comp_polarity', models.CharField(max_length=50, verbose_name='Cathode polarity towards')),
                ('comp_volt_level', models.FloatField(default=120.0, verbose_name='Rated voltage level')),
                ('comp_has_voltage', models.BooleanField(default=True, max_length=5)),
                ('comp_is_meter', models.BooleanField(default=False, max_length=5)),
                ('comp_has_control', models.BooleanField(default=False, max_length=5)),
                ('comp_ckt', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='simulations.CircuitSchematics')),
            ],
        ),
        migrations.CreateModel(
            name='ControlVariableStorage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('variable_storage_name', models.CharField(max_length=100, verbose_name='Desired variable name in control code')),
                ('storage_initial_value', models.FloatField(verbose_name='Initial value of variable')),
                ('storage_status', models.CharField(choices=[('Y', 'Yes'), ('N', 'No')], default='N', max_length=1)),
                ('control_file_name', models.CharField(max_length=100, verbose_name='Name of control file')),
                ('sim_case', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='simulations.SimulationCase')),
            ],
        ),
        migrations.CreateModel(
            name='ControlTimeEvent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('time_event_name', models.CharField(max_length=25, verbose_name='Name of time event variable')),
                ('initial_time_value', models.FloatField(verbose_name='Initial time event')),
                ('control_file', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='simulations.ControlFile')),
            ],
        ),
        migrations.CreateModel(
            name='ControlStaticVariable',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('static_variable_name', models.CharField(max_length=100, verbose_name='Desired variable name in control code')),
                ('static_initial_value', models.FloatField(default=0.0, verbose_name='Initial value of output')),
                ('control_file', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='simulations.ControlFile')),
            ],
        ),
        migrations.CreateModel(
            name='ControlOutputs',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('output_target', models.CharField(max_length=100, verbose_name='Name of controlled component')),
                ('output_variable_name', models.CharField(max_length=100, verbose_name='Desired variable name in control code')),
                ('output_initial_value', models.FloatField(verbose_name='Initial value of output')),
                ('control_file', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='simulations.ControlFile')),
            ],
        ),
        migrations.CreateModel(
            name='Controlled_Voltage_Source',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('comp_type', models.CharField(default='ControlledVoltageSource', max_length=100, verbose_name='Component type')),
                ('comp_number', models.IntegerField()),
                ('comp_pos_3D', models.CharField(max_length=50, verbose_name='Component position')),
                ('comp_pos', models.CharField(max_length=50, verbose_name='Component position')),
                ('comp_sheet', models.IntegerField()),
                ('sheet_name', models.CharField(max_length=200, verbose_name='Found in circuit schematic')),
                ('comp_tag', models.CharField(max_length=100, verbose_name='Component name')),
                ('comp_control_tag', models.CharField(default='Voltage', max_length=50, verbose_name='Control tag')),
                ('comp_control_value', models.FloatField(default=0.0, verbose_name='Controlled Voltage')),
                ('comp_polarity_3D', models.CharField(max_length=50, verbose_name='Positive polarity towards')),
                ('comp_polarity', models.CharField(max_length=50, verbose_name='Positive polarity towards')),
                ('comp_has_voltage', models.BooleanField(default=True, max_length=5)),
                ('comp_is_meter', models.BooleanField(default=False, max_length=5)),
                ('comp_has_control', models.BooleanField(default=True, max_length=5)),
                ('comp_voltage', models.FloatField(default=0.0, verbose_name='Initial voltage')),
                ('comp_ckt', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='simulations.CircuitSchematics')),
            ],
        ),
        migrations.CreateModel(
            name='ControllableComponents',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ckt_file_name', models.CharField(max_length=100)),
                ('comp_pos_3D', models.CharField(max_length=50)),
                ('comp_tag', models.CharField(max_length=100)),
                ('comp_type', models.CharField(max_length=25)),
                ('comp_name', models.CharField(max_length=100)),
                ('control_tag', models.CharField(max_length=100)),
                ('sim_case', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='simulations.SimulationCase')),
            ],
            options={
                'ordering': ['comp_type', 'comp_tag'],
            },
        ),
        migrations.CreateModel(
            name='ControlInputs',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('input_source', models.CharField(max_length=100, verbose_name='Name of meter')),
                ('input_variable_name', models.CharField(max_length=100, verbose_name='Desired variable name in control code')),
                ('control_file', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='simulations.ControlFile')),
            ],
        ),
        migrations.AddField(
            model_name='controlfile',
            name='sim_case',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='simulations.SimulationCase'),
        ),
        migrations.CreateModel(
            name='CircuitWaveforms',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('waveform_legend', models.CharField(blank=True, max_length=20, null=True)),
                ('waveform_scale', models.FloatField(default=1.0, verbose_name='Scaling Factor')),
                ('circuit_plot', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='simulations.CircuitPlot')),
                ('waveform', models.ManyToManyField(to='simulations.PlotLines')),
            ],
        ),
        migrations.AddField(
            model_name='circuitschematics',
            name='ckt_sim_case',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='simulations.SimulationCase'),
        ),
        migrations.AddField(
            model_name='circuitplot',
            name='sim_case',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='simulations.SimulationCase'),
        ),
        migrations.CreateModel(
            name='CircuitComponents',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('comp_type', models.CharField(max_length=100)),
                ('comp_number', models.IntegerField()),
                ('comp_pos_3D', models.CharField(max_length=50)),
                ('comp_pos', models.CharField(max_length=50)),
                ('comp_sheet', models.IntegerField()),
                ('sheet_name', models.CharField(max_length=200)),
                ('comp_tag', models.CharField(max_length=100)),
                ('sim_case', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='simulations.SimulationCase')),
            ],
            options={
                'ordering': ['comp_type', 'comp_tag'],
            },
        ),
        migrations.CreateModel(
            name='Capacitor',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('comp_type', models.CharField(default='Capacitor', max_length=100, verbose_name='Component type')),
                ('comp_number', models.IntegerField()),
                ('comp_pos_3D', models.CharField(max_length=50, verbose_name='Component position')),
                ('comp_pos', models.CharField(max_length=50, verbose_name='Component position')),
                ('comp_sheet', models.IntegerField()),
                ('sheet_name', models.CharField(max_length=200, verbose_name='Found in circuit schematic')),
                ('comp_tag', models.CharField(max_length=100, verbose_name='Component name')),
                ('comp_polarity_3D', models.CharField(max_length=50, verbose_name='Positive polarity towards')),
                ('comp_polarity', models.CharField(max_length=50, verbose_name='Positive polarity towards')),
                ('comp_has_voltage', models.BooleanField(default=True, max_length=5)),
                ('comp_is_meter', models.BooleanField(default=False, max_length=5)),
                ('comp_has_control', models.BooleanField(default=False, max_length=5)),
                ('comp_capacitor', models.FloatField(default=1e-05, verbose_name='Capacitor value')),
                ('comp_ckt', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='simulations.CircuitSchematics')),
            ],
        ),
        migrations.CreateModel(
            name='Ammeter',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('comp_type', models.CharField(default='Ammeter', max_length=100, verbose_name='Component type')),
                ('comp_number', models.IntegerField()),
                ('comp_pos_3D', models.CharField(max_length=50, verbose_name='Component position')),
                ('comp_pos', models.CharField(max_length=50, verbose_name='Component position')),
                ('comp_sheet', models.IntegerField()),
                ('sheet_name', models.CharField(max_length=200, verbose_name='Found in circuit schematic')),
                ('comp_tag', models.CharField(max_length=100, verbose_name='Component name')),
                ('comp_polarity_3D', models.CharField(max_length=50, verbose_name='Positive polarity towards')),
                ('comp_polarity', models.CharField(max_length=50, verbose_name='Positive polarity towards')),
                ('comp_has_voltage', models.BooleanField(default=False, max_length=5)),
                ('comp_is_meter', models.BooleanField(default=True, max_length=5)),
                ('comp_has_control', models.BooleanField(default=False, max_length=5)),
                ('comp_ckt', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='simulations.CircuitSchematics')),
            ],
        ),
    ]
