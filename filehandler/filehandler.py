import subprocess
import sys
import os

def run(cmd):
    proc = subprocess.Popen(cmd,
        stdout = subprocess.PIPE,
        stderr = subprocess.PIPE,
    )
    stdout, stderr = proc.communicate()
 
    return proc.returncode, stdout, stderr

def get_mzML_files():
    code, out, err = run([sys.executable, os.path.join("filehandler","mzMLfiles.py")])
    return [f for f in out.decode("utf-8").strip().split("\n") if len(f) > 0]
    
def get_result_dir():
    code, out, err = run([sys.executable, os.path.join("filehandler","resultdir.py")])
    return out.decode("utf-8").strip()
