from brian import pA, nS
import os
import numpy as np
import subprocess
from brian.units import second, siemens, amp
from ezrcluster.launcher import Launcher
from pysbi.config import SRC_DIR
from pysbi.wta.run import get_wta_cmds
from pysbi.wta.analysis import FileInfo

def post_wta_dcs_jobs(nodes, p_e_e, p_e_i, p_i_i, p_i_e, background_freq, trials, start_nodes=True,
                      p_dcs=0*pA, i_dcs=0*pA):
    num_groups=2
    trial_duration=4*second
    mu_0=40.0
    p_a=mu_0/100.0
    p_b=p_a
    launcher=Launcher(nodes)
    if start_nodes:
        launcher.set_application_script(os.path.join(SRC_DIR, 'sh/ezrcluster-application-script.sh'))
        launcher.start_nodes()

    contrast_range=[0.0, .016, .032, .064, .096, .128, .256, .512]
    for i,contrast in enumerate(contrast_range):
        inputs=np.zeros(2)
        inputs[0]=mu_0+p_a*contrast*100.0
        inputs[1]=mu_0-p_b*contrast*100.0
        #inputs[0]=40.0+(input_sum*(contrast+1.0)/2.0)
        #inputs[1]=40.0+input_sum-(input_sum*(contrast+1.0)/2.0)
        for t in trials:
            np.random.shuffle(inputs)
            cmds,log_file_template,out_file=get_wta_cmds(num_groups, inputs, background_freq, trial_duration,
                p_e_e, p_e_i, p_i_i, p_i_e, contrast, t, p_dcs=p_dcs, i_dcs=i_dcs, record_lfp=True,
                record_voxel=True, record_neuron_state=False, record_firing_rate=True, record_spikes=True,
                save_summary_only=False)
            launcher.add_job(cmds, log_file_template=log_file_template, output_file=out_file)


def get_dcs_cmds(num_groups, inputs, background_freq, trial_duration, p_e_e, p_e_i, p_i_i, p_i_e,
                 contrast,trial, muscimol_amount=0*nS, injection_site=0, p_dcs=0*amp, i_dcs=0*amp, record_lfp=True,
                 record_voxel=False, record_neuron_state=False, record_spikes=True, record_firing_rate=True,
                 save_summary_only=True):
    cmds = ['nohup', 'python', 'pysbi/wta/network.py']
    e_desc=''
    if muscimol_amount>0:
        e_desc+='lesioned'
    else:
        e_desc+='control'
    file_desc='wta.groups.%d.duration.%0.3f.p_e_e.%0.3f.p_e_i.%0.3f.p_i_i.%0.3f.p_i_e.%0.3f.p_dcs.%0.4f.i_dcs.%0.4f.%s.contrast.%0.4f.trial.%d' %\
              (num_groups, trial_duration, p_e_e, p_e_i, p_i_i, p_i_e, p_dcs/pA, i_dcs/pA, e_desc, contrast, trial)
    log_file='%s.log' % file_desc
    output_file='../../data/%s.h5' % file_desc
    cmds.append('--num_groups')
    cmds.append('%d' % num_groups)
    cmds.append('--inputs')
    cmds.append(','.join([str(input) for input in inputs]))
    cmds.append('--background')
    cmds.append('%0.3f' % background_freq)
    cmds.append('--trial_duration')
    cmds.append('%0.3f' % trial_duration)
    cmds.append('--p_e_e')
    cmds.append('%0.3f' % p_e_e)
    cmds.append('--p_e_i')
    cmds.append('%0.3f' % p_e_i)
    cmds.append('--p_i_i')
    cmds.append('%0.3f' % p_i_i)
    cmds.append('--p_i_e')
    cmds.append('%0.3f' % p_i_e)
    cmds.append('--output_file')
    cmds.append(output_file)
    if muscimol_amount>0:
        cmds.append('--muscimol_amount')
        cmds.append(str(muscimol_amount/siemens))
        cmds.append('--injection_site')
        cmds.append('%d' % injection_site)
    if p_dcs>0 or p_dcs<0:
        cmds.append('--p_dcs')
        cmds.append(str(p_dcs/pA))
    if i_dcs>0 or i_dcs<0:
        cmds.append('--i_dcs')
        cmds.append(str(i_dcs/pA))
    cmds.append('--record_lfp')
    if record_lfp:
        cmds.append('1')
    else:
        cmds.append('0')
    cmds.append('--record_voxel')
    if record_voxel:
        cmds.append('1')
    else:
        cmds.append('0')
    cmds.append('--record_neuron_state')
    if record_neuron_state:
        cmds.append('1')
    else:
        cmds.append('0')
    cmds.append('--record_spikes')
    if record_spikes:
        cmds.append('1')
    else:
        cmds.append('0')
    cmds.append('--record_firing_rate')
    if record_firing_rate:
        cmds.append('1')
    else:
        cmds.append('0')
    cmds.append('--save_summary_only')
    if save_summary_only:
        cmds.append('1')
    else:
        cmds.append('0')

    return cmds, log_file, output_file


