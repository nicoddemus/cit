from jenkinsapi.jenkins import Jenkins
from jenkinsapi.exceptions import UnknownJob
import xml.etree.ElementTree as ET
import os
import sys
import yaml
 
 
#===================================================================================================
# create_feature_branch_job
#===================================================================================================
def create_feature_branch_job(jenkins_url, job_name, new_job_name, branch, owner):
    jenkins = Jenkins(jenkins_url)
    try:
        job = jenkins.get_job(new_job_name)
    except UnknownJob:
        print 'Copying job "%s" to "%s"...' % (job_name, new_job_name)
        job = jenkins.copy_job(job_name, new_job_name)
        
    print 'Updating configuration for job "%s"' % new_job_name
    tree = ET.fromstring(job.get_config())
    
    branch_elements = list(tree.findall('.//hudson.plugins.git.BranchSpec/name'))
    if len(branch_elements) > 0:
        old_branch = branch_elements[0].text
        branch_elements[0].text = branch
        print '  Branch changed to "%s" (was "%s")' % (branch, old_branch)
    else:
        print '  Could not find any branch spec to replace!'
    
    recipient_elements = list(tree.findall('.//hudson.tasks.Mailer/recipients'))
    if len(recipient_elements) == 1:
        recipient_element = recipient_elements[0]
        updated = False
        if recipient_element.text:
            if owner not in recipient_element.text:
                recipient_element.text = recipient_element.text + ' ' + owner
                updated = True 
        else:
            recipient_element.text = owner
            updated = True
            
        if updated:
            print '  Added "%s" to the list of mail recipients' % owner
        else:
            print '  "%s" Already in the list of mail recipients'  % owner
            
    job.update_config(ET.tostring(tree))
    
    return job
        


#===================================================================================================
# main
#===================================================================================================
def main(argv, global_config_file=None, stdin=None):
    # default values
    if global_config_file is None:
        global_config_file = os.path.join(os.path.dirname(__file__), 'citconfig.yaml')
        
    if stdin is None:
        stdin = sys.stdin
        
    # read global config
    if not os.path.isfile(global_config_file):
        sys.exit('could not find cit config file at: %s' % global_config_file)
        
    global_config = yaml.load(file(global_config_file).read()) 
    
    # command dispatch
    if len(argv) <= 1:
        print_help() 
        return 1
    elif argv[1] == 'config':
        cit_config(global_config, stdin)
        return 0

    return 0

#===================================================================================================
# print_help
#===================================================================================================
def print_help():
    print 'Commands:'    
    print     
    print '    config:            configures jobs for feature branches'
    print    


#===================================================================================================
# cit_config
#===================================================================================================
def cit_config(global_config, stdin):
    cit_file_name, config = load_cit_config(os.getcwd())
    
    print 'Configuring jobs for feature branches: %s' % cit_file_name
    print 
    
    updated = False
    while True:
        sys.stdout.write('Source job (empty to exit): ')
        source_job = stdin.readline().strip()
        if not source_job:
            break
        
        sys.stdout.write('Feature branch job, use $fb to replace by branch name: ')
        fb_job = stdin.readline().strip()
        if not fb_job:
            break
        
        fb_data = {
            'source-job' : source_job,
            'feature-branch-job' : fb_job, 
        }
        config.setdefault('jobs', []).append(fb_data)
        updated = True
        
    print 
    if updated:
        f = file(cit_file_name, 'w')
        f.write(yaml.dump(config, default_flow_style=False))
        f.close()
        print 'Configuration updated.'
    else:
        print 'Aborted.'
    
        
#===================================================================================================
# load_cit_config
#===================================================================================================
def load_cit_config(from_dir):
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
        config = yaml.load(file(cit_file_name).read()) or {}
    return cit_file_name, config

    
#===================================================================================================
# main
#===================================================================================================
if __name__ == '__main__':
    sys.exit(main(sys.argv)) 
