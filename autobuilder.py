from Autobuilder.Misc import *
from Autobuilder.Autobuilder import *
import os,fcntl, sys
from signal import signal, SIGTERM, SIGINT

def signal_term_handler(signal, frame):
    print('Got KILL signal!!!')
    sys.exit(0)

def signal_int_handler(signal, frame):
    print('Keyboard interrupt!!!')
    sys.exit(0)

if __name__ == "__main__":
    signal(SIGTERM, signal_term_handler)
    signal(SIGINT, signal_int_handler)
    # Open the lock
    lockPath = "/var/lock/autobuild.lock"
    lockDescriptor = open(lockPath, "w")

    #clear last port for Apache conf. editing


    try:
        fcntl.lockf(lockDescriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        print("New instance running: " + str(lockDescriptor.fileno()))

        configPath = ""
        argc = 0
        for arg in sys.argv:
            if str(arg).startswith("--config"):
                if argc + 1 != len(sys.argv):
                    configPath = sys.arg[argc + 1]
            argc += 1

        if len(configPath) == 0:
            configPath = os.getcwd()
            configPath += "/autobuild.conf"

        # Run the autobuild
        autoBuilder = AutoBuilder()

        exitCode = 0

        if autoBuilder.Run(configPath):
            print(autoBuilder.LastError())



    except IOError as e:
        # another instance is running
        print("Another instance of autobuild is currently running." + str(e))
        sys.exit(0)