import numpy as np
import matplotlib
matplotlib.use('TkAgg') 
import matplotlib.pyplot as plt


pcross_sh = np.loadtxt('./water_dimer/wham/runav_rate.txt')
pcross_wf = np.loadtxt('./water_dimer_wf/wham/runav_rate.txt')
# pcross_py = np.loadtxt('total-probability.txt')
plt.plot(pcross_sh[:, 0], pcross_sh[:, -1],  label = 'CP_shoot')
plt.plot(pcross_wf[:, 0], pcross_wf[:, -1],  label = 'CP_wf')
# plt.plot(pcross_py[:, 0], pcross_py[:, -1], label = 'CP_PyRETIS')
plt.yscale('log')
plt.legend()
plt.show()