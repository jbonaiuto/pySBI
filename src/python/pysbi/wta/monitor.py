import h5py
from brian.experimental.connectionmonitor import ConnectionMonitor
import math
from matplotlib.patches import Rectangle
import numpy as np
from brian import StateMonitor, MultiStateMonitor, PopulationRateMonitor, SpikeMonitor, raster_plot, ms, hertz, nS, nA, mA, defaultclock, second, Clock
import matplotlib.pyplot as plt
from matplotlib.pyplot import figure, subplot, ylim, legend, ylabel, xlabel, show, title
# Collection of monitors for WTA network
from pysbi.util.plot import plot_network_firing_rates, plot_condition_choice_probability
from pysbi.util.utils import get_response_time, FitRT, FitWeibull


class SessionMonitor():
    def __init__(self, network, sim_params, plasticity_params, record_connections=[], conv_window=10,
                 record_firing_rates=False):
        self.sim_params=sim_params
        self.plasticity_params=plasticity_params
        self.network_params=network.params
        self.pyr_params=network.pyr_params
        self.inh_params=network.inh_params
        # Accuracy convolution window size
        self.conv_window=conv_window
        self.trial_inputs=np.zeros((self.network_params.num_groups,sim_params.ntrials))
        self.trial_rt=np.zeros((1,sim_params.ntrials))
        self.trial_resp=np.zeros((1,sim_params.ntrials))
        self.trial_correct=np.zeros((1,sim_params.ntrials))
        self.record_connections=record_connections
        self.record_firing_rates=record_firing_rates
        self.trial_weights={}
        for conn in self.record_connections:
            self.trial_weights[conn]=[]
        self.correct_avg = np.zeros((1, sim_params.ntrials))
        self.pop_rates={}
        if self.record_firing_rates:
            for i,group_e in enumerate(network.groups_e):
                self.pop_rates['excitatory_rate_%d' % i]=[]

                self.pop_rates['inhibitory_rate']=[]
        self.num_no_response=0

    def record_trial(self, trial_idx, inputs, correct_input, wta_net, wta_monitor):
        self.trial_inputs[:,trial_idx]=inputs

        e_rate_0 = wta_monitor.monitors['excitatory_rate_0'].smooth_rate(width= 5 * ms, filter = 'gaussian')
        e_rate_1 = wta_monitor.monitors['excitatory_rate_1'].smooth_rate(width= 5 * ms, filter = 'gaussian')
        i_rate = wta_monitor.monitors['inhibitory_rate'].smooth_rate(width= 5 * ms, filter = 'gaussian')

        if self.record_firing_rates:
            self.pop_rates['excitatory_rate_0'].append(e_rate_0)
            self.pop_rates['excitatory_rate_1'].append(e_rate_1)
            self.pop_rates['inhibitory_rate'].append(i_rate)

        rt, choice = get_response_time(np.array([e_rate_0, e_rate_1]), self.sim_params.stim_start_time,
            self.sim_params.stim_end_time, upper_threshold = self.network_params.resp_threshold,
            dt = self.sim_params.dt)

        correct = choice == correct_input
        if choice>-1:
            print 'response time = %.3f correct = %d' % (rt, int(correct))
        else:
            print 'no response!'
            self.num_no_response+=1
        self.trial_rt[0,trial_idx]=rt
        self.trial_resp[0,trial_idx]=choice
        self.trial_correct[0,trial_idx]=correct
        self.correct_avg[0,trial_idx] = (np.sum(self.trial_correct))/(trial_idx+1)
        for conn in self.record_connections:
            self.trial_weights[conn].append(wta_net.connections[conn].W.todense())

    def get_correct_ma(self):
        correct_ma = np.convolve(self.trial_correct[0, :], np.ones((self.conv_window,)) / self.conv_window, mode='valid')
        return correct_ma

    def get_trial_diag_weights(self):
        trial_diag_weights = np.zeros((len(self.record_connections), self.sim_params.ntrials))
        for i, conn in enumerate(self.record_connections):
            for trial_idx in range(self.sim_params.ntrials):
                trial_diag_weights[i, trial_idx] = np.mean(np.diagonal(self.trial_weights[conn][trial_idx]))
        return trial_diag_weights

    def get_perc_correct(self):
        resp_trials=np.where(self.trial_resp[0,:]>-1)[0]
        perc_correct=float(np.sum(self.trial_correct[0,resp_trials]))/float(len(resp_trials))
        return perc_correct

    def get_perc_correct_test(self):
        resp_trials = np.where(self.trial_resp[0,:]>-1)[0]
        resp_trials_test = [x for x in resp_trials if x >= self.sim_params.ntrials/2]
        perc_correct_test = float(np.sum(self.trial_correct[0,resp_trials_test]))/float(len(resp_trials_test))
        return perc_correct_test

    def get_perc_correct_training(self):
        resp_trials=np.where(self.trial_resp[0,:]>-1)[0]
        resp_trials_training = [y for y in resp_trials if y < self.sim_params.ntrials/2]
        perc_correct_training = float(np.sum(self.trial_correct[0,resp_trials_training]))/float(len(resp_trials_training))
        return perc_correct_training

    def plot_mean_firing_rates(self, trials, plt_title='Mean Firing Rates'):
        if self.record_firing_rates:
            mean_e_pop_rates=[]
            std_e_pop_rates=[]
            for i in range(self.network_params.num_groups):
                pop_rate_mat=np.array(self.pop_rates['excitatory_rate_%d' % i])
                mean_e_pop_rates.append(np.mean(pop_rate_mat[trials,:],axis=0))
                std_e_pop_rates.append(np.std(pop_rate_mat[trials,:],axis=0)/np.sqrt(len(trials)))
            mean_e_pop_rates=np.array(mean_e_pop_rates)
            std_e_pop_rates=np.array(std_e_pop_rates)
            pop_rate_mat=np.array(self.pop_rates['inhibitory_rate'])
            mean_i_pop_rate=np.mean(pop_rate_mat[trials,:],axis=0)
            std_i_pop_rate=np.std(pop_rate_mat[trials,:],axis=0)/np.sqrt(len(trials))
            plot_network_firing_rates(np.array(mean_e_pop_rates), self.sim_params, self.network_params,
                std_e_rates=std_e_pop_rates, i_rate=mean_i_pop_rate, std_i_rate=std_i_pop_rate, plt_title=plt_title)

    def plot_sorted_mean_firing_rates(self, trials, plt_title='Mean Firing Rates'):
        if self.record_firing_rates:
            chosen_pop_rates=[]
            unchosen_pop_rates=[]
            for trial_idx in trials:
                resp=self.trial_resp[0,trial_idx]
                if resp>-1:
                    chosen_pop_rates.append(self.pop_rates['excitatory_rate_%d' % resp][trial_idx])
                    unchosen_pop_rates.append(self.pop_rates['excitatory_rate_%d' % (1-resp)][trial_idx])
            if len(chosen_pop_rates)>1:
                chosen_pop_rates=np.array(chosen_pop_rates)
                unchosen_pop_rates=np.array(unchosen_pop_rates)
                mean_e_pop_rates=np.array([np.mean(chosen_pop_rates,axis=0), np.mean(unchosen_pop_rates,axis=0)])
                std_e_pop_rates=np.array([np.std(chosen_pop_rates,axis=0)/np.sqrt(len(trials)),
                                          np.std(unchosen_pop_rates,axis=0)/np.sqrt(len(trials))])
                plot_network_firing_rates(np.array(mean_e_pop_rates), self.sim_params, self.network_params,
                    std_e_rates=std_e_pop_rates, plt_title=plt_title, labels=['chosen','unchosen'])

    def plot_perc_missed(self):
        plt.figure()
        coherence_levels=self.get_coherence_levels()
        perc_missed=[]
        for coherence in coherence_levels:
            trials=self.get_coherence_trials(coherence)
            responded_trials=np.intersect1d(np.where(self.trial_resp[0,:]>-1)[0],trials)
            perc_missed.append((1.0-float(len(responded_trials))/float(len(trials)))*100.0)
        plt.plot(coherence_levels,perc_missed,'o')
        plt.xlabel('Coherence')
        plt.ylabel('% Missed')

    def plot_coherence_sat(self):
        plt.figure()
        coherence_levels=self.get_coherence_levels()
        mean_rt=[]
        mean_error=[]
        for coherence in coherence_levels:
            trials=self.get_coherence_trials(coherence)
            responded_trials=np.intersect1d(np.where(self.trial_resp[0,:]>-1)[0],trials)
            mean_rt.append(np.mean(self.trial_rt[0,responded_trials]))
            mean_error.append(np.mean(1.0-self.trial_correct[0,responded_trials])*100.0)
        plt.plot(mean_rt,mean_error,'o')
        plt.xlabel('RT')
        plt.ylabel('Error Rate')

    def plot_coherence_rt(self):
        coherence_levels=self.get_coherence_levels()
        mean_rt=[]
        std_rt=[]
        for coherence in coherence_levels:
            trials=self.get_coherence_trials(coherence)
            responded_trials=np.intersect1d(np.where(self.trial_resp[0,:]>-1)[0],trials)
            mean_rt.append(np.mean(self.trial_rt[0,responded_trials]))
            std_rt.append(np.std(self.trial_rt[0,responded_trials])/np.sqrt(len(responded_trials)))
        plt.figure()
        rt_fit = FitRT(coherence_levels, mean_rt, guess=[1,1,1], display=0)
        smoothInt = np.arange(min(coherence_levels), max(coherence_levels), 0.001)
        smoothRT = rt_fit.eval(smoothInt)
        plt.semilogx(smoothInt, smoothRT,'b')
        plt.errorbar(coherence_levels, mean_rt, yerr=std_rt, fmt='bo')
        plt.xlabel('Coherence')
        plt.ylabel('RT')

    def plot_coherence_accuracy(self):
        coherence_levels=self.get_coherence_levels()
        mean_correct=[]
        for coherence in coherence_levels:
            trials=self.get_coherence_trials(coherence)
            responded_trials=np.intersect1d(np.where(self.trial_resp[0,:]>-1)[0],trials)
            mean_correct.append(np.mean(self.trial_correct[0,responded_trials]))
        acc_fit = FitWeibull(coherence_levels, mean_correct, guess=[0.0, 0.2], display=0)
        smoothInt = np.arange(.01, 1.0, 0.001)
        smoothResp = acc_fit.eval(smoothInt)
        thresh=acc_fit.inverse(0.8)
        plt.figure()
        plt.semilogx(smoothInt, smoothResp,'b')
        plt.plot(coherence_levels,mean_correct,'ob')
        plt.plot([thresh,thresh],[0.5,1],'--b')
        plt.xlabel('Coherence')
        plt.ylabel('Accuracy')

    def plot_choice_hysteresis(self):
        # Dict of coherence levels
        coherence_choices={
            'L*':{},
            'R*':{}
        }

        # For each trial
        for trial_idx in range(1,self.sim_params.ntrials):
            direction = np.where(self.trial_inputs[:, trial_idx] == np.max(self.trial_inputs[:, trial_idx]))[0][0]
            if direction == 0:
                direction = -1
                # Get coherence - negative coherences when direction is to the left
            coherence = float('%.3f' % np.abs((self.trial_inputs[0, trial_idx] - self.network_params.mu_0) / (self.network_params.p_a * 100.0)))*direction
            last_resp=self.trial_resp[0,trial_idx-1]
            if last_resp == -1:
                last_resp=float('NaN')
            elif last_resp == 0:
                last_resp = -1
            resp=self.trial_resp[0,trial_idx]
            if resp == -1:
                resp=float('NaN')
            elif resp == 0:
                resp = -1

            if not math.isnan(last_resp) and not math.isnan(resp):
                if last_resp<0:
                    if not coherence in coherence_choices['L*']:
                        coherence_choices['L*'][coherence]=[]
                        # Append 0 to list if left (-1) or 1 if right
                    coherence_choices['L*'][coherence].append(np.max([0,resp]))
                elif last_resp>0:
                    # List of rightward choices (0=left, 1=right)
                    if not coherence in coherence_choices['R*']:
                        coherence_choices['R*'][coherence]=[]
                        # Append 0 to list if left (-1) or 1 if right
                    coherence_choices['R*'][coherence].append(np.max([0,resp]))

        fig=plt.figure()
        ax=fig.add_subplot(1,1,1)
        left_coherences=sorted(coherence_choices['L*'].keys())
        right_coherences=sorted(coherence_choices['R*'].keys())
        left_choice_probs = []
        right_choice_probs = []
        for coherence in left_coherences:
            left_choice_probs.append(np.mean(coherence_choices['L*'][coherence]))
        for coherence in right_coherences:
            right_choice_probs.append(np.mean(coherence_choices['R*'][coherence]))
        plot_condition_choice_probability(ax, 'b', left_coherences, left_choice_probs, right_coherences, right_choice_probs)


    def get_coherence_levels(self):
        trial_coherence_levels=[]
        for idx in range(self.sim_params.ntrials):
            coherence = np.abs((self.trial_inputs[0, idx] - self.network_params.mu_0) / (self.network_params.p_a * 100.0))
            trial_coherence_levels.append(float('%.3f' % coherence))
        return sorted(np.unique(trial_coherence_levels))

    def get_coherence_trials(self, coherence):
        trial_coherence_idx=[]
        for idx in range(self.sim_params.ntrials):
            trial_coherence = np.abs((self.trial_inputs[0, idx] - self.network_params.mu_0) / (self.network_params.p_a * 100.0))
            if ('%.3f' % trial_coherence)==('%.3f' % coherence):
                trial_coherence_idx.append(idx)

        return np.array(trial_coherence_idx)

    def plot(self):
        # Convolve accuracy
        correct_ma = self.get_correct_ma()

        trial_diag_weights = self.get_trial_diag_weights()

        if len(self.record_connections)>0:
            plt.figure()
            for i in range(len(self.record_connections)):
                plt.plot(trial_diag_weights[i,:]/nS, label = self.record_connections[i])
            plt.legend(loc = 'best')
            #plt.ylim(0, gmax/nS)
            plt.xlabel('trial')
            plt.ylabel('average weight')

        if self.record_firing_rates:
            self.plot_mean_firing_rates(range(self.sim_params.ntrials))
            self.plot_sorted_mean_firing_rates(range(self.sim_params.ntrials))

            coherence_levels=self.get_coherence_levels()

            for coherence in coherence_levels:
                trials=self.get_coherence_trials(coherence)
                #self.plot_mean_firing_rates(trials, plt_title='Coherence=%.3f' % coherence)
                self.plot_sorted_mean_firing_rates(trials, plt_title='Coherence=%.3f' % coherence)

        self.plot_coherence_rt()
        self.plot_coherence_accuracy()
        self.plot_coherence_sat()
        self.plot_perc_missed()
        self.plot_choice_hysteresis()

        plt.figure()
        plt.plot(self.trial_correct[0,:])
        plt.xlabel('trial')
        plt.ylabel('correct choice = 1')

        plt.figure()
        plt.plot(self.correct_avg[0,:], label = 'average')
        plt.plot(correct_ma, label = 'moving avg')
        plt.legend(loc = 'best')
        plt.ylim(0,1)
        plt.xlabel('trial')
        plt.ylabel('accuracy')

        plt.figure()
        plt.plot(self.trial_rt[0,:])
        plt.ylim(0, 2000)
        plt.xlabel('trial')
        plt.ylabel('response time')

        plt.figure()
        plt.plot(self.trial_resp[0,:])
        plt.xlabel('trial')
        plt.ylabel('choice e0=0 e1=1')
        #plt.show()

    def write_output(self, output_file):

        f = h5py.File(output_file, 'w')

        # Write basic parameters

        f.attrs['conv_window']=self.conv_window

        f_sim_params=f.create_group('sim_params')
        for attr, value in self.sim_params.iteritems():
            f_sim_params.attrs[attr] = value

        f_network_params=f.create_group('network_params')
        for attr, value in self.network_params.iteritems():
            f_network_params.attrs[attr] = value

        f_pyr_params=f.create_group('pyr_params')
        for attr, value in self.pyr_params.iteritems():
            f_pyr_params.attrs[attr] = value

        f_inh_params=f.create_group('inh_params')
        for attr, value in self.inh_params.iteritems():
            f_inh_params.attrs[attr] = value

        f_plasticity_params=f.create_group('plasticity_params')
        for attr, value in self.plasticity_params.iteritems():
            f_plasticity_params.attrs[attr] = value

        f_behav=f.create_group('behavior')
        f_behav['num_no_response']=self.num_no_response
        f_behav['trial_rt']=self.trial_rt
        f_behav['trial_resp']=self.trial_resp
        f_behav['trial_correct']=self.trial_correct

        f_neur=f.create_group('neural')
        f_neur['trial_inputs']=self.trial_inputs
        f_conns=f_neur.create_group('connections')
        for conn in self.record_connections:
            f_conn=f_conns.create_group(conn)
            for trial_idx in range(self.sim_params.ntrials):
                f_conn['trial_%d' % trial_idx]=self.trial_weights[conn][trial_idx]

        f_rates=f_neur.create_group('firing_rates')
        if self.record_firing_rates:
            for trial_idx in range(self.sim_params.ntrials):
                f_trial=f_rates.create_group('trial_%d' % trial_idx)
                f_trial['inhibitory_rate']=self.pop_rates['inhibitory_rate'][trial_idx]
                for i in range(self.network_params.num_groups):
                    f_trial['excitatory_rate_%d' % i]=self.pop_rates['excitatory_rate_%d' % i][trial_idx]
        f.close()


