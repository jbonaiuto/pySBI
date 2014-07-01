import os
from brian import defaultclock, Parameters
from brian.stdunits import ms
from brian.units import second
import matplotlib.pyplot as plt
import numpy as np
from pysbi.adaptation.popcode import default_params, ProbabilisticPopulationCode, run_pop_code, SamplingPopulationCode, Stimulus
from pysbi.util.utils import save_to_png, save_to_eps

rapid_design_params=Parameters(
    trial_duration=2*second,
    isi=100*ms,
    stim_dur=300*ms
)

long_design_params=Parameters(
    trial_duration=10*second,
    isi=6*second,
    stim_dur=100*ms
)

def adaptation_simulation(baseline, pop_class, N, network_params, sim_params, stim1_mean, stim2_mean, stim1_var,
                          stim2_var):
    # Compute stimulus start and end times
    stim1_start_time=1*second
    stim1_end_time=stim1_start_time+sim_params.stim_dur

    stim2_start_time=stim1_end_time+sim_params.isi
    stim2_end_time=stim2_start_time+sim_params.stim_dur

    pop_monitor,voxel_monitor,y_max=run_pop_code(pop_class, N, network_params,
        [Stimulus(stim1_mean, stim1_var, stim1_start_time, stim1_end_time),
         Stimulus(stim2_mean, stim2_var, stim2_start_time, stim2_end_time)],
        sim_params.trial_duration)

    if baseline=='repeated':
        pop_monitor,voxel_monitor,baseline_y_max=run_pop_code(pop_class, N, network_params,
            [Stimulus(stim1_mean,stim1_var,stim1_start_time,stim1_end_time),
             Stimulus(stim1_mean,stim1_var,stim2_start_time,stim2_end_time)],
            sim_params.trial_duration)
    elif baseline=='single':
        pop_monitor,voxel_monitor,baseline_y_max=run_pop_code(pop_class, N, network_params,
            [Stimulus(stim2_mean, stim2_var, stim1_start_time, stim1_end_time)],
            rapid_design_params.trial_duration)
    adaptation=np.abs(y_max-baseline_y_max)/baseline_y_max
    return adaptation

def run_repeated_test():
    N=150
    # Set trial duration, inter-stimulus-interval, and stimulus duration depending on design
    network_params=default_params
    sim_params=rapid_design_params

    # Compute stimulus start and end times
    stim1_start_time=1*second
    stim1_end_time=stim1_start_time+sim_params.stim_dur

    stim2_start_time=stim1_end_time+sim_params.isi
    stim2_end_time=stim2_start_time+sim_params.stim_dur

    x_delta_iter=5
    # If baseline is single stimulus - need to test x_delta=0
    x_delta_range=np.array(range(0,int(N/3),x_delta_iter))

    # High and low variance examples
    low_var=5
    x=int(N/3)

    prob_combined_y_max=np.zeros(len(x_delta_range))
    prob_repeated_y_max=np.zeros(len(x_delta_range))
    samp_combined_y_max=np.zeros(len(x_delta_range))
    samp_repeated_y_max=np.zeros(len(x_delta_range))
    for i,x_delta in enumerate(x_delta_range):
        print('x_delta=%d' % x_delta)

        pop_monitor,voxel_monitor,prob_repeated_y_max[i]=run_pop_code(ProbabilisticPopulationCode, N, network_params,
            [Stimulus(x,low_var,stim1_start_time,stim1_end_time),
             Stimulus(x+x_delta,low_var,stim2_start_time,stim2_end_time)],
            sim_params.trial_duration)
        pop_monitor,voxel_monitor,prob_first_y_max=run_pop_code(ProbabilisticPopulationCode, N, network_params,
            [Stimulus(x, low_var, stim1_start_time, stim1_end_time)],
            sim_params.trial_duration)
        pop_monitor,voxel_monitor,prob_second_y_max=run_pop_code(ProbabilisticPopulationCode, N, network_params,
            [Stimulus(x+x_delta, low_var, stim1_start_time, stim1_end_time)],
            sim_params.trial_duration)
        prob_combined_y_max[i]=prob_first_y_max+prob_second_y_max

        pop_monitor,voxel_monitor,samp_repeated_y_max[i]=run_pop_code(SamplingPopulationCode, N, network_params,
            [Stimulus(x,low_var,stim1_start_time,stim1_end_time),
             Stimulus(x+x_delta,low_var,stim2_start_time,stim2_end_time)],
            sim_params.trial_duration)
        pop_monitor,voxel_monitor,samp_first_y_max=run_pop_code(SamplingPopulationCode, N, network_params,
            [Stimulus(x, low_var, stim1_start_time, stim1_end_time)],
            sim_params.trial_duration)
        pop_monitor,voxel_monitor,samp_second_y_max=run_pop_code(SamplingPopulationCode, N, network_params,
            [Stimulus(x+x_delta, low_var, stim1_start_time, stim1_end_time)],
            sim_params.trial_duration)
        samp_combined_y_max[i]=samp_first_y_max+samp_second_y_max

    data_dir='../../data/adaptation/repeated_test/'

    fig=plt.figure()
    plt.title('Probabilistic Population Code')
    plt.plot(x_delta_range,prob_combined_y_max-prob_repeated_y_max,'r',label='prob')
    plt.plot(x_delta_range,samp_combined_y_max-samp_repeated_y_max,'b',label='samp')
    plt.legend(loc='best')
    fname='repeated_test'
    save_to_png(fig, os.path.join(data_dir,'%s.png' % fname))
    save_to_eps(fig, os.path.join(data_dir,'%s.eps' % fname))
    plt.close(fig)

