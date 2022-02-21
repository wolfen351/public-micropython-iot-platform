echo "Switching board to REPL mode.."
ampy --port /dev/ttyACM0 get lastedit.dat > /dev/null 2>&1

echo "Sending program to wipe all files.."

{ cat << EOD
import os

def rm(d):  # Remove file or tree
    try:
        if os.stat(d)[0] & 0x4000:  # Dir
            for f in os.ilistdir(d):
                if f[0] not in ('.', '..'):
                    rm("/".join((d, f[0])))  # File or Dir
            print("Removing directory:", d)
            os.rmdir(d)
        else:  # File
            print("Removing file:", d)
            os.remove(d)
    except:
        print("rm of '%s' failed" % d)

print("Erasing..")
for f in os.listdir():
    print(f)
    rm(f)
EOD
} | picocom -rx 1000 --omap lfcrlf -b 115200 /dev/ttyACM0