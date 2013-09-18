from __future__ import with_statement

#===================================================================================================
# configure_submodules_path
#===================================================================================================
def configure_submodules_path():
    '''
    Configures sys.path to detect our submodule dependencies. Must be called before trying to do
    any other imports.
    '''
    import sys, os

    directory = os.path.abspath(os.path.dirname(__file__))
    sys.path.insert(0, os.path.join(directory, 'jenkinsapi'))
    sys.path.insert(0, os.path.join(directory, 'pyyaml', 'lib'))
    sys.path.insert(0, os.path.join(directory, 'clik'))

configure_submodules_path()

#===================================================================================================
# imports
#===================================================================================================
from jenkinsapi.exceptions import UnknownJob
from jenkinsapi.jenkins import Jenkins
import contextlib
import subprocess
import xml.etree.ElementTree as ET
import yaml
import os
import sys
import urllib2
import glob
import re
import time
import clik
from optparse import make_option as opt

#===================================================================================================
# clik initialization
#
# This block is used to initialize clik framework
#
#===================================================================================================

#===================================================================================================
# get_global_config_file
#===================================================================================================
def get_global_config_file():
    '''
    Returns the path to the global config file. 
    '''
    # default values
    global_config_file = os.environ.get('CIT_CONFIG')
    if global_config_file is None:
        global_config_file = os.path.join(os.path.dirname(__file__), 'citconfig.yaml')
    return global_config_file


#===================================================================================================
# get_command_args
#===================================================================================================
def get_command_args(opts):
    '''
    Returns a dict containing all extra options that commands in this module can receive as
    arguments. 
    
    See clik framework for more details on this.
    '''
    cit_file_name, job_config = load_cit_local_config(os.getcwd())
    
    # user, email, branch
    user_name, user_email = get_git_user()
    branch = get_git_branch()
    
    global_config_file = get_global_config_file()
        
    # read global config
    if os.path.isfile(global_config_file):
        global_config = yaml.load(file(global_config_file).read())
    else:
        global_config = {}
    
    return {
        'job_config' : job_config,
        'global_config' : global_config,
        'user_name' : user_name,
        'user_email' : user_email,
        'branch' : branch,
    }



app = clik.App(
    name='cit',
    description='Command line tool for interacting with a Jenkins integration server.\n', 
    args_callback=get_command_args, 
    shell_command=False,
    console_opts=False,
)

#===================================================================================================
# Feature Branch Commands
# -----------------------
# 
# The next commands deal with feature branch jobs for the git repository in the current directory.  
# 
#===================================================================================================

#===================================================================================================
# create_feature_branch_job
#===================================================================================================
def create_feature_branch_job(jenkins, job_name, new_job_name, branch, user_email):
    try:
        job = jenkins.get_job(new_job_name)
    except UnknownJob:
        status = 'CREATED'
        job = jenkins.copy_job(job_name, new_job_name)
    else:
        status = 'UPDATED'

    print '%s => %s (%s)' % (job_name, new_job_name, status)

    original_job = jenkins.get_job(job_name)
    tree = ET.fromstring(original_job.get_config())

    branch_elements = list(tree.findall('.//hudson.plugins.git.BranchSpec/name'))
    if len(branch_elements) > 0:
        branch_elements[0].text = branch
    else:
        print '  warning: Could not find any branch spec to replace!'

    # If displayName exists adds the feature branch name to it.
    display_name_elem = tree.find('./displayName')
    if display_name_elem is not None:
        display_name_elem.text = '%(branch_name)s %(display_name)s' % {'display_name':display_name_elem.text, 'branch_name':branch}

    recipient_elements = list(tree.findall('.//hudson.tasks.Mailer/recipients'))
    if len(recipient_elements) == 1:
        recipient_element = recipient_elements[0]
        recipient_element.text = user_email

    # remove properties from the build so we can use "start" to start-up jobs
    properties_elem = tree.find('./properties')
    if properties_elem is not None:
        for elem in properties_elem.findall('./hudson.model.ParametersDefinitionProperty'):
            properties_elem.remove(elem)

    # remove build triggers after this job
    publishers_elem = tree.find('./publishers')
    if publishers_elem is not None:
        for elem in publishers_elem.findall('./hudson.tasks.BuildTrigger'):
            publishers_elem.remove(elem)

    job.update_config(ET.tostring(tree))

    return job