def run_full_adaptation_simulation(design, baseline):
    N=150
    # Set trial duration, inter-stimulus-interval, and stimulus duration depending on design
    network_params=default_params
    sim_params=rapid_design_params
    if design=='long':
        network_params.tau_a=5*second
        sim_params=long_design_params

    # High and low mean and variance examples
    low_var=5
    high_var=15
    low_mean=50
    high_mean=100

    stim=[(low_mean,low_var),(low_mean,high_var),(high_mean,low_var),(high_mean,high_var)]
    prob_adaptation=np.zeros([4,4])
    samp_adaptation=np.zeros([4,4])

    for i,(stim1_mean,stim1_var) in enumerate(stim):
        for j,(stim2_mean,stim2_var) in enumerate(stim):
            print('prob stim1: mean=%d, var=%d; stim2: mean=%d, var=%d' % (stim1_mean,stim1_var,stim2_mean,stim2_var))
            prob_adaptation[i,j]=adaptation_simulation(baseline, ProbabilisticPopulationCode, N, network_params,
                sim_params, stim1_mean, stim2_mean, stim1_var, stim2_var)
            print('prob adaptation=%.4f' % prob_adaptation[i,j])

            print('samp stim1: mean=%d, var=%d; stim2: mean=%d, var=%d' % (stim1_mean,stim1_var,stim2_mean,stim2_var))
            samp_adaptation[i,j]=adaptation_simulation(baseline, SamplingPopulationCode, N, network_params,
                sim_params, stim1_mean, stim2_mean, stim1_var, stim2_var)
            print('samp adaptation=%.4f' % samp_adaptation[i,j])

    data_dir='../../data/adaptation/full_adaptation/'

    fig=plt.figure()
    plt.title('Probabilistic Population')
    plt.imshow(prob_adaptation,interpolation='none')
    plt.colorbar()
    fname='%s.baseline-%s.prob_pop' % (design,baseline)
    save_to_png(fig, os.path.join(data_dir,'%s.png' % fname))
    save_to_eps(fig, os.path.join(data_dir,'%s.eps' % fname))
    plt.close(fig)

    fig=plt.figure()
    plt.title('Sampling Population')
    plt.imshow(samp_adaptation,interpolation='none')
    plt.colorbar()
    fname='%s.baseline-%s.samp_pop' % (design,baseline)
    save_to_png(fig, os.path.join(data_dir,'%s.png' % fname))
    save_to_eps(fig, os.path.join(data_dir,'%s.eps' % fname))
    plt.close(fig)

