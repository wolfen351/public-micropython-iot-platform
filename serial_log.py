import time
import ujson
from gc import mem_free, collect

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
    def log(message = "", message2 = None, message3 = None, message4 = None, message5 = None):

        # Check free memory, if we have less than 10k, then disable logging
        if (mem_free() < 10000):
            SerialLog.logHistoryData = ["Log history purged due to low memory"]
            collect()

        if (len(SerialLog.logHistoryData) > 100):
            SerialLog.logHistoryData.pop(0)

        if (message2 == None):
            SerialLog.logHistoryData.append(str(message))
        elif (message3 == None):
            SerialLog.logHistoryData.append("%s %s" %  (message, message2))
        elif (message4 == None):
            SerialLog.logHistoryData.append("%s %s %s" %  (message, message2, message3))
        elif (message5 == None):
            SerialLog.logHistoryData.append("%s %s %s %s" %  (message, message2, message3, message4))
        else:
            SerialLog.logHistoryData.append("%s %s %s %s %s" %  (message, message2, message3, message4, message5))

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
                        if (message5 == None):
                            print(message, message2, message3, message4)
                        else:
                            print(message, message2, message3, message4, message5)
                            
            endedAt = time.ticks_ms()

            # Logging is taking more than 1000ms PER LINE, stopping now
            diff = time.ticks_diff(endedAt, startedAt)
            if (diff > 1000):
                SerialLog.disable()