#===================================================================================================
# feature_branch_add
#===================================================================================================
@app(alias='fb.add', usage='[branch]')
def feature_branch_add(args, branch, user_email, job_config, global_config):
    '''
    Create/Update jobs associated with the current git branch.
    
    This will create one or more jobs on jenkins for the current feature branch,
    or for the one given as parameter if one is provided.
    '''
    if args:
        branch = args[0]

    jenkins_url = global_config['jenkins']['url']
    jenkins = Jenkins(jenkins_url)
    for job_name, new_job_name in get_configured_jobs(branch, job_config):
        create_feature_branch_job(jenkins, job_name, new_job_name, branch, user_email)


#===================================================================================================
# feature_branch_rm
#===================================================================================================
@app(alias='fb.rm', usage='[branch]')
def feature_branch_rm(args, branch, global_config, job_config):
    '''
    Remove jobs associated with the current git branch.
    
    This will remove one or more jobs from jenkins created previously with "feature_branch_add".
    If no branch is given the current one will be used.
    '''
    if args:
        branch = args[0]

    jenkins_url = global_config['jenkins']['url']
    jenkins = Jenkins(jenkins_url)
    for _, new_job_name in get_configured_jobs(branch, job_config):
        if jenkins.has_job(new_job_name):
            jenkins.delete_job(new_job_name)
            print new_job_name, '(REMOVED)'
        else:
            print new_job_name, '(NOT FOUND)'
            
            
#===================================================================================================
# feature_branch_start
#===================================================================================================
@app(alias='fb.start', usage='[branch]')
def feature_branch_start(args, branch, job_config, global_config):
    '''
    Start jobs associated with the current git branch.
    '''
    if args:
        branch = args[0]

    jenkins_url = global_config['jenkins']['url']
    jenkins = Jenkins(jenkins_url)

    for _, new_job_name in get_configured_jobs(branch, job_config):
        if jenkins.has_job(new_job_name):
            job = jenkins.get_job(new_job_name)
            if not job.is_running():
                job.invoke()
                status = '(STARTED)'
            else:
                status = '(RUNNING)'
        else:
            status = '(NOT FOUND)'
        print new_job_name, status
        
        
#===================================================================================================
# feature_branch_init
#===================================================================================================
@app(alias='fb.init', usage='[branch]')
def feature_branch_init():
    '''
    *Initial* feature-branch configuration for the current git repository.
    
    This command will ask in sequence for the names of the jobs you would like to use
    as basis for feature branch jobs at your Jenkins server. Usually you will want all
    job variations that build the "master" branch. 
    '''
    cit_file_name, config = load_cit_local_config(os.getcwd())

    print 'Configuring jobs for feature branches: %s' % cit_file_name
    print

    updated = 0
    while True:
        sys.stdout.write('Source job (empty to exit):      ')
        source_job = sys.stdin.readline().strip()
        if not source_job:
            break

        sys.stdout.write('Feature job (shh, use $name):    ')
        fb_job = sys.stdin.readline().strip()
        if not fb_job:
            break

        fb_data = {
            'source-job' : source_job,
            'feature-branch-job' : fb_job,
        }
        config.setdefault('jobs', []).append(fb_data)
        updated += 1
        print 'Done! Next?'
        print

    print
    if updated:
        f = file(cit_file_name, 'w')
        f.write(yaml.dump(config, default_flow_style=False))
        f.close()
        print 'Done! Configured %d job(s)!' % updated
    else:
        print 'Abort? Okaay.'
        
        
#===================================================================================================
# Server Commands
# -----------------------
# 
# The next commands deal directly with jobs on the server, and can be run from anywhere.  
# 
#===================================================================================================

