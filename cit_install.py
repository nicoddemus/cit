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
import urllib
import urllib2

if os.listdir('.'):
    sys.exit('cit must be installed in an empty directory.')

#===================================================================================================
# Download
#===================================================================================================
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
print 'Download done.'

import simplejson
from jenkinsapi.jenkins import Jenkins
import jenkinsapi.utils.retry # initializing logging, so it will shut up later and don't mess our output

#===================================================================================================
# Configure
#===================================================================================================
print '=' * 60
print 'Configuring:'
print '=' * 60
jenkins_url = raw_input('Jenkins URL (make sure to include http:// or https://): ')
config = {
    'jenkins' : {
        'url' : jenkins_url,
    }
}

filename = os.path.abspath('.citconfig')
f = file(filename, 'w')
f.write(simplejson.dumps(config))
f.close()

print 'Written configuration to: %s' % filename
print

#===================================================================================================
# Check Jenkins
#===================================================================================================
print 'Checking if Jenkins server is correct...',
try:
    jenkins = Jenkins(jenkins_url)
except urllib2.URLError, e:
    print 'Could not connect:'
    print ' --> %s' % e
    print 'Update configuration file manually.'
else:
    print 'OK'



