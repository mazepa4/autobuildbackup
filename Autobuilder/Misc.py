import os
import subprocess
import json
import threading
import inspect

#-------------------------------------------------------------------------------------------------
# FileWorker
#-------------------------------------------------------------------------------------------------
class FileWorker:

    logStream = ""

   # def __init__(self):
        #print("This is a message inside the Filereader class.")

    def readFile(self,path):
        try:
            f = open(path,"r")
            fileContent = f.read()

            return fileContent
        except Exception as e:
            print("\n "+ Tags.ErrorTag + "Failed to read file: " + path)
            return False

    def copyContent(self,extingPath,targetPath):

        out = []
        exitCode = 0
        try:
            is_folder = os.path.isdir(extingPath.replace("*",""))
            if is_folder:
                _command = "yes | cp -rf " + extingPath + " " + targetPath
            else:
                _command = "yes | cp " + extingPath  + " " + targetPath
            _out, exitCode = CommandProcessor().Run(_command)
            out += _out
            return out, exitCode
        except Exception as e:
            print("\n " + Tags.ErrorTag + "Failed to copy {0} to {1}.".format(extingPath,targetPath) + "Exception: " + str(e))
            return [("\n " + Tags.ErrorTag + "Failed to copy {0} to {1}.".format(extingPath,
                                                                                 targetPath) + "Exception: " + str(
                e))], -1




    def createPath(self,path):
        try:
            if not os.path.exists(path):
                os.makedirs(path)
        except Exception as e:
            print("\n " + Tags.ErrorTag + "Failed to create path: " + path)
            return False

    def getFileName(self,path = ""):
        return path.split("/").reverse()[0]

    def isExist(self,path):
        exist = os.path.exists(path)
        return exist

    def clearFolder(self,path,):
        try:
            os.removedirs(path)
            os.mkdir(path)
        except Exception as e:
           print("\n " + Tags.WarningTag + "Failed to clear folder: " + path)

    def createFile(self,path,content):
        try:
            file = open(path, "w")
            file.write(str(content))
        except Exception as exp:
            print("Failed to create file in '{0}', error:{1}.".format(path,str(exp)))


#-------------------------------------------------------------------------------------------------
# CommandProcessor
#-------------------------------------------------------------------------------------------------
class CommandProcessor:

    def Run(self,command,folder = None):
        """from http://blog.kagesenshi.org/2008/02/teeing-python-subprocesspopen-output.html
        """
        p = None
        if folder == None:
            p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        else:
            p = subprocess.Popen(command, shell=True,cwd=folder, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        stdout = []
        while True:
            if("./" in command and  command.index("./")==0):
                break;
            line = p.stdout.readline()
            if str(line) != b'':
                stdout.append(line)
            if line == b'' and p.poll() != None:
                break

        return stdout,p.returncode

    def getProcessPID(self,commandline):
        # ps aux | grep "python3 main.py"
        commandline = commandline.replace("+", " ")
        out, exitcode =  self.Run("ps aux | grep '" + commandline + "'")
        for line in out:
            decoded_line = bytes(line).decode("utf-8").strip("\r\n\t :.")
            if decoded_line != "":
                parts = decoded_line.split(" ")
                _parts = []
                for p in parts:
                    if p != "": _parts.append(p.replace("\\", ""))

                PID = _parts[1]
                COMMAND = ""
                if len(_parts) > 10:
                    for item in _parts[10:]:
                        COMMAND += " " + item.replace("\\", "")
                if COMMAND.strip() == commandline:
                    return str(PID)
        return 0

#-------------------------------------------------------------------------------------------------
# SourceControl
#-------------------------------------------------------------------------------------------------
class SourceControl:
    Unknown = -1
    Git = "git"
    Subversion = "subversion"

# -------------------------------------------------------------------------------------------------
# ActionKind
# -------------------------------------------------------------------------------------------------
class ActionKind:
    Unknown = -1
    Build = "build"
    Bundle = "bundle"
    Upload = "upload"
    PostProcess = "post-process"
    InstallService = "install-service"


# -------------------------------------------------------------------------------------------------
# ActionKind
# -------------------------------------------------------------------------------------------------
class CommantType:
    Unknown = -1
    Script = "script"
    File = "file"

class BuildStatus:
    Unknown = -1
    Processing = "active"
    Completed = "completed"
    Failed = "failed"

# -------------------------------------------------------------------------------------------------
# BuildMethod
# -------------------------------------------------------------------------------------------------
class BuildMethod:
    Unknown = -1
    CMake = "cmake"
    Make = "make"
    Qmake = "qmake"
    Xbuild = "xbuild"
    WebPack = "webpack"

# -------------------------------------------------------------------------------------------------
# Tags
# -------------------------------------------------------------------------------------------------
class Tags:
    StageTag = "Stage:\t\t"
    DetailTag = "Detail:\t\t"
    WarningTag = "Warning:\t"
    ErrorTag = "Error:\t\t"
    SuccessTag = "Success:\t"

# -------------------------------------------------------------------------------------------------
# Apache actions
# -------------------------------------------------------------------------------------------------
class ApacheActions:
    SetPort = "set-port"
    Restart = "restart"
    Stop = "stop"

# -------------------------------------------------------------------------------------------------
# Apache actions
# -------------------------------------------------------------------------------------------------
class Preprocess:
    GenPort = "gen-ports"



class Common:

    def loadConfig(self,configPath):
        try:
            jsonText = FileWorker().readFile(configPath).replace("\t","").replace("\n","").replace("\r","")
            return json.loads(jsonText)
        except Exception as e:
            print(str(e))
            return None

    def chunks(self,s, n):
        """Produce `n`-character chunks from `s`."""
        for start in range(0, len(s), n):
            yield s[start:start+n]

    def extract_project_properies(self,relativePath):
        parts = relativePath.split("/")

        relativePath = ""

        for num in range(len(parts) - 1):
            relativePath += "/" + parts[num]

        return relativePath, parts[len(parts) - 1]

    def lineno(self):
        """Returns the current line number in our program."""
        return inspect.currentframe().f_back.f_lineno

class CustomThread (threading.Thread):

    _threadLock = None
    _func = None
    _repository = None

    def __init__(self,func, repository,threadLock):
        self._threadLock = threadLock
        self._func = func
        self._repository = repository
        threading.Thread.__init__(self)

    def run(self):
        print ("Starting " + self.name)
        # Get lock to synchronize threads
        self._threadLock.acquire()
        open("/home/ivan/Temp/var/lastaction", "w").write(self._repository.m_name)
        self._func(self._repository)
        # Free lock to release next thread
        self._threadLock.release()
        return self._repository.m_buildStatus
