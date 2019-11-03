import numpy as np
# import uproot
import json
import datetime
import pytz
import os
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.lines as mlines
import matplotlib.ticker as ticker
from matplotlib.font_manager import FontProperties

# Define some plot constants
NBINS=37
X_MIN=70
X_MAX=181
Y_MIN=0
Y_MAX=31.5
DELTA_Y = Y_MAX - Y_MIN
HIST_LINEWIDTH=2.0

# Colours
green_m5 = '#558953'
cyan_m9 = '#89bffe'
gray = '#a9a9a9'

edges = np.asarray([ 70.,  73.,  76.,  79.,  82.,  85.,  88.,  91.,  94.,  97., 100.,
        103., 106., 109., 112., 115., 118., 121., 124., 127., 130., 133.,
        136., 139., 142., 145., 148., 151., 154., 157., 160., 163., 166.,
        169., 172., 175., 178., 181.])

ctrs = edges[:-1] + 1.5

constants = {
    'xsecs': {
        'scalexsecHZZ12': 0.0065,
        'scalexsecHZZ11': 0.0057,
        'xsecZZ412': 0.077,
        'xsecZZ2mu2e12': 0.18,
        'xsecZZ411': 0.067,
        'xsecZZ2mu2e11': 0.15,
        'xsecTTBar12' : 200.,
        'xsecTTBar11' : 177.31,
        'xsecDY5012' : 2955.,
        'xsecDY1012' : 10.742,
        'xsecDY5011' : 2475.,
        'xsecDY1011' : 9507.,
    },
    'sfs': {
        'sfZZ': 1.386,
        'sfTTBar11': 0.11,
        'sfDY': 1.12,
    },
}


lumi_settings = {
    '2011': {
        'mass4e_8TeV_low': 'el_stream_2011',
        'mass4mu_8TeV_low': 'mu_stream_2011',
        'mass2mu2e_8TeV_low': 'mu_stream_2011'
    },
    '2012': {
        'mass4e_8TeV_low': 'el_stream_2012',
        'mass4mu_8TeV_low': 'mu_stream_2012',
        'mass2mu2e_8TeV_low': 'mu_stream_2012'
    },
}

