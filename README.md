# cit

Command line tool for interacting with a continuous integration server. 

[![Build Status](https://secure.travis-ci.org/nicoddemus/cit.png?branch=master)](http://travis-ci.org/nicoddemus/cit) 

## Requirements

* Python 2.5, 2.6 or 2.7;
* [simplejson](https://github.com/simplejson/simplejson);

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
cit start [my_feature_branch]
```

### upd

Uploads to Jenkins all jobs found in given directory. The given directory must contain a sub-directory for every job to be created or updated. 
If there is a job of same name in Jenkins it updates, otherwise it creates a new job.
If Jenkins already have a job with the same name but with a different job index, the job will be renamed. To disable the search and rename just add the option --no-reindex to the command line.
Every job is configured by the use a XML configuration file named `config.xml` that must be inside job's sub-directory.

Note:

The reindex feature compare all job names matching the given pattern: $(prefix)__00-$(name)
The prefix will be used to list the existing jobs from Jenkins. 

Usage:

```
cit upd -d [dir_name]
```

Example:

```
$ cit upd -d foo_jobs\
Updating: 'foo-redhat64'
Updating: 'foo-win32'
Updating: 'foo-win64'
Update/Create jobs (yes|no):
```

### dtd

Download configuration files for all Jenkins jobs whose name matches given pattern. The pattern may be a regular expression if option `--re` is used 
otherwise it defaults to Unix filename pattern matching. Directory name may be omitted then downloaded job files will be put in a directory named 'hudson'.

Usage:

```
cit dtd [search_pattern] -d [dir_name]
```

Example:

```
$ cit dtd foo*
        foo-redhat64
        foo-win32
        foo-win64
Found: 3 jobs
Download jobs?(y|n):
```

### ls

List names and current status of all jobs in Jenkins matching given pattern. The pattern may be a regular expression if option `--re` is used otherwise 
it defaults to Unix filename pattern matching. Also for every listed file a index is shown. After jobs are listed a question about next operation is asked 
to user and this index may be used to queue a job on Jenkins or even delete a job.

Usage:

```
cit ls [search_pattern]
```

Example:

```
$ cit ls foo*
 0    FAILURE ( Wed Aug 07 14:36:22 2013) - foo-redhat64
 1    SUCCESS ( Wed Aug 07 14:36:22 2013) - foo-win32
 2    SUCCESS ( Wed Aug 07 14:36:22 2013) - foo-win64
Select an operation? (e(xit) | d(elete)| i(nvoke):
```

### del

Deletes any job matching the given pattern. The pattern may be a regular expression if option `--re` is used otherwise it defaults to Unix filename pattern 
matching. Confirmation is prompted to user before jobs are actually deleted.

Usage:

```
cit del [search_pattern]
```

Example:

```
$ cit del foo*
        foo-redhat64
        foo-win32
        foo-win64
Found: 3 jobs
Delete jobs?(y|n):
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
