from brian import set_global_preferences
import brian_no_units
import os
from brian.stdunits import Hz, nS
from brian.units import second
#from scikits.learn.linear_model.base import LinearRegression
from scikits.learn.linear_model import LinearRegression
from pysbi.wta.network import run_wta,default_params
import numpy as np
import matplotlib.pylab as plt

def test_wta(p_intra, p_inter, inputs, single_inh_pop=False, muscimol_amount=0*nS, injection_site=0):
    wta_params=default_params()
    wta_params.p_b_e=0.1
    wta_params.p_x_e=0.1
    wta_params.p_e_e=p_intra
    wta_params.p_e_i=p_inter
    wta_params.p_i_i=p_intra
    wta_params.p_i_e=p_inter

    input_freq=np.zeros(2)
    for i in range(2):
        input_freq[i]=float(inputs[i])*Hz

    run_wta(wta_params, 2, input_freq, 1.0*second, record_lfp=False, record_neuron_state=True, plot_output=True,
        single_inh_pop=single_inh_pop, muscimol_amount=muscimol_amount, injection_site=injection_site)

def test_contrast(p_intra, p_inter, num_trials, data_path, muscimol_amount=0*nS, injection_site=0, single_inh_pop=False):
    num_groups=2
    trial_duration=1.0*second

    wta_params=default_params()
    wta_params.p_b_e=0.1
    wta_params.p_x_e=0.1
    wta_params.p_e_e=p_intra
    wta_params.p_e_i=p_inter
    wta_params.p_i_i=p_intra
    wta_params.p_i_e=p_inter
    input_sum=40.0

    contrast_range=[0.0, 0.0625, 0.125, 0.25, 0.5, 1.0]
    trial_contrast=np.zeros([len(contrast_range)*num_trials,1])
    trial_max_bold=np.zeros(len(contrast_range)*num_trials)
    trial_max_exc_bold=np.zeros(len(contrast_range)*num_trials)
    for i,contrast in enumerate(contrast_range):
        print('Testing contrast %0.4f' % contrast)
        inputs=np.zeros(2)
        inputs[0]=(input_sum*(contrast+1.0)/2.0)
        inputs[1]=input_sum-inputs[0]

        for j in range(num_trials):
            print('Trial %d' % j)
            trial_contrast[i*num_trials+j]=contrast
            np.random.shuffle(inputs)

            input_freq=np.zeros(num_groups)
            for k in range(num_groups):
                input_freq[k]=float(inputs[k])*Hz

            file='wta.groups.%d.duration.%0.3f.p_b_e.%0.3f.p_x_e.%0.3f.p_e_e.%0.3f.p_e_i.%0.3f.p_i_i.%0.3f.p_i_e.%0.3f.contrast.%0.4f.trial.%d.h5' %\
                 (num_groups, trial_duration, wta_params.p_b_e, wta_params.p_x_e, wta_params.p_e_e, wta_params.p_e_i,
                  wta_params.p_i_i, wta_params.p_i_e, contrast, j)

            out_file=None
            if data_path is not None:
                out_file=os.path.join(data_path,file)
            wta_monitor=run_wta(wta_params, num_groups, input_freq, trial_duration, record_neuron_state=True,
                output_file=out_file, muscimol_amount=muscimol_amount, injection_site=injection_site, single_inh_pop=single_inh_pop)

            trial_max_bold[i*num_trials+j]=np.max(wta_monitor.voxel_monitor['y'].values)
            trial_max_exc_bold[i*num_trials+j]=np.max(wta_monitor.voxel_exc_monitor['y'].values)

    x_min=np.min(contrast_range)
    x_max=np.max(contrast_range)

    fig=plt.figure()
    clf=LinearRegression()
    clf.fit(trial_contrast,trial_max_bold)
    a=clf.coef_[0]
    b=clf.intercept_

    plt.plot(trial_contrast, trial_max_bold, 'x')
    plt.plot([x_min,x_max],[a*x_min+b,a*x_max+b],'--')
    plt.xlabel('Input Contrast')
    plt.ylabel('Max BOLD')
    plt.show()

    fig=plt.figure()
    clf=LinearRegression()
    clf.fit(trial_contrast,trial_max_exc_bold)
    a=clf.coef_[0]
    b=clf.intercept_

    plt.plot(trial_contrast, trial_max_exc_bold, 'o')
    plt.plot([x_min,x_max],[a*x_min+b,a*x_max+b],'--')
    plt.xlabel('Input Contrast')
    plt.ylabel('Max BOLD (exc only)')
    plt.show()

