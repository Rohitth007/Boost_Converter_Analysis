def gate_signal_func(interface_inputs, interface_outputs, interface_static, interface_time, interface_variablestore,                                 interface_events, circuit_components, pos, t_clock, sys_t_events):
	carr_signal=interface_static[pos]['carr_signal']
	t1=interface_time[pos]['t1']
	pwm_mod_signal=interface_variablestore['pwm_mod_signal'][0]
	pwm_carr_signal=interface_variablestore['pwm_carr_signal'][0]
	pwm_gate_signal=interface_variablestore['pwm_gate_signal'][0]
	open_control_mod_signal=interface_variablestore['open_control_mod_signal'][0]
	s1_gate=interface_outputs[pos]['6F0'][1][2]
	# Switching Frequency
	sw_freq = 10000.0
	sw_period = 1/sw_freq
	
	# Sampling Time Interval
	dt = 1.0e-6
	
	if t_clock > t1:
	    # Control Code
	    carr_signal += dt/sw_period
	    carr_signal = carr_signal % 1
	
	    # mod_signal = 0.7
	    mod_signal = open_control_mod_signal
	
	    if mod_signal > carr_signal:
	        s1_gate = 1.0
	    else:
	        s1_gate = 0.0
	
	    pwm_mod_signal = mod_signal
	    pwm_carr_signal = carr_signal
	    pwm_gate_signal = s1_gate
	
	    t1 += dt

	interface_events[pos] = 0

	if not interface_outputs[pos]['6F0'][1][2]==s1_gate:
		interface_events[pos] = 1

	circuit_components['6F0'].control_values[0]=s1_gate
	interface_outputs[pos]['6F0'][1][2]=s1_gate
	interface_static[pos]['carr_signal']=carr_signal
	interface_time[pos]['t1']=t1
	sys_t_events.append(t1)
	interface_variablestore['pwm_mod_signal'][0]=pwm_mod_signal
	interface_variablestore['pwm_carr_signal'][0]=pwm_carr_signal
	interface_variablestore['pwm_gate_signal'][0]=pwm_gate_signal
	interface_variablestore['open_control_mod_signal'][0]=open_control_mod_signal
	return

def open_loop_control_func(interface_inputs, interface_outputs, interface_static, interface_time, interface_variablestore,                                 interface_events, circuit_components, pos, t_clock, sys_t_events):
	mod_signal=interface_static[pos]['mod_signal']
	t1=interface_time[pos]['t1']
	pwm_mod_signal=interface_variablestore['pwm_mod_signal'][0]
	pwm_carr_signal=interface_variablestore['pwm_carr_signal'][0]
	pwm_gate_signal=interface_variablestore['pwm_gate_signal'][0]
	open_control_mod_signal=interface_variablestore['open_control_mod_signal'][0]
	# Switching Frequency
	sw_freq = 10000.0
	sw_period = 1/sw_freq
	
	if t_clock > t1:
	    # Slow Start/ Soft Start
	    mod_signal += 0.01
	    if mod_signal > 0.7:
	        mod_signal = 0.7
	
	    open_control_mod_signal = mod_signal
	
	    t1 += 4 * sw_period

	interface_events[pos] = 0

	interface_static[pos]['mod_signal']=mod_signal
	interface_time[pos]['t1']=t1
	sys_t_events.append(t1)
	interface_variablestore['pwm_mod_signal'][0]=pwm_mod_signal
	interface_variablestore['pwm_carr_signal'][0]=pwm_carr_signal
	interface_variablestore['pwm_gate_signal'][0]=pwm_gate_signal
	interface_variablestore['open_control_mod_signal'][0]=open_control_mod_signal
	return