class WTAMonitor():

    ## Constructor
    #       network = network to monitor
    #       lfp_source = LFP source to monitor
    #       voxel = voxel to monitor
    #       record_lfp = record LFP signals if true
    #       record_voxel = record voxel signals if true
    #       record_neuron_state = record neuron state signals if true
    #       record_spikes = record spikes if true
    #       record_firing_rate = record firing rate if true
    #       record_inputs = record inputs if true
    def __init__(self, network, lfp_source, voxel, sim_params, record_lfp=True, record_voxel=True, record_neuron_state=False,
                 record_spikes=True, record_firing_rate=True, record_inputs=False, record_connections=None,
                 save_summary_only=False, clock=defaultclock):
        self.network_params=network.params
        self.pyr_params=network.pyr_params
        self.inh_params=network.inh_params
        self.sim_params=sim_params
        self.plasticity_params=network.plasticity_params
        self.voxel_params=None
        if voxel is not None:
            self.voxel_params=voxel.params
        self.monitors={}
        self.save_summary_only=save_summary_only
        self.clock=clock
        self.record_lfp=record_lfp
        self.record_voxel=record_voxel
        self.record_neuron_state=record_neuron_state
        self.record_spikes=record_spikes
        self.record_firing_rate=record_firing_rate
        self.record_inputs=record_inputs
        self.record_connections=record_connections
        self.save_summary_only=save_summary_only

        # LFP monitor
        if self.record_lfp:
            self.monitors['lfp'] = StateMonitor(lfp_source, 'LFP', record=0, clock=clock)

        # Voxel monitor
        if self.record_voxel:
            self.monitors['voxel'] = MultiStateMonitor(voxel, vars=['G_total','G_total_exc','y'],
                record=True, clock=clock)

        # Network monitor
        if self.record_neuron_state:
            self.record_idx=[]
            for i in range(self.network_params.num_groups):
                e_idx=i*int(.8*self.network_params.network_group_size/self.network_params.num_groups)
                self.record_idx.append(e_idx)
            i_idx=int(.8*self.network_params.network_group_size)
            self.record_idx.append(i_idx)
            self.monitors['network'] = MultiStateMonitor(network, vars=['vm','g_ampa_r','g_ampa_x','g_ampa_b',
                                                                        'g_gaba_a', 'g_nmda','I_ampa_r','I_ampa_x',
                                                                        'I_ampa_b','I_gaba_a','I_nmda'],
                record=self.record_idx, clock=clock)

        # Population rate monitors
        if self.record_firing_rate:
            for i,group_e in enumerate(network.groups_e):
                self.monitors['excitatory_rate_%d' % i]=PopulationRateMonitor(group_e)

            self.monitors['inhibitory_rate']=PopulationRateMonitor(network.group_i)

        # Input rate monitors
        if record_inputs:
            self.monitors['background_rate']=PopulationRateMonitor(network.background_input)
            for i,task_input in enumerate(network.task_inputs):
                self.monitors['task_rate_%d' % i]=PopulationRateMonitor(task_input)

        # Spike monitors
        if self.record_spikes:
            for i,group_e in enumerate(network.groups_e):
                self.monitors['excitatory_spike_%d' % i]=SpikeMonitor(group_e)

            self.monitors['inhibitory_spike']=SpikeMonitor(network.group_i)

        # Connection monitors
        if self.record_connections is not None:
            for connection in record_connections:
                self.monitors['connection_%s' % connection]=ConnectionMonitor(network.connections[connection], store=True,
                    clock=Clock(dt=.5*second))

    # Plot monitor data
    def plot(self):

        # Spike raster plots
        if self.record_spikes:
            num_plots=self.network_params.num_groups+1
            figure()
            for i in range(self.network_params.num_groups):
                subplot(num_plots,1,i+1)
                raster_plot(self.monitors['excitatory_spike_%d' % i],newfigure=False)
            subplot(num_plots,1,num_plots)
            raster_plot(self.monitors['inhibitory_spike'],newfigure=False)

        # Network firing rate plots
        if self.record_firing_rate:

            e_rate_0=self.monitors['excitatory_rate_0'].smooth_rate(width=5*ms)/hertz
            e_rate_1=self.monitors['excitatory_rate_1'].smooth_rate(width=5*ms)/hertz
            i_rate=self.monitors['inhibitory_rate'].smooth_rate(width=5*ms)/hertz
            plot_network_firing_rates(np.array([e_rate_0, e_rate_1]), i_rate, self.sim_params, self.network_params)

        # Input firing rate plots
        if self.record_inputs:
            figure()
            ax=subplot(111)
            max_rate=0
            task_rates=[]
            for i in range(self.network_params.num_groups):
                task_monitor=self.monitors['task_rate_%d' % i]
                task_rate=task_monitor.smooth_rate(width=5*ms,filter='gaussian')/hertz
                if np.max(task_rate)>max_rate:
                    max_rate=np.max(task_rate)
                task_rates.append(task_rate)

            rect=Rectangle((0,0),(self.sim_params.stim_end_time-self.sim_params.stim_start_time)/ms, max_rate+5,
                alpha=0.25, facecolor='yellow', edgecolor='none')
            ax.add_patch(rect)
            #            ax.plot(self.monitors['background_rate'].times/ms,
            #                self.monitors['background_rate'].smooth_rate(width=5*ms)/hertz)
            for i in range(self.network_params.num_groups):
                ax.plot((np.array(range(len(task_rates[i])))*self.sim_params.dt)/ms-self.sim_params.stim_start_time/ms, task_rates[i])
            ylim(0,90)
            ylabel('Firing rate (Hz)')
            xlabel('Time (ms)')

        # Network state plots
        if self.record_neuron_state:
            network_monitor=self.monitors['network']
            max_conductances=[]
            for neuron_idx in self.record_idx:
                max_conductances.append(np.max(network_monitor['g_ampa_r'][neuron_idx]/nS))
                max_conductances.append(np.max(network_monitor['g_ampa_x'][neuron_idx]/nS))
                max_conductances.append(np.max(network_monitor['g_ampa_b'][neuron_idx]/nS))
                max_conductances.append(np.max(network_monitor['g_nmda'][neuron_idx]/nS))
                max_conductances.append(np.max(network_monitor['g_gaba_a'][neuron_idx]/nS))
                #max_conductances.append(np.max(self.network_monitor['g_gaba_b'][neuron_idx]/nS))
            max_conductance=np.max(max_conductances)

            fig=figure()
            for i in range(self.network_params.num_groups):
                neuron_idx=self.record_idx[i]
                ax=subplot(int('%d1%d' % (self.network_params.num_groups+1,i+1)))
                title('e%d' % i)
                ax.plot(network_monitor['g_ampa_r'].times/ms, network_monitor['g_ampa_r'][neuron_idx]/nS,
                    label='AMPA-recurrent')
                ax.plot(network_monitor['g_ampa_x'].times/ms, network_monitor['g_ampa_x'][neuron_idx]/nS,
                    label='AMPA-task')
                ax.plot(network_monitor['g_ampa_b'].times/ms, network_monitor['g_ampa_b'][neuron_idx]/nS,
                    label='AMPA-backgrnd')
                ax.plot(network_monitor['g_nmda'].times/ms, network_monitor['g_nmda'][neuron_idx]/nS,
                    label='NMDA')
                ax.plot(network_monitor['g_gaba_a'].times/ms, network_monitor['g_gaba_a'][neuron_idx]/nS,
                    label='GABA_A')
                #ax.plot(network_monitor['g_gaba_b'].times/ms, network_monitor['g_gaba_b'][neuron_idx]/nS,
                #    label='GABA_B')
                ylim(0,max_conductance)
                xlabel('Time (ms)')
                ylabel('Conductance (nS)')
                legend()

            neuron_idx=self.record_idx[self.network_params.num_groups]
            ax=subplot('%d1%d' % (self.network_params.num_groups+1,self.network_params.num_groups+1))
            title('i')
            ax.plot(network_monitor['g_ampa_r'].times/ms, network_monitor['g_ampa_r'][neuron_idx]/nS,
                label='AMPA-recurrent')
            ax.plot(network_monitor['g_ampa_x'].times/ms, network_monitor['g_ampa_x'][neuron_idx]/nS,
                label='AMPA-task')
            ax.plot(network_monitor['g_ampa_b'].times/ms, network_monitor['g_ampa_b'][neuron_idx]/nS,
                label='AMPA-backgrnd')
            ax.plot(network_monitor['g_nmda'].times/ms, network_monitor['g_nmda'][neuron_idx]/nS,
                label='NMDA')
            ax.plot(network_monitor['g_gaba_a'].times/ms, network_monitor['g_gaba_a'][neuron_idx]/nS,
                label='GABA_A')
            #ax.plot(network_monitor['g_gaba_b'].times/ms, network_monitor['g_gaba_b'][neuron_idx]/nS,
            #    label='GABA_B')
            ylim(0,max_conductance)
            xlabel('Time (ms)')
            ylabel('Conductance (nS)')
            legend()

            min_currents=[]
            max_currents=[]
            for neuron_idx in self.record_idx:
                max_currents.append(np.max(network_monitor['I_ampa_r'][neuron_idx]/nS))
                max_currents.append(np.max(network_monitor['I_ampa_x'][neuron_idx]/nS))
                max_currents.append(np.max(network_monitor['I_ampa_b'][neuron_idx]/nS))
                max_currents.append(np.max(network_monitor['I_nmda'][neuron_idx]/nS))
                max_currents.append(np.max(network_monitor['I_gaba_a'][neuron_idx]/nS))
                #max_currents.append(np.max(network_monitor['I_gaba_b'][neuron_idx]/nS))
                min_currents.append(np.min(network_monitor['I_ampa_r'][neuron_idx]/nS))
                min_currents.append(np.min(network_monitor['I_ampa_x'][neuron_idx]/nS))
                min_currents.append(np.min(network_monitor['I_ampa_b'][neuron_idx]/nS))
                min_currents.append(np.min(network_monitor['I_nmda'][neuron_idx]/nS))
                min_currents.append(np.min(network_monitor['I_gaba_a'][neuron_idx]/nS))
                #min_currents.append(np.min(network_monitor['I_gaba_b'][neuron_idx]/nS))
            max_current=np.max(max_currents)
            min_current=np.min(min_currents)

            fig=figure()
            for i in range(self.network_params.num_groups):
                ax=subplot(int('%d1%d' % (self.network_params.num_groups+1,i+1)))
                neuron_idx=self.record_idx[i]
                title('e%d' % i)
                ax.plot(network_monitor['I_ampa_r'].times/ms, network_monitor['I_ampa_r'][neuron_idx]/nA,
                    label='AMPA-recurrent')
                ax.plot(network_monitor['I_ampa_x'].times/ms, network_monitor['I_ampa_x'][neuron_idx]/nA,
                    label='AMPA-task')
                ax.plot(network_monitor['I_ampa_b'].times/ms, network_monitor['I_ampa_b'][neuron_idx]/nA,
                    label='AMPA-backgrnd')
                ax.plot(network_monitor['I_nmda'].times/ms, network_monitor['I_nmda'][neuron_idx]/nA,
                    label='NMDA')
                ax.plot(network_monitor['I_gaba_a'].times/ms, network_monitor['I_gaba_a'][neuron_idx]/nA,
                    label='GABA_A')
                #ax.plot(network_monitor['I_gaba_b'].times/ms, network_monitor['I_gaba_b'][neuron_idx]/nA,
                #    label='GABA_B')
                ylim(min_current,max_current)
                xlabel('Time (ms)')
                ylabel('Current (nA)')
                legend()

            ax=subplot(int('%d1%d' % (self.network_params.num_groups+1,self.network_params.num_groups+1)))
            neuron_idx=self.record_idx[self.network_params.num_groups]
            title('i')
            ax.plot(network_monitor['I_ampa_r'].times/ms, network_monitor['I_ampa_r'][neuron_idx]/nA,
                label='AMPA-recurrent')
            ax.plot(network_monitor['I_ampa_x'].times/ms, network_monitor['I_ampa_x'][neuron_idx]/nA,
                label='AMPA-task')
            ax.plot(network_monitor['I_ampa_b'].times/ms, network_monitor['I_ampa_b'][neuron_idx]/nA,
                label='AMPA-backgrnd')
            ax.plot(network_monitor['I_nmda'].times/ms, network_monitor['I_nmda'][neuron_idx]/nA,
                label='NMDA')
            ax.plot(network_monitor['I_gaba_a'].times/ms, network_monitor['I_gaba_a'][neuron_idx]/nA,
                label='GABA_A')
            #ax.plot(network_monitor['I_gaba_b'].times/ms, network_monitor['I_gaba_b'][neuron_idx]/nA,
            #    label='GABA_B')
            ylim(min_current,max_current)
            xlabel('Time (ms)')
            ylabel('Current (nA)')
            legend()

        # LFP plot
        if self.record_lfp:
            figure()
            ax=subplot(111)
            ax.plot(self.monitors['lfp'].times / ms, self.monitors['lfp'][0]/mA)
            xlabel('Time (ms)')
            ylabel('LFP (mA)')

        # Voxel activity plots
        if self.record_voxel:
            voxel_monitor=self.monitors['voxel']
            voxel_exc_monitor=None
            if 'voxel_exc' in self.monitors:
                voxel_exc_monitor=self.monitors['voxel_exc']
            syn_max=np.max(voxel_monitor['G_total'][0] / nS)
            y_max=np.max(voxel_monitor['y'][0])
            y_min=np.min(voxel_monitor['y'][0])
            figure()
            if voxel_exc_monitor is None:
                ax=subplot(211)
            else:
                ax=subplot(221)
                syn_max=np.max([syn_max, np.max(voxel_exc_monitor['G_total'][0])])
                y_max=np.max([y_max, np.max(voxel_exc_monitor['y'][0])])
                y_min=np.min([y_min, np.min(voxel_exc_monitor['y'][0])])
            ax.plot(voxel_monitor['G_total'].times / ms, voxel_monitor['G_total'][0] / nS)
            xlabel('Time (ms)')
            ylabel('Total Synaptic Activity (nS)')
            ylim(0, syn_max)
            if voxel_exc_monitor is None:
                ax=subplot(212)
            else:
                ax=subplot(222)
            ax.plot(voxel_monitor['y'].times / ms, voxel_monitor['y'][0])
            xlabel('Time (ms)')
            ylabel('BOLD')
            ylim(y_min, y_max)
            if voxel_exc_monitor is not None:
                ax=subplot(223)
                ax.plot(voxel_exc_monitor['G_total'].times / ms, voxel_exc_monitor['G_total'][0] / nS)
                xlabel('Time (ms)')
                ylabel('Total Synaptic Activity (nS)')
                ylim(0, syn_max)
                ax=subplot(224)
                ax.plot(voxel_exc_monitor['y'].times / ms, voxel_exc_monitor['y'][0])
                xlabel('Time (ms)')
                ylabel('BOLD')
                ylim(y_min, y_max)

        if self.record_connections:
            figure()
            ax=subplot(111)
            for mon in self.monitors:
                if mon.startswith('connection_'):
                    conn_name=mon[11:]
                    conns=np.zeros((len(self.monitors[mon].values),1))
                    conn_times=[]
                    for idx, (time, conn_matrix) in enumerate(self.monitors[mon].values):
                        conn_diag=np.diagonal(conn_matrix.todense())
                        mean_w=np.mean(conn_diag)
                        conns[idx,0]=mean_w
                        conn_times.append(time)
                    ax.plot(np.array(conn_times) / ms, conns[:,0]/nS, label=conn_name)
            legend(loc='best')
            xlabel('Time (ms)')
            ylabel('Connection Weight (nS)')

            #show()


    ## Write monitor data to HDF5 file
    #       background_input_size = number of background inputs
    #       background_freq rate = background firing rate
    #       input_freq = input firing rates
    #       network_group_size = number of neurons per input group
    #       num_groups = number of input groups
    #       output_file = filename to write to
    #       record_firing_rate = write network firing rate data when true
    #       record_neuron_stae = write neuron state data when true
    #       record_spikes = write spike data when true
    #       record_voxel = write voxel data when true
    #       record_lfp = write LFP data when true
    #       record_inputs = write input firing rates when true
    #       stim_end_time = stimulation end time
    #       stim_start_time = stimulation start time
    #       task_input_size = number of neurons in each task input group
    #       trial_duration = duration of the trial
    #       voxel = voxel for network
    #       wta_monitor = network monitor
    #       wta_params = network parameters
    def write_output(self, input_freq, output_file):

        f = h5py.File(output_file, 'w')

        # Write basic parameters
        f.attrs['input_freq'] = input_freq

        f_sim_params=f.create_group('sim_params')
        for attr, value in self.sim_params.iteritems():
            f_sim_params.attrs[attr] = value

        f_network_params=f.create_group('network_params')
        for attr, value in self.network_params.iteritems():
            f_network_params.attrs[attr] = value

        f_pyr_params=f.create_group('pyr_params')
        for attr, value in self.pyr_params.iteritems():
            f_pyr_params.attrs[attr] = value

        f_inh_params=f.create_group('inh_params')
        for attr, value in self.inh_params.iteritems():
            f_inh_params.attrs[attr] = value

        f_plasticity_params=f.create_cgroup('plasticity_params')
        for attr, value in self.plasticity_params.iteritems():
            f_plasticity_params.attrs[attr] = value

        if not self.save_summary_only:
            # Write LFP data
            if self.record_lfp:
                f_lfp = f.create_group('lfp')
                f_lfp['lfp']=self.monitors['lfp'].values

            # Write voxel data
            if self.record_voxel:
                f_vox = f.create_group('voxel')
                f_vox_params=f_vox.create_group('voxel_params')
                for attr, value in self.voxel_params.iteritems():
                    f_vox_params.attrs[attr] = value

                f_vox_total=f_vox.create_group('total_syn')
                f_vox_total['G_total'] = self.monitors['voxel']['G_total'].values
                f_vox_total['s'] = self.monitors['voxel']['s'].values
                f_vox_total['f_in'] = self.monitors['voxel']['f_in'].values
                f_vox_total['v'] = self.monitors['voxel']['v'].values
                f_vox_total['q'] = self.monitors['voxel']['q'].values
                f_vox_total['y'] = self.monitors['voxel']['y'].values

                f_vox_exc=f_vox.create_group('exc_syn')
                f_vox_exc['G_total'] = self.monitors['voxel_exc']['G_total'].values
                f_vox_exc['s'] = self.monitors['voxel_exc']['s'].values
                f_vox_exc['f_in'] = self.monitors['voxel_exc']['f_in'].values
                f_vox_exc['v'] = self.monitors['voxel_exc']['v'].values
                f_vox_exc['q'] = self.monitors['voxel_exc']['q'].values
                f_vox_exc['y'] = self.monitors['voxel_exc']['y'].values

            # Write neuron state data
            if self.record_neuron_state:
                f_state = f.create_group('neuron_state')
                f_state['g_ampa_r'] = self.monitors['network']['g_ampa_r'].values
                f_state['g_ampa_x'] = self.monitors['network']['g_ampa_x'].values
                f_state['g_ampa_b'] = self.monitors['network']['g_ampa_b'].values
                f_state['g_nmda'] = self.monitors['network']['g_nmda'].values
                f_state['g_gaba_a'] = self.monitors['network']['g_gaba_a'].values
                #f_state['g_gaba_b'] = self.monitors['network']['g_gaba_b'].values
                f_state['I_ampa_r'] = self.monitors['network']['I_ampa_r'].values
                f_state['I_ampa_x'] = self.monitors['network']['I_ampa_x'].values
                f_state['I_ampa_b'] = self.monitors['network']['I_ampa_b'].values
                f_state['I_nmda'] = self.monitors['network']['I_nmda'].values
                f_state['I_gaba_a'] = self.monitors['network']['I_gaba_a'].values
                #f_state['I_gaba_b'] = self.monitors['network']['I_gaba_b'].values
                f_state['vm'] = self.monitors['network']['vm'].values
                f_state['record_idx'] = np.array(self.record_idx)

            # Write network firing rate data
            if self.record_firing_rate:
                f_rates = f.create_group('firing_rates')
                e_rates = []
                for i in range(self.network_params.num_groups):
                    e_rates.append(self.monitors['excitatory_rate_%d' % i].smooth_rate(width=5 * ms, filter='gaussian'))
                f_rates['e_rates'] = np.array(e_rates)

                i_rates = [self.monitors['inhibitory_rate'].smooth_rate(width=5 * ms, filter='gaussian')]
                f_rates['i_rates'] = np.array(i_rates)

            # Write input firing rate data
            if self.record_inputs:
                back_rate=f.create_group('background_rate')
                back_rate['firing_rate']=self.monitors['background_rate'].smooth_rate(width=5*ms,filter='gaussian')
                task_rates=f.create_group('task_rates')
                t_rates=[]
                for i in range(self.network_params.num_groups):
                    t_rates.append(self.monitors['task_rate_%d' % i].smooth_rate(width=5*ms,filter='gaussian'))
                task_rates['firing_rates']=np.array(t_rates)

            # Write spike data
            if self.record_spikes:
                f_spikes = f.create_group('spikes')
                for idx in range(self.network_params.num_groups):
                    spike_monitor=self.monitors['excitatory_spike_%d' % idx]
                    if len(spike_monitor.spikes):
                        f_spikes['e.%d.spike_neurons' % idx] = np.array([s[0] for s in spike_monitor.spikes])
                        f_spikes['e.%d.spike_times' % idx] = np.array([s[1] for s in spike_monitor.spikes])

                spike_monitor=self.monitors['inhibitory_spike']
                if len(spike_monitor.spikes):
                    f_spikes['i.spike_neurons'] = np.array([s[0] for s in spike_monitor.spikes])
                    f_spikes['i.spike_times'] = np.array([s[1] for s in spike_monitor.spikes])

            # Write connection data
            if self.record_connections:
                f_conns=f.create_group('connections')
                for mon in self.monitors:
                    if mon.startswith('connection_'):
                        conn_name=mon[11:]
                        f_conn=f_conns.create_group(conn_name)
                        for idx, (time, conn_matrix) in enumerate(self.monitors[mon].values):
                            f_conn['time_%.4f' % time]=conn_matrix.todense()

        else:
            f_summary=f.create_group('summary')
            endIdx=int(self.sim_params.stim_end_time/self.clock.dt)
            startIdx=endIdx-500
            e_mean_final=[]
            e_max=[]
            for idx in range(self.network_params.num_groups):
                rate_monitor=self.monitors['excitatory_rate_%d' % idx]
                e_rate=rate_monitor.smooth_rate(width=5*ms, filter='gaussian')
                e_mean_final.append(np.mean(e_rate[startIdx:endIdx]))
                e_max.append(np.max(e_rate))
            rate_monitor=self.monitors['inhibitory_rate']
            i_rate=rate_monitor.smooth_rate(width=5*ms, filter='gaussian')
            i_mean_final=[np.mean(i_rate[startIdx:endIdx])]
            i_max=[np.max(i_rate)]
            f_summary['e_mean']=np.array(e_mean_final)
            f_summary['e_max']=np.array(e_max)
            f_summary['i_mean']=np.array(i_mean_final)
            f_summary['i_max']=np.array(i_max)
            f_summary['bold_max']=np.max(self.monitors['voxel']['y'].values)
            f_summary['bold_exc_max']=np.max(self.monitors['voxel_exc']['y'].values)

        f.close()