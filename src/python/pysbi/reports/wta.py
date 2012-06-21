from jinja2.environment import Environment
from jinja2.loaders import FileSystemLoader
import os
from brian.stdunits import nA, mA, Hz, ms
import matplotlib.pylab as plt
import numpy as np
from scikits.learn.linear_model.base import LinearRegression
from pysbi.analysis import FileInfo, get_roc_single_option, get_auc, get_auc_single_option, get_lfp_signal, run_bayesian_analysis
from pysbi.config import TEMPLATE_DIR
from pysbi.reports.summary import render_summary_report, SummaryData
from pysbi.reports.utils import all_trials_exist, get_tested_param_combos, make_report_dirs
from pysbi.utils import save_to_png, Struct, plot_raster


def create_all_reports(data_dir, num_groups, trial_duration, p_b_e_range, p_x_e_range, p_e_e_range, p_e_i_range,
                       p_i_i_range, p_i_e_range, num_trials, base_report_dir, regenerate_network_plots=True,
                       regenerate_trial_plots=True, smooth_missing_params=False,
                       summary_filename='wta_network_summary.h5'):

    make_report_dirs(base_report_dir)

    summary_data=SummaryData(num_groups=num_groups, num_trials=num_trials, trial_duration=trial_duration,
        p_b_e_range=p_b_e_range, p_x_e_range=p_x_e_range, p_e_e_range=p_e_e_range, p_e_i_range=p_e_i_range,
        p_i_i_range=p_i_i_range, p_i_e_range=p_i_e_range)

    bc_slope_dict={}
    bc_intercept_dict={}
    bc_r_sqr_dict={}
    auc_dict={}

    param_combos=get_tested_param_combos(data_dir, num_groups, trial_duration, num_trials)

    report_info=Struct()
    report_info.roc_auc={}
    report_info.bc_slope={}
    report_info.bc_intercept={}
    report_info.bc_r_sqr={}

    for (p_b_e,p_x_e,p_e_e,p_e_i,p_i_i,p_i_e) in param_combos:
        i=p_b_e_range.index(round(p_b_e,2))
        j=p_x_e_range.index(round(p_x_e,2))
        k=p_e_e_range.index(round(p_e_e,2))
        l=p_e_i_range.index(round(p_e_i,2))
        m=p_i_i_range.index(round(p_i_i,2))
        n=p_i_e_range.index(round(p_i_e,2))

        file_desc='wta.groups.%d.duration.%0.3f.p_b_e.%0.3f.p_x_e.%0.3f.p_e_e.%0.3f.p_e_i.%0.3f.p_i_i.%0.3f.p_i_e.%0.3f' %\
                  (num_groups, trial_duration, p_b_e, p_x_e, p_e_e, p_e_i, p_i_i, p_i_e)
        file_prefix=os.path.join(data_dir,file_desc)
        reports_dir=os.path.join(base_report_dir,file_desc)
        if all_trials_exist(file_prefix, num_trials):
            print('Creating report for %s' % file_desc)
            wta_report=create_wta_network_report(file_prefix, num_trials, reports_dir,
                regenerate_network_plots=regenerate_network_plots,
                regenerate_trial_plots=regenerate_trial_plots)

            if not (i,j,k,l,m,n) in bc_slope_dict:
                bc_slope_dict[(i,j,k,l,m,n)]=[]
            bc_slope_dict[(i,j,k,l,m,n)].append(wta_report.bold.bold_contrast_slope)
            if not (i,j,k,l,m,n) in bc_intercept_dict:
                bc_intercept_dict[(i,j,k,l,m,n)]=[]
            bc_intercept_dict[(i,j,k,l,m,n)].append(wta_report.bold.bold_contrast_intercept)
            if not (i,j,k,l,m,n) in bc_r_sqr_dict:
                bc_r_sqr_dict[(i,j,k,l,m,n)]=[]
            bc_r_sqr_dict[(i,j,k,l,m,n)].append(wta_report.bold.bold_contrast_r_sqr)
            if not (i,j,k,l,m,n) in auc_dict:
                auc_dict[(i,j,k,l,m,n)]=[]
            auc_dict[(i,j,k,l,m,n)].append(wta_report.roc.auc)

            report_info.roc_auc[(p_b_e,p_x_e,p_e_e,p_e_i,p_i_i,p_i_e)]=wta_report.roc.auc
            report_info.bc_slope[(p_b_e,p_x_e,p_e_e,p_e_i,p_i_i,p_i_e)]=wta_report.bold.bold_contrast_slope
            report_info.bc_intercept[(p_b_e,p_x_e,p_e_e,p_e_i,p_i_i,p_i_e)]=wta_report.bold.bold_contrast_intercept
            report_info.bc_r_sqr[(p_b_e,p_x_e,p_e_e,p_e_i,p_i_i,p_i_e)]=wta_report.bold.bold_contrast_r_sqr
        else:
            report_info.roc_auc[(p_b_e,p_x_e,p_e_e,p_e_i,p_i_i,p_i_e)]=0
            report_info.bc_slope[(p_b_e,p_x_e,p_e_e,p_e_i,p_i_i,p_i_e)]=0
            report_info.bc_intercept[(p_b_e,p_x_e,p_e_e,p_e_i,p_i_i,p_i_e)]=0
            report_info.bc_r_sqr[(p_b_e,p_x_e,p_e_e,p_e_i,p_i_i,p_i_e)]=0

    report_info.num_groups=num_groups
    report_info.trial_duration=trial_duration
    report_info.num_trials=num_trials
    report_info.p_b_e_range=p_b_e_range
    report_info.p_x_e_range=p_x_e_range
    report_info.p_e_e_range=p_e_e_range
    report_info.p_e_i_range=p_e_i_range
    report_info.p_i_i_range=p_i_i_range
    report_info.p_i_e_range=p_i_e_range

    summary_data.fill(auc_dict, bc_slope_dict, bc_intercept_dict, bc_r_sqr_dict,
        smooth_missing_params=smooth_missing_params)

    summary_data.write_to_file(os.path.join(base_report_dir,summary_filename))

    bayes_analysis=run_bayesian_analysis(summary_data.auc, summary_data.bc_slope, summary_data.bc_intercept,
        summary_data.bc_r_sqr, num_trials, p_b_e_range, p_e_e_range, p_e_i_range, p_i_e_range, p_i_i_range, p_x_e_range)

    render_summary_report(base_report_dir, bayes_analysis, p_b_e_range, p_e_e_range, p_e_i_range, p_i_e_range,
        p_i_i_range, p_x_e_range, report_info)


