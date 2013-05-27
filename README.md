# cit

Command line tool for interacting with a continuous integration server. 

## Installing

1. Create the folder where cit will be installed.
<pre><code>c:\cit
</code></pre>

2. Copy file `cit_install.py` to cit folder.
<pre><code>curl https://raw.github.com/nicoddemus/cit/master/cit_install.py > c:\cit\cit_install.py
</code></pre>

3. Run cit installation. As part of installation process you will be promped to provide Jenkins server address; just copy/paste the server directly from the browser and it should be OK.
```
  python c:\cit\cit_install.py
  --> pyyaml
  # snip lots of output

  ============================================================
  Configuring:
  ============================================================
  Jenkins URL (make sure to include http:// or https://): http://10.0.0.9:9090/
  Written configuration to: c:\cit\citconfig.yaml
  
  Checking if Jenkins server is correct... OK
```

## Commands

Following there is a quick overview about main commands.

### init

This command is responsible for configuring Jenkins jobs. The command will ask you the name of the source job, which is be taken a template for feature jobs. After that you have to inform the job name pattern.

Usage:

```
cd project_name
cit init # this will create a *.yaml file which can be add to the ignore list.
Configuring jobs for feature branches: \project_name\.cit.yaml

Source job (empty to exit):      project_name__1104-win32__21-project_name
Feature job (shh, use $name):    project_name-fb-$name-win32 # "$name" will be replaced by branch's name.
Done! Next?

Source job (empty to exit):

Done! Configured 1 job(s)!
```

### add

This command is responsible for adding the branchs that should be under cit's watch. Any push request to the server will trigger the related job to run (lagging a few minutes).
If you don't give a branch name the current branch will be used.

Usage:
```
cit add
project_name__1104-win32__21-project_name => project_name-fb-my_feature_branch-win32 (CREATED)
```

