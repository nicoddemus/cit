'''
Simple install script that installs cit and its dependencies without touching the local python 
installation.

Usage::
    curl -s https://raw.github.com/nicoddemus/cit/master/cit_install.py | python
'''
import subprocess
import os
import sys
import shutil

if os.listdir('.'):
    sys.exit('cit must be instealled in an empty directory.')

os.mkdir('repos')
os.chdir('repos')

print '--> simplejson'    
subprocess.check_call('git clone http://github.com/simplejson/simplejson', shell=True)
print '--> JenkinsAPI'    
subprocess.check_call('git clone http://github.com/salimfadhley/jenkinsapi', shell=True)
print '--> cit'    
subprocess.check_call('git clone http://github.com/nicoddemus/cit.git', shell=True)

os.chdir('..')
shutil.copy('repos/cit/cit.py', 'cit.py')
shutil.copytree('repos/jenkinsapi/jenkinsapi', 'jenkinsapi')
shutil.copytree('repos/simplejson/simplejson', 'simplejson')





