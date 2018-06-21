#!/usr/bin/env python3
#
# Create model outputs with P.1203 software.
#
# Requirements: install pandas, tqdm and numpy for Python.
# Also install the itu_p1203 software.
#
# Usage: put all the data in a folder called `data`,
# and place it next to the folder where this script is run.
# You may change the ROOT_PATH variable in the code.
#
# Authors: David Lindegren, Werner Robitza
#
# License: MIT

import os
from itu_p1203.p1203Pv import P1203Pv
from itu_p1203.p1203Pq import P1203Pq
import pandas as pd
import yaml
import argparse
import json
import numpy as np
from tqdm import tqdm
from collections import defaultdict

tqdm.pandas()

DB_IDS = ['TR04', 'TR06', 'VL04', 'VL13']

ROOT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')


def parse_mode3_features(pvs_id, features_mode3_path):
    pvs_features = pd.read_csv(
        os.path.join(
            features_mode3_path,
            pvs_id + '.csv')
        )
    return pvs_features


def calc_mode0_O22(row):
    pvs_features = (int(row["coding_res"]),
                    int(row["display_res"]),
                    float(row["bitrate_kbps_segment_size"]),
                    int(row["framerate"]))

    return P1203Pv.video_model_function_mode0(*pvs_features)


def calc_mode1_O22(row):
    pvs_features = (int(row["coding_res"]),
                    int(row["display_res"]),
                    float(row["bitrate_kbps_segment_size"]),
                    int(row["framerate"]),
                    [],
                    float(row["iframe_ratio"]))

    return P1203Pv.video_model_function_mode1(*pvs_features)


def calc_mode2_O22(row):
    # check if fallback is needed
    has_bitstream_data = "BS_TwoPercentQP1" in row.keys() and isinstance(row["BS_TwoPercentQP1"], str)

    try:
        avg_qp = eval(row["BS_TwoPercentQP1"])
    except Exception as e:
        has_bitstream_data = False

    if has_bitstream_data:
        frame_types = eval(row["types"])
        frames = []
        for ftyp, qp_values in zip(frame_types, avg_qp):
            frames.append({
                'type': ftyp,
                'qpValues': [qp_values]
            })

        pvs_features = (
            int(row["coding_res"]),
            int(row["display_res"]),
            int(row["framerate"]),
            frames,
            None,
            []
        )

        return P1203Pv.video_model_function_mode2(*pvs_features)
    else:
        # tqdm.write("Switching back to Mode 1 for PVS {}, sample index {}".format(row["pvs_id"], row["sample_index"]))
        return None


def calc_mode3_O22(row):
    frame_types = eval(row["types"])
    avg_qp = eval(row["BS_Av_QPBB"])

    frames = []
    for ftyp, qp_values in zip(frame_types, avg_qp):
        frames.append({
            'type': ftyp,
            'qpValues': [qp_values]
        })

    pvs_features = (
        int(row["coding_res"]),
        int(row["display_res"]),
        float(row["framerate"]),
        frames,
        None,
        []
    )

    return P1203Pv.video_model_function_mode3(*pvs_features)


def calc_O46(O21, O22, device, stall_vec=[]):
    l_buff = []
    p_buff = []
    if stall_vec:
        for l, p in stall_vec:
            l_buff.append(l)
            p_buff.append(p)

    pq_fun = P1203Pq(O21, O22, l_buff, p_buff, device)
    return pq_fun.calculate()


