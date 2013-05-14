from jenkinsapi.jenkins import Jenkins
from jenkinsapi.exceptions import UnknownJob
import xml.etree.ElementTree as ET
 
 
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
        
 
