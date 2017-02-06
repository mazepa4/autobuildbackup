from Autobuilder.Misc import *
from Autobuilder.Actions.Plugins.Preprocessor import *
from Autobuilder.Actions.Plugins.ApacheAction import *

class BundleAction():
    repositoryEntry = None
    m_deployPath = ""
    m_itemList = []
    m_sourceFile = None
    m_bundleDir = None
    useTmpDir = False
    m_tmpDir = None

    def __init__(self, repositoryEntry):
        self.repositoryEntry = repositoryEntry
        self.m_itemList = []

    def LoadConfiguration(self, actionConfig, reportException, reportInvalidProperty):

        # Assume all properties are valid
        successFlag = True

        try:
            self.m_bundleDir = actionConfig['bundleDir']

            if self.m_bundleDir == "$TEMP_DIR$":
                self.useTmpDir = True
                self.m_tmpDir= self.repositoryEntry.m_tmpDir;

            # Load items
            for item in actionConfig['items']:
                self.m_itemList.append(item)

        except Exception as e:
            successFlag = False
            self.repositoryEntry.ApppendToLog(Tags.ErrorTag + "Failed to load 'bundle' configuration.")

        return successFlag

    def Run(self):

        successFlag = True
        exitCode = 0

        # Collecting the bundle
        self.repositoryEntry.ApppendToLog(Tags.StageTag + "Bundling...")
        self.repositoryEntry.m_clock.UpdateTime()



        try:
            # Load items
            for item in self.m_itemList:

                deployPath = None
                filename = None
                template = None
                sourceFile = None
                params = None
                valuesMap = None
                preprocess = None
                apacheActions = None
                apache2Config = None
                tmpDir = None

                if "deployPath" in item:
                    deployPath = item["deployPath"]

                if "item" in item:
                    filename = item["item"]

                if "template" in item:
                    template = item["template"]

                if template:
                    if "sourceFile" in template:
                        sourceFile = self.repositoryEntry.m_cacheFolder + "/" + template["sourceFile"]

                    if "tmpDir" in template:
                        tmpDir = self.repositoryEntry.m_cacheFolder + "/" + template["tmpDir"]

                    if "preprocess" in template:
                        preprocess = template["preprocess"]

                        _preprocess = Preprocessor(preprocess,self.repositoryEntry)
                        valuesMap = _preprocess.Run()

                    if "apacheActions" in template:
                        apacheActions = template["apacheActions"]

                        _apacheActions = ApacheAction(valuesMap)
                        successFlag, apache2Config, apachePath = _apacheActions.Run(apacheActions)

                        apacheConfigStr = apache2Config.biuildNewConfig(4)

                        _deployPath = None
                        if self.useTmpDir:
                           _deployPath = self.m_tmpDir + "/apachePath.conf"
                        else:
                            _deployPath = self.repositoryEntry.m_distPath + "/" + self.m_bundleDir + "/apachePath.conf"
                        FileWorker().createFile(_deployPath,apacheConfigStr)


                    if "params" in template:
                        params = template["params"]

                    if valuesMap:
                        for value in valuesMap:
                            params[value["property"]] = value["value"]

                    if sourceFile and params:
                        templateBuilder = Template(sourceFile,params)
                        compiledJSONString = templateBuilder.compileJSON()

                        if self.useTmpDir:
                            _deployPath = self.m_tmpDir + "/" + deployPath
                        else:
                            _deployPath = self.repositoryEntry.m_distPath + "/" + self.m_bundleDir + "/" + deployPath
                        FileWorker().createPath(_deployPath)
                        FileWorker().createFile(_deployPath + "/" +template["sourceFile"],compiledJSONString)

                else:
                    _deployPath = None
                    if self.useTmpDir:
                        _deployPath = self.m_tmpDir + "/" + deployPath
                    else:
                        _deployPath = self.repositoryEntry.m_distPath + "/" + self.m_bundleDir + "/" + deployPath

                    FileWorker().createPath(_deployPath)
                    command_output, exitCode = FileWorker().copyContent(self.repositoryEntry.m_cacheFolder + "/*",
                                                                        _deployPath)
                for line in command_output:
                    decoded_line = bytes(line).decode("utf-8")
                    if decoded_line.lower().startswith("cp:"):
                        self.repositoryEntry.ApppendToLog(
                            Tags.ErrorTag + "Failed to collect the bundle because of: " + decoded_line)

        except Exception as e:
            successFlag = False
            self.repositoryEntry.ApppendToLog(Tags.ErrorTag + "Failed to run 'bundle' task.")

        if exitCode:
            successFlag = False
            self.repositoryEntry.ApppendToLog(Tags.ErrorTag + "bundling exited with " + str(exitCode))#os.WEXITSTATUS

        self.repositoryEntry.ApppendToLog(Tags.SuccessTag + "Bundling completed (" +  str(self.repositoryEntry.m_clock.DeltaMilliseconds()) + " ms).")
        self.repositoryEntry.FlushLog()
        return successFlag


class BundleItem():

    deployPath = ""
    item = ""
    sourceFile = ""


class Template():
    sourceFile = ""
    params =  None
    sourceJSON = None

    def __init__(self,sourceFile,params):
        self.sourceFile = sourceFile
        self.params = params

    def compileJSON(self):
        sourceText = FileWorker().readFile(self.sourceFile)
        self.sourceJSON = json.loads(sourceText)

        for param in self.params:
            self.findAndReplaceInPath(param,self.params[param])

        return  json.dumps(self.sourceJSON)


    def findAndReplaceInPath(self,path = None,value = None):
        curEl = None
        parts = path.split(".")
        prevKey = ""
        prevValue = ""

        if path and len(path.split(".")):
            for part in path.split("."):
                if curEl:
                    if part in  curEl:
                        curEl = curEl[part]
                        prevKey = part
                        prevValue[part] = curEl
                elif part  in self.sourceJSON:
                    curEl = self.sourceJSON[part]
                    prevKey = part
                    prevValue = self.sourceJSON[part]


            curEl = value
            prevValue[part] = curEl
            prevKey = part
        else:
            return None

        self.sourceJSON


