from Autobuilder.Misc import *
from Autobuilder import *
import shlex

class BuildAction():
    m_buildMethod = BuildMethod.Unknown
    m_buildScript = ""
    m_buildConfiguration = ""
    m_buildPlatform = ""
    m_buildDir = ""
    repositoryEntry = None
    m_target = ""

    def __init__(self,repositoryEntry):
        self.repositoryEntry = repositoryEntry
        self.processPipe = CommandProcessor()

    def LoadConfiguration(self,actionConfig,reportException,reportInvalidProperty):
        # Assume  all  properties are valid bool
        successFlag = True
        try:
            #Load properties
            self.m_buildMethod = actionConfig['buildMethod']

            if self.m_buildMethod == "webpack":
                self.m_buildDir = actionConfig['buildDir']

            self.m_buildScript = actionConfig['buildScript']
            self.m_buildConfiguration = actionConfig['buildConfiguration']
            self.m_buildPlatform = actionConfig['buildPlatform']
            if "target" in actionConfig:
                self.m_target = actionConfig['target']

            #Check properties
            if self.m_buildMethod == BuildMethod.Unknown:
                successFlag = False
                reportInvalidProperty("buildMethod")
        except Exception as e:
            print("BuildAction Line 28: " + str(e))
            successFlag = False
            reportException(Exception)

        return successFlag

    #-------------------------------------------------------------------------------------------------
    def Run(self):
        # Run specific build method
        self.repositoryEntry.ApppendToLog(Tags.StageTag + "Building...")
        self.repositoryEntry.m_clock.UpdateTime()

        if self.m_buildMethod == BuildMethod.Make:
            if self.RunMake() != True:
                self.repositoryEntry.ApppendToLog(Tags.ErrorTag + "Failed to build the repository using make.")
                return False;

        elif self.m_buildMethod == BuildMethod.Qmake:
            if self.RunQmake() != True:
                self.repositoryEntry.ApppendToLog(Tags.ErrorTag + "Failed to build the repository using qmake.")
                return False;

        elif self.m_buildMethod == BuildMethod.Xbuild:
            if self.RunXbuild() != True:
                self.repositoryEntry.ApppendToLog("\n" + Tags.ErrorTag + "Failed to build the repository using xbuild.")
                return False;
        elif self.m_buildMethod == BuildMethod.WebPack:
            if self.RunWebPack() != True:
                self.repositoryEntry.ApppendToLog("\n" + Tags.ErrorTag + "Failed to build the repository using webpack.")
                return False;

        elif self.m_buildMethod == BuildMethod.CMake:
            if self.RunCMake() != True:
                self.repositoryEntry.ApppendToLog(Tags.ErrorTag + "Failed to build the repository using cmake.")
                return False;

        self.repositoryEntry.ApppendToLog(Tags.SuccessTag + "Building completed (" + str(self.repositoryEntry.m_clock.DeltaMilliseconds()) + "ms).")

        self.repositoryEntry.FlushLog()
        return True

    #-------------------------------------------------------------------------------------------------
    def IsInstallAction(self):
        return False

    def RunMake(self):
        successFlag = True

        for conf in self.m_buildScript.split(" "):

            path, file = Common().extract_project_properies(conf)
            # Build the command line
            commandLine = ""
            #commandLine = "sudo -u ivan "
            commandLine += "make -f "
            commandLine += file
            commandLine += ' '
            commandLine += " 2>&1"


            commandLine.replace("\'", "\\\'")
            commandLine.replace( "\"", "\\\"")


            #Run the command
            try:
                command_output,exitCode = CommandProcessor().Run(commandLine, self.repositoryEntry.m_cacheFolder + path)
            except Exception as e:
                print("BuildAction Line 99: " +str(e))
                self.repositoryEntry.ApppendToLog(Tags.ErrorTag + "Failed to run command: " + commandLine)
                return False

            successFlag = True

            for line in command_output:
                decoded_line = bytes(line).decode("utf-8")
                if decoded_line.startswith("sh") or decoded_line.startswith("make") or decoded_line.find("error") >= 0:
                    successFlag = False
                    self.repositoryEntry.ApppendToLog(Tags.ErrorTag + decoded_line)

        if exitCode:
            successFlag = False
            self.repositoryEntry.ApppendToLog(Tags.ErrorTag + "make exited with " + str(exitCode))#os.WEXITSTATUS

        self.repositoryEntry.FlushLog()
        return successFlag

    def RunQmake(self):

        successFlag = True

        for conf in self.m_buildScript.split(" "):
            path, file = Common().extract_project_properies(conf)
            #build_conf += self.m_cacheFolder + "/" + conf + " "

            # Build the command line
            commandLine = ""
            #commandLine = "sudo -u ivan "
            commandLine += "qmake {0} -r -spec linux-g++-64".format(file)
            commandLine += ' '
            commandLine += " 2>&1"

            commandLine.replace("\'", "\\\'")
            commandLine.replace( "\"", "\\\"")

            #Run the command
            try:
                command_output,exitCode = self.processPipe.Run(commandLine,self.repositoryEntry.m_cacheFolder + path)
            except Exception as e:
                print("BuildAction Line 135: " +str(e))
                self.repositoryEntry.ApppendToLog(Tags.ErrorTag + "Failed to run command: " + commandLine)
                return False;


            for line in command_output:
                decoded_line = bytes(line).decode("utf-8").strip()
                if decoded_line != "":
                    if decoded_line.lower().startswith("sh") or decoded_line.startswith("make"):
                        successFlag = False
                        self.repositoryEntry.ApppendToLog(Tags.DetailTag + decoded_line)
                    elif decoded_line.lower().find("message") != -1:
                        self.repositoryEntry.ApppendToLog(Tags.DetailTag + decoded_line)
                    elif decoded_line.lower().find("warning") != -1:
                        self.repositoryEntry.ApppendToLog(Tags.WarningTag + decoded_line)
                    elif decoded_line.lower().startswith("Project MESSAGE:")!=-1:
                        self.repositoryEntry.ApppendToLog(Tags.DetailTag + decoded_line)
                    else:
                        successFlag = False
                        self.repositoryEntry.ApppendToLog(Tags.ErrorTag + decoded_line)

            if exitCode:
                successFlag = False
                self.repositoryEntry.ApppendToLog(Tags.ErrorTag + "qmake exited with " + str(exitCode))#os.WEXITSTATUS

        self.repositoryEntry.FlushLog()
        return successFlag


    def RunXbuild(self):
        command_error = ""

        # Build the command line
        commandLine = ""
        commandLine += "xbuild /nologo /verbosity:minimal /target:rebuild /property:configuration="
        commandLine += self.m_buildConfiguration
        commandLine += " /property:platform="
        commandLine += self.m_buildPlatform;
        commandLine += ' '
        commandLine += self.m_buildScript
        commandLine += " 2>&1"

        commandLine.replace("\'", "\\\'")
        commandLine.replace("\"", "\\\"")

        # Run the command
        try:
            command_output,exitCode = self.processPipe.Run(commandLine,self.repositoryEntry.m_cacheFolder)
        except Exception as e:
            print("BuildAction Line 179: " +str(e))
            self.repositoryEntry.ApppendToLog(Tags.ErrorTag + "Failed to run command: " + commandLine)
            return False;

        successFlag = True

        for line in command_output:
            decoded_line = bytes(line).decode("utf-8")
            if decoded_line.lower().startswith("sh") or decoded_line.startswith("xbuild") or decoded_line.startswith("msbuild"):
                successFlag = False
                self.repositoryEntry.ApppendToLog(Tags.ErrorTag + decoded_line)
            elif decoded_line.lower().find("warning") != -1:
                self.repositoryEntry.ApppendToLog(Tags.WarningTag + decoded_line)
            elif decoded_line.lower().find("error") != -1:
                successFlag = False
                self.repositoryEntry.ApppendToLog(Tags.ErrorTag + decoded_line)

        if exitCode:
            successFlag = False
            self.repositoryEntry.ApppendToLog(Tags.ErrorTag + "xbuild exited with " + str(exitCode))#os.WEXITSTATUS

        self.repositoryEntry.FlushLog()
        return successFlag


    def RunWebPack(self):
        command_output = ""
        command_error = ""

        path = ""

        # Build the command line
        commandLine = ""
        commandLine += "webpack -p --config "
        commandLine += self.m_buildScript
        commandLine += " -d --color"
        commandLine += ' '
        commandLine += " 2>&1"

        commandLine.replace("\'", "\\\'")
        commandLine.replace("\"", "\\\"")

        # Run the command
        try:
            command_output,exitCode = self.processPipe.Run(commandLine,self.repositoryEntry.m_cacheFolder+"/"+self.m_buildDir)
        except Exception as e:
            print("BuildAction Line 184: " + str(e))
            self.repositoryEntry.ApppendToLog(Tags.ErrorTag + "Failed to run command: " + commandLine)
            return False;

        successFlag = True

        for line in command_output:
            decoded_line = bytes(line).decode("utf-8")
            if decoded_line.lower().startswith("sh") or \
                    decoded_line.startswith("webpack") or\
                    decoded_line.startswith(
                    "webpack"):
                if decoded_line.lower().find("command not found"):
                    successFlag = False
                    self.repositoryEntry.ApppendToLog(Tags.ErrorTag + decoded_line)
                successFlag = False
                self.repositoryEntry.ApppendToLog(Tags.ErrorTag + decoded_line)
            elif decoded_line.lower().find("warning") != -1:
                self.repositoryEntry.ApppendToLog(Tags.WarningTag + decoded_line)
            elif decoded_line.lower().find("error") != -1 and decoded_line.lower().find("side effects") == -1:
                successFlag = False
                self.repositoryEntry.ApppendToLog(Tags.ErrorTag + decoded_line)

        if exitCode:
            successFlag = False
            self.repositoryEntry.ApppendToLog(Tags.ErrorTag + "webpack exited with " + str(exitCode))#os.WEXITSTATUS

        self.repositoryEntry.FlushLog()
        return successFlag

    def RunCMake(self):
        command_output = ""
        command_error = ""

        path = ""

        successFlag = self.createCmakeCache()
        if successFlag:
            # Build the command line
            commandLine = ""
            commandLine += "cmake --build"
            commandLine += ' '
            commandLine += self.repositoryEntry.m_cacheFolder
            commandLine += ' '
            commandLine += "--target "
            commandLine += self.m_target
            commandLine += ' -- -j 10'
            commandLine += " 2>&1"

            commandLine.replace("\'", "\\\'")
            commandLine.replace("\"", "\\\"")

            print(commandLine)

            # Run the command
            try:
                command_output, exitCode = self.processPipe.Run(commandLine,self.repositoryEntry.m_cacheFolder)
            except Exception as e:
                print("BuildAction Line 184: " + str(e))
                self.repositoryEntry.ApppendToLog(Tags.ErrorTag + "Failed to run command: " + commandLine)
                return False;

            successFlag = True

            for line in command_output:
                decoded_line = bytes(line).decode("utf-8")
                if decoded_line.lower().startswith("sh") :
                    if decoded_line.lower().find("command not found"):
                        successFlag = False
                        self.repositoryEntry.ApppendToLog(Tags.ErrorTag + decoded_line)
                    successFlag = False
                    self.repositoryEntry.ApppendToLog(Tags.ErrorTag + decoded_line)
                elif decoded_line.lower().find("warning") != -1:
                    self.repositoryEntry.ApppendToLog(Tags.WarningTag + decoded_line)
                elif decoded_line.lower().find("error") != -1 and decoded_line.lower().find("side effects") == -1:
                    successFlag = False
                    self.repositoryEntry.ApppendToLog(Tags.ErrorTag + decoded_line)

            if exitCode:
                successFlag = False
                self.repositoryEntry.ApppendToLog(
                    Tags.ErrorTag + "cmake exited with " + str(exitCode))  # os.WEXITSTATUS

            self.repositoryEntry.FlushLog()
            return successFlag
        else:
            return False


    def createCmakeCache(self):
        successFlag = True

        for conf in self.m_buildScript.split(" "):

            path, file = Common().extract_project_properies(conf)
            # Build the command line
            commandLine = ""
            #commandLine = "sudo -u ivan "
            commandLine += "cmake -DCMAKE_BUILD_TYPE=Release -R 'CodeBlocks - Unix Makefiles' "
            commandLine +=  self.repositoryEntry.m_cacheFolder
            commandLine += ' '
            commandLine += " 2>&1"


            commandLine.replace("\'", "\\\'")
            commandLine.replace( "\"", "\\\"")

            print(commandLine)

            #Run the command
            try:
                command_output,exitCode = CommandProcessor().Run(commandLine, self.repositoryEntry.m_cacheFolder)
            except Exception as e:
                print("BuildAction Line 99: " +str(e))
                self.repositoryEntry.ApppendToLog(Tags.ErrorTag + "Failed to run command: " + commandLine)
                return False

            successFlag = True

            for line in command_output:
                decoded_line = bytes(line).decode("utf-8")
                if decoded_line.startswith("sh") or decoded_line.find("error") >= 0:
                    successFlag = False
                    self.repositoryEntry.ApppendToLog(Tags.ErrorTag + decoded_line)

        if exitCode:
            successFlag = False
            self.repositoryEntry.ApppendToLog(Tags.ErrorTag + "cmake exited with " + str(exitCode))#os.WEXITSTATUS

        self.repositoryEntry.FlushLog()
        return successFlag


