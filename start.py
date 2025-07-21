# Main 

# This file is executed on every boot (including wake-boot from deepsleep)

from serial_log import SerialLog
SerialLog.log("Boot starting...")

def runSafe(cmd, p1 = None):
    try:
        if (p1 != None):
            return cmd(p1)
        return cmd()
    except KeyboardInterrupt:
        raise
    except Exception as e:
        SerialLog.log("Exception", str(e))
        sys.print_exception(e)
        gc.collect()

try:
    # Turn on the LED to show we are alive
    from board_system.cpu_hardware import CpuHardware
    CpuHardware.StatusLedOn()

    # set the CPU to max speed
    CpuHardware.SetCpuMaxSpeed()    

    # Connect to wifi and web and check for updates
    from modules.wifi.wifi import WifiHandler
    wifi = WifiHandler()
    wifi.preStart()

    # some storage
    ledOn = True
    
    telemetry = dict()
    allModules = [ wifi ]

    # Get the list of modules to load
    from serial_log import SerialLog
    SerialLog.log("Loading modules..")
    import ujson
    f = open("profile.json",'r')
    settings_string=f.read()
    f.close()
    settings_dict = ujson.loads(settings_string)

    # load up all other modules
    import sys
    import gc

    SerialLog.log("Ram Total:", gc.mem_alloc() + gc.mem_free())
    SerialLog.log("Ram Free:", gc.mem_free())
    SerialLog.log("Ram Allocated:", gc.mem_alloc(), "(", int(gc.mem_alloc()*100/(gc.mem_alloc() + gc.mem_free())), "%)")

    # start Web processing
    from modules.web.web_processor import WebProcessor
    web = WebProcessor()
    allModules.append(web)

    for modname in settings_dict['activeModules']:
        try:
            ramfree = gc.mem_free()
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
                pass # preloaded
            elif modname == 'ota':
                pass # special and different
            elif modname == 'builtin_button':
                from modules.builtin_button.builtin_button_control import BuiltinButtonControl
                allModules.append(BuiltinButtonControl())
            elif modname == 'dht11':
                from modules.dht11.dht11 import Dht11Monitor
                allModules.append(Dht11Monitor())
            elif modname == 'dht22':
                from modules.dht22.dht22 import Dht22Monitor
                allModules.append(Dht22Monitor())
            elif modname == 'ds18b20temp':
                from modules.ds18b20temp.ds18b20_temp import DS18B20Temp
                allModules.append(DS18B20Temp())
            elif modname == 'temphistory':
                from modules.temphistory.temphistory import TempHistory
                allModules.append(TempHistory())
            elif modname == 'ntp':
                from modules.ntp.ntp import NtpSync
                allModules.append(NtpSync())
            elif modname == 'lilygo_battery':
                from modules.lilygo_battery.lilygo_battery import LilyGoBattery
                allModules.append(LilyGoBattery())
            elif modname == 'four_relay':
                from modules.four_relay.four_relay import FourRelay
                allModules.append(FourRelay())
            elif modname == 'four_button':
                from modules.four_button.four_button_control import FourButton
                allModules.append(FourButton())
            elif modname == "dion_hallway_lights":
                from modules.dion_hallway_lights.dion_hallway_lights import DionHallwayLightsControl
                allModules.append(DionHallwayLightsControl())
            elif modname == "pir":
                from modules.pir.pirDetect import PIRDetect
                allModules.append(PIRDetect())
            elif modname == "ac_remote":
                from modules.ac_remote.ac_remote import AcRemote
                allModules.append(AcRemote())
            elif modname == "binary_clock":
                from modules.binary_clock.binary_clock import BinaryClock
                allModules.append(BinaryClock())
            elif modname == "mosfet":
                from modules.mosfet.mosfet_control import MosfetControl
                allModules.append(MosfetControl())            
            elif modname == "gps":
                from modules.gps.gps_control import GPSControl
                allModules.append(GPSControl())    
            elif modname == "ledstrip":
                from modules.ledstrip.ledstrip_control import LedStripControl
                allModules.append(LedStripControl())   
            elif modname == "us_range":
                from modules.us_range.us_range_sensor import USRangeSensor
                allModules.append(USRangeSensor())
            elif modname == "garage_door_closer":
                from modules.garage_door_closer.garage_door_control import GarageDoorControl
                allModules.append(GarageDoorControl())
            elif modname == "touchscreen":
                from modules.touchscreen.touchscreen import TouchScreen
                allModules.append(TouchScreen())
            elif modname == "wdt":
                from modules.wdt.wdt import WDTControl
                allModules.append(WDTControl())
            elif modname == "relay":
                from modules.relay.relay import Relay
                allModules.append(Relay())
            elif modname == "sim800l":
                from modules.sim800l.sim800l import SIM800LControl
                allModules.append(SIM800LControl())
            elif modname == "schedule":
                from modules.schedule.schedule import Schedule
                allModules.append(Schedule())
            elif modname == "relayx2":
                from modules.relayx2.relayx2 import Relayx2
                allModules.append(Relayx2())
            elif modname == "worldclock":
                from modules.worldclock.world_clock import WorldClock
                allModules.append(WorldClock())
            else:
                SerialLog.log("Error: Unsupported Module! ", modname);
            SerialLog.log("Completed loading ", modname, " Ram Used:", ramfree - gc.mem_free())
            SerialLog.log("Ram Allocated:", gc.mem_alloc(), "(", int(gc.mem_alloc()*100/(gc.mem_alloc() + gc.mem_free())), "%)")
        except ImportError as e:
            SerialLog.log("Error: Module not found! ", modname);
            SerialLog.log("Error: ", e);

    gc.collect()
    SerialLog.log("All code compiled. Ram Free:", gc.mem_free())
   
    # start all the modules up
    routes = {}
    panels = {}
    for mod in allModules:
        SerialLog.log("Starting: ", str(type(mod)).replace("<class '", "").replace("'>", ""))
        runSafe(mod.start)
        routes.update(runSafe(mod.getRoutes))
        panels.update(runSafe(mod.getIndexFileName))

    SerialLog.log("Setting up Web Routes:")
    web.setRoutes(routes)
    web.setTelemetry(telemetry)
    web.setPanels(panels)

    # Switch off the led before the loop, it will flash if it needs to
    CpuHardware.StatusLedOff()

    gc.collect()
    SerialLog.log("All modules loaded. Ram Free:", gc.mem_free())

    SerialLog.log("Main loop starting...")
    while True:

        # tick all modules
        for mod in allModules:
            runSafe(mod.tick)

        # get all telemetry
        for mod in allModules:
            # merge all telemetry into the telemetry object
            newTel = runSafe(mod.getTelemetry)
            runSafe(telemetry.update, newTel)

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
                    CpuHardware.StatusLedOn()
            else:
                CpuHardware.StatusLedOff()
        else:
            if (ledOn):
                CpuHardware.StatusLedOff()


except KeyboardInterrupt:
    raise
except Exception as e:
    from sys import print_exception
    from time import sleep
    from serial_log import SerialLog
    print_exception(e)
    SerialLog.log("Fatal exception, will reboot in 10s")
    for y in range(0, 100): # lots of little sleeps, hopefully means repl can connect
        sleep(0.1)
    from machine import reset
    reset()

