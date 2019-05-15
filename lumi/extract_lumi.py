#!/bin/usr/env python
"""Script to extract integrated lumi per file."""
import os
import subprocess
import json
import csv
from collections import defaultdict


"""
Steps for each data set:
1. Query data set using cmsdasgoclient, get files -> dasgoclient_osx --query="file dataset=/DoubleMuParked/Run2012B-22Jan2013-v1/AOD" --json -> /store/data/Run2012B/DoubleMuParked/AOD/22Jan2013-v1/10000/1EC938EF-ABEC-E211-94E0-90E6BA442F24.root
2. Loop over text file containing corresponding file names -> less ../cms-higgs-4l-full/datasets/CMS_Run2012B_DoubleMuParked_AOD_22Jan2013-v1_10000_file_index.txt contains e.g. root://eospublic.cern.ch//eos/opendata/cms/Run2012B/DoubleMuParked/AOD/22Jan2013-v1/10000/1EC938EF-ABEC-E211-94E0-90E6BA442F24.root
3. Match the two file names (mind, S3 data name starts with s3/higgs-demo/eos/opendata/cms/)
4. Query dasgoclient for the lumi section -> dasgoclient_osx --query="lumi file=/store/data/Run2012B/DoubleMuParked/AOD/22Jan2013-v1/10000/1EC938EF-ABEC-E211-94E0-90E6BA442F24.root" --json ->
[
{"das":{"expire":1556807423,"instance":"prod/global","primary_key":"lumi.number","record":1,"services":["dbs3:filelumis"]},"lumi":[{"file":"/store/data/Run2012B/DoubleMuParked/AOD/22Jan2013-v1/10000/1EC938EF-ABEC-E211-94E0-90E6BA442F24.root","lumi_section_num":[1056,818,819,1057,1058,817],"number":[1056,818,819,1057,1058,817],"run.run_number":null,"run_number":195397}],"qhash":"3db2beb14e9770fc4385858cbfcb3d12"} ,
{"das":{"expire":1556807423,"instance":"prod/global","primary_key":"lumi.number","record":1,"services":["dbs3:filelumis"]},"lumi":[{"file":"/store/data/Run2012B/DoubleMuParked/AOD/22Jan2013-v1/10000/1EC938EF-ABEC-E211-94E0-90E6BA442F24.root","lumi_section_num":[317,324,328,340,320,327,311,239,193,186,81,241,242,338,352,316,339,86,237,240,84,88,313,351,243,188,238,244,312,315,322,326,342,325,314,85,87,318,341,353,321,82,190,354,189,83,187,323,192,236,185,191,319],"number":[317,324,328,340,320,327,311,239,193,186,81,241,242,338,352,316,339,86,237,240,84,88,313,351,243,188,238,244,312,315,322,326,342,325,314,85,87,318,341,353,321,82,190,354,189,83,187,323,192,236,185,191,319],"run.run_number":null,"run_number":195399}],"qhash":"3db2beb14e9770fc4385858cbfcb3d12"} ,
{"das":{"expire":1556807423,"instance":"prod/global","primary_key":"lumi.number","record":1,"services":["dbs3:filelumis"]},"lumi":[{"file":"/store/data/Run2012B/DoubleMuParked/AOD/22Jan2013-v1/10000/1EC938EF-ABEC-E211-94E0-90E6BA442F24.root","lumi_section_num":[70,69,66,67,68],"number":[70,69,66,67,68],"run.run_number":null,"run_number":195013}],"qhash":"3db2beb14e9770fc4385858cbfcb3d12"}
]

"""

# 2011 data: http://opendata.cern.ch/record/1051/files/2011lumibyls.csv
# 2012 data: http://opendata.cern.ch/record/1052/files/2012lumibyls.csv

RUN_LUMI_DICT = None