#===================================================================================================
# server_list_jobs
#===================================================================================================
re_option = opt('--re', help='pattern is a regular expression', default=False, action='store_true')
list_jobs_opts = [
    re_option,
    opt('-i', '--interactive', help='interactively remove or start them', default=False, action='store_true'),
]
@app(alias='sv.ls', usage='<pattern> [options]', opts=list_jobs_opts)
def server_list_jobs(args, global_config, opts):
    '''
    Lists the jobs whose name match a given pattern.
    '''
    import fnmatch
    
    if len(args) < 1:
        print >> sys.stderr, 'error: missing pattern'
        return 2
    
    # TODO: other commands call this one; we should refactor this to make most of the functionality
    # reusable
    if not hasattr(opts, 'interactive'):
        opts.interactive = False
    
    pattern = args[0]

    jenkins_url = global_config['jenkins']['url']
    jenkins = Jenkins(jenkins_url)
    
    def match(job_name):
        if opts.re:
            return re.match(pattern, job_name)
        else:
            return fnmatch.fnmatch(jobname, pattern)

    jobs = []
    for jobname in jenkins.iterkeys():
        if match(jobname):
            job = jenkins.get_job(jobname)
            if opts.interactive:
                print get_job_status(jobname, job, len(jobs))
            else:
                print '\t', jobname
            jobs.append((jobname, job))

    def delete_jobs(jobs):
        while True:
            job_index = raw_input('Delete job? id = ')
            try:
                job_index = int(job_index)
            except:
                break
            else:
                try:
                    job_name, job = jobs[job_index]
                except:
                    pass
                else:
                    ans = raw_input('Delete job (y(es)|n(o)? %r: ' % job_name).lower()
                    if ans.startswith('y'):
                        jenkins.delete_job(job_name)
        
    # TODO: remove this option from here, it belongs in a separate command
    if opts.interactive:
        ans = raw_input('Select an operation? (rm | start | e(xit)): ').lower()
        if not ans or ans.startswith('e'):
            return
        
        elif ans == 'rm':
            delete_jobs(jobs)
        
        elif ans == 'start':
            job_index = raw_input('Invoke job? id = ')
            if job_index:
                try:
                    job_index = int(job_index)
                except:
                    pass
                else:
    
                    try:
                        job_name, job = jobs[job_index]
                    except:
                        pass
                    else:
                        print 'Invoking job: %r' % job_name
                        job.invoke()

    return jenkins, jobs

            
#===================================================================================================
# get_job_status
#===================================================================================================
def get_job_status(job_name, job, job_index=None):
    try:
        build = job.get_last_build()
    except:
        status = 'NONE'
        if job.is_running():
            status = 'Running'
        timestamp = '-'
    else:
        if build.is_running():
            status = 'RUNNING'
        else:
            status = build.get_status()
        # get_timestamp - the number of milliseconds since January 1, 1970, 00:00:00 GMT represented by this date.
        timestamp = str(time.ctime(build.get_timestamp() / 1000.0))

    if job_index is None:
        job_index = ''
    return '%2s %10s (%25s) - %s' % (job_index, status, timestamp, job_name)


#===================================================================================================
# JobInfo
#===================================================================================================
class JobInfo(object):
    
    REGEX_JOB_NAME = re.compile(r'(.+__)(\d{2,3})-(.+)')
                
    def __init__(self, directory):
        '''
        
        :param directory:
        '''
        self.directory = directory
        self.name = os.path.basename(directory)
        config_filename = os.path.join(directory, 'config.xml')
        if os.path.exists(config_filename):
            self.config_filename = config_filename
        else:
            self.config_filename = None
        
    def BaseName(self):
        '''
        :return str: The job name without it's index  
        '''
        match = self.REGEX_JOB_NAME.match(self.name)
        if match:
            return match.group(1) + match.group(3)
    
    def SearchPattern(self):
        '''
        :return str: THe pattern to list the jobs
        '''
        match = self.REGEX_JOB_NAME.match(self.name)
        if match:
            return match.group(1) + '*'
        

