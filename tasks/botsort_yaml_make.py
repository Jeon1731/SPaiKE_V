import sys
import os
import yaml

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import utils.config as config

class BotsortYamlMaker:
    def start(self):
        print("BotsortYMaker: start")

        dir_path = os.path.dirname(config.BOTSORT_TRACKER_PATH)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)

        parameters = {
            'tracker_type' : 'botsort',
            'track_high_thresh' : 0.75,
            'track_low_thresh' : 0.1,
            'new_track_thresh' : 0.75,
            'track_buffer' : 100,
            'match_thresh' : 0.8,
            'fuse_score' : True,
            'gmc_method' : 'sparseOptFlow',
            'proximity_thresh' : 0.5,
            'appearance_thresh' : 0.25,
            'with_reid' : True,
            'model' : 'auto'
        }

        with open(config.BOTSORT_TRACKER_PATH, 'w', encoding='utf-8') as f:
            yaml.dump(parameters, f, allow_unicode=True, default_flow_style=False)

        print("BotsortYMaker: finished")