sampledata = {
    # Higgs 2012
    'sm12_dr53x_smhiggstozzto4l_m-125_8tev-pw15-j3-py6': {
        'id': 'Higgs 2012',
        'group': 'higgs',
        'datatype': 'mc',
        'lumi': '2012',
        'xsec': constants['xsecs']['scalexsecHZZ12'],
        'pickup': ['mass4mu_8TeV_low', 'mass4e_8TeV_low', 'mass2mu2e_8TeV_low'],
        'nfiles': '34'
    },
    # Higgs 2011
    'sm11legdr_smhiggstozzto4l_m-125_7tev-pw15-j3-py6': {
        'id': 'Higgs 2011',
        'group': 'higgs',
        'datatype': 'mc',
        'lumi': '2011',
        'xsec': constants['xsecs']['scalexsecHZZ11'],
        'pickup': ['mass4mu_8TeV_low', 'mass4e_8TeV_low', 'mass2mu2e_8TeV_low'],
        'nfiles': '22'
    },
    # ZZ 2012
    'sm12_dr53x_zzto4mu_8tev-pw-py6': {
        'id': r'ZZ $\rightarrow 4\mu$ 2012',
        'group': 'zz',
        'datatype': 'mc',
        'lumi': '2012',
        'xsec': constants['xsecs']['xsecZZ412'] * constants['sfs']['sfZZ'],
        'pickup': ['mass4mu_8TeV_low'],
        'nfiles': '151'
    },
    'sm12_dr53x_zzto4e_8tev-pw-py6': {
        'id': r'ZZ $\rightarrow 4$e 2012',
        'group': 'zz',
        'datatype': 'mc',
        'lumi': '2012',
        'xsec': constants['xsecs']['xsecZZ412'] * constants['sfs']['sfZZ'],
        'pickup': ['mass4e_8TeV_low'],
        'nfiles': '143'
    },
    'sm12_dr53x_zzto2e2mu_8tev-pw-py6': {
        'id': r'ZZ $\rightarrow 2\mu$2e 2012',
        'group': 'zz',
        'datatype': 'mc',
        'lumi': '2012',
        'xsec': constants['xsecs']['xsecZZ2mu2e12'] * constants['sfs']['sfZZ'],
        'pickup': ['mass2mu2e_8TeV_low'],
        'nfiles': '161'
    },
    # ZZ 2011
    'sm11legdr_zzto4mu_mll4_7tev-pw-py6': {
        'id': r'ZZ $\rightarrow 4\mu$ 2011',
        'group': 'zz',
        'datatype': 'mc',
        'lumi': '2011',
        'xsec': constants['xsecs']['xsecZZ411'] * constants['sfs']['sfZZ'],
        'pickup': ['mass4mu_8TeV_low'],
        'nfiles': '92'
    },
    'sm11legdr_zzto4e_mll4_7tev-pw-py6': {
        'id': r'ZZ $\rightarrow 4$e 2011',
        'group': 'zz',
        'datatype': 'mc',
        'lumi': '2011',
        'xsec': constants['xsecs']['xsecZZ411'] * constants['sfs']['sfZZ'],
        'pickup': ['mass4e_8TeV_low'],
        'nfiles': '96'
    },
    'sm11legdr_zzto2e2mu_mll4_7tev-pw-py6': {
        'id': r'ZZ $\rightarrow 2\mu$2e 2011',
        'group': 'zz',
        'datatype': 'mc',
        'lumi': '2011',
        'xsec': constants['xsecs']['xsecZZ2mu2e11'] * constants['sfs']['sfZZ'],
        'pickup': ['mass2mu2e_8TeV_low'],
        'nfiles': '97'
    },
    # TTbar 2011
    'sm11legdr_ttto2l2nu2b_7tev-pw-py6': {
        'id': r'$t\bar{t}$ 2011',
        'group': 'ttbar',
        'datatype': 'mc',
        'lumi': '2011',
        'xsec': constants['xsecs']['xsecTTBar11'] * constants['sfs']['sfTTBar11'],
        'pickup': ['mass4mu_8TeV_low', 'mass4e_8TeV_low', 'mass2mu2e_8TeV_low'],
        'nfiles': '676'
    },
    # TTbar 2012
    'sm12_dr53x_ttbar_8tev-madspin_amcatnlo-herwig': {
        'id': r'$t\bar{t}$ 2012',
        'group': 'ttbar',
        'datatype': 'mc',
        'lumi': '2012',
        'xsec': constants['xsecs']['xsecTTBar12'],
        'pickup': ['mass4mu_8TeV_low', 'mass4e_8TeV_low', 'mass2mu2e_8TeV_low'],
        'nfiles': '696'
    },
    # DY 2011
    'sm11legdr_dyjetstoll_m-10to50_tunez2_7tev-py6': {
        'id': r'DY m10-50 2011',
        'group': 'dy',
        'datatype': 'mc',
        'lumi': '2011',
        'xsec': constants['xsecs']['xsecDY1011'] * constants['sfs']['sfDY'],
        'pickup': ['mass4mu_8TeV_low', 'mass4e_8TeV_low', 'mass2mu2e_8TeV_low'],
        'nfiles': '1771'
    },
    'sm11legdr_dyjetstoll_m-50_7tev-madgraph-py6-tauola': {
        'id': r'DY m50 2011',
        'group': 'dy',
        'datatype': 'mc',
        'lumi': '2011',
        'xsec': constants['xsecs']['xsecDY1011'] * constants['sfs']['sfDY'],
        'pickup': ['mass4mu_8TeV_low', 'mass4e_8TeV_low', 'mass2mu2e_8TeV_low'],
        'nfiles': '7501'
    },
    # DY 2012
    'sm12_dr53x_dyjetstoll_m-10to50_ht-200to400_tz2_8tev-mgt': {
        'id': r'DY m10-50 low 2012',
        'group': 'dy',
        'datatype': 'mc',
        'lumi': '2012',
        'xsec': constants['xsecs']['xsecDY1012'] * constants['sfs']['sfDY'],
        'pickup': ['mass4mu_8TeV_low', 'mass4e_8TeV_low', 'mass2mu2e_8TeV_low'],
        'nfiles': '430',
    },
    'sm12_dr53x_dyjetstoll_m-10to50_ht-400toinf_tz2_8tev-mgt': {
        'id': r'DY m10-50 high 2012',
        'group': 'dy',
        'datatype': 'mc',
        'lumi': '2012',
        'xsec': constants['xsecs']['xsecDY1012'] * constants['sfs']['sfDY'],
        'pickup': ['mass4mu_8TeV_low', 'mass4e_8TeV_low', 'mass2mu2e_8TeV_low'],
        'nfiles': '277',
    },
    'sm12_dr53x_dyjetstoll_m-50_tz2_8tev-mgtt-taupolaroff': {
        'id': r'DY m50 2012',
        'group': 'dy',
        'datatype': 'mc',
        'lumi': '2012',
        'xsec': constants['xsecs']['xsecDY1012'] * constants['sfs']['sfDY'],
        'pickup': ['mass4mu_8TeV_low', 'mass4e_8TeV_low', 'mass2mu2e_8TeV_low'],
        'nfiles': '2467',
    },
    # Data
    'cms_run2012b_doublemuparked_aod_22jan2013-v1': {
        'id': r'Data Run 2012B $\mu\mu$',
        'group': 'data',
        'datatype': 'data',
        'pickup': ['mass4mu_8TeV_low', 'mass2mu2e_8TeV_low'],
        'nfiles': '2279'
    },
    'cms_run2012b_doubleelectron_aod_22jan2013-v1': {
        'id': r'Data Run 2012B ee',
        'group': 'data',
        'datatype': 'data',
        'pickup': ['mass4e_8TeV_low'],
        'nfiles': '1643'
    },
    'cms_run2012c_doublemuparked_aod_22jan2013-v1': {
        'id': r'Data Run 2012C $\mu\mu$',
        'group': 'data',
        'datatype': 'data',
        'pickup': ['mass4mu_8TeV_low', 'mass2mu2e_8TeV_low'],
        'nfiles': '2920'
    },
    'cms_run2012c_doubleelectron_aod_22jan2013-v1': {
        'id': r'Data Run 2012C ee',
        'group': 'data',
        'datatype': 'data',
        'pickup': ['mass4e_8TeV_low'],
        'nfiles': '2389'
    },
    'cms_run2011a_doublemu_aod_12oct2013-v1': {
        'id': r'Data Run 2011A $\mu\mu$',
        'group': 'data',
        'datatype': 'data',
        'pickup': ['mass4mu_8TeV_low', 'mass2mu2e_8TeV_low'],
        'nfiles': '1378'
    },
    'cms_run2011a_doubleelectron_aod_12oct2013-v1': {
        'id': r'Data Run 2011A ee',
        'group': 'data',
        'datatype': 'data',
        'pickup': ['mass4e_8TeV_low'],
        'nfiles': '1697'
    },
}

