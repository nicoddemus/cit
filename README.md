# cit

Command line tool for interacting with a Jenkins server. 

The main workflow for this tool is to help work with feature branches, so that you can
easily setup jenkins jobs to run your tests in that feature branch:

```bash
$ cit fb.add   # executed from repository at branch <my_feature_branch> 
project_name_master => project_name_my_feature_branch (CREATED)
```

[![Build Status](https://secure.travis-ci.org/nicoddemus/cit.png?branch=master)](http://travis-ci.org/nicoddemus/cit)

## Requirements

* Python 2.5, 2.6 or 2.7;
* [simplejson](https://github.com/simplejson/simplejson);

It also depends on these libraries as [submodules](http://git-scm.com/book/ch6-6.html): 

* [pyyaml](http://github.com/yaml/pyyaml) 
* [jenkinsapi](http://github.com/salimfadhley/jenkinsapi)
* [clik](https://github.com/jds/clik.git)

But these are installed transparently and don't have to be installed system-wide.

## Installing

1. Clone the repository:

```bash
$ git clone https://github.com/nicoddemus/cit.git
```

2. Execute `python install.py` in the directory to fetch dependencies and execute initial configuration.

```bash
$ cd cit
$ python install.py
============================================================
Configuration
============================================================
- Enter Jenkins URL: http://localhost:8080   

Checking Jenkins server... OK
```

## Commands

Following there is a quick overview about main commands.

### fb.init

This command is responsible for configuring Jenkins jobs. The command will ask you the name of the source job, which will be taken as a template for feature jobs. After that you have to inform the job name pattern.

Tips:
* You can insert as many job templates as you want (e.g. one for each platform).
* The variable `$name` contains the name of the branch used on the template.


Usage:

```bash
$ cd project_name
$ cit fb.init
Configuring jobs for feature branches: \project_name\.cit.yaml

Source job (empty to exit):      project_name_master
Feature job (shh, use $name):    project_name_$name 
Done! Next?

Source job (empty to exit):

Done! Configured 1 job(s)!
```

This will create a `.cit.yaml` file at the project's root which should be commited to version control.

### fb.add

This command is responsible for adding the branches that should be under cit's watch.
If you don't give a branch name the current branch will be used.

Usage:

```bash
$ cit fb.add [my_feature_branch]
project_name_master => project_name_my_feature_branch (CREATED)
```

### fb.rm

This will remove jobs associated with a feature branch from Jenkins. 

Usage:

```bash
$ cit fb.rm [my_feature_branch]
project_name_master => project_name_my_feature_branch (REMOVED)
```

If you don't give a branch name the current branch will be used.

### fb.start

This command will start jobs related to the given branch.

Usage:

```bash
$ cit fb.start [my_feature_branch]
project_name_master => project_name_my_feature_branch (STARTED)
```


### sv.up

Uploads to Jenkins all jobs found in given directory. The given directory must contain a sub-directory for every job to be created or updated. 
Every job is configured by a XML configuration file named `config.xml` inside each job sub-directory.

If there is a job of same name in Jenkins it updates, otherwise it creates a new job.
If Jenkins already have a job with the same name but with a different $(job_index), the job will be renamed. To disable the search and rename just add the option --no-reindex to the command line.


Note:

The reindex feature compare all job names matching the given pattern: $(prefix)__$(job_index)-$(name).

The prefix will be used to list the existing jobs from Jenkins.

e.g. my_project__01-base

Usage:

```bash
$ cit sv.up [--reindex] <dir_name>
```

Example:

```
$ cit sv.up ./foo_jobs
Updating: 'foo-redhat64'
Updating: 'foo-win32'
Updating: 'foo-win64'
Update/Create jobs (y|n):
```

### sv.down

Download configuration files for all Jenkins jobs whose name matches given pattern. The pattern may be a regular expression if option `--re` is used 
otherwise it defaults to Unix filename pattern matching. 
Directory name may be omitted then downloaded job files will be put in the current directory.

Usage:

```bash
$ cit sv.down <search_pattern> [dir_name]
```

Example:

```bash
$ cit sv.down foo*
        foo-redhat64
        foo-win32
        foo-win64
Found: 3 jobs
Download jobs?(y|n):
```

### sv.ls

List names and current status of all jobs in Jenkins matching given pattern. The pattern may be a regular expression if option `--re` is used otherwise 
it defaults to Unix filename pattern matching. 

If you use the `--interactive` flag, you can start or remove jobs listed by passing
its index to the command.

Usage:

```bash
$ cit sv.ls [search_pattern]
```

Example:

```bash
$ cit sv.ls foo*
 0    FAILURE ( Wed Aug 07 14:36:22 2013) - foo-redhat64
 1    SUCCESS ( Wed Aug 07 14:36:22 2013) - foo-win32
 2    SUCCESS ( Wed Aug 07 14:36:22 2013) - foo-win64
Select an operation? (rm | start | e(xit)): 
```

### sv.rm

Deletes any job matching the given pattern. The pattern may be a regular expression if option `--re` is used otherwise it defaults to Unix filename pattern 
matching. Confirmation is prompted to user before jobs are actually deleted.

Usage:

```bash
$ cit sv.rm [search_pattern]
```

Example:

```bash
$ cit sv.del foo*
        foo-redhat64
        foo-win32
        foo-win64
Found: 3 jobs
Delete jobs?(y|n):
```


## Developing

Information about developing cit.

### Testing

[pytest](pytest.org) is used for testing, so executing the test suite is simple as:

```bash
$ py.test 
```
 
Some tests require a Jenkins server running at the local machine. To run these tests execute:

```bash
$ py.test --jenkins-available
```
