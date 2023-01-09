import time
import ujson
       
class SerialLog(object):

    enabled = True
    logHistoryData = []

    @staticmethod
    def enable():
        SerialLog.enabled = True

    @staticmethod
    def disable():
        SerialLog.enabled = False

    @staticmethod
    def logHistory():
        return ujson.dumps(SerialLog.logHistoryData)

    @staticmethod
    def log(message = "", message2 = None, message3 = None, message4 = None):

        if (len(SerialLog.logHistoryData) > 40):
            SerialLog.logHistoryData.pop(0)

        if (message2 == None):
            SerialLog.logHistoryData.append(str(message))
        elif (message3 == None):
            SerialLog.logHistoryData.append(str(message) + " " + str(message2))
        elif (message4 == None):
            SerialLog.logHistoryData.append(str(message) + " " + str(message2) + " " + str(message3))
        else:
            SerialLog.logHistoryData.append(str(message) + " " + str(message2) + " " + str(message3) + " " + str(message4))

        if SerialLog.enabled:
            startedAt = time.ticks_ms()
            if (message2 == None):
                print(message)
            else:
                if (message3 == None):
                    print(message, message2)
                else:
                    if (message4 == None):
                        print(message, message2, message3)
                    else:
                        print(message, message2, message3, message4)
            endedAt = time.ticks_ms()

            # # Logging is taking more than 1000ms PER LINE, stopping now
            # diff = time.ticks_diff(endedAt, startedAt)
            # if (diff > 1000):
            #     SerialLog.disable()





