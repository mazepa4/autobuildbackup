from Autobuilder.Misc import *

class Preprocessor():

     m_action = ""
     m_range = ""
     m_valuesMap = []
     repositoryEntry = None
     m_lastPortPath = ""


     def __init__(self,config,repositoryEntry):

          self.repositoryEntry = repositoryEntry

          self.m_lastPortPath =  "{0}lastPort".format(self.repositoryEntry.m_logFolder)

          if "actionKind" in config:
               self.m_action = config["actionKind"]
          if "range" in config:
                ranges = config["range"].split("-")
                if ranges:
                    if len(ranges) == 2:
                         self.m_range = {
                              "min":int(ranges[0]),
                              "max": int(ranges[1])
                         }
                    else:
                         self.m_range = {
                              "min": int(ranges[0]),
                              "max": int(ranges[0])*3
                         }


          if "map" in config:
               for name in config["map"]:
                    self.m_valuesMap.append({
                         "property":  name,
                         "value": None
                    })

     def Run(self):
          if self.m_action == Preprocess.GenPort:

               lastPort = FileWorker().readFile(self.m_lastPortPath)
               if lastPort:
                   lastPort = int(lastPort)
               else:
                   lastPort = 0
               for port in range(self.m_range["min"],self.m_range["max"]):
                    if self.checkBusyPort(port) or lastPort >= port:
                         continue
                    else:
                         count = 0
                         for map in self.m_valuesMap:
                              if map["value"] == None:
                                   map["value"] = port
                                   FileWorker().createFile(self.m_lastPortPath,port)
                                   break
                              else:
                                   count  = count + 1
                         if count == len(self.m_valuesMap):
                              break
          return self.m_valuesMap

     def checkBusyPort(self,port):
          try:
               command_output, exitCode = CommandProcessor().Run('netstat -peant | grep ":{0} "'.format(port))
               if exitCode:
                    for line in command_output:
                         decoded_line = bytes(line).decode("utf-8")
                         if decoded_line and (("Not all processes" in decoded_line) == False and  ("see it all" in decoded_line) == False):
                              return True
               else:
                    return False
          except Exception as e:
               self.repositoryEntry.ApppendToLog(
                    Tags.ErrorTag + "Failed to check if port: {0} busy. Exception: {1} .".format(port, str(e)))
               return True

          return False