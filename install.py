'''
Simple install script to update submodules and execute initial configuration.

Usage::
    python cit_install.py
'''
import subprocess

print '=' * 60
print 'Fetching submodules'
print '=' * 60
subprocess.check_call('git submodule init', shell=True)
subprocess.check_call('git submodule update', shell=True)
subprocess.check_call('python cit.py install', shell=True)
