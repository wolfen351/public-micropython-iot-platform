class SerialLog(object):

    enabled = False

    @staticmethod
    def enable():
        SerialLog.enabled = True

    @staticmethod
    def disable():
        SerialLog.enabled = False

    @staticmethod
    def log(message = "", message2 = None, message3 = None):
        if SerialLog.enabled:
            if (message2 == None):
                print(message)
            else:
                if (message3 == None):
                    print(message, message2)
                else:
                    print(message, message2, message3)