colour_dict = {
    'higgs': 'red',
    'zz': cyan_m9,
    'dy': green_m5,
    'ttbar': gray,
    'data': 'black'
}


plotdata = {
    'samples': {},
    'lumi_data': {
        'mu_stream_2012': 0,
        'mu_stream_2011': 0,
        'el_stream_2012': 0,
        'el_stream_2011': 0
    }
}

def update(d):
    if not 'samplename' in d: return
    sname = d['samplename']
    if not sname in sampledata: return

    pickups = sampledata[sname]['pickup']

    plotdata['samples'].setdefault(sname,{})
    for pick in pickups:
        plotdata['samples'][sname].setdefault(pick,[])
        plotdata['samples'][sname][pick] += [d[pick]]

    plotdata['samples'][sname].setdefault('processed',0)
    plotdata['samples'][sname]['processed'] += d['processed']

    if d.get('lumi'):
        lumikey = d['lumi']['stream']
        lumival = d['lumi']['value']
        plotdata['lumi_data'][lumikey] += lumival/1000000.0

def weight_samples(pd):
    weighted_and_summed = {}
    for sname,s in pd['samples'].items():
        for p in sampledata[sname]['pickup']:
            if not 'cms_run' in sname:
                processed = s['processed']
                lumikey = sampledata[sname]['lumi']
                lumikey = lumi_settings[lumikey][p]
                lumi = pd['lumi_data'][lumikey]
                xsec = sampledata[sname]['xsec']
                x = np.asarray(s[p]) / processed * lumi * xsec
            else:
                x = np.asarray(s[p])
            summed = np.sum(x, axis=0)
            weighted_and_summed.setdefault(sname,{})[p] = summed
    return weighted_and_summed


