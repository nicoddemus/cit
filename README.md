# cit

Command line tool for interacting with a continuous integration server. 

## Installing

1. Create the folder where cit will be installed.

```
c:\cit
```


2. Copy file `cit_install.py` to cit folder.

```
curl -O https://raw.github.com/nicoddemus/cit/master/cit_install.py
```

or 

```
wget https://raw.github.com/nicoddemus/cit/master/cit_install.py
```

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
cit init
Configuring jobs for feature branches: \project_name\.cit.yaml

Source job (empty to exit):      project_name__1104-win32__21-project_name
Feature job (shh, use $name):    project_name-fb-$name-win32 # "$name" will be replaced by branch's name.
Done! Next?

Source job (empty to exit):

Done! Configured 1 job(s)!
```

This will create a `.cit.yaml` file at the project's root which should be commited to version control.

### add

This command is responsible for adding the branchs that should be under cit's watch. Any push request to the server will trigger the related job to run (lagging a few minutes).
If you don't give a branch name the current branch will be used.

Usage:

```
cit add my_feature_branch
project_name__1104-win32__21-project_name => project_name-fb-my_feature_branch-win32 (CREATED)
```

### rm

This command is responsible for removing the branchs under cit's watch. That means that jobs related to removed branch will be also removed from Jenkins.
If you don't give a branch name the current branch will be taken.

Usage:

```
cit rm my_feature_branch
project_name__1104-win32__21-project_name => project_name-fb-my_feature_branch-win32 (REMOVED)
```

### start

This command will force jobs related to the given branch to start running.

Usage:

```
cit start my_feature_branch
```