def run_mean_adaptation_simulation(design, baseline):
    N=150
    # Set trial duration, inter-stimulus-interval, and stimulus duration depending on design
    network_params=default_params
    sim_params=rapid_design_params
    if design=='long':
        network_params.tau_a=5*second
        sim_params=long_design_params

    x_delta_iter=5
    # If baseline is single stimulus - need to test x_delta=0
    x_delta_range=np.array(range(0,int(N/3),x_delta_iter))

    # High and low variance examples
    low_var=5
    high_var=15
    x=int(N/3)

    prob_low_var_adaptation=np.zeros(len(x_delta_range))
    prob_high_var_adaptation=np.zeros(len(x_delta_range))
    samp_low_var_adaptation=np.zeros(len(x_delta_range))
    samp_high_var_adaptation=np.zeros(len(x_delta_range))
    for i,x_delta in enumerate(x_delta_range):
        print('x_delta=%d' % x_delta)

        prob_low_var_adaptation[i]=adaptation_simulation(baseline, ProbabilisticPopulationCode, N, network_params,
            sim_params, x, x+x_delta, low_var, low_var)
        prob_high_var_adaptation[i]=adaptation_simulation(baseline, ProbabilisticPopulationCode, N, network_params,
            sim_params, x, x+x_delta, high_var, high_var)

        samp_low_var_adaptation[i]=adaptation_simulation(baseline, SamplingPopulationCode, N, network_params,
            sim_params, x, x+x_delta, low_var, low_var)
        samp_high_var_adaptation[i]=adaptation_simulation(baseline, SamplingPopulationCode, N, network_params,
            sim_params, x, x+x_delta, high_var, high_var)

    data_dir='../../data/adaptation/mean_shift/'

    fig=plt.figure()
    plt.title('Probabilistic Population Code')
    plt.plot(x_delta_range,prob_low_var_adaptation,'r',label='low var')
    plt.plot(x_delta_range,prob_high_var_adaptation,'b',label='high var')
    plt.legend(loc='best')
    fname='%s.baseline-%s.prob_pop.mean_adaptation' % (design, baseline)
    save_to_png(fig, os.path.join(data_dir,'%s.png' % fname))
    save_to_eps(fig, os.path.join(data_dir,'%s.eps' % fname))
    plt.close(fig)

    fig=plt.figure()
    plt.title('Sampling Population Code')
    plt.plot(x_delta_range,samp_low_var_adaptation,'r',label='low var')
    plt.plot(x_delta_range,samp_high_var_adaptation,'b',label='high var')
    plt.legend(loc='best')
    fname='%s.baseline-%s.samp_pop.mean_adaptation' % (design, baseline)
    save_to_png(fig, os.path.join(data_dir,'%s.png' % fname))
    save_to_eps(fig, os.path.join(data_dir,'%s.eps' % fname))
    plt.close(fig)


def run_uncertainty_adaptation_simulation(design, baseline):

    N=150
    # Set trial duration, inter-stimulus-interval, and stimulus duration depending on design
    network_params=default_params
    sim_params=rapid_design_params
    if design=='long':
        network_params.tau_a=5*second
        sim_params=long_design_params

    # Variance and mean values used
    low_var=5
    high_var=15
    x=int(N/3)

    print('prob low->high')
    prob_low_high_adaptation=adaptation_simulation(baseline, ProbabilisticPopulationCode, N, network_params, sim_params,
        x, x, low_var, high_var)
    print('prob high->low')
    prob_high_low_adaptation=adaptation_simulation(baseline, ProbabilisticPopulationCode, N, network_params, sim_params,
        x, x, high_var, low_var)

    print('samp low->high')
    samp_low_high_adaptation=adaptation_simulation(baseline, SamplingPopulationCode, N, network_params, sim_params,
        x, x, low_var, high_var)
    print('samp high->low')
    samp_high_low_adaptation=adaptation_simulation(baseline, SamplingPopulationCode, N, network_params, sim_params,
        x, x, high_var, low_var)

    data_dir='../../data/adaptation/var_shift/'

    fig=plt.figure()
    plt.plot([0,1],[prob_low_high_adaptation, prob_high_low_adaptation],label='prob')
    plt.plot([0,1],[samp_low_high_adaptation, samp_high_low_adaptation],label='samp')
    plt.legend(loc='best')
    fname='%s.baseline-%s.var.adaptation' % (design,baseline)
    save_to_png(fig, os.path.join(data_dir,'%s.png' % fname))
    save_to_eps(fig, os.path.join(data_dir,'%s.eps' % fname))
    plt.close(fig)