def group_samples(weighted_and_summed):
    groups = {}
    for k,v in weighted_and_summed.items():
        group = sampledata[k]['group']
        for p in sampledata[k]['pickup']:
            counts = v[p]
            groups.setdefault(group,[])
            groups[group].append(counts.tolist())
    return groups

def plot(ax,groups, hide = None):
    hide = hide or []
    ax.clear()
    bottom = np.zeros(NBINS)
    if 'zz' in groups and not 'zz' in hide:
        summed = np.sum(groups['zz'],axis=0)
        ax.bar(ctrs,summed, width = 3, facecolor = 'steelblue', label = 'zz')
        bottom = summed
    if 'higgs' in groups and not 'higgs' in hide:
        summed = np.sum(groups['higgs'],axis=0)
        ax.bar(ctrs,summed, width = 3, bottom = bottom, facecolor = 'red', label = 'higgs')
    if 'data' in groups and not 'data' in hide:
        data = np.sum(groups['data'],axis=0)
        ax.errorbar(ctrs, data, yerr = np.sqrt(data), marker = 'o', fmt='o', c = 'k')
        ax.errorbar(ctrs, data, xerr = 1.5*np.ones_like(data), marker = 'o', fmt='o', c = 'k', markersize = 5, linewidth = 3, label = 'data')
    ax.set_xlim(70,181)
    ax.set_ylim(0,25)

def reset_plotdata():
    global plotdata
    plotdata = {
        'samples': {},
        'lumi_data': {
            'mu_stream_2012': 0,
            'mu_stream_2011': 0,
            'el_stream_2012': 0,
            'el_stream_2011': 0
        }
    }


def init_mpl():
    # matplotlib general settings
    # plt.rc('text', usetex=True)
    # plt.rcParams['text.latex.preamble']=[
    #     r"\usepackage{amsmath}",
    # ]
    plt.rcParams["mathtext.default"] = 'regular'
    plt.rcParams["mathtext.fontset"] = "stix"
    fontP = FontProperties()
    fontP.set_size(32)


def plot_binned_data(axes, binedges, data, *args, **kwargs):
    # The dataset values are the bin centres
    x = (binedges[1:] + binedges[:-1]) / 2.0
    # The weights are the y-values of the input binned data
    weights = data
    return axes.hist(x, bins=binedges, weights=weights,
               *args, **kwargs)


def get_legend_handles():
    handles = []
    handles.append(
        (mlines.Line2D([], [], color='k', linestyle='-', marker = 'o', markersize=8, linewidth=3), 'Data')
        )
    handles.append(
        (mpatches.Patch(facecolor='white', edgecolor='red', linewidth=HIST_LINEWIDTH), r'm$_\mathrm{\mathsf{H}}$ = 125 GeV')
        )
    handles.append(
        (mpatches.Patch(facecolor=cyan_m9, edgecolor='black', linewidth=HIST_LINEWIDTH), r'ZZ $\rightarrow$ 4l')
        )
    handles.append(
        (mpatches.Patch(facecolor=green_m5, edgecolor='black', linewidth=HIST_LINEWIDTH), r'Z$\gamma$* + X')
        )
    handles.append(
        (mpatches.Patch(facecolor=gray, edgecolor='black', linewidth=HIST_LINEWIDTH), r'$\mathrm{\mathsf{t}}\bar{\mathrm{\mathsf{t}}}$')
        )
    return handles


