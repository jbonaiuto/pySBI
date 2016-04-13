from brian import Hz, nS, pA, second
import h5py
import os
from pysbi.wta.monitor import SessionMonitor
from pysbi.wta.network import default_params, pyr_params, simulation_params
from pysbi.wta.virtual_subject import VirtualSubject, generate_virtual_subject
import numpy as np
import matplotlib.pyplot as plt

def run_virtual_subjects(subj_ids, conditions, output_dir, behavioral_param_file):
    """
    Runs a set of virtual subjects on the given conditions
    subj_ids = list of subject IDs
    conditions = dictionary: {condition name: simulation_params}
    output_dir = directory to store h5 output files
    behavioral_param_file = h5 file containing softmax-RL parameter distributions, background freq is sampled using
        inverse temp param distribution
    """

    # Run each subject
    for subj_id in subj_ids:
        print('***** Running subject %d *****' % subj_id)

        subject=generate_virtual_subject(subj_id, behavioral_param_file)

        # Run through each condition
        for condition, sim_params in conditions.iteritems():
            # Reinitialize state variables in subject network
            subject.net.reinit(states=True)
            # Run session
            run_session(subject, condition, sim_params,
                output_file=os.path.join(output_dir, 'subject.%d.%s.h5' % (subj_id,condition)))


def run_session(subject, condition, sim_params, output_file=None, plot=False):
    """
    Run session in subject
    subject = subject object
    sim_params = simulation params
    output_file = if not none, writes h5 output to filename
    plot = plots session data if True
    """
    print('** Condition: %s **' % condition)

    # Create session monitor
    session_monitor=SessionMonitor(subject.wta_network, sim_params, {}, record_connections=[], conv_window=40,
        record_firing_rates=True)

    # Run on six coherence levels
    coherence_levels=[0.032, .064, .128, .256, .512]
    # Trials per coherence level
    trials_per_level=20
    # Create inputs for each trial
    trial_inputs=np.zeros((trials_per_level*len(coherence_levels),2))
    # Create left and right directions for each coherence level
    for i in range(len(coherence_levels)):
        coherence = coherence_levels[i]
        # Left
        min_idx=i*trials_per_level
        max_idx=i*trials_per_level+trials_per_level/2
        trial_inputs[min_idx:max_idx, 0] = subject.wta_params.mu_0 + subject.wta_params.p_a * coherence * 100.0
        trial_inputs[min_idx:max_idx, 1] = subject.wta_params.mu_0 - subject.wta_params.p_b * coherence * 100.0

        #Right
        min_idx=i*trials_per_level+trials_per_level/2
        max_idx=i*trials_per_level + trials_per_level
        trial_inputs[min_idx:max_idx, 0] = subject.wta_params.mu_0 - subject.wta_params.p_b * coherence * 100.0
        trial_inputs[min_idx:max_idx, 1] = subject.wta_params.mu_0 + subject.wta_params.p_a * coherence * 100.0

    # Shuffle trials
    trial_inputs=np.random.permutation(trial_inputs)

    # Simulate each trial
    for t in range(sim_params.ntrials):
        print('Trial %d' % t)

        # Get task input for trial and figure out which is correct
        task_input_rates=trial_inputs[t,:]
        correct_input=np.where(task_input_rates==np.max(task_input_rates))[0]

        # Run trial
        subject.run_trial(sim_params, task_input_rates)

        # subject.wta_monitor.plot()
        # plt.show()

        # Record trial
        session_monitor.record_trial(t, task_input_rates, correct_input, subject.wta_network, subject.wta_monitor)

    # Write output
    if output_file is not None:
        session_monitor.write_output(output_file)

    # Plot
    if plot:
        if sim_params.ntrials>1:
            session_monitor.plot()
        else:
            subject.wta_monitor.plot()
        plt.show()

if __name__=='__main__':
    # Trials per condition
    trials_per_condition=100
    # Max stimulation intensity
    stim_intensity_max=2*pA
    # Stimulation conditions
    conditions={
        'control': simulation_params(ntrials=trials_per_condition),
        'depolarizing': simulation_params(ntrials=trials_per_condition, p_dcs=stim_intensity_max, i_dcs=-0.5*stim_intensity_max,
            dcs_start_time=0*second, dcs_end_time=4*second),
        'hyperpolarizing': simulation_params(ntrials=trials_per_condition, p_dcs=-1*stim_intensity_max, i_dcs=0.5*stim_intensity_max,
            dcs_start_time=0*second, dcs_end_time=4*second)
    }
    # run_virtual_subjects(range(20), conditions, '/home/jbonaiuto/Projects/pySBI/data/rdmd/',
    #     '/home/jbonaiuto/Projects/pySBI/data/rerw/subjects/fitted_behavioral_params.h5')
    run_virtual_subjects(range(16,20), conditions, '/home/jbonaiuto/Projects/pySBI/data/rdmd/',
        '/home/jbonaiuto/Projects/pySBI/data/rerw/subjects/fitted_behavioral_params.h5')
