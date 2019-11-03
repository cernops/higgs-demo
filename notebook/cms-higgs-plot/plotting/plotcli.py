import os
import json
import glob

import matplotlib
matplotlib.use('PS')   # generate postscript output by default

import higgsplot
import time

import numpy as np
import random
import click
import matplotlib.pyplot as plt


@click.command()
@click.option('--datadir', default = 'testdata')
@click.option('--groupsfile', default = 'groups.json')
@click.option('--plotfile', default = 'plot.png')
def make_plot(datadir,groupsfile,plotfile):
    read_files = True
    dict_files_processed = {}

    if read_files:

        files = glob.glob('{}/*/*.json'.format(datadir))[:]
        files = np.random.choice(files, replace = False, size = len(files))
        for sample in higgsplot.sampledata.keys():
            count = 0
            for f in files:
                if f.find(sample) >= 0:
                    count += 1
            dict_files_processed[sample] = count

        print(len(files),'files')

        data = [json.load(open(f)) for f in files]
        higgsplot.reset_plotdata()
        for d in data:
            higgsplot.update(d)

        start = time.time()
        weighted_and_summed = higgsplot.weight_samples(higgsplot.plotdata)
        groups = higgsplot.group_samples(weighted_and_summed)
        json.dump(groups, open(groupsfile,'w'))

    else:
        groups = json.load(open(groupsfile))

    higgsplot.init_mpl()
    handles = higgsplot.get_legend_handles()

    fig, (ax, ax_right) = plt.subplots(1, 2, figsize=(22, 10), dpi= 80, facecolor='w', edgecolor='k')


    txt = higgsplot.new_plot(ax, groups, handles)
    higgsplot.update_progress(ax_right, dict_files_processed)

    plt.savefig(
        plotfile,
        bbox_extra_artists=(txt,), #ensure that the upper text is drawn
        bbox_inches='tight'
    )

    plt.close(fig)


if __name__ == '__main__':
    make_plot()