#===================================================================================================
# server_upload_jobs
#===================================================================================================
reindex_opt = opt('--reindex', default=False, action='store_true', help='reindexes jobs')
@app(alias='sv.up', usage='<directory>', opts=[reindex_opt])
def server_upload_jobs(args, global_config, opts):
    '''
    Uploads jobs found in a directory directly to jenkins.
    
    The jobs should be defined as with a "config.xml" file per job, while the directory containing the
    "config.xml" file will be used as the name of the job:
        
        source-dir
            /job-name1
                /config.xml
            /job-name2
                /config.xml
                
    Executing "cit server_upload_jobs source-dir" will upload "job-1" and "job-2" to jenkins,
    creating or updating them.
    '''
    if not args:
        print >> sys.stderr, "error: Must pass a directory name"
        return 2
    
    directory = args[0]
    if not os.path.exists(directory):
        print >> sys.stderr, 'error: Directory "%s" does not exist' % directory
        return 2


    jenkins_url = global_config['jenkins']['url']
    jenkins = Jenkins(jenkins_url)

    search_pattern = None
    local_jobs = []
    for dir_name in glob.glob(directory + '/*'):
        # Ignore all files
        if not os.path.isdir(dir_name):
            continue

        job_info = JobInfo(dir_name)
        if job_info.config_filename is None:
            print 'Missing config.xml file from %r' % dir_name
            continue
        
        if opts.reindex:
            if search_pattern is None:
                search_pattern = job_info.SearchPattern()
            elif search_pattern != job_info.SearchPattern():
                raise ValueError('Bad job names pattern: %r != %r' % (search_pattern, job_info.SearchPattern()))
        
        job_info.update = jenkins.has_job(job_info.name)
        local_jobs.append(job_info)
        
    rename_jobs = {}
    delete_jobs = []
    if opts.reindex:
        remote_jobs = get_remote_job_infos(search_pattern, global_config, jenkins=jenkins)
        remote_basenames = dict((ji.BaseName(), ji) for ji in remote_jobs)
        
        for job_info in local_jobs:
            base_name = job_info.BaseName()
            remote_job = remote_basenames.pop(base_name, None)
            if remote_job is not None and remote_job.name != job_info.name:
                rename_jobs[job_info.name] = remote_job.name
        
        delete_jobs = [ji.name for ji in remote_basenames.itervalues()]
        
    for job_info in local_jobs:
        if job_info.name in rename_jobs:
            print 'Renaming %r -> %r' % (rename_jobs[job_info.name], job_info.name)
            
        elif job_info.update:
            print 'Updating %r' % job_info.name
        else:
            print 'Creating %r' % job_info.name
            
    for job_name in delete_jobs:
        print
        print 'Deleting %r' % job_name
        print
            
    if len(local_jobs) > 0:
        ans = raw_input('Update jobs (y|*n): ')
        if ans.startswith('y'):
            for job_info in local_jobs:
                config_xml = file(job_info.config_filename).read()
                
                if job_info.name in rename_jobs:
                    remote_name = rename_jobs[job_info.name]
                    print '\tUpdating job'
                    job = jenkins.get_job(remote_job.name)
                    job.update_config(config_xml)
                    
                    print 'Renaming %r -> %r' % (remote_name, job_info.name)
                    jenkins.rename_job(remote_name, job_info.name)
                    
                else:
                    if job_info.update:
                        print 'Updating %r' % job_info.name
                        job = jenkins.get_job(job_info.name)
                        job.update_config(config_xml)
                    else:
                        print 'Creating %r' % job_info.name
                        job = jenkins.create_job(job_info.name, config_xml)

            for job_name in delete_jobs:
                print 'Deleting %r' % job_name
                job = jenkins.delete_job(job_name)


#===================================================================================================
# server_download_jobs
#===================================================================================================
@app(alias='sv.down', usage='<pattern> [directory] [options]', opts=[re_option])
def server_download_jobs(args, opts, global_config):
    '''
    Downloads jobs from jenkins whose name match the given pattern (fnmatch or regex style).
    
    If the directory is not given, it will default to "."
    '''
    if len(args) < 1:
        print >> sys.stderr, 'error: Missing pattern argument'
        return 2
    
    pattern = args[0]
    
    if len(args) > 1:
        directory = args[1]
    else:
        directory = '.'
        
    jenkins, jobs_to_download = server_list_jobs([pattern], global_config, opts)
    
    print 'Found: %d jobs' % len(jobs_to_download)
    ans = raw_input("Download jobs?(y|*n): ")
    
    if not ans.lower().startswith('y'):
        return
        
    directory = directory or 'hudson'
    if not os.path.exists(directory):
        os.mkdir(directory)

    for jobname, job in jobs_to_download:
        print 'Downloading: %r' % jobname
        job_dir = os.path.join(directory, jobname) 
        os.mkdir(job_dir)
        xml_filename = os.path.join(job_dir, 'config.xml')
        job_xml = job.get_config()
        file(xml_filename, 'w').write(job_xml)


#===================================================================================================
# get_remote_job_infos
#===================================================================================================
def get_remote_job_infos(pattern, global_config, use_re=False, jenkins=None):
    '''
    :param jenkins:
    '''
    import fnmatch
    
    if jenkins is None:
        jenkins_url = global_config['jenkins']['url']
        jenkins = Jenkins(jenkins_url)

    regex = re.compile(pattern)
    
    def match(job_name):
        if use_re:
            return regex.match(job_name)
        else:
            return fnmatch.fnmatch(jobname, pattern)

    jobs = []
    for jobname in jenkins.iterkeys():
        if match(jobname):
            jobs.append(JobInfo(jobname))
            
    return jobs
    

