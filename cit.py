from __future__ import with_statement
import glob
import re
import time



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

#===================================================================================================
# cit commands
# ------------
#
# Functions below handle the actual "meat" of cit's commands.
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
        display_name_elem.text = '%s (%s)' % (display_name_elem.text, branch)

    recipient_elements = list(tree.findall('.//hudson.tasks.Mailer/recipients'))
    if len(recipient_elements) == 1:
        recipient_element = recipient_elements[0]
        recipient_element.text = user_email

    # remove properties from the build so we can use "start" to start-up jobs
    properties_elem = tree.find('./properties')
    if properties_elem is not None:
        for elem in properties_elem.findall('./hudson.model.ParametersDefinitionProperty'):
            properties_elem.remove(elem)

    # add a scm poll trigger for the build with 5 min intervals
    triggers_elem = tree.find('./triggers')
    scm_trigger = ET.SubElement(triggers_elem, 'hudson.triggers.SCMTrigger')
    ET.SubElement(scm_trigger, 'spec')
    ET.SubElement(scm_trigger, 'ignorePostCommitHooks').text = 'false'

    # remove build triggers after this job
    publishers_elem = tree.find('./publishers')
    if publishers_elem is not None:
        for elem in publishers_elem.findall('./hudson.tasks.BuildTrigger'):
            publishers_elem.remove(elem)

    job.update_config(ET.tostring(tree))

    return job



#===================================================================================================
# cit_add
#===================================================================================================
def cit_add(branch, global_config):
    cit_file_name, job_config = load_cit_local_config(os.getcwd())

    if branch is None:
        branch = get_git_branch(cit_file_name)

    jenkins_url = global_config['jenkins']['url']
    jenkins = Jenkins(jenkins_url)
    for job_name, new_job_name in get_configured_jobs(branch, job_config):
        user_name, user_email = get_git_user(cit_file_name)
        create_feature_branch_job(jenkins, job_name, new_job_name, branch, user_email)


def cit_get_job_status(job_name, job, job_index=None):
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
# cit_up_from_dir
#===================================================================================================
def cit_up_from_dir(directory, global_config):
    jenkins_url = global_config['jenkins']['url']
    jenkins = Jenkins(jenkins_url)

    directory = directory or 'hudson'
    if not os.path.exists(directory):
        print 'Directory not found: %r' % directory
        return

    jobs_to_update = {}
    for dir_name in glob.glob(directory + '/*'):
        # Ignore all files
        if not os.path.isdir(dir_name):
            continue

        job_name = os.path.basename(dir_name)
        xml_filename = os.path.join(dir_name, 'config.xml')
        has_config = os.path.exists(xml_filename)
        if not has_config:
            print 'Missing %r' % dir_name
            continue

        if jenkins.has_job(job_name):
            print 'Updating: %r' % job_name
            jobs_to_update[job_name] = False, xml_filename
        else:
            print 'Creating: %r' % job_name
            jobs_to_update[job_name] = True, xml_filename

    if len(jobs_to_update) > 0:
        ans = raw_input('Update/Create jobs (yes|no): ')
        if ans.startswith('y'):
            for job_name, (create_job, xml_filename) in jobs_to_update.iteritems():
                config_xml = file(xml_filename).read()
                if create_job:
                    job = jenkins.create_job(job_name, config_xml)
                else:
                    job = jenkins.get_job(job_name)
                    job.update_config(config_xml)


#===================================================================================================
# cit_down_to_dir
#===================================================================================================
def cit_down_to_dir(directory, pattern, global_config, use_re=False):
    
    jenkins, jobs_to_download = cit_list_jobs(pattern, global_config, use_re=use_re, print_status=False)
    
    print 'Found: %d jobs' % len(jobs_to_download)
    ans = raw_input("Download jobs?(y|n): ")
    
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
# cit_list_jobs
#===================================================================================================
def cit_list_jobs(pattern, global_config, use_re=False, invoke=False, print_status=True):
    import fnmatch

    jenkins_url = global_config['jenkins']['url']
    jenkins = Jenkins(jenkins_url)

    regex = re.compile(pattern)
    def Match(job_name):
        if use_re:
            return regex.match(job_name)
        else:
            return fnmatch.fnmatch(jobname, pattern)

    jobs = []
    for jobname in jenkins.iterkeys():
        if Match(jobname):
            job = jenkins.get_job(jobname)
            if print_status:
                print cit_get_job_status(jobname, job, len(jobs))
            else:
                print '\t', jobname
            jobs.append((jobname, job))

    def DeleteJobs(jobs):
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
        
    if invoke:
        ans = raw_input('Select an operation? (e(xit) | d(elete)| i(nvoke): ').lower()
        if not ans or ans.startswith('e'):
            return
        
        elif ans.startswith('d'):
            DeleteJobs(jobs)
        
        elif ans.startswith('i'):
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
                        print 'Invoking job: %r' % jobs[job_index][0]
                        job.invoke()

    return jenkins, jobs


