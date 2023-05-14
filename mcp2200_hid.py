import os

hidraw_sys = "/sys/class/hidraw"
hidraw_path = ""
verbose = 0

# Detect which /dev/hidrawX goes to MCP2200
for filename in os.listdir(hidraw_sys):
    # Check if the file is a symlink
    if os.path.islink(os.path.join(hidraw_sys, filename)):
        symlink_target = os.readlink(os.path.join(hidraw_sys, filename))
        if '04D8:00DF' in symlink_target:
            hidraw_path = f"/dev/{filename}"
            if verbose:
                print(f"Detected MCP2200: {hidraw_path}")

if hidraw_path == "": exit(1)

def write_read(hidraw_file, write_content, read_len=0):
    # Write the data to the device
    hidraw_file.write(write_content)
    if read_len==0: return []
    # Move the file pointer back to the beginning
    hidraw_file.seek(0)
    # Read read_len bytes from the device
    return hidraw_file.read(read_len)

def mcp2200_read_bmap(hidraw_file):
    # Create a bytes object to write
    READ_ALL = b'\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    result = write_read(hidraw_file, READ_ALL, 16)
    if len(result)!=16 or result[0]!=READ_ALL[0]:
        print("READ_ALL failed")
        return -1
    else:
        if verbose:
            print(f"IO_bmap: {result[4]:08b}")
            print(f"IO_Port_Val_bmap: {result[10]:08b}")
        return int(result[10])

def mcp2200_set_clear_bits(hidraw_file, set_bitmap, clear_bitmap):
    SET_CLEAR_OUTPUTS = bytearray([0x08,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00])
    SET_CLEAR_OUTPUTS[11] = set_bitmap
    SET_CLEAR_OUTPUTS[12] = clear_bitmap
    result = write_read(hidraw_file, SET_CLEAR_OUTPUTS)

with open(hidraw_path, "wb+") as hidraw_file:
    mcp2200_set_clear_bits(hidraw_file, 7, 1)
    print(f"{mcp2200_read_bmap(hidraw_file):08b}")
