# mcp2200_hid

Control MCP2200 via HID interface

This is a little python script which allows to control MCP2200 via HID.  
It's coded without any special libraries just low level write/read on the `/dev/hidraw` file.  
It autodetects which of `/dev/hidrawX` files points to MCP2200 (only works with the first find).  
It locks the device file to serialize accesses.

## References

- [MCP2200 HID Interface Command Description](http://ww1.microchip.com/downloads/en/DeviceDoc/93066A.pdf)

## Examples

### Get help

```bash
# python3 mcp2200_hid.py --help
usage: mcp2200_hid.py [--help] [--verbose] [--set SET] [--clear CLEAR] [--status STATUS] [--io_bmap IO_BMAP] [--default_bmap DEFAULT_BMAP] [--status-all]

options:
  --help, -h            Show help
  --verbose, -v         Increase verbosity
  --set SET, -i SET     Set/switch on given GPIO port
  --clear CLEAR, -o CLEAR
                        Clear/switch off given GPIO port
  --status STATUS, -s STATUS
                        Status of given GPIO port
  --io_bmap IO_BMAP     Configure Input/Output for all GPIO ports (bitmap: 0=output, 1=input)
  --default_bmap DEFAULT_BMAP
                        Configure default value for all output GPIO ports (bitmap)
  --status-all, -S      Status of all GPIO ports (bitmap)
```

### Set GP0 to ON

```bash
# python3 mcp2200_hid.py -i 0

### Clear GP3 (set to OFF)

```bash
# python3 mcp2200_hid.py -o 3
```

### Get status of GP2

```bash
# python3 mcp2200_hid.py -s 2
```

### Get status of all GPs and also chip configuration

```bash
# python3 mcp2200_hid.py -S -v
```

## Usage with HomeAssistent example

I used it with Denkovi USB relay v2 board.  

Copied the files from this project to `/config/mcp2200_hid`:

```bash
homeassistant:/config/mcp2200_hid# ls /config/mcp2200_hid/
mcp2200_hid.py  switches.yaml  groups.yaml
```

Edited `/config/configuration.yaml` - added these lines:

```yaml
# Denkovi
group: !include mcp2200_hid/groups.yaml
switch: !include mcp2200_hid/switches.yaml
```

And restarted HomeAssistent (reloading yaml was insufficient).