def add_cms_label(ax):
    cms_label = 'CMS Open Data'
    # cms_label = r'''\textbf{CMS Open Data}'''
    # cms_label = r'''\textbf{CMS} \textit{Open Data}'''

    ax.text(
        X_MIN+(X_MAX-X_MIN)*0.04, Y_MAX-0.08*DELTA_Y,
        cms_label,
        fontsize=32
        )


def label_axes(ax):
    # Label axes
    ax.set_xlabel(
        r'm$_{4\mathrm{\mathsf{l}}}$ (GeV)', fontsize=32,
        horizontalalignment='right', x=1.0,
    )
    # by hand y label, in pyplot 1.4 it aligns properly, here not
    ax.set_ylabel(
        r'Events / 3 GeV', fontsize=32,
        horizontalalignment='right',
        y=0.94 #shifts the label down just right
    )


def format_axes(ax):
    ax.set_xlim(X_MIN, X_MAX)
    ax.set_ylim(Y_MIN, Y_MAX)

    # Major ticks every 20, minor ticks every 5
    major_ticks = np.arange(80, 181, 20)
    minor_ticks = np.arange(75, 181, 5)
    ax.set_xticks(major_ticks)
    ax.set_xticks(minor_ticks, minor=True)

    ax.xaxis.set_major_formatter(
        ticker.FormatStrFormatter("%d")
        )
    ax.yaxis.set_major_formatter(
        ticker.FormatStrFormatter("%d")
        )
    # might need to replot this later
    loc = ticker.MultipleLocator(base=1) # this locator puts ticks at regular intervals
    ax.yaxis.set_minor_locator(loc)
    ax.tick_params(axis='both', labelsize=29, which='both', direction='in')



def add_legend(handles, ax):
    x = lambda vv: [i for i, _ in vv]
    y = lambda vv: [i for _, i in vv]
    ax.legend(
        x(handles),
        y(handles),
        bbox_to_anchor=(0.52, 0.58, 0.38, 0.38),#, .55, .102),
        loc=1,
        ncol=1, mode="expand", borderaxespad=0.,
        fontsize=27,
        frameon=False,
    )


def add_lumi(lumi_data, ax):
    # Receiving a dict with the following keys: mu_stream_2012, mu_stream_2011, el_stream_2012, el_stream_2011
    lumi_2011 = 0.001*(max(lumi_data['mu_stream_2011'], lumi_data['el_stream_2011']))
    lumi_2012 = 0.001*(max(lumi_data['mu_stream_2012'], lumi_data['el_stream_2012']))
    txt = ax.text(
    X_MIN+(X_MAX-X_MIN)*0.01, Y_MAX+0.025*DELTA_Y,
    r'%2.1f fb$^{\mathsf{-1}}$ (7 TeV), %2.1f fb$^{\mathsf{-1}}$ (8 TeV)' % (lumi_2011, lumi_2012),
    fontsize=29,
    horizontalalignment='left'
    )
    return txt


def add_processed(lumi_data, ax):
    # Receiving a dict with the following keys: mu_stream_2012, mu_stream_2011, el_stream_2012, el_stream_2011
    lumi_2011 = 0.001*(max(lumi_data['mu_stream_2011'], lumi_data['el_stream_2011']))
    lumi_2012 = 0.001*(max(lumi_data['mu_stream_2012'], lumi_data['el_stream_2012']))
    txt = ax.text(
    X_MIN+(X_MAX-X_MIN)*0.01, Y_MAX+0.025*DELTA_Y,
    r'%2.1f fb$^{\mathsf{-1}}$ (7 TeV), %2.1f fb$^{\mathsf{-1}}$ (8 TeV)' % (lumi_2011, lumi_2012),
    fontsize=29,
    horizontalalignment='left'
    )
    return txt


def add_timestamp(ax):
    tz = pytz.timezone(os.environ.get('CMS_PLOT_TIMEZONE','Europe/Madrid'))
    time_now = datetime.datetime.now(tz).time()
    # cms_label = r'''\textbf{CMS} \textit{Open Data}'''

    ax.text(
        X_MIN-(X_MAX-X_MIN)*0.1, Y_MIN-(Y_MAX-Y_MIN)*0.11,
        # 0,0,
        time_now.strftime('%H:%M:%S'),
        fontsize=32
        )