#===================================================================================================
# cit_delete_jobs
#===================================================================================================
def cit_delete_jobs(pattern, global_config, use_re=False):
    jenkins, jobs_to_delete = cit_list_jobs(pattern, global_config, use_re, print_status=False)

    if len(jobs_to_delete) > 0:
        print 'Found: %d jobs' % len(jobs_to_delete)
        ans = raw_input("Delete jobs?(y|n): ")
        if ans.startswith('y'):
            for jobname, job in jobs_to_delete:
                print 'Deleting: %r' % jobname
                jenkins.delete_job(jobname)


#===================================================================================================
# cit_rm
#===================================================================================================
def cit_rm(branch, global_config):
    cit_file_name, job_config = load_cit_local_config(os.getcwd())

    if branch is None:
        branch = get_git_branch(cit_file_name)

    jenkins_url = global_config['jenkins']['url']
    jenkins = Jenkins(jenkins_url)
    for _, new_job_name in get_configured_jobs(branch, job_config):
        if jenkins.has_job(new_job_name):
            jenkins.delete_job(new_job_name)
            print new_job_name, '(REMOVED)'
        else:
            print new_job_name, '(NOT FOUND)'

#===================================================================================================
# cit_start
#===================================================================================================
def cit_start(branch, global_config):
    cit_file_name, job_config = load_cit_local_config(os.getcwd())

    if branch is None:
        branch = get_git_branch(cit_file_name)

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
# git helpers
# -----------
#
# Git-related helper functions to extract user name, current branch, etc.
#
#===================================================================================================


#===================================================================================================
# get_git_user
#===================================================================================================
def get_git_user(cit_file_name):
    with chdir(cit_file_name):
        user_name = check_output('git config --get user.name', shell=True).strip()
        user_email = check_output('git config --get user.email', shell=True).strip()
        return user_name, user_email


#===================================================================================================
# get_git_branch
#===================================================================================================
def get_git_branch(cit_file_name):
    with chdir(cit_file_name):
        return check_output('git rev-parse --abbrev-ref HEAD', shell=True).strip()


#===================================================================================================
# cit configuration
# -----------------
#
# Functions and commands that deal with cit's configuration.
#
#===================================================================================================

#===================================================================================================
# cit_init
#===================================================================================================
def cit_init(global_config, stdin):
    cit_file_name, config = load_cit_local_config(os.getcwd())

    print 'Configuring jobs for feature branches: %s' % cit_file_name
    print

    updated = 0
    while True:
        sys.stdout.write('Source job (empty to exit):      ')
        source_job = stdin.readline().strip()
        if not source_job:
            break

        sys.stdout.write('Feature job (shh, use $name):    ')
        fb_job = stdin.readline().strip()
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
# cit_install
#===================================================================================================
def cit_install(global_config_file, stdin):
    print '=' * 60
    print 'Configuration'
    print '=' * 60
    sys.stdout.write('- Enter Jenkins URL:   ')
    jenkins_url = stdin.readline().strip()
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

    f = file(global_config_file, 'w')
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
    tries = 0
    max_tries = 20
    while True:
        gitdir = os.path.join(from_dir, '.git')
        if os.path.isdir(gitdir):
            break
        from_dir = os.path.dirname(from_dir)

        tries += 1
        if tries >= max_tries:
            raise RuntimeError('could not find .git directory')

    cit_file_name = os.path.join(from_dir, '.cit.yaml')

    config = {}
    if os.path.isfile(cit_file_name):
        loaded_config = yaml.load(file(cit_file_name).read()) or {}
        config.update(loaded_config)

    return cit_file_name, config


def parse_args():
    from optparse import OptionParser

    usage = "usage: %prog <filename> [options]"
    parser = OptionParser(usage=usage, version='0.2')
    parser.add_option(
        "-p", "--pattern", dest="pattern",
        help="Job name match pattern"
    )
    parser.add_option(
        "-d", "--directory", dest="directory",
        help="Local directory to search for jobs"
    )
    parser.add_option(
        "--re", action="store_true", dest="use_re", default=False,
        help="Use Regular Expressions"
    )

    return parser.parse_args()


