from brian import Clock, Hz, second, PoissonGroup, network_operation, pA, Network, nS
import h5py
from pysbi.wta.monitor import WTAMonitor, SessionMonitor
from pysbi.wta.network import default_params, pyr_params, inh_params, simulation_params, WTANetworkGroup, plasticity_params
import numpy as np
import matplotlib.pyplot as plt

def generate_virtual_subject(subj_id, behavioral_param_file):
    # Load alpha and beta params of control group from behavioral parameter file
    f = h5py.File(behavioral_param_file)
    control_group=f['control']
    alpha_vals=np.array(control_group['alpha'])
    beta_vals=np.array(control_group['beta'])

    # Sample beta from subject distribution - don't use subjects with high alpha
    beta_hist,beta_bins=np.histogram(beta_vals[np.where(alpha_vals<.99)[0]], density=True)
    bin_width=beta_bins[1]-beta_bins[0]
    beta_bin=np.random.choice(beta_bins[:-1], p=beta_hist*bin_width)
    beta=beta_bin+np.random.rand()*bin_width

    # Create virtual subject parameters - background freq from beta dist, resp threshold between 15 and 25Hz
    wta_params=default_params(background_freq=(beta-161.08)/-.17, resp_threshold=15+np.random.uniform(10))
    # Set initial input weights and modify NMDA recurrent
    pyramidal_params=pyr_params(w_nmda=0.15*nS, w_ampa_ext_correct=1.6*nS, w_ampa_ext_incorrect=0.0*nS)

    # Create a virtual subject
    subject=VirtualSubject(subj_id, wta_params=wta_params, pyr_params=pyramidal_params)
    return subject


class VirtualSubject:
    def __init__(self, subj_id, wta_params=default_params(), pyr_params=pyr_params(), inh_params=inh_params(),
                 plasticity_params=plasticity_params(), sim_params=simulation_params()):
        self.subj_id = subj_id
        self.wta_params = wta_params
        self.pyr_params = pyr_params
        self.inh_params = inh_params
        self.plasticity_params = plasticity_params
        self.sim_params = sim_params

        self.simulation_clock = Clock(dt=self.sim_params.dt)
        self.input_update_clock = Clock(dt=1 / (self.wta_params.refresh_rate / Hz) * second)

        self.background_input = PoissonGroup(self.wta_params.background_input_size,
            rates=self.wta_params.background_freq, clock=self.simulation_clock)
        self.task_inputs = []
        for i in range(self.wta_params.num_groups):
            self.task_inputs.append(PoissonGroup(self.wta_params.task_input_size,
                rates=self.wta_params.task_input_resting_rate, clock=self.simulation_clock))

        # Create WTA network
        self.wta_network = WTANetworkGroup(params=self.wta_params, background_input=self.background_input,
            task_inputs=self.task_inputs, pyr_params=self.pyr_params, inh_params=self.inh_params,
            plasticity_params=self.plasticity_params, clock=self.simulation_clock)


        # Create network monitor
        self.wta_monitor = WTAMonitor(self.wta_network, None, None, self.sim_params, record_lfp=False,
                                      record_voxel=False, record_neuron_state=False, record_spikes=False,
                                      record_firing_rate=True, record_inputs=True, record_connections=None,
                                      save_summary_only=False, clock=self.simulation_clock)


        # Create Brian network and reset clock
        self.net = Network(self.background_input, self.task_inputs, self.wta_network,
            self.wta_network.connections.values(), self.wta_monitor.monitors.values())


    def run_trial(self, sim_params, input_freq):
        self.wta_monitor.sim_params=sim_params
        self.net.reinit(states=False)

        @network_operation(when='start', clock=self.input_update_clock)
        def set_task_inputs():
            for idx in range(len(self.task_inputs)):
                rate = self.wta_params.task_input_resting_rate
                if sim_params.stim_start_time <= self.simulation_clock.t < sim_params.stim_end_time:
                    rate = input_freq[idx] * Hz + np.random.randn() * self.wta_params.input_var
                    if rate < self.wta_params.task_input_resting_rate:
                        rate = self.wta_params.task_input_resting_rate
                self.task_inputs[idx]._S[0, :] = rate

        @network_operation(clock=self.simulation_clock)
        def inject_current():
            if sim_params.dcs_start_time < self.simulation_clock.t <= sim_params.dcs_end_time:
                self.wta_network.group_e.I_dcs = sim_params.p_dcs
                self.wta_network.group_i.I_dcs = sim_params.i_dcs
            else:
                self.wta_network.group_e.I_dcs = 0 * pA
                self.wta_network.group_i.I_dcs = 0 * pA

        @network_operation(when='start', clock=self.simulation_clock)
        def inject_muscimol():
            if sim_params.muscimol_amount > 0:
                self.wta_network.groups_e[sim_params.injection_site].g_muscimol = sim_params.muscimol_amount

        self.net.remove(set_task_inputs, inject_current, inject_muscimol, self.wta_network.stdp.values())

        self.net.add(set_task_inputs, inject_current, inject_muscimol)
        if sim_params.plasticity:
            self.net.add(self.wta_network.stdp.values())

        self.net.run(sim_params.trial_duration, report='text')

        #self.wta_monitor.plot()
        self.net.remove(set_task_inputs, inject_current, inject_muscimol, self.wta_network.stdp.values())
