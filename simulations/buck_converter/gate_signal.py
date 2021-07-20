# Switching Frequency
sw_freq = 10000.0
sw_period = 1/sw_freq

# Sampling Time Interval
dt = 1.0e-6

if t_clock > t1:
    # Control Code
    carr_signal += dt/sw_period
    carr_signal = carr_signal % 1

    # mod_signal = 0.3
    mod_signal = open_control_mod_signal

    if mod_signal > carr_signal:
        s1_gate = 1.0
    else:
        s1_gate = 0.0

    pwm_mod_signal = mod_signal
    pwm_carr_signal = carr_signal
    pwm_gate_signal = s1_gate

    t1 += dt
