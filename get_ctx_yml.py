#!/usr/bin/env python

import argparse
import os
import subprocess
import yaml
import base64
import sys

parser = argparse.ArgumentParser(description="")

parser.add_argument(
    "-k",
    "--kubeconfig",
    dest="file",
    help="kubeconfig file",
    required=False,
    default=os.getenv("KUBECONFIG"),
)
parser.add_argument(
    "-c",
    "--context",
    dest="ctx",
    help="context name",
    required=False,
)
parser.add_argument(
    "-o",
    "--oupfile",
    dest="oupfile",
    help="output kubeconfig file",
    required=True,
)

args = parser.parse_args()

if args.file == "":
    print("KUBECONFIG not set")
    exit(1)

cmd = [
    "kubectl",
    "--kubeconfig",
    args.file,
    "config",
    "view",
    "-o",
    "yaml",
    "--minify",
    "--raw",
]
if args.ctx:
    cmd.append("--context")
    cmd.append(args.ctx)

cfg_str = ""
try:
    result = subprocess.run(
        cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    cfg_str = result.stdout.decode("utf-8")
except subprocess.CalledProcessError as e:
    print(e.stderr.decode("utf-8"))
    sys.exit(e.returncode)


cfg = yaml.safe_load(cfg_str)
crt_file = cfg["users"][0]["user"]["client-certificate"]
key_file = cfg["users"][0]["user"]["client-key"]
crt_dir = os.path.dirname(args.file)
crt_path = os.path.join(crt_dir, crt_file)
key_path = os.path.join(crt_dir, key_file)

crt = bytes()
with open(crt_path, "rb") as f:
    crt = f.read()
encoded_crt = base64.b64encode(crt)
encoded_crt_str = encoded_crt.decode("utf-8")

key = bytes()
with open(key_path, "rb") as f:
    key = f.read()
encoded_key = base64.b64encode(key)
encoded_key_str = encoded_key.decode("utf-8")

del cfg["users"][0]["user"]["client-certificate"]
del cfg["users"][0]["user"]["client-key"]

cfg["users"][0]["user"]["client-certificate-data"] = encoded_crt_str
cfg["users"][0]["user"]["client-key-data"] = encoded_key_str

with open(args.oupfile, "w") as f:
    yaml.dump(cfg, f)
