# Switching Frequency
sw_freq = 10000.0
sw_period = 1/sw_freq

if t_clock > t1:
    # Slow Start/ Soft Start
    mod_signal += 0.01
    if mod_signal > 0.3:
        mod_signal = 0.3

    open_control_mod_signal = mod_signal

    t1 += 2 * sw_period
