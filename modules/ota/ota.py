import gc
import uos
from micropython import const
from serial_log import SerialLog
import ujson
import network

GZDICT_SZ = const(31)
ota_config = {}
shortName = ""

def load_ota_cfg():
    try:
        f = open("profile.json",'r')
        settings_string=f.read()
        f.close()
        basicSettings = ujson.loads(settings_string)
        global shortName
        global ota_config
        ota_config.update(basicSettings['ota'])
        shortName = basicSettings["shortName"]
        return True
    except OSError:
        SerialLog.log('Cannot find ota config file in profile.json. OTA is disabled.')
        return False

def recursive_delete(path: str):
    # prevent deleting the whole filesystem and skip non-existent files
    if not path or not uos.stat(path):
        return

    path = path[:-1] if path.endswith('/') else path

    try:
        children = uos.listdir(path)
        # no exception thrown, this is a directory
        for child in children:
            recursive_delete(path + '/' + child)
    except OSError:
        uos.remove(path)
        return
    uos.rmdir(path)

def check_free_space(min_free_space: int) -> bool:
    if not any([isinstance(min_free_space, int), isinstance(min_free_space, float)]):
        SerialLog.log('min_free_space must be an int or float')
        return False

    fs_stat = uos.statvfs('/')
    block_sz = fs_stat[0]
    free_blocks = fs_stat[3]
    free_kb = block_sz * free_blocks / 1024
    SerialLog.log('Update size: %s kB' % min_free_space)
    SerialLog.log('Free disk space: %s kB' % free_kb)
    return free_kb >= min_free_space

def local_version():
    try:
        with open('version', 'r') as f:
            local_version = f.read().strip()
            return local_version
    except OSError:
            return "unknown!"
    
def force_update():
    SerialLog.purge()
    SerialLog.log("Forcing update")
    if check_for_updates(False):
        install_new_firmware()
    else:
        return "Update failed"
    return "Update forced"

def check_for_update_file() -> bool:
    try:
        if uos.stat(ota_config['tmp_filename']):
            SerialLog.log("Previous firmware found")
            # make a new file next to tmp_filename with a .1 extension to indicate that we are attempting to install it
            # if the file exists with the .1 extension, then we delete both files
            # this allows us to recover from a failed install
            try:
                uos.stat(ota_config['tmp_filename'] + ".1")
                SerialLog.log("Previous attempt to install firmware file failed. Deleting it")
                uos.remove(ota_config['tmp_filename'])
                uos.remove(ota_config['tmp_filename'] + ".1")
                return False
            except OSError:
                SerialLog.log("This is the first attempt to install")

            # if the file is too small delete it
            if uos.stat(ota_config['tmp_filename'])[6] < 10000:
                SerialLog.log("Firmware file is too small, deleting it")
                uos.remove(ota_config['tmp_filename'])
                return False
            
            # create a blank file with .1 extension to show we are attempting to install the firmware
            with open(ota_config['tmp_filename'] + ".1", 'w') as f:
                f.write("Attempt")
            
            return True
    except OSError as e:
        SerialLog.log("No previous firmware file found")
    return False

