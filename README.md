# cit

Command line tool for interacting with a continuous integration server. 

## Installing

1. Clone the repository:

    ```
    git clone https://github.com/nicoddemus/cit.git
    ```

2. Execute `python install.py` in the directory to fetch dependencies and execute initial configuration.

    ```
    cd cit
    python install.py
    ```

    As part of installation process you will be promped to provide Jenkins server address: 
    
    ```
    ============================================================
    Configuration
    ============================================================
    - Enter Jenkins URL:   
    ```
    
    just copy/paste the server directly from the browser and it should be OK.
    
    ```
    - Jenkins URL:   http://localhost:8080
    
    Checking Jenkins server... OK
    ```

## Commands

Following there is a quick overview about main commands.

### init

This command is responsible for configuring Jenkins jobs. The command will ask you the name of the source job, which will be taken as a template for feature jobs. After that you have to inform the job name pattern.

Tips:
* You can insert as many job templates as you want (e.g. one for each platform).
* The variable `$name` contains the name of the branch used on the template.


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

This command is responsible for adding the branches that should be under cit's watch. Any push request to the server will trigger the related job to run (lagging a few minutes).
If you don't give a branch name the current branch will be used.

Usage:

```
cit add [my_feature_branch]
project_name__1104-win32__21-project_name => project_name-fb-my_feature_branch-win32 (CREATED)
```

### rm

This command is responsible for removing the branches from cit's watch. That means that jobs related to the removed branch will be also removed from Jenkins.
If you don't give a branch name the current branch will be taken.

Usage:

```
cit rm [my_feature_branch]
project_name__1104-win32__21-project_name => project_name-fb-my_feature_branch-win32 (REMOVED)
```

### start

This command will force jobs related to the given branch to start running.

Usage:

```
cit start my_feature_branch
```

## Developing

Information about developing cit.

### Testing

pytest (pytest.org) is used for testing, so executing the test suite is simple as:

```
py.test 
```
 
Some tests require a Jenkins server running at the local machine. To run these tests execute:

```
py.test --jenkins-available
```
