from Autobuilder.Repository import *
import threading


class RepositoryEntry(Repository):
    m_requiresInstallation = False

class AutoBuilder():



    m_repositoryList = [] #RepositoryEntry
    m_lastError = ""

    def Run(self,configPath):
        self.m_repositoryList.clear()

        # Load configuration
        if self.LoadConfiguration(configPath) == False:
            return False

        #Update and build repositories
        buildingThreadList = []
        reposWithDep = []
        threadLock = threading.Lock()

        def _run_task_(repository):
            repository.m_requiresInstallation = repository.UpdateAndBuild() and repository.RequiresInstallation()
            return repository.m_requiresInstallation

        def taskCompleted(name,status):
            print("Task '{0}', now has status: {1}".format(name,status))
            if(status == "completed" or  status == "failed"):
                for index,repository in enumerate(reposWithDep):
                    validDep = 0
                    for dep in repository.m_dependencies:
                        if(dep["name"] == name):
                            if status == "completed":
                                validDep = validDep + 1
                                dep["status"] = "completed"
                            elif status == "failed":
                                reposWithDep.pop(index)

                        else:
                            if dep["status"] == "completed":
                                validDep = validDep + 1
                    if validDep == len(repository.m_dependencies) and repository.m_buildStatus != "completed":
                        threadLock = threading.Lock()
                        reposWithDep.pop(index)
                        buildingThreadList.append(CustomThread(_run_task_, repository, threadLock))
                        #buildingThread = (CustomThread(_run_task_, repository, threadLock))
                        #buildingThread.run()


        """
        for repository in self.m_repositoryList:
            repository.taskStatusChanged = taskCompleted
            for index,dep_name in enumerate(repository.m_dependencies):
                _dependeny = [_repositoty for _repositoty in self.m_repositoryList if _repositoty.m_name == dep_name]
                if _dependeny:
                    repository.m_dependencies[index] = _dependeny[0]
        """


        for repository in self.m_repositoryList:
            repository.taskStatusChanged = taskCompleted
            try:
                if len(repository.m_dependencies) == 0:
                    buildingThreadList.append(CustomThread(_run_task_,repository,threadLock))
                else:
                    reposWithDep.append(repository)
            except:
                print("Error: unable to start thread")


       # while len(buildingThreadList) > 0:
            # Wait for all threads to complete
        for index,buildingThread in enumerate(buildingThreadList):
            #if buildingThread.run() == BuildStatus.Completed:
            buildingThread.run()
            #buildingThreadList.pop(index)

        #if len(reposWithDep):
        #    input("There some unfinished actions, please wait...")

        return True


    def LoadConfiguration(self,configPath):

        try:
            common = Common()
            configs  = common.loadConfig(configPath)

            logDir = configs['logDir']
            reposDir = configs['reposDir']
            distPath = configs['distPath']

            #FileWorker().createPath(logDir)
            #FileWorker().createPath(reposDir)
            #FileWorker().createPath(distPath)


            if configs == None:
                return False
            else:
                for repo in configs['repos']:
                    repository =  Repository(logDir,reposDir,distPath)
                    repository.LoadConfiguration(repo)
                    self.m_repositoryList.append(repository)



        except Exception as e:
            self.m_lastError = str(e)
            return False
        return True

    def LastError(self):
        return self.m_lastError

    def StopService(self,serviceName,logStream):
        return True

    def StartService(self,serviceName,logStream):
        return True
