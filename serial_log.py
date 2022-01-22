import time

class SerialLog(object):

    enabled = True

    @staticmethod
    def enable():
        SerialLog.enabled = True

    @staticmethod
    def disable():
        SerialLog.enabled = False

    @staticmethod
    def log(message = "", message2 = None, message3 = None):
        if SerialLog.enabled:
            startedAt = time.ticks_ms()
            if (message2 == None):
                print(message)
            else:
                if (message3 == None):
                    print(message, message2)
                else:
                    print(message, message2, message3)
            endedAt = time.ticks_ms()

            # Logging is taking more than 1000ms PER LINE, stopping now
            diff = time.ticks_diff(endedAt, startedAt)
            if (diff > 1000):
                SerialLog.disable()





