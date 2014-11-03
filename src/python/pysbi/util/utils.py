from scipy import optimize
from brian import ms, second
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


def weibull(x, alpha, beta):
    return 1.0-0.5*np.exp(-(x/alpha)**beta)


def rt_function(x, a, k, tr):
    return a/(k*x)*np.tanh(a*k*x)+tr


def exp_decay(x, n, lam):
    return n*np.exp(-lam*x)

def get_response_time(e_firing_rates, stim_start_time, stim_end_time, upper_threshold=60, lower_threshold=None, dt=.1*ms):
    rate_1=e_firing_rates[0]
    rate_2=e_firing_rates[1]
    times=np.array(range(len(rate_1)))*(dt/second)
    rt=None
    decision_idx=-1
    for idx,time in enumerate(times):
        time=time*second
        if stim_start_time < time < stim_end_time:
            if rt is None:
                if rate_1[idx]>=upper_threshold and (lower_threshold is None or rate_2[idx]<=lower_threshold):
                    decision_idx=0
                    rt=(time-stim_start_time)/ms
                    break
                elif rate_2[idx]>=upper_threshold and (lower_threshold is None or rate_1[idx]<=lower_threshold):
                    decision_idx=1
                    rt=(time-stim_start_time)/ms
                    break
    return rt,decision_idx

def reject_outliers(data, m = 2.):
    d = np.abs(data - np.median(data))
    mdev = np.median(d)
    s = d/mdev if mdev else 0
    return data[s<m]

class _baseFunctionFit:
    """Not needed by most users except as a superclass for developping your own functions

    You must overide the eval and inverse methods and a good idea to overide the _initialGuess
    method aswell.
    """

    def __init__(self, xx, yy, sems=1.0, guess=None, display=1,
                 expectedMin=0.5):
        self.xx = np.asarray(xx)
        self.yy = np.asarray(yy)
        self.sems = np.asarray(sems)
        self.expectedMin = expectedMin
        self.display=display
        # for holding error calculations:
        self.ssq=0
        self.rms=0
        self.chi=0
        #initialise parameters
        if guess==None:
            self.params = self._initialGuess()
        else:
            self.params = guess

        #do the calculations:
        self._doFit()

    def _doFit(self):
        #get some useful variables to help choose starting fit vals
        self.params = optimize.fmin_powell(self._getErr, self.params, (self.xx,self.yy,self.sems),disp=self.display)
        #        self.params = optimize.fmin_bfgs(self._getErr, self.params, None, (self.xx,self.yy,self.sems),disp=self.display)
        self.ssq = self._getErr(self.params, self.xx, self.yy, 1.0)
        self.chi = self._getErr(self.params, self.xx, self.yy, self.sems)
        self.rms = self.ssq/len(self.xx)

    def _initialGuess(self):
        xMin = min(self.xx); xMax = max(self.xx)
        xRange=xMax-xMin; xMean= (xMax+xMin)/2.0
        guess=[xMean, xRange/5.0]
        return guess

    def _getErr(self, params, xx,yy,sems):
        mod = self.eval(xx, params)
        err = sum((yy-mod)**2/sems)
        return err

    def eval(self, xx=None, params=None):
        """Returns fitted yy for any given xx value(s).
        Uses the original xx values (from which fit was calculated)
        if none given.

        If params is specified this will override the current model params."""
        yy=xx
        return yy

    def inverse(self, yy, params=None):
        """Returns fitted xx for any given yy value(s).

        If params is specified this will override the current model params.
        """
        #define the inverse for your function here
        xx=yy
        return xx


class FitWeibull(_baseFunctionFit):
    """Fit a Weibull function (either 2AFC or YN)
    of the form::

        y = chance + (1.0-chance)*(1-exp( -(xx/alpha)**(beta) ))

    and with inverse::

        x = alpha * (-log((1.0-y)/(1-chance)))**(1.0/beta)

    After fitting the function you can evaluate an array of x-values
    with ``fit.eval(x)``, retrieve the inverse of the function with
    ``fit.inverse(y)`` or retrieve the parameters from ``fit.params``
    (a list with ``[alpha, beta]``)"""
    def eval(self, xx=None, params=None):
        if params==None:  params=self.params #so the user can set params for this particular eval
        alpha = params[0];
        if alpha<=0: alpha=0.001
        beta = params[1]
        xx = np.asarray(xx)
        yy =  self.expectedMin + (1.0-self.expectedMin)*(1-np.exp( -(xx/alpha)**(beta) ))
        return yy
    def inverse(self, yy, params=None):
        if params==None: params=self.params #so the user can set params for this particular inv
        alpha = params[0]
        beta = params[1]
        xx = alpha * (-np.log((1.0-yy)/(1-self.expectedMin))) **(1.0/beta)
        return xx

class FitRT(_baseFunctionFit):
    """Fit a Weibull function (either 2AFC or YN)
    of the form::

        y = chance + (1.0-chance)*(1-exp( -(xx/alpha)**(beta) ))

    and with inverse::

        x = alpha * (-log((1.0-y)/(1-chance)))**(1.0/beta)

    After fitting the function you can evaluate an array of x-values
    with ``fit.eval(x)``, retrieve the inverse of the function with
    ``fit.inverse(y)`` or retrieve the parameters from ``fit.params``
    (a list with ``[alpha, beta]``)"""
    def eval(self, xx=None, params=None):
        if params==None:  params=self.params #so the user can set params for this particular eval
        a = params[0]
        k = params[1]
        tr = params[2]
        xx = np.asarray(xx)
        yy = a*np.tanh(k*xx)+tr
        return yy
    def inverse(self, yy, params=None):
        if params==None: params=self.params #so the user can set params for this particular inv
        a = params[0]
        k = params[1]
        tr = params[2]
        xx = np.arctanh((yy-tr)/a)/k
        return xx

class FitSigmoid(_baseFunctionFit):
    def eval(self, xx=None, params=None):
        if params==None:  params=self.params #so the user can set params for this particular eval
        x0 = params[0]
        y0 = params[1]
        c = params[2]
        k = params[3]
        xx = np.asarray(xx)
        yy = c/(1.0+np.exp(-k*(xx-x0)))+y0
        return yy

    def inverse(self, yy, params=None):
        if params==None:  params=self.params #so the user can set params for this particular eval
        x0 = params[0]
        y0 = params[1]
        c = params[2]
        k = params[3]
        xx = x0-(np.ln(c/(yy-y0)-1)/k)
        return xx