#    fig=plt.figure()
#    plt.title('Probabilistic Population')
#    plt.plot(prob_low_high_voxel_monitor['y'][0], 'b', label='low->high')
#    plt.plot(prob_low_high_baseline_voxel_monitor['y'][0], 'b--', label='low->high baseline')
#    plt.plot(prob_high_low_voxel_monitor['y'][0], 'r', label='high->low')
#    plt.plot(prob_high_low_baseline_voxel_monitor['y'][0], 'r--', label='high->low baseline')
#    plt.legend(loc='best')
#    fname='%s.baseline-%s.var.adaptation.prob.bold' % (design,baseline)
#    save_to_png(fig, os.path.join(data_dir,'%s.png' % fname))
#    save_to_eps(fig, os.path.join(data_dir,'%s.eps' % fname))
#    plt.close(fig)
#
#    fig=plt.figure()
#    plt.subplot(411)
#    plt.title('Probabilistic Population - low->high')
#    plt.imshow(prob_low_high_pop_monitor['e'][:],aspect='auto')
#    plt.clim(0,1)
#    plt.colorbar()
#    plt.subplot(412)
#    plt.title('low->high baseline')
#    plt.imshow(prob_low_high_baseline_pop_monitor['e'][:],aspect='auto')
#    plt.clim(0,1)
#    plt.colorbar()
#    plt.subplot(413)
#    plt.title('high->low')
#    plt.imshow(prob_high_low_pop_monitor['e'][:],aspect='auto')
#    plt.clim(0,1)
#    plt.colorbar()
#    plt.subplot(414)
#    plt.title('high->low baseline')
#    plt.imshow(prob_high_low_baseline_pop_monitor['e'][:],aspect='auto')
#    plt.clim(0,1)
#    plt.colorbar()
#    fname='%s.baseline-%s.var.adaptation.prob.e' % (design,baseline)
#    save_to_png(fig, os.path.join(data_dir,'%s.png' % fname))
#    save_to_eps(fig, os.path.join(data_dir,'%s.eps' % fname))
#    plt.close(fig)
#
#    fig=plt.figure()
#    plt.title('Probabilistic Population')
#    plt.plot(prob_low_high_pop_monitor['total_e'][0],'b',label='low->high')
#    plt.plot(prob_low_high_baseline_pop_monitor['total_e'][0],'b-.',label='low->high baseline')
#    plt.plot(prob_high_low_pop_monitor['total_e'][0],'r',label='high->low')
#    plt.plot(prob_high_low_baseline_pop_monitor['total_e'][0],'r-.',label='high->low baseline')
#    plt.legend(loc='best')
#    fname='%s.baseline-%s.var.adaptation.prob.total_e' % (design,baseline)
#    save_to_png(fig, os.path.join(data_dir,'%s.png' % fname))
#    save_to_eps(fig, os.path.join(data_dir,'%s.eps' % fname))
#    plt.close(fig)
#
#    fig=plt.figure()
#    plt.title('Probabilistic Population')
#    plt.plot(prob_low_high_pop_monitor['total_r'][0],'b',label='low->high')
#    plt.plot(prob_low_high_baseline_pop_monitor['total_r'][0],'b-.',label='low->high baseline')
#    plt.plot(prob_high_low_pop_monitor['total_r'][0],'r',label='high->low')
#    plt.plot(prob_high_low_baseline_pop_monitor['total_r'][0],'r-.',label='high->low baseline')
#    plt.legend(loc='best')
#    fname='%s.baseline-%s.var.adaptation.prob.total_r' % (design,baseline)
#    save_to_png(fig, os.path.join(data_dir,'%s.png' % fname))
#    save_to_eps(fig, os.path.join(data_dir,'%s.eps' % fname))
#    plt.close(fig)
#
#    fig=plt.figure()
#    plt.title('Probabilistic Population')
#    plt.plot(prob_low_high_voxel_monitor['G_total'][0][0:100000],'b',label='low->high')
#    plt.plot(prob_low_high_baseline_voxel_monitor['G_total'][0][0:100000],'b-.',label='low->high baseline')
#    plt.plot(prob_high_low_voxel_monitor['G_total'][0][0:100000],'r',label='high->low')
#    plt.plot(prob_high_low_baseline_voxel_monitor['G_total'][0][0:100000],'r-.',label='high->low baseline')
#    plt.legend(loc='best')
#    fname='%s.baseline-%s.var.adaptation.prob.g_total' % (design,baseline)
#    save_to_png(fig, os.path.join(data_dir,'%s.png' % fname))
#    save_to_eps(fig, os.path.join(data_dir,'%s.eps' % fname))
#    plt.close(fig)
#
#    fig=plt.figure()
#    plt.title('Sampling Population')
#    plt.plot(samp_low_high_voxel_monitor['y'][0], 'b', label='low->high')
#    plt.plot(samp_low_high_baseline_voxel_monitor['y'][0], 'b-.', label='low->high baseline')
#    plt.plot(samp_high_low_voxel_monitor['y'][0], 'r', label='high->low')
#    plt.plot(samp_high_low_baseline_voxel_monitor['y'][0], 'r-.', label='high->low baseline')
#    plt.legend(loc='best')
#    fname='%s.baseline-%s.var.adaptation.samp.bold' % (design,baseline)
#    save_to_png(fig, os.path.join(data_dir,'%s.png' % fname))
#    save_to_eps(fig, os.path.join(data_dir,'%s.eps' % fname))
#    plt.close(fig)
#
#    fig=plt.figure()
#    plt.subplot(411)
#    plt.title('Sampling Population - low->high')
#    plt.imshow(samp_low_high_pop_monitor['e'][:],aspect='auto')
#    plt.clim(0,1)
#    plt.colorbar()
#    plt.subplot(412)
#    plt.title('low->high baseline')
#    plt.imshow(samp_low_high_baseline_pop_monitor['e'][:],aspect='auto')
#    plt.clim(0,1)
#    plt.colorbar()
#    plt.subplot(413)
#    plt.title('high->low')
#    plt.imshow(samp_high_low_pop_monitor['e'][:],aspect='auto')
#    plt.clim(0,1)
#    plt.colorbar()
#    plt.subplot(414)
#    plt.title('high->low baseline')
#    plt.imshow(samp_high_low_baseline_pop_monitor['e'][:],aspect='auto')
#    plt.clim(0,1)
#    plt.colorbar()
#    fname='%s.baseline-%s.var.adaptation.samp.e' % (design,baseline)
#    save_to_png(fig, os.path.join(data_dir,'%s.png' % fname))
#    save_to_eps(fig, os.path.join(data_dir,'%s.eps' % fname))
#    plt.close(fig)
#
#    fig=plt.figure()
#    plt.title('Sampling Population')
#    plt.plot(samp_low_high_pop_monitor['total_e'][0],'b',label='low->high')
#    plt.plot(samp_low_high_baseline_pop_monitor['total_e'][0],'b-.',label='low->high baseline')
#    plt.plot(samp_high_low_pop_monitor['total_e'][0],'r',label='high->low')
#    plt.plot(samp_high_low_baseline_pop_monitor['total_e'][0],'r-.',label='high->low baseline')
#    plt.legend(loc='best')
#    fname='%s.baseline-%s.var.adaptation.samp.total_e' % (design,baseline)
#    save_to_png(fig, os.path.join(data_dir,'%s.png' % fname))
#    save_to_eps(fig, os.path.join(data_dir,'%s.eps' % fname))
#    plt.close(fig)
#
#    fig=plt.figure()
#    plt.title('Sampling Population')
#    plt.plot(samp_low_high_pop_monitor['total_r'][0],'b',label='low->high')
#    plt.plot(samp_low_high_baseline_pop_monitor['total_r'][0],'b-.',label='low->high baseline')
#    plt.plot(samp_high_low_pop_monitor['total_r'][0],'r',label='high->low')
#    plt.plot(samp_high_low_baseline_pop_monitor['total_r'][0],'r-.',label='high->low baseline')
#    plt.legend(loc='best')
#    fname='%s.baseline-%s.var.adaptation.samp.total_r' % (design,baseline)
#    save_to_png(fig, os.path.join(data_dir,'%s.png' % fname))
#    save_to_eps(fig, os.path.join(data_dir,'%s.eps' % fname))
#    plt.close(fig)
#
#    fig=plt.figure()
#    plt.title('Sampling Population')
#    plt.plot(samp_low_high_voxel_monitor['G_total'][0][0:100000],'b',label='low->high')
#    plt.plot(samp_low_high_baseline_voxel_monitor['G_total'][0][0:100000],'b-.',label='low->high baseline')
#    plt.plot(samp_high_low_voxel_monitor['G_total'][0][0:100000],'r',label='high->low')
#    plt.plot(samp_high_low_baseline_voxel_monitor['G_total'][0][0:100000],'r-.',label='high->low baseline')
#    plt.legend(loc='best')
#    fname='%s.baseline-%s.var.var.adaptation.samp.g_total' % (design,baseline)
#    save_to_png(fig, os.path.join(data_dir,'%s.png' % fname))
#    save_to_eps(fig, os.path.join(data_dir,'%s.eps' % fname))
#    plt.close(fig)