def create_wta_network_report(file_prefix, num_trials, reports_dir, regenerate_network_plots=True, regenerate_trial_plots=True):

    make_report_dirs(reports_dir)

    report_info=Struct()
    report_info.trials=[]

    (data_dir, data_file_prefix) = os.path.split(file_prefix)

    trial_contrast=np.zeros([num_trials,1])
    trial_max_bold=np.zeros(num_trials)
    trial_max_input=np.zeros([num_trials,1])
    trial_max_rate=np.zeros([num_trials])
    for i in range(num_trials):
        file_name='%s.trial.%d.h5' % (file_prefix, i)
        print('opening %s' % file_name)
        data=FileInfo(file_name)

        if not i:
            report_info.wta_params=data.wta_params
            report_info.voxel_params=data.voxel_params
            report_info.num_groups=data.num_groups
            report_info.trial_duration=data.trial_duration
            report_info.background_rate=data.background_rate
            report_info.stim_start_time=data.stim_start_time
            report_info.stim_end_time=data.stim_end_time
            report_info.network_group_size=data.network_group_size
            report_info.background_input_size=data.background_input_size
            report_info.task_input_size=data.task_input_size

        trial = create_trial_report(data, reports_dir, i, regenerate_plots=regenerate_trial_plots)
        trial_contrast[i]=trial.input_contrast
        trial_max_bold[i]=trial.max_bold
        trial_max_input[i]=trial.max_input
        trial_max_rate[i]=trial.max_rate
        report_info.trials.append(trial)

    clf=LinearRegression()
    clf.fit(trial_max_input,trial_max_rate)
    a=clf.coef_[0]
    b=clf.intercept_
    report_info.io_slope=a
    report_info.io_intercept=b
    report_info.io_r_sqr=clf.score(trial_max_input,trial_max_rate)

    furl='img/input_output_rate.png'
    fname=os.path.join(reports_dir, furl)
    report_info.input_output_rate_url=furl
    if regenerate_network_plots or not os.path.exists(fname):
        fig=plt.figure()
        plt.plot(trial_max_input, trial_max_rate, 'x')
        x_min=np.min(trial_max_input)
        x_max=np.max(trial_max_input)
        plt.plot([x_min,x_max],[x_min,x_max],'--')
        plt.plot([x_min,x_max],[a*x_min+b,a*x_max+b],'--')
        plt.xlabel('Max Input Rate')
        plt.ylabel('Max Population Rate')
        save_to_png(fig, fname)
        plt.close()

    report_info.bold=create_bold_report(reports_dir, trial_contrast, trial_max_bold,
        regenerate_plot=regenerate_network_plots)

    report_info.roc=create_roc_report(file_prefix, report_info.num_groups, num_trials, reports_dir,
        regenerate_plot=regenerate_network_plots)

    #create report
    template_file='wta_network_instance.html'
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template=env.get_template(template_file)

    output_file='wta_network.%s.html' % data_file_prefix
    fname=os.path.join(reports_dir,output_file)
    stream=template.stream(rinfo=report_info)
    stream.dump(fname)

    return report_info


