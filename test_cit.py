from jenkinsapi.jenkins import Jenkins
import cit
import hashlib
import os
import pytest
import time
import xml.etree.ElementTree as ET
import StringIO
import yaml


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
def jenkins(request):
    config = file(os.path.join(os.path.dirname(__file__), 'test_config.xml')).read()
    
    jenkins = Jenkins(JENKINS_URL)
    
    hasher = hashlib.sha1(str(time.time()))
    job_name = '%s%s' % (JOB_TEST_PREFIX, hasher.hexdigest())
    
    job = jenkins.create_job(job_name, config)
    job.update_config(config) 
    
    jenkins.cit_test_job_name = job_name
    
    return jenkins
    

#===================================================================================================
# test_create_feature_branch
#===================================================================================================
def test_create_feature_branch(jenkins, capsys):
    branch = 'my-feature'
    new_job_name = jenkins.cit_test_job_name + '-' + branch
    owner = 'nicoddemus@gmail.com'
    cit.create_feature_branch_job(JENKINS_URL, jenkins.cit_test_job_name, new_job_name, branch, owner)
    
    jenkins.poll()
    
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
    assert recipient_element.text == 'someone@somewhere.com nicoddemus@gmail.com'
    
    
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
    cit.main(['cit', 'config'], stdin=stdin, global_config_file=global_config_file)
    
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
    pytest.main(['-s', '-ktest_cit_config'])