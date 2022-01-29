# Main 
def runSafe(cmd, p1 = None):
    try:
        if (p1 != None):
            return cmd(p1)
        return cmd()
    except KeyboardInterrupt:
        raise
    except Exception as e:
        SerialLog.log(e)
        sys.print_exception(e)
        gc.collect()

try:
    # Turn on the LED to show we are alive
    from machine import Pin
    led = Pin(15, Pin.OUT)
    led.on()

    # set the CPU frequency to 240 MHz
    from serial_log import SerialLog
    SerialLog.log()
    SerialLog.log("CPU 240Mhz")
    import machine
    machine.freq(240000000) 

    # Import other modules needed
    SerialLog.log("Loading code..")
    from mqtt_control import MqttControl
    from homeassistant_control import HomeAssistantControl
    from thingsboard_control import ThingsboardControl
    from web_processor import WebProcessor
    from wifi import WifiHandler
    import sys
    import gc
    from temp_monitor import TempMonitor
    
    #SerialLog.disable() # disable for live, otherwise you pay 10s startup cost

    basicSettings = { 
        'Name': 'Temperature Sensor',
        'ShortName': 'TempMon'
    }

    # register all the modules
    wifi = WifiHandler(basicSettings)
    temp = TempMonitor(basicSettings)
    mqtt = MqttControl(basicSettings)
    homeassistant = HomeAssistantControl(basicSettings)
    tb = ThingsboardControl(basicSettings)
    web = WebProcessor(basicSettings)
    allModules = [ wifi, temp, mqtt, homeassistant, tb, web ]
    
    # start all the modules up
    for mod in allModules:
        SerialLog.log("Starting: ", mod)
        mod.start()

    ledOn = True


    telemetry = dict()

    while True:

        # tick all modules
        for mod in allModules:
            runSafe(mod.tick)

        # get all telemetry
        for mod in allModules:
            # merge all telemetry into the telemetry object
            telemetry.update(runSafe(mod.getTelemetry))

        # process all telemetry
        for mod in allModules:
            runSafe(mod.processTelemetry, telemetry)

        # get all commands
        commands = []
        for mod in allModules:
            # add all commands to the commands list
            commands.extend(runSafe(mod.getCommands))

        # process all commands
        for mod in allModules:
            runSafe(mod.processCommands, commands)

        # blink blue 
        ledOn = not ledOn
        if (ledOn):
            led.on()
        else:
            led.off()

except KeyboardInterrupt:
    raise
except Exception as e:
    import sys
    from serial_log import SerialLog
    import machine
    sys.print_exception(e)
    SerialLog.log("Fatal exception, will reboot in 10s")
    machine.sleep(10000)
    machine.reset()
