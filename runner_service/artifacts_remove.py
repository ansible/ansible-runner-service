import argparse
import os
import time
import datetime
import shutil


def main(playbooks_root_dir, artifacts_remove_age):
    artifacts_dir = os.path.join(playbooks_root_dir, "artifacts")
    dir_list = os.listdir(artifacts_dir)
    time_now = time.mktime(time.localtime())
    for artifacts in dir_list:
        date = os.path.getmtime("{}/{}".format(artifacts_dir, artifacts))
        time_difference = datetime.timedelta(seconds=time_now - date)
        if time_difference.days >= artifacts_remove_age:
            shutil.rmtree(os.path.join(artifacts_dir, artifacts))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Remove old artifacts')
    parser.add_argument('--playbooks_root_dir', required=True)
    parser.add_argument('--artifacts_remove_age', required=True, type=int)
    args = parser.parse_args()

    main(args.playbooks_root_dir, args.artifacts_remove_age)
