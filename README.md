# P.1203 Open Dataset

This open dataset from the ITU-T P.1203 standardization procedure (P.NATS) contains the following data:

- 2 training and 2 validation databases
- Feature data:
    - Mode 0 (metadata-level)
    - Mode 1 (packet-header-level)
    - Mode 3 (bitstream-level)
- Subjective ratings
- Model scores

The data was analyzed with the [ITU-T P.1203 implementation](https://github.com/itu-p1203/itu-p1203/) from the same authors. Please carefully read the license of that software.

## Acknowledgement

If you use this software in your research, you must

1. Include the link to this repository
2. Cite the following publication:

    Robitza, W., Göring, S., Raake, A., Lindegren, D., Heikkilä, G., Gustafsson, J., List, P., Feiten, B., Wüstenhagen, U., Garcia, M.-N., Yamagishi, K., Broom, S. (2018). HTTP Adaptive Streaming QoE Estimation with ITU-T Rec. P.1203 – Open Databases and Software. In 9th ACM Multimedia Systems Conference. Amsterdam.

        @inproceedings{Robitza2017d,
        address = {Amsterdam},
        author = {Robitza, Werner and G{\"{o}}ring, Steve and Raake, Alexander and Lindegren, David and Heikkil{\"{a}}, Gunnar and Gustafsson, J{\"{o}}rgen and List, Peter and Feiten, Bernhard and W{\"{u}}stenhagen, Ulf and Garcia, Marie-Neige and Yamagishi, Kazuhisa and Broom, Simon},
        booktitle = {9th ACM Multimedia Systems Conference},
        doi = {10.1145/3204949.3208124},
        isbn = {9781450351928},
        title = {{HTTP Adaptive Streaming QoE Estimation with ITU-T Rec. P.1203 – Open Databases and Software}},
        year = {2018}
        }


## File Layout

The following features are available:

- `features/features_mode0.csv`: Per-output-sample aggregated features used for Pv mode 0, as parsed by the measurement window, columns:
    - `bitrate_kbps_segment_size`: Actual segment bitrate
    - `bitrate_kbps_target`: Encoding target bitrate
    - `coding_height`: Encoding height in pixels
    - `coding_res`: Number of encoded pixels
    - `coding_width`: Encoding width in pixels
    - `display_height`: Height of the display in pixels
    - `display_res`: Number of pixels in display
    - `display_width`: Width of the display in pixels
    - `dts`: Frame decoding timestamps
    - `framerate`: Encoding frames per second
    - `sample_index`: Index of the output sample (1 per second)
    - `pvs_id`: Identifier of the PVS
- `features/features_mode1.csv`: Per-output-sample aggregated features used for Pv mode 1, as parsed by the measurement window, columns:
    - `bitrate_kbps_segment_size`: Actual segment bitrate
    - `bitrate_kbps_target`: Encoding target bitrate
    - `coding_height`: Encoding height in pixels
    - `coding_res`: Number of encoded pixels
    - `coding_width`: Encoding width in pixels
    - `display_height`: Height of the display in pixels
    - `display_res`: Number of pixels in display
    - `display_width`: Width of the display in pixels
    - `dts`: Frame decoding timestamps
    - `framerate`: Encoding frames per second
    - `gop_length`: GOP length in seconds
    - `i_sizes_average`: Average size of I frames in Bytes
    - `iframe_ratio`: Ratio between I and Non-I frame sizes
    - `noni_sizes_average`: Average size of non-I frames
    - `sample_index`: Index of the output sample (1 per second)
    - `pvs_id`: Identifier of the PVS
- `features/features_mode3.tar.bz2`: Per-output-sample aggregated features used for Pv mode 2 and 3, as parsed by the measurement window. One CSV file for each PVS, with columns:
    - `pvs_id`: Identifier of the PVS
    - `mode`: (fixed to 3)
    - `codec`: Video codec (fixed to H.264)
    - `index`
    - `dts`: Frame decoding timestamps
    - `types`: Frame types
    - `sizes`: Frame sizes
    - `framerate`: Encoding frames per second
    - `bitrate_kbps_target`: Encoding target bitrate
    - `coding_res`: Number of encoded pixels
    - `display_res`: Number of pixels in display
    - `quant`: Model-internal parameter
    - `BS_DecodedMbs`: Number of decoded macroblocks
    - `BS_MbTypes`: Count of macroblock types, meaning of array indices:
        - `0`: Skipped
        - `1`: Forward
        - `2`: Backward
        - `3`: Bidirect
        - `4`: Direct
        - `5`: Intra4
        - `6`: Intra16
    - `BS_Av_QPBB`: Average QP of 100% of bitstream.
    - `BS_TwoPercentQP1`: Average QP of 2% of bitstream, used for running model in Mode 2.

The subjective data is contained in the following files:

- `subjective_scores/mos.csv`: Per-PVS subjective MOS with 95% CI, columns:
    - `pvs_id`: Identifier of the PVS
    - `context`: "pc" or "mobile"
    - `mos`: MOS
    - `n`: Number of ratings considered for MOS
    - `sd`: Standard deviation of the MOS
    - `ci`: 95% confidence interval
- `subjective_scores/ratings.csv`: Per-subject ratings for each PVS, columns:
    - `pvs_id`: Identifier of the PVS
    - `context`: "pc" or "mobile"
    - `subject`: Subject identifier (unique only within context/database)
    - `rating`: The subject's rating from 1 to 5 (Bad to Excellent) according to P.910 ACR scale.

The following data relates to model output:

- `O21.csv`: Per-output-sample O21 (audio quality) data, valid for all modes, columns:
    - `pvs_id`: Identifier of the PVS
    - `sample_index`: Index of the output sample (1 per second)
    - `O21`: Audio quality score
- `O22.csv`: Per-output-sample O22 (video quality) data, for all modes, columns:
    - `pvs_id`: Identifier of the PVS
    - `mode`: Calculated mode
    - `sample_index`: Index of the output sample (1 per second)
    - `O22`: Video quality score
- `O46.csv`: Per-PVS O46 (video quality) data, for all modes, columns:
    - `pvs_id`: Identifier of the PVS
    - `mode`: Calculated mode
    - `context`: PC or mobile
    - `O46`: Integrated audiovisual quality score

Detailed model output as produced by the P.1203 software:

- `mode0`: One JSON file for each PVS and context (PC/mobile), containing all output keys
- `mode1`: same as above
- `mode2`: same as above
- `mode3`: same as above

Subjective test database design:

- `test_configs/*.yaml`: YAML file containing test configuration
    - `audioVisualQualityLevels`: list of quality representations, with the following entries:
        - video height
        - video target bitrate
        - quality level identifier
        - audio target bitrate
    - `defaultVideoDurationInSec`: PVS duration
    - `displayHeight`: height of the display, fixed to 1080p
    - `ffmpegCommonAudioParams`: common settings for ffmpeg audio encoding
    - `ffmpegCommonVideoParams`: common settings for ffmpeg video encoding
    - `hrcList`: list of HRCs, with each key being the HRC ID
        - `eventList`: list of events in each HRC, each event being a tuple of (event type, duration in seconds), where event type can be a quality representation ID or a "stall" event
    - `segmentDurationInSec`: default duration of video segments
    - `srcList`: list of SRC IDs and a hash of their name
    - `testName`: database ID
    - `x264CommonParams`: common settings for x264 encoder
- `test_configs/*.svg`: SVG plot of database design

## License

Copyright 2018 Deutsche Telekom AG, LM Ericsson, NETSCOUT Systems Inc.

Permission is hereby granted, free of charge, to use this dataset for non-commercial research purposes.

NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY THIS LICENSE. THE DATASET IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE DATASET OR THE USE OR OTHER DEALINGS IN THE DATASET.

## Authors

Main developers:

* David Lindegren, LM Ericsson
* Werner Robitza, Deutsche Telekom AG / Technische Universität Ilmenau

Contributors:

* Marie-Neige Garcia, Technische Universität Berlin
* Steve Göring, Technische Universität Ilmenau
* Alexander Raake, Technische Universität Ilmenau
* Peter List, Deutsche Telekom AG
* Bernhard Feiten, Deutsche Telekom AG
* Ulf Wüstenhagen, Deutsche Telekom AG
* Jörgen Gustafsson, LM Ericsson
* Gunnar Heikkilä, LM Ericsson
* Junaid Shaikh, LM Ericsson
* Simon Broom, NETSCOUT Systems Inc.