import os
import fcntl
import argparse

hidraw_sys = "/sys/class/hidraw"
verbose = 0

def detect_mcp2200():
    # Detect which /dev/hidrawX goes to MCP2200
    for filename in os.listdir(hidraw_sys):
        # Check if the file is a symlink
        if os.path.islink(os.path.join(hidraw_sys, filename)):
            symlink_target = os.readlink(os.path.join(hidraw_sys, filename))
            if '04D8:00DF' in symlink_target:
                hidraw_path = f"/dev/{filename}"
                if verbose:
                    print(f"Detected MCP2200: {hidraw_path}")
                return hidraw_path
    return None

def write_read(hidraw_file, write_content, read_len=0):
    # Write the data to the device
    hidraw_file.write(write_content)
    # Return if no read is expected
    if read_len==0: return []
    # Move the file pointer back to the beginning
    hidraw_file.seek(0)
    # Read read_len bytes from the device
    return hidraw_file.read(read_len)

def mcp2200_read_all(hidraw_file):
    # Create a bytes object to write
    READ_ALL = bytearray([0x80,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00])
    result = write_read(hidraw_file, READ_ALL, 16)
    if len(result)!=16 or result[0]!=READ_ALL[0]:
        print("READ_ALL failed")
        return []
    return result

def mcp2200_read_bmap(hidraw_file):
    result = mcp2200_read_all(hidraw_file)
    if len(result):
        if verbose:
            print(f"IO_bmap: {result[4]:08b}")
            print(f"Config_Alt_Pins: {result[5]:08b}")
            print(f"IO_Default_Val_bmap: {result[6]:08b}")
            print(f"Config_Alt_Options: {result[7]:08b}")
            print(f"Baud_H: {result[8]}")
            print(f"Baud_L: {result[9]}")
            print(f"desired_baud_rate: {12000000 / ((int(result[8])<<8) + int(result[9]) + 1)}")
            print(f"IO_Port_Val_bmap: {result[10]:08b}")
        return int(result[10])
    return -1
    
def mcp2200_configure(hidraw_file, IO_bmap=-1, Config_Alt_Pins=-1, IO_Default_Val_Bmap=-1, Config_Alt_Options=-1):
    # First do READ_ALL
    result = mcp2200_read_all(hidraw_file)
    if len(result):
        # if READ_ALL work, copy all values and override some
        CONFIGURE = bytearray([0x10,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00])
        CONFIGURE[4] = result[4]
        if IO_bmap != -1:
            if verbose:
                print(f"Changing IO_bmap from {CONFIGURE[4]} to {IO_bmap}")
            CONFIGURE[4] = IO_bmap
        CONFIGURE[5] = result[5]
        if Config_Alt_Pins != -1:
            if verbose:
                print(f"Changing Config_Alt_Pins from {CONFIGURE[5]} to {Config_Alt_Pins}")
            CONFIGURE[5] = Config_Alt_Pins
        CONFIGURE[6] = result[6]
        if IO_Default_Val_Bmap != -1:
            if verbose:
                print(f"Changing IO_Default_Val_Bmap from {CONFIGURE[6]} to {IO_Default_Val_Bmap}")
            CONFIGURE[6] = IO_Default_Val_Bmap
        CONFIGURE[7] = result[7]
        if Config_Alt_Options != -1:
            if verbose:
                print(f"Changing Config_Alt_Options from {CONFIGURE[7]} to {Config_Alt_Options}")
            CONFIGURE[7] = Config_Alt_Options
        CONFIGURE[8] = result[8]
        CONFIGURE[9] = result[8]
        write_read(hidraw_file, CONFIGURE)

def mcp2200_set_clear_bits(hidraw_file, set_bitmap, clear_bitmap):
    SET_CLEAR_OUTPUTS = bytearray([0x08,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00])
    SET_CLEAR_OUTPUTS[11] = set_bitmap
    SET_CLEAR_OUTPUTS[12] = clear_bitmap
    write_read(hidraw_file, SET_CLEAR_OUTPUTS)

def on_off(bitmap, bit):
    return 'ON' if ((bitmap & (1<<bit)) != 0) else "OFF"

def main():
    parser = argparse.ArgumentParser(argument_default=argparse.SUPPRESS, conflict_handler='resolve')
    parser.add_argument(
        "--help", "-h", dest="Help", default=False, action="store_true", help="Show help"
    )
    parser.add_argument(
        "--verbose", "-v", dest="Verbose", default=False, action="store_true", help="Increase verbosity"
    )
    parser.add_argument(
        "--set", "-i", dest="Set", default=-1, type=int, action="store", help="Set/switch on given GPIO port"
    )   
    parser.add_argument(
        "--clear", "-o", dest="Clear", default=-1, type=int, action="store", help="Clear/switch off given GPIO port"
    )   
    parser.add_argument(
        "--status", "-s", dest="Status", default=-1, type=int, action="store", help="Status of given GPIO port"
    )   
    parser.add_argument(
        "--io_bmap", dest="IO_bmap", default=-1, type=int, action="store", help="Configure Input/Output for all GPIO ports (bitmap: 0=output, 1=input)"
    )   
    parser.add_argument(
        "--default_bmap", dest="Default_bmap", default=-1, type=int, action="store", help="Configure default value for all output GPIO ports (bitmap)"
    )   
    parser.add_argument(
        "--status-all", "-S", dest="All", default=None, action="store_true", help="Status of all GPIO ports (bitmap)"
    )   
    args = parser.parse_args()
    global verbose
    verbose = args.Verbose

    if (args.Help):
        parser.print_help()
        exit(0)

    hidraw_path = detect_mcp2200()
    if not hidraw_path:
        print("No MCP2200 connected? Try lsusb(1)")
        exit(0)

    with open(hidraw_path, "wb+") as hidraw_file:
        # Acquire a lock on the HID device file
        fcntl.flock(hidraw_file.fileno(), fcntl.LOCK_EX)
        try:
            # Perform read/write operations on the HID device
            if args.IO_bmap != -1:
                mcp2200_configure(hidraw_file, IO_bmap=args.IO_bmap)
            if args.Default_bmap != -1:
                mcp2200_configure(hidraw_file, IO_Default_Val_Bmap=args.Default_bmap)
            if args.Set != -1:
                mcp2200_set_clear_bits(hidraw_file, (1<<args.Set), 0)
            if args.Clear != -1:
                mcp2200_set_clear_bits(hidraw_file, 0, (1<<args.Clear))
            bitmap = mcp2200_read_bmap(hidraw_file)
            if args.All:
                print(f"{bitmap:08b}")
                if verbose:
                    for i in range(8):
                        print(f"GP{i}: {on_off(bitmap, i)}")
            if args.Status != -1:
                rettxt = on_off(bitmap, args.Status)
                print(f"{rettxt}")
                exit(int(rettxt == "ON"))

        finally:
            # Release the lock on the HID device file
            fcntl.flock(hidraw_file.fileno(), fcntl.LOCK_UN)    

if __name__ == "__main__":
    main()