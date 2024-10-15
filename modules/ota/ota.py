"""
Update firmware written in MicroPython over the air.

MIT license; Copyright (c) 2021 Martin Komon
"""

import gc
import uos
from micropython import const
from serial_log import SerialLog
import ujson

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
    """
    Delete a directory recursively, removing files from all sub-directories before
    finally removing empty directory. Works for both files and directories.

    No limit to the depth of recursion, will fail on too deep dir structures.
    """
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
    """
    Check available free space in filesystem and return True/False if there is enough free space
    or not.

    min_free_space is measured in kB
    """
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
    SerialLog.log("Forcing update")
    if check_for_updates(False):
        install_new_firmware()
    else:
        return "Update failed"
    return "Update forced"

def check_for_updates(version_check=True) -> bool:
    """
    Check for available updates, download new firmware if available and return True/False whether
    it's ready to be installed, there is enough free space and file hash matches.
    """
    gc.collect()

    try:
        import requests
    except ImportError:
        SerialLog.log('requests module not found, attempting to install from online sources')
        import mip
        mip.install('requests')
        import requests

    if not load_ota_cfg():
        return False

    if not ota_config['url'].endswith('/'):
        ota_config['url'] = ota_config['url'] + '/'

    latestUrl = ota_config['url']  + shortName + '/latest'
    SerialLog.log("Checking for updates on: ", latestUrl)
    response = requests.get(latestUrl)
    SerialLog.log("Update Response:", response.status_code, response.text)
    if (response.status_code != 200):
        SerialLog.log("Unable to check for updates, bad response from server. Giving up!")
        return False

    remote_version, remote_filename, *optional = response.text.strip().rstrip(';').split(';')
    min_free_space, *remote_hash = optional if optional else (0, '')
    min_free_space = int(min_free_space)
    remote_hash = remote_hash[0] if remote_hash else ''

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

        downloadUrl = ota_config['url']  + shortName + '/' + remote_filename
        SerialLog.log("Fetching update on: ", downloadUrl)
        if requests == None:
            SerialLog.log("Warning: Requests is None")
        try:
            response = requests.get(downloadUrl)
            SerialLog.log("Download Response:", response.status_code)
            with open(ota_config['tmp_filename'], 'wb') as f:
                while True:
                    chunk = response.raw.read(512)
                    if not chunk:
                        break
                    f.write(chunk)
            SerialLog.log("Downloaded update to flash")
            return True
        except Exception as e:
            SerialLog.log("Error downloading update: ", e)
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

    try:
        import tarfile
    except ImportError:
        SerialLog.log('tarfile module not found, attempting to install from online sources')
        import mip
        mip.install('tarfile')
        import tarfile

    with open(ota_config['tmp_filename'], 'rb') as f1:
        with (deflate.DeflateIO(f1, deflate.GZIP)) as f2:
            f3 = tarfile.TarFile(fileobj=f2)
            for _file in f3:
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
                file_obj = f3.extractfile(_file)
                with open(file_name, 'wb') as f_out:
                    written_bytes = 0
                    while True:
                        buf = file_obj.read(512)
                        if not buf:
                            break
                        written_bytes += f_out.write(buf)
                    SerialLog.log('file %s (%s B) written to flash' % (file_name, written_bytes))

    uos.remove(ota_config['tmp_filename'])
    if load_ota_cfg():
        for filename in ota_config['delete']:
            recursive_delete(filename)
