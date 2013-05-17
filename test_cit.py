from __future__ import with_statement
from jenkinsapi.jenkins import Jenkins
import cit
import hashlib
import os
import pytest
import time
import xml.etree.ElementTree as ET
import StringIO
import yaml
import mock


JENKINS_URL = 'http://localhost:8080'
JOB_TEST_PREFIX = 'cit-test-job-'

#===================================================================================================
# teardown_module
#===================================================================================================
def teardown_module(module):
    jenkins = Jenkins(JENKINS_URL)
    for name, job in jenkins.get_jobs():
        if name.startswith(JOB_TEST_PREFIX):
            jenkins.delete_job(name)

#===================================================================================================
# jenkins
#===================================================================================================
@pytest.fixture
def tmp_job_name():
    config = file(os.path.join(os.path.dirname(__file__), 'test_config.xml')).read()
    
    jenkins = Jenkins(JENKINS_URL)
    
    hasher = hashlib.sha1(str(time.time()))
    job_name = '%s%s' % (JOB_TEST_PREFIX, hasher.hexdigest())
    
    job = jenkins.create_job(job_name, config)
    job.update_config(config) 
    
    return job_name
    

#===================================================================================================
# test_add
#===================================================================================================
def test_add(tmp_job_name, tmpdir):
    cwd = str(tmpdir.join('.git', 'src', 'plk'))
    os.makedirs(cwd)
    os.chdir(cwd)
    
    global_config_file = str(tmpdir.join('citconfig.yaml'))
    global_config = {'jenkins' : {'url' : JENKINS_URL}}
    yaml.dump(global_config, file(global_config_file, 'w'))
    
    cit_config = {
        'jobs' : [{
            'source-job' : tmp_job_name,
            'feature-branch-job' : tmp_job_name + '-$fb',
        }],
    }
    cit_config_file = str(tmpdir.join('.cit.yaml'))
    yaml.dump(cit_config, file(cit_config_file, 'w'))
    
    branch = 'new-feature'
    with mock.patch('cit.get_git_user', autospec=True) as mock_get_git_user:
        mock_get_git_user.return_value = ('anonymous', 'anonymous@somewhere.com')
        assert cit.main(['cit', 'add', branch], global_config_file=global_config_file) == 0
    
    jenkins = Jenkins(JENKINS_URL)
    new_job_name = tmp_job_name + '-' + branch
    assert jenkins.has_job(new_job_name), "no job %s found. available: %s" % (new_job_name, jenkins.get_jobs_list())
    
    config_xml = jenkins.get_job(new_job_name).get_config()
    
    config = ET.fromstring(config_xml)
    branches_elements = list(config.findall('.//branches'))
    assert len(branches_elements) == 1
    branches_elem = branches_elements[0]
    name_elem = branches_elem.findall('hudson.plugins.git.BranchSpec/name')[0]    
    assert name_elem.text == branch
    
    recipient_elements = list(config.findall('.//hudson.tasks.Mailer/recipients'))
    assert len(recipient_elements) == 1
    recipient_element = recipient_elements[0]
    assert recipient_element.text == 'anonymous@somewhere.com'
    
    
#===================================================================================================
# test_cit_config
#===================================================================================================
def test_cit_config(tmpdir, capsys):    
    cwd = str(tmpdir.join('.git', 'src', 'plk'))
    os.makedirs(cwd)
    os.chdir(cwd)
    
    global_config_file = str(tmpdir.join('citconfig.yaml'))
    global_config = {'jenkins' : {'url' : JENKINS_URL}}
    yaml.dump(global_config, file(global_config_file, 'w'))
    
    input_lines = [
        'project_win32', 
        'project_$fb_win32',
        'project_win64', 
        'project_$fb_win64',
        '',
    ]
    stdin = StringIO.StringIO('\n'.join(input_lines))
    assert cit.main(['cit', 'config'], stdin=stdin, global_config_file=global_config_file) == 0
    
    cit_file = tmpdir.join('.cit.yaml')
    assert cit_file.ensure()
    contents = cit_file.read()
    obtained = yaml.load(contents)
    
    expected = {
        'jobs' : [
            {
                'source-job': 'project_win32',
                'feature-branch-job' : 'project_$fb_win32', 
            },
            {
                'source-job': 'project_win64',
                'feature-branch-job' : 'project_$fb_win64', 
            },
        ]
    }
    assert obtained == expected 
    
    
#===================================================================================================
# main    
#===================================================================================================
if __name__ == '__main__':    
    pytest.main()