def test_contrast_lesion_one_param(p_range, trial_numbers, data_path, muscimol_amount=0*nS, injection_site=0,
                                   single_inh_pop=False):
    for p in p_range:
        param_data_path=os.path.join(data_path,'p.%0.3f' % p)
        if not os.path.exists(param_data_path):
            os.mkdir(param_data_path)
        test_contrast_lesion(p, p, trial_numbers, param_data_path,muscimol_amount=muscimol_amount,
            injection_site=injection_site,single_inh_pop=single_inh_pop, plot_summary=False)

def test_contrast_lesion_two_param(p_range, trial_numbers, data_path, muscimol_amount=0*nS, injection_site=0,
                                   single_inh_pop=False):
    for p_intra in p_range:
        for p_inter in p_range:
            param_data_path=os.path.join(data_path,'p_intra.%0.3f.p_inter.%0.3f' % (p_intra,p_inter))
            if not os.path.exists(param_data_path):
                os.mkdir(param_data_path)
            test_contrast_lesion(p_intra, p_inter, trial_numbers, param_data_path,muscimol_amount=muscimol_amount,
                injection_site=injection_site,single_inh_pop=single_inh_pop, plot_summary=False)

def test_contrast_lesion(p_intra, p_inter, trial_numbers, data_path, muscimol_amount=0*nS, injection_site=0,
                         single_inh_pop=False, plot_summary=True):
    num_groups=2
    trial_duration=1.0*second

    wta_params=default_params()
    wta_params.p_b_e=0.1
    wta_params.p_x_e=0.1
    wta_params.p_e_e=p_intra
    wta_params.p_e_i=p_inter
    wta_params.p_i_i=p_intra
    wta_params.p_i_e=p_inter
    input_sum=40.0

    contrast_range=[0.0, 0.0625, 0.125, 0.25, 0.5, 1.0]
    num_trials=len(trial_numbers)
    trial_contrast=np.zeros([len(contrast_range)*num_trials,1])
    trial_max_bold=np.zeros(len(contrast_range)*num_trials)
    trial_max_exc_bold=np.zeros(len(contrast_range)*num_trials)
    for i,contrast in enumerate(contrast_range):
        print('Testing contrast %0.4f' % contrast)
        inputs=np.zeros(2)
        inputs[0]=(input_sum*(contrast+1.0)/2.0)
        inputs[1]=input_sum-inputs[0]

        for j,trial_idx in enumerate(trial_numbers):
            print('Trial %d' % trial_idx)
            trial_contrast[i*num_trials+j]=contrast
            np.random.shuffle(inputs)

            input_freq=np.zeros(num_groups)
            for k in range(num_groups):
                input_freq[k]=float(inputs[k])*Hz

            file='wta.groups.%d.duration.%0.3f.p_b_e.%0.3f.p_x_e.%0.3f.p_e_e.%0.3f.p_e_i.%0.3f.p_i_i.%0.3f.p_i_e.%0.3f.contrast.%0.4f.trial.%d.h5' %\
                 (num_groups, trial_duration, wta_params.p_b_e, wta_params.p_x_e, wta_params.p_e_e, wta_params.p_e_i,
                  wta_params.p_i_i, wta_params.p_i_e, contrast, trial_idx)

            out_file=None
            if not data_path is None:
                out_file=os.path.join(data_path,file)
            wta_monitor=run_wta(wta_params, num_groups, input_freq, trial_duration, output_file=out_file,
                single_inh_pop=single_inh_pop, record_spikes=False, record_lfp=False, save_summary_only=True)

            trial_max_bold[i*num_trials+j]=np.max(wta_monitor.voxel_monitor['y'].values)
            trial_max_exc_bold[i*num_trials+j]=np.max(wta_monitor.voxel_exc_monitor['y'].values)

    lesioned_trial_max_bold=np.zeros(len(contrast_range)*num_trials)
    lesioned_trial_max_exc_bold=np.zeros(len(contrast_range)*num_trials)
    for i,contrast in enumerate(contrast_range):
        print('Testing contrast %0.4f' % contrast)
        inputs=np.zeros(2)
        inputs[0]=(input_sum*(contrast+1.0)/2.0)
        inputs[1]=input_sum-inputs[0]

        for j,trial_idx in enumerate(trial_numbers):
            print('Trial %d' % j)
            trial_contrast[i*num_trials+j]=contrast
            np.random.shuffle(inputs)

            input_freq=np.zeros(num_groups)
            for k in range(num_groups):
                input_freq[k]=float(inputs[k])*Hz

            file='lesioned.wta.groups.%d.duration.%0.3f.p_b_e.%0.3f.p_x_e.%0.3f.p_e_e.%0.3f.p_e_i.%0.3f.p_i_i.%0.3f.p_i_e.%0.3f.contrast.%0.4f.trial.%d.h5' %\
                 (num_groups, trial_duration, wta_params.p_b_e, wta_params.p_x_e, wta_params.p_e_e, wta_params.p_e_i,
                  wta_params.p_i_i, wta_params.p_i_e, contrast, trial_idx)

            out_file=None
            if not data_path is None:
                out_file=os.path.join(data_path,file)
            wta_monitor=run_wta(wta_params, num_groups, input_freq, trial_duration, output_file=out_file,
                muscimol_amount=muscimol_amount, injection_site=injection_site, single_inh_pop=single_inh_pop,
                record_spikes=False, record_lfp=False, save_summary_only=True)

            lesioned_trial_max_bold[i*num_trials+j]=np.max(wta_monitor.voxel_monitor['y'].values)
            lesioned_trial_max_exc_bold[i*num_trials+j]=np.max(wta_monitor.voxel_exc_monitor['y'].values)

    if plot_summary:
        x_min=np.min(contrast_range)
        x_max=np.max(contrast_range)

        fig=plt.figure()
        control_clf=LinearRegression()
        control_clf.fit(trial_contrast,trial_max_bold)
        control_a=control_clf.coef_[0]
        control_b=control_clf.intercept_

        lesion_clf=LinearRegression()
        lesion_clf.fit(trial_contrast,lesioned_trial_max_bold)
        lesion_a=lesion_clf.coef_[0]
        lesion_b=lesion_clf.intercept_

        plt.plot(trial_contrast, trial_max_bold, 'xb')
        plt.plot(trial_contrast, lesioned_trial_max_bold, 'xr')
        plt.plot([x_min,x_max],[control_a*x_min+control_b,control_a*x_max+control_b],'--b',label='Control')
        plt.plot([x_min,x_max],[lesion_a*x_min+lesion_b,lesion_a*x_max+lesion_b],'--r',label='Lesioned')
        plt.xlabel('Input Contrast')
        plt.ylabel('Max BOLD')
        plt.legend()
        plt.show()

        fig=plt.figure()
        control_exc_clf=LinearRegression()
        control_exc_clf.fit(trial_contrast,trial_max_exc_bold)
        control_exc_a=control_exc_clf.coef_[0]
        control_exc_b=control_exc_clf.intercept_

        lesion_exc_clf=LinearRegression()
        lesion_exc_clf.fit(trial_contrast,lesioned_trial_max_exc_bold)
        lesion_exc_a=lesion_exc_clf.coef_[0]
        lesion_exc_b=lesion_exc_clf.intercept_

        plt.plot(trial_contrast, trial_max_exc_bold, 'ob')
        plt.plot(trial_contrast, lesioned_trial_max_exc_bold, 'or')
        plt.plot([x_min,x_max],[control_exc_a*x_min+control_exc_b,control_exc_a*x_max+control_exc_b],'--b',label='Control')
        plt.plot([x_min,x_max],[lesion_exc_a*x_min+lesion_exc_b,lesion_exc_a*x_max+lesion_exc_b],'--r',label='Lesioned')
        plt.xlabel('Input Contrast')
        plt.ylabel('Max BOLD (exc only)')
        plt.legend()
        plt.show()