def run_isi_simulation():
    N=150
    network_params=default_params
    trial_duration=2*second
    var=10
    x1=50
    x2=100
    isi_times=range(25,750,25)
    stim_dur=100*ms
    adaptation=np.zeros(len(isi_times))
    for i,isi in enumerate(isi_times):
        print('Testing isi=%dms' % isi)
        stim1_start_time=1*second
        stim1_end_time=stim1_start_time+stim_dur

        stim2_start_time=stim1_end_time+isi*ms
        stim2_end_time=stim2_start_time+stim_dur

        same_pop_monitor,same_voxel_monitor=run_pop_code(ProbabilisticPopulationCode, N, network_params, [x1,x1], [var,var],
            [stim1_start_time,stim2_start_time], [stim1_end_time,stim2_end_time],trial_duration)
        diff_pop_monitor,diff_voxel_monitor=run_pop_code(ProbabilisticPopulationCode, N, network_params, [x1,x2], [var,var],
            [stim1_start_time,stim2_start_time], [stim1_end_time,stim2_end_time],trial_duration)

        same_y_max=np.max(same_voxel_monitor['y'][0])
        diff_y_max=np.max(diff_voxel_monitor['y'][0])
        adaptation[i]=(diff_y_max-same_y_max)/diff_y_max*100.0

    data_dir='../../data/adaptation/isi'
    fig=plt.figure()
    plt.plot(isi_times,adaptation)
    plt.xlabel('ISI (ms)')
    plt.ylabel('Adaptation')
    fname='adaptation.isi.%s'
    save_to_png(fig, os.path.join(data_dir,fname % 'png'))
    save_to_eps(fig, os.path.join(data_dir,fname % 'eps'))
    plt.close(fig)


