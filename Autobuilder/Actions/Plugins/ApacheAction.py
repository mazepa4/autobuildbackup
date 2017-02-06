from Autobuilder.Actions.Plugins.ApacheParser import *
from Autobuilder.Misc import *


class ApacheAction():

    m_template = ""
    m_action = ""
    m_template = ""
    m_apacheVal = ""
    m_templateKey = ""
    m_apacheKey = ""
    m_value = ""
    m_apache2Config = None

    valuesMap = []

    re_comment = re.compile(r"""^#.*$""")
    re_section_start = re.compile(r"""^<Proxy\s*(?P<value>[^>]+)?>$""")
    re_section_end = re.compile(r"""^</Proxy>$""")
    re_section_apache_value = re.compile(r"{(.*?)}")

    def __init__(self,valuesMap = []):
        self.valuesMap = valuesMap


    def Run(self,apacheActions):

        # Assume all properties are valid
        successFlag = True

        preprocess = None
        actionKind = None
        templateLines = None
        apacheKey = None
        value = None
        items = None



        try:
            if "template" in apacheActions:
                templatePath = apacheActions["template"]
                templateLines = open(templatePath).readlines()
                config = ApacheConfig("api", section=True)
                self.m_apache2Config = config.lookForChilds(templateLines)
            if "items" in apacheActions and self.m_apache2Config:
                for action in apacheActions["items"]:
                    templateKey = action["template-key"]
                    apacheKey = action["apache-key"]
                    value = action["value"]
                    self.replaceInPath(apacheKey,templateKey,value)
        except Exception as e:
            successFlag = False
            self.repositoryEntry.ApppendToLog(Tags.ErrorTag + "Failed to load 'apache' configuration.")

        return successFlag,self.m_apache2Config,templatePath


    def replaceInPath(self,path = "",templateKey = " ",value = ""):
        mapResult = [x for x in self.valuesMap if x["property"] == templateKey]
        try:
            searchResults = self.m_apache2Config.find(path)
            if searchResults:
                searchResults.values = value.format(mapResult[0]["value"]).split()
        except Exception as e:
            print(str(e))