def get_das_files(dataset):
    try:
        completed = subprocess.run(
            ['dasgoclient_osx', '-query', 'file dataset=%s' % dataset],
            stdout=subprocess.PIPE,
            # stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as err:
        print('ERROR:', err)
    else:
        # print('returncode:', completed.returncode)
        das_files = completed.stdout.decode('utf-8').split('\n')[:-1]
        print(f'Found {len(das_files)} files on DAS for {dataset}')
    return das_files


def get_run_lumisections(file_name):
    print(f'Getting run/lumisections for {file_name}')
    lumi_dict = {}
    try:
        completed = subprocess.run(
            ['dasgoclient_osx', '-query', 'lumi file=%s' % file_name, '--json'],
            stdout=subprocess.PIPE,
            # stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as err:
        print('ERROR:', err)
    else:
        # print('returncode:', completed.returncode)
        lumi_json = json.loads(completed.stdout.decode('utf-8'))
        for lumi_item in lumi_json:
            # print(lumi_item['lumi'][0]['run_number'], lumi_item['lumi'][0]['lumi_section_num'])
            lumi_dict[lumi_item['lumi'][0]['run_number']] = list(lumi_item['lumi'][0]['lumi_section_num'])
    return lumi_dict


def get_run_lumi_dict():
    """Loop over CSV file and return run:ls:lumi dict."""
    my_list = []
    csv_file_names = ['2011lumibyls.csv', '2012lumibyls.csv']
    for csv_file_name in csv_file_names:
        with open(csv_file_name) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            line_count = 0
            for row in csv_reader:
                if line_count == 1:
                    print(f'Column names are {", ".join(row)}')
                elif row[0].startswith("#"):
                    continue
                else:
                    # print(f'Run {row[0]}, lumi section {row[1]}: {row[6]}/ub delivered.')
                    line_count += 1
                    run = int(row[0].split(":")[0])
                    ls = int(row[1].split(":")[0])
                    lumi = float(row[6])
                    my_list.append((run, ls, lumi))
                # if line_count > 10:
                #     break
                line_count += 1
            print(f'Processed {line_count} lines.')
    # Using a defaultdict here to just return 0 in case the run or lumisection are not part of the JSON file
    run_lumi_dict = defaultdict(lambda: defaultdict(int))
    for i in my_list:
        run_lumi_dict[i[0]][i[1]] = i[2]
    return run_lumi_dict


def get_lumi(run_lumisections):
    """Get summed up lumi."""
    global RUN_LUMI_DICT
    # print(run_lumisections)
    lumi = 0
    for run, lumisections in run_lumisections.items():
        for ls in lumisections:
            # print(run, ls)
            lumi += RUN_LUMI_DICT[run][ls]
    return lumi


def get_opendata_file_list():
    opendata_file_list = []
    dataset_txt_directory = "../datasets/"
    for txt_filename in os.listdir(dataset_txt_directory):
        if txt_filename.startswith("CMS_Run201"):
            with open(dataset_txt_directory+txt_filename) as txt_file:
                for line in txt_file:
                    opendata_file_list.append(line.strip('\n'))
    return opendata_file_list


def get_file_list_dict(opendata_file_list, das_files):
    file_list_dict = {}
    for das_file in das_files:
        opendata_prefix = "root://eospublic.cern.ch//eos/opendata/cms/"
        das_prefix = "/store/data/"
        opendata_file_name = das_file.replace(das_prefix, opendata_prefix)
        if opendata_file_name in opendata_file_list:
            file_list_dict[opendata_file_name] = das_file
        else:
            print(f"ERROR: {das_file} not found in OpenData list.")
    return file_list_dict


def get_all_run_lumisections(file_list_dict):
    all_run_lumisections = {}
    total = float(len(file_list_dict))
    counter = 0.
    for key, das_file_name in file_list_dict.items():
        print(f'{counter/total*100}% done')
        all_run_lumisections[key] = get_run_lumisections(das_file_name)
        counter += 1
    return all_run_lumisections


def get_file_lumi_dict(all_run_lumisections_dict):
    file_lumi_dict = {}
    for key, run_lumisections in all_run_lumisections_dict.items():
        file_lumi_dict[key] = get_lumi(run_lumisections)
    return file_lumi_dict


def main():
    global RUN_LUMI_DICT

    RUN_LUMI_DICT = get_run_lumi_dict()

    datasets = ["/DoubleElectron/Run2011A-12Oct2013-v1/AOD",
                "/DoubleElectron/Run2012B-22Jan2013-v1/AOD",
                "/DoubleElectron/Run2012C-22Jan2013-v1/AOD",
                "/DoubleMu/Run2011A-12Oct2013-v1/AOD",
                "/DoubleMuParked/Run2012B-22Jan2013-v1/AOD",
                "/DoubleMuParked/Run2012C-22Jan2013-v1/AOD",
                ]
    for dataset in datasets:
        # 1. Query data set using cmsdasgoclient, get files
        das_files = get_das_files(dataset)
        # das_files = das_files[:3]
        # 2. Loop over text file containing corresponding file names
        opendata_file_list = get_opendata_file_list()
        print(f'Found {len(opendata_file_list)} OpenData files in {dataset}')
        # 3. Match the two file names (mind, S3 data name starts with s3/higgs-demo/eos/opendata/cms/)
        file_list_dict = get_file_list_dict(opendata_file_list, das_files)
        print(f'Found {len(file_list_dict)} matches with DAS files')
        # 4. Query dasgoclient for the lumi section
        all_run_lumisections_dict = get_all_run_lumisections(file_list_dict)
        # 5. Sum up the lumi for each file
        file_lumi_dict = get_file_lumi_dict(all_run_lumisections_dict)
        # 6. Cross-check that sum is OK
        print(sum(file_lumi_dict.values()))
        # 7. Write dictionary/JSON to disk
        with open(dataset.replace("/", "_")[1:]+".json", 'w') as fp:
            json.dump(file_lumi_dict, fp, indent=4)

    # das_file_name = "/store/data/Run2012B/DoubleMuParked/AOD/22Jan2013-v1/20000/E2ADC893-7668-E211-866F-90E6BA19A24A.root" # das_files[0]
    # das_file_name = "/store/data/Run2012B/DoubleMuParked/AOD/22Jan2013-v1/310000/FEDD2A3C-9B6F-E211-9673-485B39800BFB.root" # das_files[0]
    # run_lumisections = get_run_lumisections(das_file_name)
    # print(run_lumisections)
    # RUN_LUMI_DICT = get_run_lumi_dict()
    # print(f'Found {len(RUN_LUMI_DICT)} runs.')
    # # print(f'Run 194314, LS 76: {RUN_LUMI_DICT[194314][76]}')
    # # print(f'Run 195915, LS 128: {RUN_LUMI_DICT[195915][128]}')
    # # print(f'Run 333333, LS 666: {RUN_LUMI_DICT[333333][666]}')
    # # print(RUN_LUMI_DICT[195916])
    # # print(RUN_LUMI_DICT[333333])
    # lumi = get_lumi(run_lumisections)
    # print(lumi)


if __name__ == "__main__":
    main()