def test_simulation():
    N=150
    network_params=default_params
    network_params.tau_a=5*second
    trial_duration=10*second
    #isi=6*second
    isi=100*ms
    #stim_duration=100*ms
    stim_duration=300*ms
    var=10
    x1=50
    x2=100
    stim1_start_time=1*second
    stim1_end_time=stim1_start_time+stim_duration
    stim2_start_time=stim1_end_time+isi
    stim2_end_time=stim2_start_time+stim_duration

    same_pop_monitor,same_voxel_monitor=run_pop_code(ProbabilisticPopulationCode, N, network_params, [x1,x1], [var,var],
        [stim1_start_time,stim2_start_time], [stim1_end_time,stim2_end_time],trial_duration)
    diff_pop_monitor,diff_voxel_monitor=run_pop_code(ProbabilisticPopulationCode, N, network_params, [x1,x2], [var,var],
        [stim1_start_time,stim2_start_time], [stim1_end_time,stim2_end_time],trial_duration)
    single_pop_monitor,single_voxel_monitor=run_pop_code(ProbabilisticPopulationCode, N, network_params, [x1], [var],
        [stim1_start_time], [stim1_end_time], trial_duration)

    data_dir='../../data/adaptation/adaptation_test/rapid'
    fig=plt.figure()
    plt.subplot(311)
    plt.title('Same')
    plt.imshow(same_pop_monitor['r'][:],aspect='auto')
    plt.xlabel('time')
    plt.ylabel('neuron')
    plt.colorbar()
    plt.subplot(312)
    plt.title('Different')
    plt.imshow(diff_pop_monitor['r'][:],aspect='auto')
    plt.xlabel('time')
    plt.ylabel('neuron')
    plt.colorbar()
    plt.subplot(313)
    plt.title('Single')
    plt.imshow(single_pop_monitor['r'][:],aspect='auto')
    plt.xlabel('time')
    plt.ylabel('neuron')
    plt.colorbar()
    fname='firing_rate.%s'
    save_to_png(fig, os.path.join(data_dir,fname % 'png'))
    save_to_eps(fig, os.path.join(data_dir,fname % 'eps'))
    plt.close(fig)

    fig=plt.figure()
    plt.subplot(311)
    plt.title('Same')
    plt.imshow(same_pop_monitor['e'][:],aspect='auto')
    plt.xlabel('time')
    plt.ylabel('neuron')
    plt.colorbar()
    plt.clim(0,1)
    plt.subplot(312)
    plt.title('Different')
    plt.imshow(diff_pop_monitor['e'][:],aspect='auto')
    plt.xlabel('time')
    plt.ylabel('neuron')
    plt.colorbar()
    plt.clim(0,1)
    plt.subplot(313)
    plt.title('Single')
    plt.imshow(single_pop_monitor['e'][:],aspect='auto')
    plt.xlabel('time')
    plt.ylabel('neuron')
    plt.colorbar()
    plt.clim(0,1)
    fname='efficacy.%s'
    save_to_png(fig, os.path.join(data_dir,fname % 'png'))
    save_to_eps(fig, os.path.join(data_dir,fname % 'eps'))
    plt.close(fig)

    fig=plt.figure()
    plt.title('BOLD')
    plt.plot(same_voxel_monitor['y'][0],label='same')
    plt.plot(diff_voxel_monitor['y'][0],label='different')
    plt.plot(single_voxel_monitor['y'][0],label='single')
    plt.legend(loc='best')
    fname='bold.%s'
    save_to_png(fig, os.path.join(data_dir,fname % 'png'))
    save_to_eps(fig, os.path.join(data_dir,fname % 'eps'))
    plt.close(fig)

    fig=plt.figure()
    plt.plot(same_pop_monitor['total_e'][0],label='same')
    plt.plot(diff_pop_monitor['total_e'][0],label='different')
    plt.plot(single_pop_monitor['total_e'][0],label='single')
    plt.legend(loc='best')
    fname='total_e.%s'
    save_to_png(fig, os.path.join(data_dir,fname % 'png'))
    save_to_eps(fig, os.path.join(data_dir,fname % 'eps'))
    plt.close(fig)

    fig=plt.figure()
    plt.plot(same_pop_monitor['total_r'][0],label='same')
    plt.plot(diff_pop_monitor['total_r'][0],label='different')
    plt.plot(single_pop_monitor['total_r'][0],label='single')
    plt.legend(loc='best')
    fname='total_r.%s'
    save_to_png(fig, os.path.join(data_dir,fname % 'png'))
    save_to_eps(fig, os.path.join(data_dir,fname % 'eps'))
    plt.close(fig)

    fig=plt.figure()
    plt.plot(same_voxel_monitor['G_total'][0][0:100000],label='same')
    plt.plot(diff_voxel_monitor['G_total'][0][0:100000],label='different')
    plt.plot(single_voxel_monitor['G_total'][0][0:100000],label='single')
    plt.legend(loc='best')
    fname='g_total.%s'
    save_to_png(fig, os.path.join(data_dir,fname % 'png'))
    save_to_eps(fig, os.path.join(data_dir,fname % 'eps'))
    plt.close(fig)