def check_for_updates(version_check=True) -> bool:
    gc.collect()

    if not load_ota_cfg():
        return False

    # If we have previously downloaded firmware, we should install it
    if (check_for_update_file()):
        return True

    try:
        import requests
    except ImportError:
        SerialLog.log('requests module not found, attempting to install from online sources')
        import mip
        mip.install('requests')


    if not ota_config['url'].endswith('/'):
        ota_config['url'] = ota_config['url'] + '/'

    latestUrl = ota_config['url']  + shortName + '/latest'
    SerialLog.log("Checking for updates on: ", latestUrl)

    for attempt in range(20):
        try:
            response = requests.get(latestUrl)
        except Exception as e:
            SerialLog.log("Attempt", attempt + 1, "failed with error: ", e, ", retrying...")
            continue

        SerialLog.log("Update Response:", response.status_code, response.text)
        if response.status_code == 200:
            break

        SerialLog.log("Attempt", attempt + 1, "failed, retrying...")
        response.close()
    else:
        SerialLog.log("Unable to check for updates, bad response from server. Giving up!")
        return False

    remote_version, remote_filename, *optional = response.text.strip().rstrip(';').split(';')
    min_free_space, *remote_hash = optional if optional else (0, '')
    min_free_space = int(min_free_space)
    remote_hash = remote_hash[0] if remote_hash else ''
    response.close()

    try:
        with open('version', 'r') as f:
            local_version = f.read().strip()
    except OSError:
        if version_check:
            SerialLog.log('local version information missing, cannot proceed')
            return False
        SerialLog.log('local version information missing, ignoring it')

    SerialLog.log("Local version:  ", local_version)
    SerialLog.log("Remote version: ", remote_version)
    if not version_check or remote_version > local_version:
        SerialLog.log('new version %s is available' % remote_version)
        if not check_free_space(min_free_space):
            SerialLog.log('Error! Not enough free space for the new firmware, staying on this version')
            return False

        gc.collect()
        downloadUrl = ota_config['url']  + shortName + '/' + remote_filename
        SerialLog.log("Fetching update on: ", downloadUrl)
        for attempt in range(20):
            try:
                response = requests.get(downloadUrl)
                SerialLog.log("Download Response:", response.status_code)
                if response.status_code == 200:
                    with open(ota_config['tmp_filename'], 'wb') as f:
                        while True:
                            chunk = response.raw.read(512)
                            if not chunk:
                                break
                            f.write(chunk)
                    SerialLog.log("Downloaded update to flash")
                    return True
                else:
                    SerialLog.log("Attempt", attempt + 1, "failed with status code ", response.status_code, "retrying...")
            except Exception as e:
                SerialLog.log("Attempt", attempt + 1, "failed with error: ", str(e), "retrying...")
                gc.collect()
        SerialLog.log("Error! Unable to download update after multiple attempts")
        return False
    else:
        SerialLog.log("Up to date!")
    return False

def install_new_firmware(quiet=False):

    gc.collect()

    if not load_ota_cfg():
        return

    try:
        uos.stat(ota_config['tmp_filename'])
    except OSError:
        SerialLog.log('No new firmware file found in flash.')
        return

        
    try:
        import deflate
    except ImportError:
        SerialLog.log('deflate module not found, attempting to install from online sources')
        import mip
        mip.install('deflate')
        import deflate
        del mip

    try:
        import tarfile
    except ImportError:
        SerialLog.log('tarfile module not found, attempting to install from online sources')
        import mip
        mip.install('tarfile')
        import tarfile
        del mip

    # take drastic measures to ensure that enough ram is free
    if (gc.mem_free() < 40000):
        SerialLog.purge()
        sta_if = network.WLAN(network.STA_IF)
        sta_if.active(False)
        del sta_if    
        gc.collect()
    SerialLog.log("Free memory: ", gc.mem_free())
    

    try:
        with open(ota_config['tmp_filename'], 'rb') as f1:
            with (deflate.DeflateIO(f1, deflate.GZIP)) as f2:
                tar = tarfile.TarFile(fileobj=f2)
                for _file in tar:
                    file_name = _file.name
                    if file_name in ota_config['excluded_files']:
                        item_type = 'directory' if file_name.endswith('/') else 'file'
                        SerialLog.log('Skipping excluded %s %s' % (item_type, file_name))
                        continue

                    if file_name.endswith('/'):  # is a directory
                        try:
                            SerialLog.log('creating directory %s ... ' % file_name)
                            uos.mkdir(file_name[:-1])  # without trailing slash or fail with errno 2
                            SerialLog.log('ok')
                        except OSError as e:
                            if e.errno == 17:
                                SerialLog.log('already exists')
                            else:
                                raise e
                        continue
                    file_obj = tar.extractfile(_file)
                    with open(file_name, 'wb') as f_out:
                        written_bytes = 0
                        while True:
                            buf = file_obj.read(512)
                            if not buf:
                                break
                            written_bytes += f_out.write(buf)
                        SerialLog.log('file %s (%s B) written to flash' % (file_name, written_bytes))
    except EOFError as e:
        SerialLog.log("EOF Error: ", e)

    uos.remove(ota_config['tmp_filename'])
    if load_ota_cfg():
        for filename in ota_config['delete']:
            recursive_delete(filename)
