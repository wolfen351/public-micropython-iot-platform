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
    led = Pin(3, Pin.OUT)
    led.on()

    # set the CPU to max speed
    from board_system.cpu_hardware import CpuHardware
    CpuHardware.SetCpuMaxSpeed()    

    # some storage
    ledOn = True
    telemetry = dict()

    # Import other modules needed
    from serial_log import SerialLog
    SerialLog.log("Loading modules..")
    allModules = [ ];

    # Get the list of modules to load
    import ujson
    f = open("profile.json",'r')
    settings_string=f.read()
    f.close()
    settings_dict = ujson.loads(settings_string)

    # Preload the web module, it is special
    from modules.web.web_processor import WebProcessor
    web = WebProcessor()
    allModules.append(web)

    # load up all other modules
    import sys
    import gc
    for modname in settings_dict['activeModules']:
        SerialLog.log("Loading module:", modname)
        if modname == 'basic':
            pass
        elif modname == 'mqtt':
            from modules.mqtt.mqtt_control import MqttControl
            allModules.append(MqttControl())
        elif modname == 'homeassistant':
            from modules.homeassistant.homeassistant_control import HomeAssistantControl
            allModules.append(HomeAssistantControl())
        elif modname == 'thingsboard':
            from modules.thingsboard.thingsboard_control import ThingsboardControl
            allModules.append(ThingsboardControl())
        elif modname == 'web':
            pass # preloaded
        elif modname == 'wifi':
            from modules.wifi.wifi import WifiHandler
            allModules.append(WifiHandler())
        elif modname == 'builtin_button':
            from modules.builtin_button.builtin_button_control import BuiltinButtonControl
            allModules.append(BuiltinButtonControl())
        elif modname == 'dht22':
            from modules.dht22.dht22 import Dht22Monitor
            allModules.append(Dht22Monitor())
        elif modname == 'ota':
            pass # used differently
        elif modname == 'ds18b20temp':
            from modules.ds18b20temp.ds18b20_temp import DS18B20Temp
            allModules.append(DS18B20Temp())
        elif modname == 'ntp':
            from modules.ntp.ntp import NtpSync
            allModules.append(NtpSync())
        else:
            SerialLog.log("Error: Unsupported Module! ", modname);
   
    # start all the modules up
    routes = {}
    panels = {}
    for mod in allModules:
        SerialLog.log("Starting: ", mod)
        runSafe(mod.start)
        routes.update(runSafe(mod.getRoutes))
        panels.update(runSafe(mod.getIndexFileName))

    web.setRoutes(routes)
    web.setTelemetry(telemetry)
    web.setPanels(panels)

    # Switch off the led before the loop, it will flash if it needs to
    led.off()
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
        if len(commands) > 0:
            SerialLog.log("Commands: ", commands)
            for mod in allModules:
                runSafe(mod.processCommands, commands)

        # blink blue 
        if (web.getLedEnabled()):
            ledOn = not ledOn
            if (ledOn):
                led.on()
            else:
                led.off()
        else:
            if (ledOn):
                led.off()

except KeyboardInterrupt:
    raise
except Exception as e:
    import sys
    from serial_log import SerialLog
    import machine
    sys.print_exception(e)
    SerialLog.log("Fatal exception, will reboot in 10s")
    for y in range(0, 100): # lots of little sleeps, hopefully means repl can connect
        machine.sleep(100)
    machine.reset()

