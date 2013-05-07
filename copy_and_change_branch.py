from jenkinsapi.jenkins import Jenkins
from jenkinsapi.exceptions import UnknownJob
from xml.etree.ElementTree import ElementTree
import StringIO
 
jenkins = Jenkins('http://localhost:8080')
target_job = 'ss_copy' 
try:
    job = jenkins.get_job(target_job)
except UnknownJob:
    print 'Copying job for feature branch'
    job = jenkins.copy_job('ss', target_job)
    
    config = job.get_config()
    ss = StringIO.StringIO(config)
     
    tree = ElementTree()
    tree.parse(ss)
    branches = list(tree.iter('hudson.plugins.git.BranchSpec'))[0]
    branches.find('name').text = 'feature-branch'
    
    ss = StringIO.StringIO()
    tree.write(ss)
    
    job.update_config(ss.getvalue())

print 'Invoking Job'
job.invoke(skip_if_running=True)