def run_wta_dcs_jobs(p_e_e, p_e_i, p_i_i, p_i_e, background_freq, trials, p_dcs=0*pA, i_dcs=0*pA):
    num_groups=2
    trial_duration=4*second
    mu_0=40.0
    p_a=mu_0/100.0
    p_b=p_a

    contrast_range=[0.0, .016, .032, .064, .096, .128, .256, .512]
    for i,contrast in enumerate(contrast_range):
        inputs=np.zeros(2)
        #inputs[0]=40.0+(input_sum*(contrast+1.0)/2.0)
        #inputs[1]=40.0+input_sum-(input_sum*(contrast+1.0)/2.0)
        inputs[0]=mu_0+p_a*contrast*100.0
        inputs[1]=mu_0-p_b*contrast*100.0
        for t in trials:
            np.random.shuffle(inputs)
            cmds,log_file,out_file=get_dcs_cmds(num_groups, inputs, background_freq, trial_duration, p_e_e, p_e_i,
                p_i_i, p_i_e, contrast, t, p_dcs=p_dcs, i_dcs=i_dcs, record_lfp=True, record_voxel=True,
                record_neuron_state=False, record_firing_rate=True, record_spikes=True, save_summary_only=False)
            subprocess.Popen(cmds,stdout=log_file)


def run_broken_dcs_jobs(p_e_e, p_e_i, p_i_i, p_i_e, background_freq, trials, p_dcs=0*pA, i_dcs=0*pA):
    num_groups=2
    trial_duration=4*second
    mu_0=40.0
    p_a=mu_0/100.0
    p_b=p_a

    contrast_range=[0.0, .016, .032, .064, .096, .128, .256, .512]
    for i,contrast in enumerate(contrast_range):
        inputs=np.zeros(2)
        #inputs[0]=40.0+(input_sum*(contrast+1.0)/2.0)
        #inputs[1]=40.0+input_sum-(input_sum*(contrast+1.0)/2.0)
        inputs[0]=mu_0+p_a*contrast*100.0
        inputs[1]=mu_0-p_b*contrast*100.0
        for t in trials:
            np.random.shuffle(inputs)
            cmds,log_file_name,out_file=get_dcs_cmds(num_groups, inputs, background_freq, trial_duration, p_e_e, p_e_i,
                p_i_i, p_i_e, contrast, t, p_dcs=p_dcs, i_dcs=i_dcs, record_lfp=True, record_voxel=True,
                record_neuron_state=False, record_firing_rate=True, record_spikes=True, save_summary_only=False)
            try:
                data=FileInfo(out_file)
            except:
                log_file=open(log_file_name,'w  ')
                subprocess.Popen(cmds,stdout=log_file)