def demo(N, network_params, trial_duration, x1, x2, low_var, high_var, isi, stim_dur):
    stim1_start_time=1*second
    stim1_end_time=stim1_start_time+stim_dur

    stim2_start_time=stim1_end_time+isi
    stim2_end_time=stim2_start_time+stim_dur

    low_var_prob_pop_monitor,low_var_prob_voxel_monitor=run_pop_code(ProbabilisticPopulationCode, N, network_params,
        [x1,x2],[low_var,low_var], [stim1_start_time,stim2_start_time], [stim1_end_time,stim2_end_time],trial_duration)

    high_var_prob_pop_monitor,high_var_prob_voxel_monitor=run_pop_code(ProbabilisticPopulationCode, N, network_params,
        [x1,x2],[high_var,high_var], [stim1_start_time,stim2_start_time], [stim1_end_time,stim2_end_time],
        trial_duration)

    low_var_samp_pop_monitor,low_var_samp_voxel_monitor=run_pop_code(SamplingPopulationCode, N, network_params, [x1,x2],
        [low_var,low_var], [stim1_start_time,stim2_start_time], [stim1_end_time,stim2_end_time],trial_duration)

    high_var_samp_pop_monitor,high_var_samp_voxel_monitor=run_pop_code(SamplingPopulationCode, N, network_params, [x1,x2],
        [high_var,high_var], [stim1_start_time,stim2_start_time], [stim1_end_time,stim2_end_time],trial_duration)

    data_dir='../../data/adaptation/demo'

    fig=plt.figure()
    plt.subplot(411)
    plt.title('Probabilistic population, low variance - rate')
    plt.imshow(low_var_prob_pop_monitor['r'][:],aspect='auto')
    plt.xlabel('time')
    plt.ylabel('neuron')
    plt.colorbar()
    plt.clim(0,.2)
    plt.subplot(412)
    plt.title('Probabilistic population, high variance - rate')
    plt.imshow(high_var_prob_pop_monitor['r'][:],aspect='auto')
    plt.xlabel('time')
    plt.ylabel('neuron')
    plt.colorbar()
    plt.clim(0,.2)
    plt.subplot(413)
    plt.title('Sampling population, low variance - rate')
    plt.imshow(low_var_samp_pop_monitor['r'][:],aspect='auto')
    plt.xlabel('time')
    plt.ylabel('neuron')
    plt.colorbar()
    plt.clim(0,.2)
    plt.subplot(414)
    plt.title('Sampling population, high variance - rate')
    plt.imshow(high_var_samp_pop_monitor['r'][:],aspect='auto')
    plt.xlabel('time')
    plt.ylabel('neuron')
    plt.colorbar()
    plt.clim(0,.2)
    fname='firing_rate.%s'
    save_to_png(fig, os.path.join(data_dir,fname % 'png'))
    save_to_eps(fig, os.path.join(data_dir,fname % 'eps'))
    plt.close(fig)

    fig=plt.figure()
    plt.subplot(411)
    plt.title('Probabilistic population, low variance - efficacy')
    plt.imshow(low_var_prob_pop_monitor['e'][:],aspect='auto')
    plt.xlabel('time')
    plt.ylabel('neuron')
    plt.colorbar()
    plt.clim(0,1)
    plt.subplot(412)
    plt.title('Probabilistic population, high variance - efficacy')
    plt.imshow(high_var_prob_pop_monitor['e'][:],aspect='auto')
    plt.xlabel('time')
    plt.ylabel('neuron')
    plt.colorbar()
    plt.clim(0,1)
    plt.subplot(413)
    plt.title('Sampling population, low variance - efficacy')
    plt.imshow(low_var_samp_pop_monitor['e'][:],aspect='auto')
    plt.xlabel('time')
    plt.ylabel('neuron')
    plt.colorbar()
    plt.clim(0,1)
    plt.subplot(414)
    plt.title('Sampling population, high variance - efficacy')
    plt.imshow(high_var_samp_pop_monitor['e'][:],aspect='auto')
    plt.xlabel('time')
    plt.ylabel('neuron')
    plt.colorbar()
    plt.clim(0,1)
    fname='efficacy.%s'
    save_to_png(fig, os.path.join(data_dir, fname % 'png'))
    save_to_eps(fig, os.path.join(data_dir, fname % 'eps'))
    plt.close(fig)

    fig=plt.figure()
    plt.title('BOLD')
    plt.plot(low_var_prob_voxel_monitor['y'][0],label='prob,low var')
    plt.plot(high_var_prob_voxel_monitor['y'][0],label='prob,high var')
    plt.plot(low_var_samp_voxel_monitor['y'][0],label='samp,low var')
    plt.plot(high_var_samp_voxel_monitor['y'][0],label='samp,high var')
    plt.legend(loc='best')
    fname='bold.%s'
    save_to_png(fig, os.path.join(data_dir, fname % 'png'))
    save_to_eps(fig, os.path.join(data_dir, fname % 'eps'))
    plt.close(fig)

    stim1_mid_time=stim1_start_time+(stim1_end_time-stim1_start_time)/2
    idx1=int(stim1_mid_time/defaultclock.dt)
    stim2_mid_time=stim2_start_time+(stim2_end_time-stim2_start_time)/2
    idx2=int(stim2_mid_time/defaultclock.dt)

    fig=plt.figure()
    plt.title('Probabilistic Population snapshot')
    plt.plot(low_var_prob_pop_monitor['r'][:,idx1],'r', label='low var, stim 1')
    plt.plot(low_var_prob_pop_monitor['r'][:,idx2],'r--', label='low var stim 2')
    plt.plot(high_var_prob_pop_monitor['r'][:,idx1],'b', label='high var, stim 1')
    plt.plot(high_var_prob_pop_monitor['r'][:,idx2],'b--', label='high var stim 2')
    plt.legend(loc='best')
    fname='prob_pop.firing_rate.snapshot.%s'
    save_to_png(fig, os.path.join(data_dir, fname % 'png'))
    save_to_eps(fig, os.path.join(data_dir, fname % 'eps'))
    plt.close(fig)

    fig=plt.figure()
    plt.title('Sampling Population snapshot')
    plt.plot(low_var_samp_pop_monitor['r'][:,idx1],'r', label='low var, stim 1')
    plt.plot(low_var_samp_pop_monitor['r'][:,idx2],'r--', label='low var, stim 2')
    plt.plot(high_var_samp_pop_monitor['r'][:,idx1],'b', label='high var, stim 1')
    plt.plot(high_var_samp_pop_monitor['r'][:,idx2],'b--', label='high var, stim 2')
    plt.legend(loc='best')
    fname='samp_pop.firing_rate.snapshot.%s'
    save_to_png(fig, os.path.join(data_dir, fname % 'png'))
    save_to_eps(fig, os.path.join(data_dir, fname % 'eps'))
    plt.close(fig)


if __name__=='__main__':
    #demo(150, default_params, 2.0*second, 50,75,5,15, 100*ms, 300*ms)
    #test_simulation()
    run_mean_adaptation_simulation()
    #run_uncertainty_adaptation_simulation()
    #run_isi_simulation()
    #run_full_adaptation_simulation()

