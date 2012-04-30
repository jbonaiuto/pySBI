from math import exp
from brian import Equations, NeuronGroup, Parameters, second
from brian.neurongroup import linked_var
from brian.stdunits import nA

default_params=Parameters(
    G_base=28670*nA,
    # synaptic efficacy (value from Zheng et al., 2002)
    eta=0.5 * second,
    # signal decay time constant (value from Zheng et al., 2002)
    tau_s=0.8 * second,
    # autoregulatory feedback time constant (value from Zheng et al., 2002)
    tau_f=0.4 * second,
    # Grubb's parameter
    alpha=0.2,
    # venous time constant (value from Friston et al., 2000)
    tau_o=1*second,
    # resting net oxygen extraction fraction by capillary bed (value
    # from Friston et al., 2000)
    e_base=0.8,
    # resting blood volume fraction (value from Friston et al., 2000)
    v_base=0.02,
    # resting intravascular transverse relaxation time (41.4ms at 4T, from
    # Yacoub et al, 2001)
    T_2E=.0414,
    # resting extravascular transverse relaxation time (23.5ms at 4T from
    # Yacoub et al, 2001)
    T_2I=.0235,
    # effective intravascular spin density (assumed to be equal to
    # extravascular spin density, from Behzadi & Liu, 2005)
    s_e_0=1,
    # effective extravascular spin density (assumed to be equal to
    # intravascular spin density, from Behzadi & Liu, 2005)
    s_i_0=1,
    # Main magnetic field strength
    B0=4.7,
    # Echo time
    TE=.02,
    # MR parameters (from Obata et al, 2004)
    computed_parameters = '''
        freq_offset=40.3*(B0/1.5)
        k1=4.3*freq_offset*e_base*TE
        r_0=25*(B0/1.5)**2
    ''')

class Voxel(NeuronGroup):
    def __init__(self, params=default_params, network=None):
        eqs=Equations('''
        G_total                                                                        : amp
        ds/dt=eta*(G_total-G_base)/G_base-s/tau_s-(f_in-1.0)/tau_f                     : 1
        df_in/dt=s/second                                                              : 1
        dv/dt=1/tau_o*(f_in-f_out)                                                     : 1
        f_out=v**(1.0/alpha)                                                           : 1
        o_e=1-(1-e_base)**(1/f_in)                                                     : 1
        dq/dt=1/tau_o*((f_in*o_e/e_base)-f_out*q/v)                                    : 1
        y=v_base*((k1+k2)*(1-q)-(k2+k3)*(1-v))                                         : 1
        G_base                                                                         : amp
        eta                                                                            : 1/second
        tau_s                                                                          : second
        tau_f                                                                          : second
        alpha                                                                          : 1
        tau_o                                                                          : second
        e_base                                                                         : 1
        v_base                                                                         : 1
        k1                                                                             : 1
        k2                                                                             : 1
        k3                                                                             : 1
        ''')
        NeuronGroup.__init__(self, 1, model=eqs, compile=True, freeze=True)

        self.G_base=params.G_base
        self.eta=params.eta
        self.tau_s=params.tau_s
        self.tau_f=params.tau_f
        self.alpha=params.alpha
        self.tau_o=params.tau_o
        self.e_base=params.e_base
        self.v_base=params.v_base
        self.k1=params.k1
        s_e=params.s_e_0*exp(-params.TE/params.T_2E)
        s_i=params.s_i_0*exp(-params.TE/params.T_2I)
        beta=s_e/s_i
        self.k2=beta*params.r_0*self.e_base*params.TE
        self.k3=beta-1

        self.f_in=1
        self.s=0
        self.f_in=1
        self.f_out=1
        self.v=1
        self.q=1
        self.y=0

        if network is not None:
            self.G_total = linked_var(network, 'g_syn', func=sum)