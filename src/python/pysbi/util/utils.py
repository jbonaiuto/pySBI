from time import time
from brian import ms
from brian.connections.delayconnection import DelayConnection
from matplotlib.backends.backend_agg import FigureCanvasAgg
import matplotlib.pylab as plt
import numpy as np

class Struct():
    def __init__(self):
        pass

def save_to_png(fig, output_file):
    fig.set_facecolor("#FFFFFF")
    canvas = FigureCanvasAgg(fig)
    canvas.print_png(output_file, dpi=72)

def save_to_eps(fig, output_file):
    fig.set_facecolor("#FFFFFF")
    canvas = FigureCanvasAgg(fig)
    canvas.print_eps(output_file, dpi=72)

def plot_raster(group_spike_neurons, group_spike_times, group_sizes):
    if len(group_spike_times) and len(group_spike_neurons)==len(group_spike_times):
        spacebetween = .1
        allsn = []
        allst = []
        for i, spike_times in enumerate(group_spike_times):
            mspikes=zip(group_spike_neurons[i],group_spike_times[i])

            if len(mspikes):
                sn, st = np.array(mspikes).T
            else:
                sn, st = np.array([]), np.array([])
            st /= ms
            allsn.append(i + ((1. - spacebetween) / float(group_sizes[i])) * sn)
            allst.append(st)
        sn = np.hstack(allsn)
        st = np.hstack(allst)
        fig=plt.figure()
        plt.plot(st, sn, '.')
        plt.ylabel('Group number')
        plt.xlabel('Time (ms)')
        return fig

def init_rand_weight_connection(pop1, pop2, target_name, min_weight, max_weight, p, delay, allow_self_conn=True):
    """
    Initialize a connection between two populations
    pop1 = population sending projections
    pop2 = populations receiving projections
    target_name = name of synapse type to project to
    min_weight = min weight of connection
    max_weight = max weight of connection
    p = probability of connection between any two neurons
    delay = delay
    allow_self_conn = allow neuron to project to itself
    """
    W=min_weight+np.random.rand(len(pop1),len(pop2))*(max_weight-min_weight)
    conn=DelayConnection(pop1, pop2, target_name, sparseness=p, W=W, delay=delay)

    # Remove self-connections
    if not allow_self_conn and len(pop1)==len(pop2):
        for j in xrange(len(pop1)):
            conn[j,j]=0.0
            conn.delay[j,j]=0.0
            conn[j,j]=0.0
            conn.delay[j,j]=0.0
    return conn

def init_connection(pop1, pop2, target_name, weight, p, delay, allow_self_conn=True):
    """
    Initialize a connection between two populations
    pop1 = population sending projections
    pop2 = populations receiving projections
    target_name = name of synapse type to project to
    weight = weight of connection
    p = probability of connection between any two neurons
    delay = delay
    allow_self_conn = allow neuron to project to itself
    """
    conn=DelayConnection(pop1, pop2, target_name, sparseness=p, weight=weight, delay=delay)

    # Remove self-connections
    if not allow_self_conn and len(pop1)==len(pop2):
        for j in xrange(len(pop1)):
            conn[j,j]=0.0
            conn.delay[j,j]=0.0
            conn[j,j]=0.0
            conn.delay[j,j]=0.0
    return conn





