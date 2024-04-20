from modules.basic.basic_module import BasicModule
from serial_log import SerialLog
from machine import UART, Pin
from modules.sim800l.sim800ldriver import Modem
import json

class SIM800LControl(BasicModule):

    # pin 7 and pin 5 are used for serial communication
    uart = None

    def __init__(self):
        SerialLog.log('Starting up...')

        # Create new modem object on the right Pins
        modem = Modem(
                    MODEM_PWKEY_PIN    = None,
                    MODEM_RST_PIN      = None,
                    MODEM_POWER_ON_PIN = None,
                    MODEM_TX_PIN       = 9,
                    MODEM_RX_PIN       = 7)

        # Initialize the modem
        modem.initialize()

        # Run some optional diagnostics
        SerialLog.log('Modem info: "{}"'.format(modem.get_info()))
        SerialLog.log('Network scan: "{}"'.format(modem.scan_networks()))
        SerialLog.log('Current network: "{}"'.format(modem.get_current_network()))
        SerialLog.log('Signal strength: "{}%"'.format(modem.get_signal_strength()*100))

        # Connect the modem
        modem.connect(apn='internet', user='', pwd='') #leave username and password empty if your network don't require them
        SerialLog.log('\nModem IP address: "{}"'.format(modem.get_ip_addr()))

        # Example GET
        SerialLog.log('\nNow running demo http GET...')
        url = 'http://checkip.dyn.com/'
        response = modem.http_request(url, 'GET')
        SerialLog.log('Response status code:', response.status_code)
        SerialLog.log('Response content:', response.content)

        # Example POST
        SerialLog.log('Now running demo https POST...')
        url  = 'https://postman-echo.com/post'
        data = json.dumps({'myparameter': 42})
        response = modem.http_request(url, 'POST', data, 'application/json')
        SerialLog.log('Response status code:', response.status_code)
        SerialLog.log('Response content:', response.content)

        # Disconnect Modem
        modem.disconnect()

     
    def start(self):
        pass
     
    def tick(self):
        pass
     
    def getTelemetry(self):
        return {} 

     
    def processTelemetry(self, telemetry):
        pass

     
    def getCommands(self):
        return []

     
    def processCommands(self, commands):
        pass

     
    def getRoutes(self):
        return {
        }

     
    def getIndexFileName(self):
        return { "sim800l" : "/modules/sim800l/sim800l_index.html" }

    # Internal code here

