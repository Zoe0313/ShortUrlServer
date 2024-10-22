#!/usr/bin/env python

# Copyright 2023 VMware, Inc.  All rights reserved. -- VMware Confidential

'''
Module docstring.  
redis_backup.py
'''
import os
import subprocess
from datetime import datetime

pod_name = "redis-stack-server-master-0"
backup_dir = "/url-shortener/backup/"
kubectl_file = '/url-shortener/cronjob/vsanperf-shorturl-kubectl.yaml'

if not os.path.exists(backup_dir):
    os.makedirs(backup_dir)

def backup_redis(backup_file, remote_file):
    try:
        local_backup_path = os.path.join(backup_dir, backup_file)
        if os.path.exists(local_backup_path):
            os.remove(local_backup_path)

        compress_command = [
            "kubectl", f"--kubeconfig={kubectl_file}",
            "exec", "-it", pod_name, "--",
            "tar", "-czvf", f"/data/{backup_file}", remote_file
        ]
        print("Compressing Redis RDB file in the Pod...")
        subprocess.run(compress_command, check=True)

        print(f"Copying {backup_file} to local backup directory...")
        copy_command = [
            "kubectl", f"--kubeconfig={kubectl_file}",
            "cp", f"{pod_name}:/data/{backup_file}", local_backup_path
        ]
        subprocess.run(copy_command, check=True)

        print(f"Backup successful! File saved at: {local_backup_path}")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred during the backup: {e}")
    finally:
        cleanup_command = [
            "kubectl", f"--kubeconfig={kubectl_file}",
            "exec", "-it", pod_name, "--",
            "rm", f"/data/{backup_file}"
        ]
        subprocess.run(cleanup_command, check=True)
        print(f"Cleanup complete: {backup_file} removed from the Pod.")

if __name__ == "__main__":
    timestamp = datetime.now().strftime("%Y%m%d")
    backup_infos = [
        {"source": "/data/dump.rdb", "target": f"dump.rdb.{timestamp}.tar.gz"},
        {"source": "/data/appendonly.aof", "target": f"appendonly.aof.{timestamp}.tar.gz"}
    ]
    for backup_info in backup_infos:
        backup_file = backup_info["target"]
        remote_file = backup_info["source"]
        backup_redis(backup_file, remote_file)