def create_bold_report(reports_dir, trial_contrast, trial_max_bold, regenerate_plot=True):

    report_info=Struct()

    clf=LinearRegression()
    clf.fit(trial_contrast,trial_max_bold)
    a=clf.coef_[0]
    b=clf.intercept_
    report_info.bold_contrast_slope=a
    report_info.bold_contrast_intercept=b
    report_info.bold_contrast_r_sqr=clf.score(trial_contrast,trial_max_bold)

    furl='img/contrast_bold.png'
    fname=os.path.join(reports_dir, furl)
    report_info.contrast_bold_url=furl
    if regenerate_plot or not os.path.exists(fname):
        fig=plt.figure()
        plt.plot(trial_contrast, trial_max_bold, 'x')
        x_min=np.min(trial_contrast)
        x_max=np.max(trial_contrast)
        plt.plot([x_min,x_max],[a*x_min+b,a*x_max+b],'--')
        plt.xlabel('Input Contrast')
        plt.ylabel('Max BOLD')
        save_to_png(fig, fname)
        plt.close()

    return report_info

def create_trial_report(data, reports_dir, trial_idx, regenerate_plots=True):
    trial = Struct()
    trial.input_freq=data.input_freq
    trial.input_contrast=abs(data.input_freq[0]-data.input_freq[1])/sum(data.input_freq)

    max_input_idx=np.where(trial.input_freq==np.max(trial.input_freq))[0][0]
    trial.max_input=trial.input_freq[max_input_idx]
    trial.max_rate=np.max(data.e_firing_rates[max_input_idx])

    trial.e_raster_url = None
    trial.i_raster_url = None
    if data.e_spike_neurons is not None and data.i_spike_neurons is not None:
        furl='img/e_raster.trial.%d.png' % trial_idx
        fname=os.path.join(reports_dir, furl)
        trial.e_raster_url = furl
        if regenerate_plots or not os.path.exists(fname):
            e_group_sizes=[int(4*data.network_group_size/5) for i in range(data.num_groups)]
            fig=plot_raster(data.e_spike_neurons, data.e_spike_times, e_group_sizes)
            save_to_png(fig, fname)
            plt.close()

        furl='img/i_raster.trial.%d.png' % trial_idx
        fname=os.path.join(reports_dir, furl)
        trial.i_raster_url = furl
        if regenerate_plots or not os.path.exists(fname):
            i_group_sizes=[int(data.network_group_size/5) for i in range(data.num_groups)]
            fig=plot_raster(data.i_spike_neurons, data.i_spike_times, i_group_sizes)
            save_to_png(fig, fname)
            plt.close()

    trial.firing_rate_url = None
    if data.e_firing_rates is not None and data.i_firing_rates is not None:
        furl = 'img/firing_rate.trial.%d.png' % trial_idx
        fname = os.path.join(reports_dir, furl)
        trial.firing_rate_url = furl
        if regenerate_plots or not os.path.exists(fname):
            fig = plt.figure()
            ax = plt.subplot(211)
            for i, pop_rate in enumerate(data.e_firing_rates):
                ax.plot(np.array(range(len(pop_rate))) *.1, pop_rate / Hz, label='group %d' % i)
            plt.xlabel('Time (ms)')
            plt.ylabel('Firing Rate (Hz)')
            ax = plt.subplot(212)
            for i, pop_rate in enumerate(data.i_firing_rates):
                ax.plot(np.array(range(len(pop_rate))) *.1, pop_rate / Hz, label='group %d' % i)
            plt.xlabel('Time (ms)')
            plt.ylabel('Firing Rate (Hz)')
            save_to_png(fig, fname)
            plt.close()

    trial.neural_state_url=None
    if data.neural_state_rec is not None:
        furl = 'img/neural_state.trial.%d.png' % trial_idx
        fname = os.path.join(reports_dir, furl)
        trial.neural_state_url = furl
        if regenerate_plots or not os.path.exists(fname):
            fig = plt.figure()
            for i in range(data.num_groups):
                times=np.array(range(len(data.neural_state_rec['g_ampa_r'][i*2])))*.1
                ax = plt.subplot(data.num_groups * 100 + 20 + (i * 2 + 1))
                ax.plot(times, data.neural_state_rec['g_ampa_r'][i * 2] / nA, label='AMPA-recurrent')
                ax.plot(times, data.neural_state_rec['g_ampa_x'][i * 2] / nA, label='AMPA-task')
                ax.plot(times, data.neural_state_rec['g_ampa_b'][i * 2] / nA, label='AMPA-backgrnd')
                ax.plot(times, data.neural_state_rec['g_nmda'][i * 2] / nA, label='NMDA')
                ax.plot(times, data.neural_state_rec['g_gaba_a'][i * 2] / nA, label='GABA_A')
                plt.xlabel('Time (ms)')
                plt.ylabel('Conductance (nA)')
                ax = plt.subplot(data.num_groups * 100 + 20 + (i * 2 + 2))
                ax.plot(times, data.neural_state_rec['g_ampa_r'][i * 2 + 1] / nA, label='AMPA-recurrent')
                ax.plot(times, data.neural_state_rec['g_ampa_x'][i * 2 + 1] / nA, label='AMPA-task')
                ax.plot(times, data.neural_state_rec['g_ampa_b'][i * 2 + 1] / nA, label='AMPA-backgrnd')
                ax.plot(times, data.neural_state_rec['g_nmda'][i * 2 + 1] / nA, label='NMDA')
                ax.plot(times, data.neural_state_rec['g_gaba_a'][i * 2 + 1] / nA, label='GABA_A')
                plt.xlabel('Time (ms)')
                plt.ylabel('Conductance (nA)')
            save_to_png(fig, fname)
            plt.close()

    trial.lfp_url = None
    if data.lfp_rec is not None:
        furl = 'img/lfp.trial.%d.png' % trial_idx
        fname = os.path.join(reports_dir, furl)
        trial.lfp_url = furl
        if regenerate_plots or not os.path.exists(fname):
            fig = plt.figure()
            ax = plt.subplot(111)
            lfp=get_lfp_signal(data)
            ax.plot(np.array(range(len(lfp))), lfp / mA)
            plt.xlabel('Time (ms)')
            plt.ylabel('LFP (mA)')
            save_to_png(fig, fname)
            plt.close()

    trial.voxel_url = None
    trial.max_bold=0
    if data.voxel_rec is not None:
        trial.max_bold=np.max(data.voxel_rec['y'][0])
        furl = 'img/voxel.trial.%d.png' % trial_idx
        fname = os.path.join(reports_dir, furl)
        trial.voxel_url = furl
        if regenerate_plots or not os.path.exists(fname):
            end_idx=int(data.trial_duration/ms/.1)
            fig = plt.figure()
            ax = plt.subplot(211)
            ax.plot(np.array(range(end_idx))*.1, data.voxel_rec['G_total'][0][:end_idx] / nA)
            plt.xlabel('Time (ms)')
            plt.ylabel('Total Synaptic Activity (nA)')
            ax = plt.subplot(212)
            ax.plot(np.array(range(len(data.voxel_rec['y'][0])))*.1*ms, data.voxel_rec['y'][0])
            plt.xlabel('Time (s)')
            plt.ylabel('BOLD')
            save_to_png(fig, fname)
            plt.close()
    return trial


def create_roc_report(file_prefix, num_groups, num_trials, reports_dir, regenerate_plot=True):
    num_extra_trials=10
    roc_report=Struct()
    roc_report.auc=get_auc(file_prefix, num_trials, num_extra_trials, num_groups)
    roc_report.auc_single_option=[]
    roc_url = 'img/roc.png'
    fname=os.path.join(reports_dir, roc_url)
    roc_report.roc_url=roc_url
    if regenerate_plot or not os.path.exists(fname):
        fig=plt.figure()
        for i in range(num_groups):
            roc=get_roc_single_option(file_prefix, num_trials, num_extra_trials, i)
            plt.plot(roc[:,0],roc[:,1],'x-',label='option %d' % i)
            roc_report.auc_single_option.append(get_auc_single_option(file_prefix, num_trials, num_extra_trials, i))
        plt.plot([0,1],[0,1],'--')
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        save_to_png(fig, fname)
        plt.close()
    return roc_report

if __name__=='__main__':
    param_range=[float(x)*.01 for x in range(0,11)]
    create_all_reports('../../data/wta-output',2,1.0,[0.1],[0.03],param_range,param_range,param_range,param_range,20,
        '../../data/reports',regenerate_network_plots=False,regenerate_trial_plots=False)