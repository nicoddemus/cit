'''
Simple install script that installs cit and its dependencies without touching the local python 
installation.

Usage::
    wget https://raw.github.com/nicoddemus/cit/master/cit_install.py 
    python cit_install.py
'''
import subprocess
import os
import sys

# can only start installation if in an empty directory or if directory contains this file
contents = os.listdir('.')
print contents 
if contents and contents != [os.path.basename(__file__)]:
    sys.exit('cit must be installed in an empty directory.')
    
print '=' * 60
print 'Fetching Cit'
print '=' * 60    
subprocess.check_call('git clone http://github.com/nicoddemus/cit.git .', shell=True)
subprocess.check_call('git submodule init', shell=True)
subprocess.check_call('git submodule update', shell=True)
subprocess.check_call('python cit.py --install', shell=True)