#===================================================================================================
# main
#===================================================================================================
def main(argv, global_config_file=None, stdin=None):
    # default values
    if global_config_file is None:
        global_config_file = os.path.join(os.path.dirname(__file__), 'citconfig.yaml')

    if stdin is None:
        stdin = sys.stdin

    # --install option: used to initialize configuration
    if '--install' in argv:
        cit_install(global_config_file, stdin)
        return RETURN_CODE_OK

    # read global config
    if not os.path.isfile(global_config_file):
        print >> sys.stderr, 'could not find cit config file at: %s' % global_config_file
        return RETURN_CODE_CONFIG_NOT_FOUND

    global_config = yaml.load(file(global_config_file).read())

    # command dispatch
    if len(argv) <= 1:
        print_help()
        return RETURN_CODE_OK
    elif argv[1] == 'init':
        cit_init(global_config, stdin)
        return RETURN_CODE_OK
    elif argv[1] in ('add', 'start', 'rm'):
        if len(argv) > 2:
            branch = argv[2]
        else:
            branch = None
        if argv[1] == 'add':
            cit_add(branch, global_config)
        elif argv[1] == 'start':
            cit_start(branch, global_config)
        elif argv[1] == 'rm':
            cit_rm(branch, global_config)
        return RETURN_CODE_OK
    else:
        (options, args) = parse_args()
        cmd = args[0]
        if cmd == 'upd':
            directory = options.directory
            cit_up_from_dir(directory, global_config)
            return RETURN_CODE_OK

        elif cmd == 'dtd':
            directory = options.directory
            pattern = options.pattern
            if pattern is None:
                if len(args) > 1:
                    pattern = args[1]
                else:
                    print 'Provide a job name pattern, e.g. "jobs.*_\d+"'
                    return RETURN_CODE_OK

            cit_down_to_dir(directory, pattern, global_config, use_re=options.use_re)
            return RETURN_CODE_OK

        elif cmd == 'ls':
            pattern = options.pattern
            if pattern is None:
                if len(args) > 1:
                    pattern = args[1]
                else:
                    print 'Provide a job name pattern, e.g. "jobs.*_\d+"'
                    return RETURN_CODE_OK

            cit_list_jobs(pattern, global_config, invoke=True, use_re=options.use_re)

            return RETURN_CODE_OK

        elif cmd == 'del':
            pattern = options.pattern
            if len(args) > 1:
                pattern = args[1]
            else:
                print 'Provide a job name pattern, e.g. "jobs.*_\d+"'
                return RETURN_CODE_OK

            cit_delete_jobs(pattern, global_config, use_re=options.use_re)

            return RETURN_CODE_OK

        print 'Unknown command: "%s"' % argv[1]
        print_help()
        return RETURN_CODE_UNKNOWN_COMMAND

    return RETURN_CODE_OK


# Error Codes --------------------------------------------------------------------------------------

RETURN_CODE_OK = 0
RETURN_CODE_UNKNOWN_COMMAND = 2
RETURN_CODE_CONFIG_NOT_FOUND = 3


#===================================================================================================
# print_help
#===================================================================================================
def print_help():
    print 'Commands:'
    print
    print '    init                   configures jobs for feature branches for this git repo'
    print '    add [BRANCH]           add a new feature branch job to Jenkins'
    print '    start [BRANCH]         starts a new build for the given feature branch'
    print '    rm [BRANCH]            removes job for feature branches given'
    print
    print 'Specials:'
    print
    print '    upd -d $(dir_name)       Update or create jobs from the sub directories in $(dir_name)'
    print '    dtd $(search_pattern) -d $(dir_name)       Download jobs to sub directories in $(dir_name)'
    print '    del $(search_pattern)    Delete jobs from the server that matches the given pattern'
    print '        --re                     match jobs using a regular expression'
    print '    ls $(search_pattern)     List jobs from the server that matches the given pattern'


#===================================================================================================
# general utilities
# -----------------
#
# General utilities that didn't fit in any other category.
#
#===================================================================================================

#===================================================================================================
# chdir
#===================================================================================================
@contextlib.contextmanager
def chdir(cwd):
    old_cwd = os.getcwd()
    if os.path.isfile(cwd):
        cwd = os.path.dirname(cwd)
    os.chdir(cwd)
    yield
    os.chdir(old_cwd)


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
            raise subprocess.CalledProcessError
        return stdout

#===================================================================================================
# main
#===================================================================================================
if __name__ == '__main__':
    sys.exit(main(sys.argv))
