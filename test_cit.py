from __future__ import with_statement
from jenkinsapi.jenkins import Jenkins
import StringIO
import cit # must be imported first to install submodules on PYTHONPATH
import hashlib
import mock
import os
import pytest
import time
import xml.etree.ElementTree as ET
import yaml
import sys


JENKINS_URL = 'http://localhost:8080'
JOB_TEST_PREFIX = 'cit-test-job-'

#===================================================================================================
# jenkins
#===================================================================================================
@pytest.fixture
def tmp_job_name(request):
    config = file(os.path.join(os.path.dirname(__file__), 'test_config.xml')).read()
    
    jenkins = Jenkins(JENKINS_URL)
    
    hasher = hashlib.sha1(str(time.time()))
    job_name = '%s%s' % (JOB_TEST_PREFIX, hasher.hexdigest())
    
    job = jenkins.create_job(job_name, config)
    job.update_config(config) 
    
    def delete_test_jobs():
        '''
        finalizer for this fixture that removes left-over test jobs from the live jenkins server.
        '''
        jenkins = Jenkins(JENKINS_URL)
        for name, job in jenkins.get_jobs():
            if name.startswith(JOB_TEST_PREFIX):
                jenkins.delete_job(name)
                
    request.addfinalizer(delete_test_jobs)
    return job_name


#===================================================================================================
# change_cwd
#===================================================================================================
@pytest.fixture
def change_cwd(tmpdir):
    '''
    creates a suitable source directory to ensure our configuration suite is being found and loaded
    correctly. 
    
    :return: working directory, as a sub-directory of the given temp dir 
    '''
    os.makedirs(str(tmpdir.join('.git')))
    
    cwd = str(tmpdir.join('src', 'plk'))
    os.makedirs(cwd)
    os.chdir(cwd)
    
    
#===================================================================================================
# global_config_file
#===================================================================================================
@pytest.fixture
def global_config_file(tmpdir):    
    '''
    fixture that initializes a config file in the given temp directory. Useful to test cit 
    commands when it has already been correctly configured. 
    '''
    global_config_file = str(tmpdir.join('citconfig.yaml'))
    global_config = {'jenkins' : {'url' : JENKINS_URL}}
    yaml.dump(global_config, file(global_config_file, 'w'))
    return global_config_file
    

#===================================================================================================
# test_add
#===================================================================================================
@pytest.mark.skipif('not config.option.jenkins_available')
@pytest.mark.usefixtures('change_cwd')
@pytest.mark.parametrize('branch', ['new-feature', None])
def test_add(tmp_job_name, tmpdir, global_config_file, branch):
    '''
    test command "add"
    
    :param branch: 
        parametrized to test adding passing a branch name in the command line and without
        (which means "use current branch as branch name") 
    '''
    cit_config = {
        'jobs' : [{
            'source-job' : tmp_job_name,
            'feature-branch-job' : tmp_job_name + '-$name',
        }],
    }
    cit_config_file = str(tmpdir.join('.cit.yaml'))
    yaml.dump(cit_config, file(cit_config_file, 'w'))
    
    with mock.patch('cit.get_git_branch', autospec=True) as mock_get_git_branch:
        mock_get_git_branch.return_value = 'new-feature'
        
        with mock.patch('cit.get_git_user', autospec=True) as mock_get_git_user:
            mock_get_git_user.return_value = ('anonymous', 'anonymous@somewhere.com')
            
            with mock.patch('cit.get_global_config_file', autospec=True) as mock_get_global_config_file:
                mock_get_global_config_file.return_value = str(global_config_file)
                argv = ['fb.add']
                if branch:
                    argv.append(branch)
                assert cit.app.main(argv) is None
    
    branch = 'new-feature'
    
    jenkins = Jenkins(JENKINS_URL)
    new_job_name = tmp_job_name + '-' + branch
    assert jenkins.has_job(new_job_name), "no job %s found. available: %s" % (new_job_name, jenkins.get_jobs_list())
    
    config_xml = jenkins.get_job(new_job_name).get_config()
    
    # ensure we configured branch correctly
    config = ET.fromstring(config_xml)
    branches_elements = list(config.findall('.//branches'))
    assert len(branches_elements) == 1
    branches_elem = branches_elements[0]
    name_elem = branches_elem.findall('hudson.plugins.git.BranchSpec/name')[0]    
    assert name_elem.text == branch
    
    # ensure we have updated the display name with the feature branch's name
    display_name_elements = list(config.findall('.//displayName'))
    assert len(display_name_elements) == 1
    display_name_element = display_name_elements[0]
    assert display_name_element.text == '%s SS win32' % branch
    
    # ensure we have set the user email recipient
    recipient_elements = list(config.findall('.//hudson.tasks.Mailer/recipients'))
    assert len(recipient_elements) == 1
    recipient_element = recipient_elements[0]
    assert recipient_element.text == 'anonymous@somewhere.com'
    
    # ensure we don't have build parameters anymore
    params = list(config.findall('.//hudson.model.ParametersDefinitionProperty'))
    assert len(params) == 0

    # ensure no build is triggered after the job
    build_triggers = list(config.findall('.//hudson.tasks.BuildTrigger'))
    assert len(build_triggers) == 0
    
    
#===================================================================================================
# test_cit_init
#===================================================================================================
@pytest.mark.usefixtures('change_cwd')
def test_cit_init(tmpdir):    
    input_lines = [
        'project_win32', 
        'project_$name_win32',
        'project_win64', 
        'project_$name_win64',
        '',
    ]
    stdin = StringIO.StringIO('\n'.join(input_lines))
    try:
        sys.stdin = stdin
        assert cit.app.main(['fb.init']) is None
    finally:
        sys.stdin = sys.__stdin__
    
    cit_file = tmpdir.join('.cit.yaml')
    assert cit_file.ensure()
    contents = cit_file.read()
    obtained = yaml.load(contents)
    
    expected = {
        'jobs' : [
            {
                'source-job': 'project_win32',
                'feature-branch-job' : 'project_$name_win32', 
            },
            {
                'source-job': 'project_win64',
                'feature-branch-job' : 'project_$name_win64', 
            },
        ]
    }
    assert obtained == expected 
    
    
#===================================================================================================
# test_cit_install
#===================================================================================================
@pytest.mark.usefixtures('change_cwd')
def test_cit_install(tmpdir):    
    global_config_file = tmpdir.join('citconfig.yaml')
    
    with mock.patch('cit.get_global_config_file', autospec=True) as mock_get_global_config_file:
        mock_get_global_config_file.return_value = str(global_config_file)
    
        input_lines = [
            'localhost:8080',
            '',
        ]
        stdin = StringIO.StringIO('\n'.join(input_lines))
        sys.stdin = stdin        
        try:
            assert cit.app.main(['install']) is None
        finally:
            sys.stdin = sys.__stdin__ 
        
        assert global_config_file.ensure()
        contents = global_config_file.read()
        obtained = yaml.load(contents)
        assert obtained == {'jenkins' : {'url' : 'http://localhost:8080'}}     
    
    
#===================================================================================================
# main    
#===================================================================================================
if __name__ == '__main__':    
    pytest.main()
