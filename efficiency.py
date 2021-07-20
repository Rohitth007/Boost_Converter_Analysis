import streamlit as st

import matplotlib.pyplot as plt
import numpy as np
from math import sqrt

st.title('Boost Converter Analysis')
choice = st.radio('Select:', ('CCM-DCM Transition', 'CCM Efficiency'))

if choice == 'CCM-DCM Transition':
    '## CCM-DCM Transition'
    'Critical Current = $\\frac{VoD(1-D)^2}{2LT_s}$'
    'If you go below critical current, boost is higher for same D and vice-versa'
    '---'

    '### Duty Cycle vs Load Current'
    Vin = st.sidebar.slider("Vin:", 1, 100, 12)
    Vo = st.sidebar.slider("Vout:", Vin, 10*Vin, 2*Vin)
    L = st.sidebar.slider("Inductance:(μH)", 1, 5000, 500) * 0.000001
    T = st.sidebar.slider("Switching Period:(μs)", 10, 100, 100) * 0.000001

    D = np.linspace(0, 1, num=50, endpoint=False)
    I_b = (Vo*D*T*(1-D)**2) / (2*L)
    plt.plot(I_b, D)
    plt.xlabel('Current')
    plt.ylabel('D')
    plt.fill_between(I_b, D, alpha=0.2)

    M = Vo/Vin
    d = 1 - 1/M
    I_crit = (Vo*d*(1-d)**2*T) / (2*L)
    I = np.linspace(0, 2*I_crit, num=100)
    D = []
    for i in I:
        if i > I_crit:
            D.append(d)
        else:
            D.append(sqrt(2*L*i*((2*M-1)**2 - 1) / (4*Vo*T)))
    plt.plot(I, D)

    st.pyplot()
    '### Legend'
    '**Blue**: Critical Current Line'
    '**Blue Shaded**: DCM Mode'
    '**Unshaded**: CCM Mode'
    '**Orange**: Constant $\\frac{V_{out}}{V_{in}}$ Line'
    '---'
    'For Buck Converter the graph is simpler'


elif choice == 'CCM Efficiency':
    '## CCM Efficiency'
    'Can\'t achieve Infinite Boost!'
    'Efficiency calculated in CCM mode by using the small ripple approximation.'
    '### $\eta = \\frac{1}{1 + \\frac{R_{l} + (1-D)R_{d} + DR_{sw}}{R(1-D)^2}}$'
    '### $\\frac{V_{out}}{V_{in}} = \\frac{\eta}{1-D}$'
    '---'

    R_l = st.sidebar.slider("Inductive Resistance:", 0.00, 1.00, 0.1)
    R = st.sidebar.slider("Load Resistance:", 0, 100, 10)
    R_d = st.sidebar.slider("Diode Resistance:", 0.00, 1.00, 0.1)
    R_sw = st.sidebar.slider("Switch On Resistance:", 0.00, 1.00, 0.01)

    concat = st.sidebar.slider("Concatenate Boost Converters", 0, 10, 1)

    '### $\\frac{V_{out}}{V_{in}}$ vs Duty Ratio'
    D = np.linspace(0, 1, num=50, endpoint=False)
    M = (1 / ((1 - D)*(1 + (R_l + (1-D)*R_d + D*R_sw)/(R*(1-D)**2))))**concat
    plt.plot(D, M)
    plt.ylabel('M')
    plt.xlabel('D')
    st.pyplot()
    '---'

    '### Efficiency vs Duty Ratio'
    D = np.linspace(0, 1, num=50, endpoint=False)
    eta = 100 * (1 / (1 + (R_l + (1-D)*R_d + D*R_sw)/(R*(1-D)**2)))**concat
    plt.plot(D, eta)
    plt.ylabel('Efficiency')
    plt.xlabel('D')
    st.pyplot()
    '---'
