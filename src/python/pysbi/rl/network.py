from brian.clock import defaultclock
from brian.stdunits import ms
from brian.units import second
import numpy as np
from pysbi.wta.network import default_params, run_wta

def run_rl_simulation():
    wta_params=default_params
    num_groups=2
    exp_rew=np.array([0.5, 0.5])
    trial_duration=3*second
    background_freq=5
    alpha=0.4

    trials=200
    prob_walk=np.array([[0.4197, 0.3703, 0.3990, 0.4112, 0.4055, 0.3905, 0.3677, 0.3618, 0.3947, 0.4318, 0.4761, 0.5465, 0.6117,
                0.6469, 0.6927, 0.6940, 0.6212, 0.5137, 0.3800, 0.2323, 0.1533, 0.1628, 0.1857, 0.2473, 0.3139, 0.3746,
                0.4496, 0.5419, 0.6458, 0.7450, 0.8435, 0.8676, 0.8896, 0.8790, 0.8272, 0.7818, 0.7464, 0.6754, 0.6470,
                0.6379, 0.6003, 0.5610, 0.5746, 0.5189, 0.4720, 0.4533, 0.4873, 0.4451, 0.4328, 0.4388, 0.4756, 0.4896,
                0.5283, 0.5667, 0.6192, 0.6385, 0.6159, 0.5686, 0.5466, 0.4635, 0.3701, 0.3665, 0.4218, 0.4855, 0.5891,
                0.6723, 0.6486, 0.6271, 0.6058, 0.5674, 0.6251, 0.7356, 0.8164, 0.8306, 0.8359, 0.7510, 0.6455, 0.5328,
                0.4391, 0.3050, 0.2469, 0.1969, 0.1527, 0.1887, 0.2810, 0.3332, 0.3458, 0.3526, 0.3109, 0.2091, 0.0981,
                0.0540, 0.0696, 0.1009, 0.2128, 0.2844, 0.3522, 0.3808, 0.4227, 0.6350, 0.6350, 0.4227, 0.3808, 0.3522,
                0.2844, 0.2128, 0.1009, 0.0696, 0.0540, 0.0981, 0.2091, 0.3109, 0.3526, 0.3458, 0.3332, 0.2810, 0.1887,
                0.1527, 0.1969, 0.2469, 0.3050, 0.4391, 0.5328, 0.6455, 0.7510, 0.8359, 0.8306, 0.8164, 0.7356, 0.6251,
                0.5674, 0.6058, 0.6271, 0.6486, 0.6723, 0.5891, 0.4855, 0.4218, 0.3665, 0.3701, 0.4635, 0.5466, 0.5686,
                0.6159, 0.6385, 0.6192, 0.5667, 0.5283, 0.4896, 0.4756, 0.4388, 0.4328, 0.4451, 0.4873, 0.4533, 0.4720,
                0.5189, 0.5746, 0.5610, 0.6003, 0.6379, 0.6470, 0.6754, 0.7464, 0.7818, 0.8272, 0.8790, 0.8896, 0.8676,
                0.8435, 0.7450, 0.6458, 0.5419, 0.4496, 0.3746, 0.3139, 0.2473, 0.1857, 0.1628, 0.1533, 0.2323, 0.3800,
                0.5137, 0.6212, 0.6940, 0.6927, 0.6469, 0.6117, 0.5465, 0.4761, 0.4318, 0.3947, 0.3618, 0.3677, 0.3905,
                0.4055, 0.4112, 0.3990, 0.3703, 0.4197],
               [0.4264, 0.4323, 0.4482, 0.4994, 0.5490, 0.6017, 0.5782, 0.5907, 0.6173, 0.6329, 0.6293, 0.7235, 0.7433,
                0.7308, 0.7008, 0.6365, 0.5682, 0.5570, 0.5564, 0.5362, 0.5618, 0.5483, 0.4979, 0.4382, 0.4543, 0.4369,
                0.4291, 0.4370, 0.4373, 0.3139, 0.2655, 0.2213, 0.1867, 0.1790, 0.2068, 0.2487, 0.3319, 0.4194, 0.4890,
                0.5745, 0.6040, 0.5711, 0.5138, 0.4818, 0.4405, 0.3866, 0.3055, 0.2788, 0.3075, 0.3354, 0.3940, 0.5144,
                0.6042, 0.6508, 0.6947, 0.7392, 0.7785, 0.8159, 0.8189, 0.8548, 0.8364, 0.7897, 0.7165, 0.6266, 0.5157,
                0.4703, 0.4483, 0.4441, 0.4433, 0.4616, 0.4569, 0.4534, 0.4687, 0.5270, 0.6394, 0.6988, 0.7017, 0.7671,
                0.7969, 0.7755, 0.8377, 0.9301, 0.9492, 0.9195, 0.8628, 0.7883, 0.7186, 0.6153, 0.5695, 0.5842, 0.5788,
                0.6028, 0.5895, 0.5516, 0.4788, 0.4324, 0.3825, 0.4052, 0.4731, 0.4356, 0.4356, 0.4731, 0.4052, 0.3825,
                0.4324, 0.4788, 0.5516, 0.5895, 0.6028, 0.5788, 0.5842, 0.5695, 0.6153, 0.7186, 0.7883, 0.8628, 0.9195,
                0.9492, 0.9301, 0.8377, 0.7755, 0.7969, 0.7671, 0.7017, 0.6988, 0.6394, 0.5270, 0.4687, 0.4534, 0.4569,
                0.4616, 0.4433, 0.4441, 0.4483, 0.4703, 0.5157, 0.6266, 0.7165, 0.7897, 0.8364, 0.8548, 0.8189, 0.8159,
                0.7785, 0.7392, 0.6947, 0.6508, 0.6042, 0.5144, 0.3940, 0.3354, 0.3075, 0.2788, 0.3055, 0.3866, 0.4405,
                0.4818, 0.5138, 0.5711, 0.6040, 0.5745, 0.4890, 0.4194, 0.3319, 0.2487, 0.2068, 0.1790, 0.1867, 0.2213,
                0.2655, 0.3139, 0.4373, 0.4370, 0.4291, 0.4369, 0.4543, 0.4382, 0.4979, 0.5483, 0.5618, 0.5362, 0.5564,
                0.5570, 0.5682, 0.6365, 0.7008, 0.7308, 0.7433, 0.7235, 0.6293, 0.6329, 0.6173, 0.5907, 0.5782, 0.6017,
                0.5490, 0.4994, 0.4482, 0.4323, 0.4264]])
    mags=np.array([[0.7400, 0.0900, 0.6800, 0.7500, 0.2300, 0.7000, 0.7400, 0.9100, 0.9700, 0.8200, 0.4900, 0.0200, 0.7700,
           0.4700, 0.9100, 0.1100, 0.1700, 0.5600, 0.6800, 1.0000, 0.5900, 0.9500, 0.7000, 0.2700, 0.3300, 0.1200,
           0.7800, 0.6500, 0.7800, 0.2900, 0.4400, 0.3700, 0.9100, 0.3500, 0.6200, 0.6000, 0.5100, 0.5500, 0.4400,
           0.5500, 0.5400, 0.4800, 0.6000, 0.6200, 0.6800, 0.4700, 0.5700, 0.6000, 0.6500, 0.5200, 0.6900, 0.5400,
           0.5000, 0.6100, 0.5000, 0.7100, 0.5100, 0.6500, 0.6300, 0.8800, 0.9700, 0.8800, 0.5400, 0.6700, 0.5400,
           0.4800, 0.6300, 0.5800, 0.5900, 0.5200, 0.6400, 0.6000, 0.6800, 0.5900, 0.5400, 0.5000, 0.5500, 0.4700,
           0.6400, 0.8400, 0.9400, 1.0200, 1.0600, 0.8300, 0.9300, 0.8100, 0.7800, 0.7900, 0.8000, 0.8800, 0.9500,
           1.0000, 0.9300, 1.0400, 0.8300, 0.9100, 0.7000, 0.6200, 0.7300, 0.5000, 0.5000, 0.7300, 0.6200, 0.7000,
           0.9100, 0.8300, 1.0400, 0.9300, 1.0000, 0.9500, 0.8800, 0.8000, 0.7900, 0.7800, 0.8100, 0.9300, 0.8300,
           1.0600, 1.0200, 0.9400, 0.8400, 0.6400, 0.4700, 0.5500, 0.5000, 0.5400, 0.5900, 0.6800, 0.6000, 0.6400,
           0.5200, 0.5900, 0.5800, 0.6300, 0.4800, 0.5400, 0.6700, 0.5400, 0.8800, 0.9700, 0.8800, 0.6300, 0.6500,
           0.5100, 0.7100, 0.5000, 0.6100, 0.5000, 0.5400, 0.6900, 0.5200, 0.6500, 0.6000, 0.5700, 0.4700, 0.6800,
           0.6200, 0.6000, 0.4800, 0.5400, 0.5500, 0.4400, 0.5500, 0.5100, 0.6000, 0.6200, 0.3500, 0.9100, 0.3700,
           0.4400, 0.2900, 0.7800, 0.6500, 0.7800, 0.1200, 0.3300, 0.2700, 0.7000, 0.9500, 0.5900, 1.0000, 0.6800,
           0.5600, 0.1700, 0.1100, 0.9100, 0.4700, 0.7700, 0.0200, 0.4900, 0.8200, 0.9700, 0.9100, 0.7400, 0.7000,
           0.2300, 0.7500, 0.6800, 0.0900, 0.7400],
          [ 1.1000, 0.7500, 0.8500, 0.3500, 0.4000, 0.6800, 0.0800, 0.9200, 0.5300, 0.7900, 0.1600, 1.0400, 0.4000,
            0.8500, 0.6300, 1.0800, 0.1400, 0.5900, 0.2800, 0.2500, 0.0700, 0.4800, 0.5400, 0.4400, 0.5900, 0.3000,
            0.9800, 0.8500, 0.8100, 0.4600, 0.9900, 0.9300, 0.2200, 0.9500, 1.0300, 0.8600, 0.7700, 0.6700, 0.6800,
            0.5400, 0.6800, 0.5500, 0.5400, 0.3600, 0.6700, 0.5500, 0.9500, 0.9700, 0.8900, 0.6700, 0.6100, 0.4600,
            0.4900, 0.5300, 0.6900, 0.6100, 0.7000, 0.4700, 0.4900, 0.4800, 0.5600, 0.5300, 0.5500, 0.4800, 0.5700,
            0.7000, 0.6900, 0.6500, 0.6200, 0.6800, 0.7300, 0.7600, 0.5700, 0.6200, 0.8300, 0.6500, 0.5600, 0.6100,
            0.5700, 0.6300, 0.6700, 0.5900, 0.2900, 0.3200, 0.4300, 0.3900, 0.6000, 0.5800, 0.5500, 0.3700, 0.3600,
            0.3400, 0.4800, 0.6700, 0.6600, 0.5800, 0.6400, 0.6000, 0.5200, 0.7100, 0.7100, 0.5200, 0.6000, 0.6400,
            0.5800, 0.6600, 0.6700, 0.4800, 0.3400, 0.3600, 0.3700, 0.5500, 0.5800, 0.6000, 0.3900, 0.4300, 0.3200,
            0.2900, 0.5900, 0.6700, 0.6300, 0.5700, 0.6100, 0.5600, 0.6500, 0.8300, 0.6200, 0.5700, 0.7600, 0.7300,
            0.6800, 0.6200, 0.6500, 0.6900, 0.7000, 0.5700, 0.4800, 0.5500, 0.5300, 0.5600, 0.4800, 0.4900, 0.4700,
            0.7000, 0.6100, 0.6900, 0.5300, 0.4900, 0.4600, 0.6100, 0.6700, 0.8900, 0.9700, 0.9500, 0.5500, 0.6700,
            0.3600, 0.5400, 0.5500, 0.6800, 0.5400, 0.6800, 0.6700, 0.7700, 0.8600, 1.0300, 0.9500, 0.2200, 0.9300,
            0.9900, 0.4600, 0.8100, 0.8500, 0.9800, 0.3000, 0.5900, 0.4400, 0.5400, 0.4800, 0.0700, 0.2500, 0.2800,
            0.5900, 0.1400, 1.0800, 0.6300, 0.8500, 0.4000, 1.0400, 0.1600, 0.7900, 0.5300, 0.9200, 0.0800, 0.6800,
            0.4000, 0.3500, 0.8500, 0.7500, 1.1000]])

               
    for trial in range(trials):
        input_freq=8+exp_rew*3.0
        reward_probs=prob_walk[:,trial]
        reward_mags=mags[:,trial]
        trial_monitor=run_wta(wta_params, num_groups, input_freq, trial_duration, background_freq=background_freq,
            record_lfp=False, record_voxel=False, record_neuron_state=False, record_spikes=False,
            record_firing_rate=True, record_inputs=False, plot_output=False)
        endIdx=int((trial_duration-1*second)/defaultclock.dt)
        startIdx=endIdx-500
        e_mean_final=[]
        for i in range(num_groups):
            rate_monitor=trial_monitor.monitors['excitatory_rate_%d' % i]
            e_rate=rate_monitor.smooth_rate(width=5*ms, filter='gaussian')
            e_mean_final.append(np.mean(e_rate[startIdx:endIdx]))
        decision_idx=0
        if e_mean_final[1]>e_mean_final[0]:
            decision_idx=1
        print('Input frequencies=[%.2f, %.2f]' % (input_freq[0],input_freq[1]))
        print('Expected reward=[%.2f, %.2f]' % (exp_rew[0],exp_rew[1]))
        print('Decision=%d' % decision_idx)
        reward=0.0
        if np.random.random()<=reward_probs[decision_idx]:
            reward=reward_mags[decision_idx]
        print('Reward=%.2f' % reward)
        exp_rew[decision_idx]=(1.0-alpha)*exp_rew[decision_idx]+alpha*reward

if __name__=='__main__':
    run_rl_simulation()