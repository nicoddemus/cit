# cit

Command line tool for interacting with a continuous integration server. 

## Installing

1. Create the folder where cit will be installed.
<pre><code>c:\cit
</code></pre>

2. Copy file `cit_install.py` to cit folder.
<pre><code>curl https://raw.github.com/nicoddemus/cit/master/cit_install.py > c:\cit\cit_install.py
</code></pre>

3. Run cit installation. As part of installation process you will be promped to provide Jenkins server address.
  <pre><code>python c:\cit\cit_install.py
  --> pyyaml
  Cloning into 'pyyaml'...
  remote: Counting objects: 2072, done.
  remote: Compressing objects: 100% (689/689), done.
  remote: Total 2072 (delta 1032), reused 2067 (delta 1027)
  Receiving objects: 100% (2072/2072), 370.62 KiB | 208 KiB/s, done.
  Resolving deltas: 100% (1032/1032), done.
  --> JenkinsAPI
  Cloning into 'jenkinsapi'...
  remote: Counting objects: 1177, done.
  remote: Compressing objects: 100% (549/549), done.
  
  Receiving objects: 100% (1177/1177), 218.29 KiB | 241 KiB/s, done.
  Resolving deltas: 100% (689/689), done.
  --> cit
  Cloning into 'cit'...
  remote: Counting objects: 94, done.
  remote: Compressing objects: 100% (46/46), done.
  remote: Total 94 (delta 58), reused 83 (delta 48)
  Unpacking objects: 100% (94/94), done.
  Download done.
  ============================================================
  Configuring:
  ============================================================
  Jenkins URL (make sure to include http:// or https://): http://10.0.0.9:9090/
  Written configuration to: c:\cit\citconfig.yaml
  
  Checking if Jenkins server is correct... OK
  </code></pre>

## Commands

Following there is a quick overview about main commands.

### init

This command is responsible for configuring Jenkins jobs. The command will ask you the name of the source job, which is be taken a template for feature jobs. After that you have to inform the job name pattern.

Usage:
<pre><code>cd project_name
cit init # this will create a *.yaml file which can be add to the ignore list.
Configuring jobs for feature branches: \project_name\.cit.yaml

Source job (empty to exit):      project_name__1104-win32__21-project_name
Feature job (shh, use $name):    project_name-fb-$name-win32 # $name will be replaced by branch's name.
Done! Next?

Source job (empty to exit):

Done! Configured 1 job(s)!
</code></pre>

### add

This command is responsible for adding the branchs that should be under cit's watch. Any push request to the server will trigger the related job to run.

Usage:
<pre><code>cit add
project_name__1104-win32__21-project_name => project_name-fb-my_feature_branch-win32 (CREATED)
</code></pre>

