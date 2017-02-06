from Autobuilder.Actions.BuildAction import *
from Autobuilder.Actions.PostProcessAction import *
from Autobuilder.Actions.BundleAction import *
import re
import io

class Repository(SharedState):

    m_sourceControlLogin = ""
    m_sourceControlPassword = ""
    m_sourceUrl = ""
    m_actionList = []
    m_lastAttemptFailed = False
    m_hasUpdates = False
    m_sourceControl = ""
    m_name = ""
    m_reposDir = ""
    m_dependencies = []
    m_buildStatus = ""
    m_distPath  = ""
    m_tmpDir = None

    taskStatusChanged = None

    def __init__(self,logDir,reposDir, distPath):
        self.m_reposDir = reposDir
        self.m_logFolder = logDir
        self.m_distPath = distPath
        self.m_actionList = []
        self.m_dependencies  = [];




    def LoadConfiguration(self,configuration=None):
        if configuration == None:
            return False

        def reportException(exc):
            print("!Exception: " + str(exc))

        def reportInvalidProperty(exc):
            print("!Unknown property: "+exc)

        def addAction(action):
            print("Missing implemetation")

        # Assume all properties are valid bool
        successFlag = True

        try:
            self.m_cacheFolder = self.m_reposDir + configuration['cacheFolder']
            self.m_sourceControl = configuration['sourceControl']
            self.m_sourceControlLogin = configuration['sourceControlLogin']
            self.m_sourceControlPassword = configuration['sourceControlPassword']
            self.m_sourceUrl = configuration['sourceUrl']
            if "dependencies" in configuration:
                for dependency in configuration['dependencies']:
                    self.m_dependencies.append({"name":dependency,"status":None})
            self.m_name = configuration['name']

            if "tmpDir" in  configuration:
                self.m_tmpDir = self.m_reposDir + configuration['tmpDir']
                FileWorker().createPath(self.m_tmpDir)
                FileWorker().clearFolder(self.m_tmpDir)

            print("Initializing repository: '{0}{1}' ...".format(self.m_reposDir, self.m_name))

            if self.m_sourceControl == SourceControl.Unknown :
                successFlag = False
                reportInvalidProperty("sourceControl")

            for action in configuration['actions']:

                newAction = None

                if action['actionKind'] == ActionKind.Build:
                    newAction = BuildAction(self)
                elif action['actionKind'] == ActionKind.Bundle:
                    newAction = BundleAction(self)
                elif action['actionKind'] == ActionKind.InstallService:
                    addAction(newAction)
                elif action['actionKind'] == ActionKind.PostProcess:
                    newAction = PostProcessAction(self)

                if newAction != None :
                    if newAction.LoadConfiguration(action, reportException, reportInvalidProperty):
                        self.m_actionList.append(newAction)
                    else:
                        successFlag = False
                else:
                    successFlag = False
                    reportInvalidProperty(action['actionKind'])

                self.m_buildStatus = BuildStatus.Unknown
        except Exception as e:
            successFlag = False
            reportException(e)

        return successFlag

    def UpdateAndBuild(self):

        self.m_buildStatus = BuildStatus.Processing
        self.taskStatusChanged(self.m_name, self.m_buildStatus)

        #Setup logging
        if self.OpenLogStream() == True:
            self.m_buildStatus = BuildStatus.Failed
            self.taskStatusChanged(self.m_name, self.m_buildStatus)
            return False

        #Update or reload
        if self.Update() == False:
            self.m_buildStatus = BuildStatus.Failed
            self.taskStatusChanged(self.m_name, self.m_buildStatus)
            return False

        #Nothing to build
        if self.RequiresInstallation() == False:
            if self.m_lastAttemptFailed == False:
                self.m_buildStatus = BuildStatus.Completed
                self.taskStatusChanged(self.m_name, self.m_buildStatus)
            return True

        #Run all non-install actions
        for action in self.m_actionList:
                action.m_logStream = self.m_logStream
                action.m_cacheFolder = self.m_cacheFolder
                if action.Run() == False:
                    self.m_buildStatus = BuildStatus.Failed
                    self.taskStatusChanged(self.m_name, self.m_buildStatus)
                    return False

        self.m_buildStatus = BuildStatus.Completed
        self.taskStatusChanged(self.m_name, self.m_buildStatus)
        return True

    def Install(self):
        for action in self.m_actionList:
            if action.IsInstallAction():
                if action.Run() == False:
                    return False
        return True

    def RequiresInstallation(self):
        print("Has updates: {}; LastAttemptFailed:{}".format(self.m_hasUpdates, self.m_lastAttemptFailed))

        return self.m_hasUpdates or self.m_lastAttemptFailed

    def OpenLogStream(self):
        logPath = ""
        logPath += self.m_logFolder
        #logPath += "/" + self.m_name + ".log"

        #Try extract last build status before the log will be overwritten
        self.m_lastAttemptFailed = False

        self.ExtractLastAttemptStatus(logPath + "/" + self.m_name + ".log")

        #Ensure log folder exists
        try:
            FileWorker().createPath(logPath)
        except Exception as e:
            return False

        if self.m_logStream == None or self.m_logStream.isatty() == False:
            self.m_logStream = io.open(logPath + "/" + self.m_name + ".log", "a")

        return self.m_logStream.closed

    def ExtractLastAttemptStatus(self,logFilePath):
        logFile = FileWorker().readFile(logFilePath)

        if logFile == False:
            self.m_lastAttemptFailed = True
            return

        textLines = logFile.split("\n")
        for line in textLines:
            if line.lower().startswith("error"):
                self.m_lastAttemptFailed = True
                self.m_logStream = io.open(logFilePath, "r+")
                self.m_logStream.truncate()
                break

    def Update(self):
        #Run specific source control to update a local copy of the repository
        log = "\n"+ Tags.StageTag + "Updating...";
        #self.m_logStream.write("\n"+ Tags.StageTag + "Updating...")
        self.m_clock.UpdateTime()

        if self.m_sourceControl == SourceControl.Subversion:
            if FileWorker().isExist(self.m_cacheFolder + "/.svn"):
                currentRevision = 0
                updatedRevision = 0

                status,currentRevision,log = self.SubversionGetRevision(log);
                if status == False:
                    log = log+"\n"+ Tags.WarningTag + "Local copy is corrupted, trying to download a new one."
                    #self.m_logStream.write("\n"+ Tags.WarningTag + "Local copy is corrupted, trying to download a new one.")

                status,updatedRevision,log = self.SubversionUpdate(log);
                if status == False:
                    log = log + "\n"+ Tags.WarningTag + "Failed to update local copy, trying to download a new one."
                    #self.m_logStream.write("\n"+ Tags.WarningTag + "Failed to update local copy, trying to download a new one.")

                self.m_hasUpdates = (currentRevision < updatedRevision)
                log = log + "\n"+ Tags. SuccessTag+ "Updating completed (" + str(self.m_clock.DeltaMilliseconds()) + " ms)."
                #self.m_logStream.write("\n"+ Tags. SuccessTag+ "Updating completed (" + str(self.m_clock.DeltaMilliseconds()) + " ms).")

                if self.m_hasUpdates:
                    # Truncate log file and open for writing
                    try:
                        self.m_logStream = io.open(self.m_logFolder + "/" + self.m_name + ".log", "r+")
                        self.m_logStream.truncate()
                        self.m_logStream.write(log)
                        self.m_logStream.flush()
                    except Exception as e:
                        print("Exception on line {0}: {1}".format(Common().lineno(),str(e)))
                return True
            else:
                try:
                    self.m_logStream = io.open(self.m_logFolder + "/" + self.m_name + ".log", "r+")
                    self.m_logStream.truncate()
                    self.m_logStream.write(log)
                    self.m_logStream.flush()
                    self.m_logStream.write("\n" + Tags.WarningTag + "Local copy not found, trying to download a new one.")
                except Exception as e:
                    print("Exception on line {0}: {1}".format(Common().lineno(), str(e)))
        elif self.m_sourceControl == SourceControl.Git:
            if FileWorker().isExist(self.m_cacheFolder + "/.git"):

                status, revisionValue, log = self.GitGetRevision(log);
                if status == False:
                    log = log+"\n"+ Tags.WarningTag + "Local copy is corrupted, trying to download a new one."
                    #self.m_logStream.write("\n"+ Tags.WarningTag + "Local copy is corrupted, trying to download a new one.")

                status, hasUpdates, log = self.GitUpdate(log)
                if status == False:
                    log = log+"\n"+ Tags.WarningTag + "Local copy is corrupted, trying to download a new one."
                    #self.m_logStream.write("\n"+ Tags.WarningTag + "Local copy is corrupted, trying to download a new one.")

                self.m_hasUpdates = hasUpdates
                log = log + "\n"+ Tags. SuccessTag+ "Updating completed (" + str(self.m_clock.DeltaMilliseconds()) + " ms)."
                #self.m_logStream.write("\n"+ Tags. SuccessTag+ "Updating completed (" + str(self.m_clock.DeltaMilliseconds()) + " ms).")

                if self.m_hasUpdates:
                    # Truncate log file and open for writing
                    try:
                        self.m_logStream = io.open(self.m_logFolder + "/" + self.m_name + ".log", "r+")
                        self.m_logStream.truncate()
                        self.m_logStream.write(log)
                        self.m_logStream.flush()
                    except Exception as e:
                        print("Exception on line {0}: {1}".format(Common().lineno(),str(e)))
                return True
            else:
                try:
                    self.m_logStream = io.open(self.m_logFolder + "/" + self.m_name + ".log", "r+")
                    self.m_logStream.truncate()
                    self.m_logStream.write(log)
                    self.m_logStream.flush()
                    self.m_logStream.write("\n" + Tags.WarningTag + "Local copy not found, trying to download a new one.")
                except Exception as e:
                    print("Exception on line {0}: {1}".format(Common().lineno(), str(e)))

        #Run specific source control to load a local copy of the repository
        self.m_logStream.write("\n"+ Tags.StageTag + "Loading...")
        self.m_clock.UpdateTime()

        if self.m_sourceControl == SourceControl.Subversion:
            try:
                FileWorker().clearFolder(self.m_cacheFolder)
            except Exception as e:
                self.m_logStream.write("\n"+ Tags.ErrorTag + "Unable to clear the repository because of: " + str(e))
                return False

            if self.SubversionLoad() == False:
                self.m_logStream.write("\n"+ Tags.ErrorTag + "Failed to load the repository using subversion.")
                return False

            self.m_hasUpdates = True
            self.m_logStream.write("\n"+ Tags. SuccessTag+ "Loading completed (" + str(self.m_clock.DeltaMilliseconds()) + "ms).")
        elif self.m_sourceControl == SourceControl.Git:
            try:
                FileWorker().clearFolder(self.m_cacheFolder)
            except Exception as e:
                self.m_logStream.write("\n"+ Tags.ErrorTag + "Unable to clear the repository because of: " + str(e))
                return False

            if self.GitLoad() == False:
                self.m_logStream.write("\n"+ Tags.ErrorTag + "Failed to load the repository using git.")
                return False

            self.m_hasUpdates = True
            self.m_logStream.write("\n"+ Tags. SuccessTag+ "Loading completed (" + str(self.m_clock.DeltaMilliseconds()) + "ms).")

        return True

    def SubversionGetRevision(self,log):
        #Build the command line
        commandLine = ""

        commandLine += "svn info "
        commandLine += self.m_cacheFolder
        commandLine += ' '
        commandLine += " 2>&1"

        commandLine.replace("\'", "\\\'")
        commandLine.replace("\"", "\\\"")
        try:
            commandOutput,exitCode = CommandProcessor().Run(commandLine)
        except Exception as e:
            print("Exception:  Repository.py Line 214: " + str(e))
            log = log + "\n"+ Tags.ErrorTag + "Failed to run command: " + commandLine
            #self.m_logStream.write("\n"+ Tags.ErrorTag + "Failed to run command: " + commandLine )
            return False

        #Read subversion output
        successFlag = False
        revisionValue = 0

        for line in commandOutput:
            decoded_line = bytes(line).decode("utf-8").lower()
            if decoded_line.startswith("sh") or decoded_line.startswith("svn"):
                self.m_logStream.write("\n"+ Tags.ErrorTag+decoded_line)
            if decoded_line.lower().startswith("revision"):
                revisionStr = line
                decoded_line = decoded_line.strip("\r\n\t :.")

                revisionValue = int(re.findall('\d+', decoded_line)[0])

                #revisionValue = np.fromstring(decoded_line,dtype =np.int32)#Common().atoi(decoded_line)

                successFlag =True

        self.m_logStream.flush()
        return successFlag,revisionValue,log

    def SubversionUpdate(self,log):
        #Build the command line
        commandLine = ""

        commandLine += "svn update --force --no-auth-cache --non-interactive --trust-server-cert --accept theirs-full --username "
        commandLine += self.m_sourceControlLogin
        commandLine += " --password "
        commandLine += self.m_sourceControlPassword
        commandLine += " "
        commandLine += self.m_cacheFolder
        commandLine += ' '
        commandLine += " 2>&1"

        commandLine.replace("\'", "\\\'")
        commandLine.replace("\"", "\\\"")

        try:
            commandOutput,errorCode = CommandProcessor().Run(commandLine)
        except Exception as e:
            print("Exception:  Repository.py Line 257: " + str(e))
            log = log + "\n"+ Tags.ErrorTag + "Failed to run command: " + commandLine
            #self.m_logStream.write("\n"+ Tags.ErrorTag + "Failed to run command: " + commandLine )
            return False

        #Read subversion output
        successFlag = False
        revisionValue = 0

        for line in commandOutput:
            decoded_line = bytes(line).decode("utf-8").lower()
            if decoded_line.startswith("sh") or decoded_line.startswith("svn"):
                log = log + "\n"+ Tags.ErrorTag+decoded_line
            elif decoded_line.startswith("updating") or decoded_line.startswith("fetching") or decoded_line.startswith("external"):
                log = log + "\n"+ Tags.DetailTag+decoded_line
            if decoded_line.startswith("updated to revision") or decoded_line.startswith("at revision"):
                revisionStr = decoded_line
                decoded_line = decoded_line.strip("\r\n\t :.")

                revisionValue = int(re.findall('\d+', decoded_line)[0])

                successFlag =True

                log = log + "\n"+ Tags.DetailTag+decoded_line
                #self.m_logStream.write("\n"+ Tags.DetailTag+decoded_line)

        self.m_logStream.flush()
        return successFlag,revisionValue,log

    def SubversionLoad(self):
        #Build the command line
        commandLine = ""

        commandLine += "svn checkout --force --no-auth-cache --non-interactive --trust-server-cert --username "
        commandLine += self.m_sourceControlLogin
        commandLine += " --password "
        commandLine += self.m_sourceControlPassword
        commandLine += " "
        commandLine += self.m_sourceUrl
        commandLine += " "
        commandLine += self.m_cacheFolder
        commandLine += ' '
        commandLine += " 2>&1"

        commandLine.replace("\'", "\\\'")
        commandLine.replace("\"", "\\\"")

        try:
            commandOutput,erorCode = CommandProcessor().Run(commandLine)
        except Exception as e:
            print("Exception:  Repository.py Line 297: " + str(e))
            self.m_logStream.write("\n"+ Tags.ErrorTag + "Failed to run command: " + commandLine)
            return False

        #Read subversion output
        successFlag = False

        for line in commandOutput:
            decoded_line = bytes(line).decode("utf-8").lower()
            if decoded_line.startswith("sh") or decoded_line.startswith("svn"):
                self.m_logStream.write("\n"+ Tags.ErrorTag+decoded_line)
            elif decoded_line.lower().startswith("fetching"):
                self.m_logStream.write("\n"+ Tags.DetailTag+decoded_line)
            elif decoded_line.lower().startswith("checked out"):
                self.m_logStream.write("\n"+ Tags.DetailTag+decoded_line)
                if decoded_line.lower().find("external"):
                    successFlag = True

        self.m_logStream.flush()
        return successFlag

    def GitGetRevision(self,log):
        # Build the command line
        commandLine = ""

        commandLine += "git log "
        commandLine += ' '
        commandLine += " 2>&1"

        commandLine.replace("\'", "\\\'")
        commandLine.replace("\"", "\\\"")
        try:
            commandOutput, exitCode = CommandProcessor().Run(commandLine,self.m_cacheFolder)
        except Exception as e:
            print("Exception:  Repository.py Line 214: " + str(e))
            log = log + "\n" + Tags.ErrorTag + "Failed to run command: " + commandLine
            # self.m_logStream.write("\n"+ Tags.ErrorTag + "Failed to run command: " + commandLine )
            return False

        # Read subversion output
        successFlag = False
        revisionValue = ""

        for line in commandOutput:
            decoded_line = bytes(line).decode("utf-8").lower()
            if decoded_line.startswith("sh") or decoded_line.startswith("svn"):
                self.m_logStream.write("\n" + Tags.ErrorTag + decoded_line)
            elif decoded_line.lower().startswith("commit"):
                decoded_line = decoded_line.strip("\r\n\t :.")
                revisionValue = decoded_line[6:].strip("\r\n\t :.")
                successFlag = True
                break

        self.m_logStream.flush()
        return successFlag, revisionValue, log


    def GitFetch(self,log):
        # Build the command line
        commandLine = ""

        commandLine += "git fetch origin"
        commandLine += ' '
        commandLine += "2>&1"
        commandLine.replace("\'", "\\\'")
        commandLine.replace("\"", "\\\"")

        try:
            commandOutput, errorCode = CommandProcessor().Run(commandLine,self.m_cacheFolder)
        except Exception as e:
            print("Exception:  Repository.py Line 257: " + str(e))
            log = log + "\n" + Tags.ErrorTag + "Failed to run command: " + commandLine
            return False

        # Read subversion output
        successFlag = True

        log = log + "\n" + Tags.DetailTag + "Fetching repository..."

        for line in commandOutput:
            decoded_line = bytes(line).decode("utf-8").lower()
            if decoded_line.startswith("remote:"):
                log = log + "\n" + Tags.DetailTag + decoded_line
            elif decoded_line.startswith("fatal:"):
                log = log + "\n" + Tags.ErrorTag + decoded_line
                successFlag = False

        return successFlag,log

    def GitPull(self,log):
        # Build the command line
        commandLine = ""
        commandLine += "git pull"
        commandLine += ' '
        commandLine += "2>&1"
        commandLine.replace("\'", "\\\'")
        commandLine.replace("\"", "\\\"")

        try:
            commandOutput, errorCode = CommandProcessor().Run(commandLine,self.m_cacheFolder)
        except Exception as e:
            print("Exception:  Repository.py Line 257: " + str(e))
            log = log + "\n" + Tags.ErrorTag + "Failed to run command: " + commandLine
            return False

        # Read subversion output
        successFlag = True
        updatesAvailable = False

        for line in commandOutput:
            decoded_line = bytes(line).decode("utf-8").lower()
            if decoded_line.startswith("already up-to-date."):
                log = log + "\n" + Tags.DetailTag + decoded_line
                updatesAvailable = False
            elif decoded_line.startswith("updating"):
                log = log + "\n" + Tags.DetailTag + decoded_line
                updatesAvailable = True
            elif decoded_line.find("file changed") >= 0 or decoded_line.find("insertion") >= 0 or decoded_line.find("deletion") >= 0:
                log = log + "\n" + Tags.DetailTag + decoded_line
                updatesAvailable = True
            elif decoded_line.find("error") >= 0 or decoded_line.find("fatal") >= 0:
                log = log + "\n" + Tags.ErrorTag + decoded_line
                updatesAvailable = False
                successFlag = False

        return successFlag,updatesAvailable,log


    def GitUpdate(self,log):

        updatesAvailable = False
        successFlag,log = self.GitFetch(log)

        if(successFlag):
            successFlag,updatesAvailable,log = self.GitPull(log)

        return successFlag, updatesAvailable, log

    def GitLoad(self):
        # Build the command line
        righturl = self.m_sourceUrl[:8] + self.m_sourceControlLogin + ":" + self.m_sourceControlPassword + "@" + self.m_sourceUrl[8:]
        commandLine = ""
        commandLine += "git clone"
        commandLine += ' '
        commandLine += righturl
        commandLine += " "
        commandLine += "2>&1"
        commandLine.replace("\'", "\\\'")
        commandLine.replace("\"", "\\\"")

        try:
            commandOutput, errorCode = CommandProcessor().Run(commandLine,self.m_reposDir)
        except Exception as e:
            print("Exception:  Repository.py Line 257: " + str(e))
            self.m_logStream.write("\n" + Tags.ErrorTag + "Failed to run command: " + commandLine)
            return False

        # Read subversion output
        successFlag = True

        for line in commandOutput:
            decoded_line = bytes(line).decode("utf-8").lower()
            if decoded_line.startswith("already up-to-date."):
                self.m_logStream.write("\n" + Tags.DetailTag + decoded_line)
            elif decoded_line.startswith("cloning into"):
                self.m_logStream.write("\n" + Tags.DetailTag + decoded_line)
            elif decoded_line.startswith("remote"):
                self.m_logStream.write("\n" + Tags.DetailTag + decoded_line)
            elif decoded_line.startswith("receiving objects") or decoded_line.startswith("resolving deltas"):
                self.m_logStream.write("\n" + Tags.ErrorTag + decoded_line)
                successFlag = False

        return successFlag