#===================================================================================================
# server_rm_jobs
#===================================================================================================
@app(alias='sv.rm', usage='<pattern> [directory] [options]', opts=[re_option])
def server_rm_jobs(args, opts, global_config):
    jenkins, jobs_to_delete = server_list_jobs(args, global_config, opts)

    if len(jobs_to_delete) > 0:
        print 'Found: %d jobs' % len(jobs_to_delete)
        ans = raw_input("Delete jobs?(y|*n): ")
        if ans.startswith('y'):
            for jobname, job in jobs_to_delete:
                print 'Deleting: %r' % jobname
                jenkins.delete_job(jobname)


#===================================================================================================
# git helpers
# -----------
#
# Git-related helper functions to extract user name, current branch, etc.
#
#===================================================================================================

#===================================================================================================
# get_git_user
#===================================================================================================
def get_git_user():
    try:
        user_name = check_output('git config --get user.name', shell=True).strip()
        user_email = check_output('git config --get user.email', shell=True).strip()
    except subprocess.CalledProcessError:
        return None, None
    else:
        return user_name, user_email


#===================================================================================================
# get_git_branch
#===================================================================================================
def get_git_branch():
    try:
        return check_output('git rev-parse --abbrev-ref HEAD', shell=True).strip()
    except subprocess.CalledProcessError:
        return None


#===================================================================================================
# cit_install
#===================================================================================================
@app(alias='install')
def cit_install():
    '''
    Configures cit for the first time.
    
    This command should be used to configure cit for the first time. 
    '''
    print '=' * 60
    print 'Configuration'
    print '=' * 60
    sys.stdout.write('- Enter Jenkins URL:   ')
    jenkins_url = sys.stdin.readline().strip()
    if not jenkins_url.startswith('http'):
        jenkins_url = 'http://' + jenkins_url

    print
    print 'Checking Jenkins server...',
    try:
        Jenkins(jenkins_url)
    except urllib2.URLError, e:
        print 'ERROR (%s)' % e
    else:
        print 'OK'

    config = {
    'jenkins' : {
        'url' : jenkins_url,
        }
    }

    f = file(get_global_config_file(), 'w')
    f.write(yaml.dump(config, default_flow_style=False))
    f.close()


#===================================================================================================
# get_configured_jobs
#===================================================================================================
def get_configured_jobs(branch, job_config):
    for job_config in job_config['jobs']:
        job_name = job_config['source-job']
        new_job_name = job_config['feature-branch-job'].replace('$name', branch)
        yield job_name, new_job_name


#===================================================================================================
# load_cit_local_config
#===================================================================================================
def load_cit_local_config(from_dir):
    git_dir = find_git_directory(from_dir)
    if git_dir is None:
        return None, {}
    
    cit_file_name = os.path.join(os.path.dirname(git_dir), '.cit.yaml')

    result = {}
    if os.path.isfile(cit_file_name):
        loaded_config = yaml.load(file(cit_file_name).read()) or {}
        result.update(loaded_config)

    return cit_file_name, result


#===================================================================================================
# find_git_directory
#===================================================================================================
def find_git_directory(from_dir):
    tries = 0
    max_tries = 20
    while True:
        git_dir = os.path.join(from_dir, '.git')
        if os.path.isdir(git_dir):
            break
        from_dir = os.path.dirname(from_dir)

        tries += 1
        if tries >= max_tries:
            return None
        
    return git_dir
    

#===================================================================================================
# general utilities
# -----------------
#
# General utilities that didn't fit in any other category.
#
#===================================================================================================

#===================================================================================================
# check_output
#===================================================================================================
def check_output(*args, **kwargs):
    '''
    Support subprocess.check_output for Python < 2.7
    '''
    try:
        return subprocess.check_output(*args, **kwargs)
    except AttributeError:
        kwargs['stdout'] = subprocess.PIPE
        popen = subprocess.Popen(*args, **kwargs)
        stdout, stderr = popen.communicate()
        if popen.returncode != 0:
            raise subprocess.CalledProcessError(popen.returncode, args[0])
        return stdout

#===================================================================================================
# main
#===================================================================================================
if __name__ == '__main__':
    sys.exit(app.main())