def plot_cosmetics(ax, handles, lumidata):
    label_axes(ax)
    add_cms_label(ax)
    format_axes(ax)
    add_cms_label(ax)
    add_timestamp(ax)
    add_legend(handles, ax)
    txt = add_lumi(lumidata, ax)
    return txt


def new_plot(ax, groups, handles, hide=None):
    hide = hide or []
    ax.clear()
    txt = plot_cosmetics(ax, handles, plotdata['lumi_data'])
    bottom = np.zeros(NBINS)
    bottom_no_zz = np.zeros(NBINS)
    summed = np.zeros(NBINS)
    if 'ttbar' in groups and not 'ttbar' in hide:
        summed = np.sum(groups['ttbar'], axis=0)
        plot_binned_data(ax, edges, summed, histtype="stepfilled", bottom = bottom, facecolor = gray, edgecolor='black', label = 'ttbar', linewidth=HIST_LINEWIDTH)
        bottom += summed
        bottom_no_zz += summed
    if 'dy' in groups and not 'dy' in hide:
        summed = np.sum(groups['dy'], axis=0)
        plot_binned_data(ax, edges, summed, histtype="stepfilled", bottom = bottom, facecolor = green_m5, edgecolor='black', label = 'dy', linewidth=HIST_LINEWIDTH)
        bottom += summed
        bottom_no_zz += summed
    if 'zz' in groups and not 'zz' in hide:
        summed = np.sum(groups['zz'], axis=0)
        # ax.bar(ctrs,summed, width = 3, facecolor = cyan_m9, edgecolor='black', label = 'zz')
        # plot_binned_data(ax, edges, summed, histtype="stepfilled", bottom = bottom, facecolor = cyan_m9, edgecolor='black', label = 'zz')
        # ax.hist(summed, edges, histtype='stepfilled', facecolor = cyan_m9, edgecolor='black', label = 'zz')
        bottom += summed
    if 'higgs' in groups and not 'higgs' in hide:
        summed = np.sum(groups['higgs'], axis=0)
        # ax.bar(ctrs,summed, width = 3, bottom = bottom, facecolor = 'red', label = 'higgs')
        plot_binned_data(ax, edges, summed, histtype="stepfilled", bottom = bottom, facecolor = 'white', edgecolor='red', label = 'higgs', linewidth=HIST_LINEWIDTH)
    # redo zz for overlapping lines
    if 'zz' in groups and not 'zz' in hide:
        summed = np.sum(groups['zz'],axis=0)
        plot_binned_data(ax, edges, summed, histtype="stepfilled", bottom = bottom_no_zz, facecolor = cyan_m9, edgecolor='black', label = 'zz', linewidth=HIST_LINEWIDTH)
    if 'data' in groups and not 'data' in hide:
        data = np.sum(groups['data'],axis=0)
        ax.errorbar(ctrs, data, yerr = np.sqrt(data), marker = 'o', fmt='o', c = 'k')
        ax.errorbar(ctrs, data, xerr = 1.5*np.ones_like(data), marker = 'o', fmt='o', c = 'k', markersize = 5, linewidth = 3, label = 'data')
    return txt


def update_progress(ax, dict_files_processed):
    samples = list(sampledata[key]['id'] for key in sampledata.keys())
    y_pos = np.arange(len(samples))
    progress = [dict_files_processed[key]/float(sampledata[key]['nfiles'])*100 if key in dict_files_processed else 0. for key in sampledata.keys()]
    colours = list(colour_dict[sampledata[key]['group']] for key in sampledata.keys())

    ax.barh(y_pos, progress, align='center',
            color=colours, ecolor='black')
    ax.set_yticks(y_pos)
    ax.set_yticklabels(samples)
    ax.invert_yaxis()  # labels read top-to-bottom
    ax.set_xlabel('Jobs done per sample (\%)',
        fontsize=32,

    )
    ax.set_title('Progress', fontsize=32)
    ax.tick_params(axis='x', labelsize=29, which='both', direction='out')
    ax.xaxis.set_major_formatter(ticker.FormatStrFormatter("%d"))
    ax.set_xlim(0, 100)