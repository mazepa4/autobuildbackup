import time

class Clock:

    start_time = 0

    #def __init__(self):

    def UpdateTime(self):
        self.start_time = time.time()

    def DeltaMilliseconds(self):
        return int(round((time.time()-self.start_time) * 1000))

class SharedState:

    m_logFolder = ""
    m_cacheFolder = ""
    m_bundle = None #Bundle
    m_logStream = None #Filestream
    processPipe = None
    m_clock = Clock()

    def ApppendToLog(self,log):
        self.m_logStream.write("\n"+log)

    def FlushLog(self):
        self.m_logStream.flush()

