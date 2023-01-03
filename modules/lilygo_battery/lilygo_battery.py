from machine import Pin, ADC

class LilyGoBattery:
    def __init__(self):
        pass

    def start(self):
        self.pot = ADC(Pin(2))
        self.pot.atten(ADC.ATTN_11DB)       #Full range: 3.3v

    def tick(self):
        pass

    def getTelemetry(self):

        pot_value = self.pot.read()

        return { 
            "voltage": pot_value * 2 / 1000
        }

    def processTelemetry(self, telemetry):
        pass

    def getCommands(self):
        return []

    def processCommands(self, commands):
        pass

    def getRoutes(self):
        return { }


    def getIndexFileName(self):
        return {  }