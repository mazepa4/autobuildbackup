**Configuration file description:**

_Basic file format:_

{  

    path configuraions  
    repositories  
}

**Path configuraions:**
    
logDir: Path to logs
reposDir: Path where repositories pull&builds
distPath: Path to  build results

**Repositories configurations:**

 repos:  
 {   
 
    name: Repository name
    sourceControl: Git or Subversion
    sourceControlLogin: Login to VCS
    sourceControlPassword: Passowrd to VCS
    sourceUrl: Repository URL
    tmpDir: Folder for temporary files
    actions: Actions(See description below)
 }


**Actions configuration:**


**Post processing**: Action which should be performed before  next action or after some action. For example: stop service & start sevice

**Usage**: actionKind : post-process

`actionKind`: _Type of action(Possible values: build,bundle,upload,post-process,install-service)_

`procDir`: _Folder build process should started_

`postProcDir`: _Folder where builded program should started_

`description`: _Dscription of action_

`postprocessScripts`: _Bash scripts to run_



**Bundle action**: This is action which can copy files&folders and can generate files up to target templates.

**Usage**: actionKind: bundle

`bundleDir`: Target folder on copy files&folders

`items`: List of subtasks. See description below

`deployPath`: SubPath to deploy

`item`: Deploy item
 
**Additionaly this task support "Templates"**:

**Usage**: template: {}

**Avaliable options**:

`sourceFile`: _Relative path to template file_


Perform preprocess before taking on template
Usage:
preprocess:{
    actionKind: {gen-ports} | Action type
    range: Port range
    map: Map of generated properties 
}

Apache Actions:
Usage: 
apacheActions:{
    template: Path to source file
    action: What to do with generated file
    items: List of action. See details below 
}

