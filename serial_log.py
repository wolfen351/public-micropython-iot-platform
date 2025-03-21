import ujson
from gc import mem_free, collect

class SerialLog(object):

    enabled = True
    logHistoryData = []

    @staticmethod
    def logHistory():
        return ujson.dumps(SerialLog.logHistoryData)
    
    @staticmethod
    def purge():
        SerialLog.logHistoryData = []

    @staticmethod
    def log(*messages):
        # Check free memory, if we have less than 10k, then clear logs
        if mem_free() < 20000:
            SerialLog.logHistoryData.clear()
            SerialLog.logHistoryData.append("Log history purged due to low memory")
            collect()

        # Concatenate messages into a single string
        log_message = " ".join(str(message) for message in messages if message is not None)

        if len(SerialLog.logHistoryData) > 50:
            SerialLog.logHistoryData.pop(0)

        SerialLog.logHistoryData.append(log_message)
        print(log_message)
