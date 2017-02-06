from Autobuilder.Misc import *
from Autobuilder.SharedState import *

class PostProcessAction():

    repositoryEntry = None
    m_deployPath = ""
    m_postprocessScripts = []
    m_description = ""
    m_processDir =""
    m_postProcessDir = ""
    m_itemList = []


    def __init__(self,repositoryEntry):
        self.repositoryEntry = repositoryEntry
        self.m_postprocessScripts = []
        self.m_processDir = ""

    def LoadConfiguration(self,actionConfig,reportException,reportInvalidProperty):

        # Assume all properties are valid
        successFlag = True

        try:
            # Load postprocesses scripts
            for item in actionConfig['postprocessScripts']:
                self.m_postprocessScripts.append(item)

            #loading others properties
            self.m_description = actionConfig['description']
            self.m_processDir = actionConfig['procDir']
            self.m_postProcessDir = actionConfig['postProcDir']

        except Exception as e:
            successFlag = False
            self.repositoryEntry.ApppendToLog(Tags.ErrorTag + "Failed to load 'post-process' configuration.")

        return successFlag

    def Run(self):

        successFlag = True
        exitCode = 0
        #Collecting the bundle
        self.repositoryEntry.ApppendToLog(Tags.StageTag + "Postprocess action...")
        self.repositoryEntry.m_clock.UpdateTime()

        try:
            # Load items
            for item in self.m_postprocessScripts:
                try:
                    workFolder = ""
                    if self.m_processDir != "":
                        workFolder = self.repositoryEntry.m_cacheFolder+"/"+self.m_processDir
                    else:
                        workFolder = self.m_postProcessDir

                    if "pkill" in item:
                        item = "./"+item.split(" ")[1]
                        PID = CommandProcessor().getProcessPID(item)
                        if PID != 0:
                            command_output, exitCode = CommandProcessor().Run("kill -9 "+PID)
                            PID = CommandProcessor().getProcessPID(item)
                            start_time = time.time()
                            while PID != 0:
                                command_output, exitCode = CommandProcessor().Run("kill -9" + PID)
                                PID = CommandProcessor().getProcessPID(item)
                                end_time = time.time()
                                if end_time - start_time > 10:
                                    self.repositoryEntry.ApppendToLog(
                                        Tags.ErrorTag + "Failed to stop apigate process!")
                                    successFlag = False
                                    break;


                    else:
                        if workFolder == "":
                            command_output, exitCode = CommandProcessor().Run(item)
                        else:
                            command_output,exitCode = CommandProcessor().Run(item,workFolder)
                        for line in command_output:
                            decoded_line = bytes(line).decode("utf-8")
                            if decoded_line.lower().startswith("chown:") or decoded_line.lower().startswith("chmod:"):
                                self.repositoryEntry.ApppendToLog(
                                    Tags.ErrorTag + "Failed to run postprocess action because of: " + decoded_line)
                except Exception as e:
                    print("Postprocess command {0}  failed : {1}".format(item,str(e)))
                    self.repositoryEntry.ApppendToLog(Tags.ErrorTag + "Failed to run command: {0} because of: {1}".format(item,str(e)))
                    return False
        except Exception as e:
            successFlag = False
            self.repositoryEntry.ApppendToLog(Tags.ErrorTag + "Failed to run postprocess  tasks.")

        if exitCode:
            successFlag = False
            self.repositoryEntry.ApppendToLog(Tags.ErrorTag + "postprocess action  exited with " + str(exitCode))#os.WEXITSTATUS

        self.repositoryEntry.ApppendToLog(Tags.DetailTag + self.m_description + "' completed.")
        self.repositoryEntry.ApppendToLog(Tags.SuccessTag + "Postprocess action completed (" + str(self.repositoryEntry.m_clock.DeltaMilliseconds()) + " ms)." )
        self.repositoryEntry.FlushLog()
        return successFlag