def main(args):

    db_data = pd.DataFrame()

    O21_path = os.path.join(ROOT_PATH, 'data', 'O21.csv')
    stalling_dir_path = os.path.join(ROOT_PATH, 'data', 'test_configs')
    features_mode0_path = os.path.join(ROOT_PATH, 'data', 'features', 'features_mode0.csv')
    features_mode1_path = os.path.join(ROOT_PATH, 'data', 'features', 'features_mode1.csv')
    features_mode2_path = os.path.join(ROOT_PATH, 'data', 'features', 'features_mode2')
    features_mode3_path = os.path.join(ROOT_PATH, 'data', 'features', 'features_mode3')

    # read in data
    # O21
    O21_data = pd.read_csv(O21_path)

    # stalling
    yaml_per_db = {}
    for db_id in DB_IDS:
        yaml_per_db[db_id] = yaml.load(
            open(os.path.join(stalling_dir_path, db_id + '-config.yaml')))

    # read in from hdf-files if they exist, otherwise run pv-calc
    if args.create_hdfs:
        print('Calculating O22 scores for all modes ...')

        # mode0 features
        print('Reading mode 0 features ...')
        mode0_features = pd.read_csv(features_mode0_path)

        # mode1 features
        print('Reading mode 1 features ...')
        mode1_features = pd.read_csv(features_mode1_path)

        # mode2 features
        print('Reading mode 2 features (may take a while) ...')
        pvss = mode1_features["pvs_id"].unique()
        list_of_dataframes_for_mode2 = []
        for pvs_id in tqdm(pvss):
            pvs_data_all = pd.read_csv(os.path.join(features_mode2_path, pvs_id + '.csv'))
            if "BS_TwoPercentQP1" in pvs_data_all.keys():
                list_of_dataframes_for_mode2.append(
                    pvs_data_all[[
                        "pvs_id", "sample_index", "framerate", "types", "sizes", "quant", "coding_res", "display_res", "BS_TwoPercentQP1"
                    ]].copy()
                )
            else:
                # no bitstream data available
                list_of_dataframes_for_mode2.append(
                    pvs_data_all[[
                        "pvs_id", "sample_index", "framerate", "types", "sizes", "coding_res", "display_res"
                    ]].copy()
                )
        mode2_features = pd.concat(list_of_dataframes_for_mode2, ignore_index=True)

        # mode3 features
        print('Reading mode 3 features (may take a while) ...')
        pvss = mode1_features["pvs_id"].unique()
        list_of_dataframes_for_mode3 = []
        for pvs_id in tqdm(pvss):
            pvs_data_all = pd.read_csv(os.path.join(features_mode3_path, pvs_id + '.csv'))
            list_of_dataframes_for_mode3.append(
                pvs_data_all[[
                    "pvs_id", "sample_index", "framerate", "types", "quant", "coding_res", "display_res", "BS_Av_QPBB"
                ]].copy()
            )
        mode3_features = pd.concat(list_of_dataframes_for_mode3, ignore_index=True)

        # calc Pv
        # mode0
        print('Calculating mode 0 Pv')
        mode0_features['O22'] = mode0_features.progress_apply(calc_mode0_O22, axis=1)

        # mode1
        print('Calculating mode 1 Pv')
        mode1_features['O22'] = mode1_features.progress_apply(calc_mode1_O22, axis=1)

        # mode2
        print('Calculating mode 2 Pv')
        mode2_features['O22'] = mode2_features.progress_apply(calc_mode2_O22, axis=1)

        missing_values_indices = np.where(pd.isnull(mode2_features.O22))[0]
        # go through each sample index that has no value yet
        print('Re-calculating mode 2 Pv missing values')
        for idx in tqdm(missing_values_indices):
            # get required features from mode 1, ...
            pvs_id = mode2_features.iloc[idx]['pvs_id']
            sample_index = mode2_features.iloc[idx]['sample_index']
            row = mode1_features.loc[(mode1_features["pvs_id"] == pvs_id) & (mode1_features["sample_index"] == sample_index)]
            # and calculate Mode 1 score instead
            mode1_O22 = calc_mode1_O22(row)
            # overwrite data in Mode 2 data frame
            # https://stackoverflow.com/a/43968774/435093
            mode2_features.iat[idx, mode2_features.columns.get_loc("O22")] = mode1_O22

        # mode3
        print('Calculating mode 3 Pv')
        mode3_features['O22'] = mode3_features.progress_apply(calc_mode3_O22, axis=1)

        mode0_features.to_hdf(os.path.join(ROOT_PATH, "data_original", "save.h5"), key='mode0')
        mode1_features.to_hdf(os.path.join(ROOT_PATH, "data_original", "save.h5"), key='mode1')
        mode2_features.to_hdf(os.path.join(ROOT_PATH, "data_original", "save.h5"), key='mode2')
        mode3_features.to_hdf(os.path.join(ROOT_PATH, "data_original", "save.h5"), key='mode3')
    else:
        if os.path.isfile(os.path.join(ROOT_PATH, "data_original", "save.h5")):
            mode0_features = pd.read_hdf(os.path.join(ROOT_PATH, "data_original", "save.h5"), key='mode0')
            mode1_features = pd.read_hdf(os.path.join(ROOT_PATH, "data_original", "save.h5"), key='mode1')
            mode2_features = pd.read_hdf(os.path.join(ROOT_PATH, "data_original", "save.h5"), key='mode2')
            mode3_features = pd.read_hdf(os.path.join(ROOT_PATH, "data_original", "save.h5"), key='mode3')
        else:
            print('No h5 file found, please rerun with -c flag')
            quit()

    # parse buffering data from -config.yaml
    stalling_per_db_hrc = defaultdict(dict)
    for db_id in yaml_per_db:
        for hrc_id in yaml_per_db[db_id]['hrcList']:
            buffts = 0
            buff_events = []  # ts, dur
            for (event, ts) in yaml_per_db[db_id]['hrcList'][hrc_id]["eventList"]:
                if event in ['stall', 'buffering']:
                    buff_events.append([buffts, ts])
                else:
                    buffts += ts
            stalling_per_db_hrc[db_id][hrc_id] = buff_events

    pvss = mode1_features["pvs_id"].unique()
    per_pvs_data = {}

    print('Creating O21/22-json files ...')
    O22_tocsv = pd.DataFrame(columns=['pvs_id', 'mode', 'sample_index', 'O22'])
    list_to_concat = []
    for pvs_id in tqdm(pvss):
        db_id = pvs_id.split('_')[0]
        if db_id not in DB_IDS:
            print("WARNING: Saved PVS {} not in required DBs".format(pvs_id))
            continue
        src_id = pvs_id.split('_')[1]
        hrc_id = pvs_id.split('_')[2]

        per_pvs_data[pvs_id] = {}
        per_pvs_data[pvs_id]['O21'] = O21_data[O21_data["pvs_id"] ==
                                               pvs_id].sort_values(by=['sample_index'])["O21"].tolist()

        per_pvs_data[pvs_id]['O22'] = {}
        per_pvs_data[pvs_id]['O22']['mode0'] = \
            mode0_features[mode0_features["pvs_id"] == pvs_id].sort_values(by=['sample_index'])["O22"].tolist()
        per_pvs_data[pvs_id]['O22']['mode1'] = \
            mode1_features[mode1_features["pvs_id"] == pvs_id].sort_values(by=['sample_index'])["O22"].tolist()
        per_pvs_data[pvs_id]['O22']['mode2'] = \
            mode2_features[mode2_features["pvs_id"] == pvs_id].sort_values(by=['sample_index'])["O22"].tolist()
        per_pvs_data[pvs_id]['O22']['mode3'] = \
            mode3_features[mode3_features["pvs_id"] == pvs_id].sort_values(by=['sample_index'])["O22"].tolist()

        per_pvs_data[pvs_id]['I23'] = {"stalling": stalling_per_db_hrc[db_id][hrc_id]}

        per_pvs_data[pvs_id]['IGen'] = {}
        per_pvs_data[pvs_id]['IGen']['displaySize'] = str(int(
            yaml_per_db[db_id]["displayHeight"] * 1.7777778)) + 'x' + str(yaml_per_db[db_id]["displayHeight"])

        # this should be inserted below when producing the o46 scores
        per_pvs_data[pvs_id]['IGen']['device'] = ''

        # write .json outputs from pv (O21, O22, i23, igen)
        for mode_id in ['mode0', 'mode1', 'mode2', 'mode3']:
            csv_index = 0

            for o22_sample in per_pvs_data[pvs_id]['O22'][mode_id]:
                csv_row = {
                    'pvs_id': pvs_id, 'mode': mode_id[-1], 'sample_index': csv_index, 'O22': o22_sample}
                csv_row_df = pd.DataFrame(csv_row, index=[0])
                list_to_concat.append(csv_row_df)
                csv_index += 1

            os.makedirs(os.path.join(ROOT_PATH, 'data', mode_id), exist_ok=True)
            json_filename = os.path.join(
                ROOT_PATH,
                'data',
                mode_id,
                'O21O22-{}.json'.format(pvs_id)
            )
            #- `data/mode0/O21O22-TR01_SRCxxx_HRCxxx.json`
            data_to_write = per_pvs_data[pvs_id].copy()
            data_to_write['O22'] = per_pvs_data[pvs_id]['O22'][mode_id]
            with open(json_filename, 'w') as outfile:
                json.dump(data_to_write, outfile)

    print('Writing O22 CSV file ...')
    O22_tocsv = pd.concat(list_to_concat, ignore_index=True)
    O22_tocsv.to_csv(
        os.path.join(ROOT_PATH, 'data', 'O22.csv'),
        columns=['pvs_id', 'mode', 'sample_index', 'O22'],
        index=False
    )

    # calc pq for each .json.
    print('Calculating Pq-scores ...')
    O46_tocsv = pd.DataFrame(columns=['pvs_id', 'mode', 'context', 'O46'])
    list_to_concat = []
    for pvs_id in tqdm(pvss):
        pvs_data = per_pvs_data[pvs_id]
        for device in ['mobile', 'pc']:
            for curr_mode in pvs_data['O22']:
                O46_vals = calc_O46(
                    pvs_data['O21'], pvs_data['O22'][curr_mode], device, pvs_data['I23']['stalling'])

                # O21, O22, O23, O34, O35, O46, mode
                O46_output_data = {}
                O46_output_data['O23'] = O46_vals['O23']
                O46_output_data['O34'] = O46_vals['O34']
                O46_output_data['O35'] = O46_vals['O35']
                O46_output_data['O46'] = O46_vals['O46']
                O46_output_data['O22'] = pvs_data['O22'][curr_mode]
                O46_output_data['O21'] = pvs_data['O21']
                O46_output_data['mode'] = curr_mode[-1]

                # write o46-jsons
                #- `data/mode0/O46-TR01_SRCxxx_HRCxxx-pc.json`

                csv_row = {
                    'pvs_id': pvs_id,
                    'mode': curr_mode[-1],
                    'context': device,
                    'O46': O46_vals['O46']
                }
                csv_row_df = pd.DataFrame(csv_row, index=[0])
                list_to_concat.append(csv_row_df)

                json_filename = os.path.join(
                    ROOT_PATH,
                    'data',
                    curr_mode,
                    "046-{pvs_id}-{device}.json".format(**locals())
                )
                with open(json_filename, 'w') as outfile:
                    json.dump(O46_output_data, outfile)

    print('Writing O46 CSV file ...')
    O46_tocsv = pd.concat(list_to_concat, ignore_index=True)
    outfile = os.path.join(ROOT_PATH, 'data', 'O46.csv')
    print('Writing to {}'.format(outfile))
    O46_tocsv.to_csv(
        outfile,
        columns=['pvs_id', 'mode', 'context', 'O46'],
        index=False
    )


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Creating model O46-scores and intermediate outputs',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        '-c', '--create-hdfs',
        action='store_true',
        help='Create a temporary h5 file for O22-data'
    )
    args = parser.parse_args()
    main(args)
