import json
import os
import matplotlib.pyplot as plt
import plotting.higgsplot as hp
import time
import redis
import numpy as np
import time

testdata  = {}

def setup_figure():
    hp.init_mpl()
    handles = hp.get_legend_handles()

    fig, ax = plt.subplots(
    1, 1,
        figsize=(12, 10),
        facecolor='w',
        edgecolor='k', dpi = 40
    )
    fig.canvas.layout.width = '500px'
    figure = fig, ax, None, handles
    update_plot(figure,[])
    return figure

def update_plotdata(jsondocs):
    hp.reset_plotdata()
    for x in jsondocs:
        hp.update(json.loads(x))
    weighted_and_summed = hp.weight_samples(hp.plotdata)
    groups = hp.group_samples(weighted_and_summed)
    return groups

def update_plot(figure,jsondocs):
    fig, ax, ax_right, handles = figure
    ax.clear()
    groups = update_plotdata(jsondocs)
    hp.new_plot(ax, groups, handles)
    fig.canvas.draw()

def reset_data(source = None):
    source = source or os.environ.get('CMS_PLOT_SOURCE','disk:testdata.json')
    if 'redis' in source:
        r = redis.StrictRedis(host = os.environ['REDIS_HOST'])
        r.delete(key)
    if 'testing' in source:
        global testdata
        global testindex
        items = list(json.load(open('testdata.json')).items())
        indices = np.random.choice(np.arange(len(items)), replace = False, size = 50)
        testdata  = dict([items[idx] for idx in indices])
        time.sleep(os.environ.get('CMS_TESTING_SLEEP',100))

def load_data(source = None):
    source = source or os.environ.get('CMS_PLOT_SOURCE','disk:testdata.json')
    if 'disk' in source:
        #e.g. disk:myfile.json
        _, fname = source.split(':')
        return json.load(open(fname)).values()
    if 'redis' in source:
        #e.g. disk:myrediskey
        r = redis.StrictRedis(host = os.environ['REDIS_HOST'])
        _, key = source.split(':')
        return r.hgetall(key).values()
    if 'testing'in source:
        global testdata
        data = json.load(open('testdata.json'))

        items = list(data.items())
        remaining_indices = [i for i,(k,v) in enumerate(items) if k not in testdata]
        if not remaining_indices:
            return testdata.values()

        indices = list(np.random.choice(remaining_indices, replace = False, size = min(20,len(remaining_indices))))

        for index in indices:
            k,v = items[index]
            testdata[k] = v
        return testdata.values()
