# svd-tools Repository

This repository groups a set of tools using svd features.

[SVD](https://arm-software.github.io/CMSIS_5/SVD/html/index.html): System View Description:
> The CMSIS System View Description format(CMSIS-SVD) formalizes the description of the system
> contained in Arm Cortex-M processor-based microcontrollers, in particular, the memory mapped
> registers of peripherals. The detail contained in system view descriptions is comparable to
> the data in device reference manuals. The information ranges from high level functional
> descriptions of a peripheral all the way down to the definition and purpose of an individual
> bit field in a memory mapped register.

## gdb-svd
It's a python module for gdb. This adds some gdb commands to:
- get information on peripherals | registers | fields
- get registers values | register fields
- set registers values | register fields
- dump registers values to file

### Dependencies
- [openocd](http://openocd.org/) or other
- [gdb](https://www.gnu.org/software/gdb/)
- [cmsis-svd](https://pypi.org/project/cmsis-svd/) python: cmsis-svd parser
- [terminaltables](https://pypi.org/project/terminaltables/) python: terminaltables

> On microprocessor: I advise to use openocd, in order to access at physical memory
> without need to enable/disable MMU (thanks to openocd with `mdw phys`
> option).

### How to use
These commands support tab completion to look-up file, peripherals, registers or fields
- Source the gdb-svd module in gdb interface:
```
(gdb) source ../svd_tools/gdb-svd.py
```
- Load svd file descriptor for your microcontroller (it might several seconds depending on the file size):
```
(gdb) svd ../cmsis-svd/data/STMicro/STM32F7x9.svd
Svd Loading ../cmsis-svd/data/STMicro/STM32F7x9.svd Done
```

- Help:
```
(gdb) help svd
The CMSIS SVD (System View Description) inspector commands
        This allows easy access to all peripheral registers supported by the system
        in the GDB debug environment

        svd [filename] load an SVD file and to create the command for inspecting
        that object

List of svd subcommands:
svd dump -- Get register(s) value(s): svd dump <filename> [peripheral]
svd get -- Get register(s) value(s): svd get [peripheral] [register]
svd info -- Info on Peripheral|register|field: svd info <peripheral> [register] [field]
svd set -- Set register value: svd set <peripheral> <register> [field] <value>
```
#### Info on peripheral register field

> **Note**:
> The last parameter can be or not a fullname, a filter is applied with your string.

 - Information on all ADC
```
(gdb) svd info ADC
+Peripherals--------+--------+-----------------------------+
| name | base       | access | description                 |
+------+------------+--------+-----------------------------+
| ADC1 | 0x40012000 | None   | Analog-to-digital converter |
| ADC2 | 0x40012100 | None   | Analog-to-digital converter |
| ADC3 | 0x40012200 | None   | Analog-to-digital converter |
+------+------------+--------+-----------------------------+
```
 - Information on all ADC1 registers beginning by S
```
(gdb) svd info ADC1 S
+Registers-----------+------------+-----------------------------+
| name  | address    | access     | description                 |
+-------+------------+------------+-----------------------------+
| SR    | 0x40012000 | read-write | status register             |
| SMPR1 | 0x4001200c | read-write | sample time register 1      |
| SMPR2 | 0x40012010 | read-write | sample time register 2      |
| SQR1  | 0x4001202c | read-write | regular sequence register 1 |
| SQR2  | 0x40012030 | read-write | regular sequence register 2 |
| SQR3  | 0x40012034 | read-write | regular sequence register 3 |
+-------+------------+------------+-----------------------------+
```
 - Information on all fields (peripheral: ADC1 register: CR1) beginning by J
```
(gdb) svd info ADC1 CR1 J
+Fields---+-----------+--------+---------------------------------------------+
| name    | [msb:lsb] | access | description                                 |
+---------+-----------+--------+---------------------------------------------+
| JAWDEN  | [22:22]   | None   | Analog watchdog enable on injected channels |
| JDISCEN | [12:12]   | None   | Discontinuous mode on injected channels     |
| JAUTO   | [10:10]   | None   | Automatic injected group conversion         |
| JEOCIE  | [7:7]     | None   | Interrupt enable for injected channels      |
+---------+-----------+--------+---------------------------------------------+
```
#### Get value
 - Get all registers of WWDG
```
(gdb) svd get WWDG
+Registers----------+------------+----------------------------------------------------------+
| name | address    | value      | fields                                                   |
+------+------------+------------+----------------------------------------------------------+
| CR   | 0x40002c00 | 0x0000007f | WDGA[7:7]=0x0 T[6:0]=0x7f                                |
| CFR  | 0x40002c04 | 0x0000007f | EWI[9:9]=0x0 WDGTB1[8:8]=0x0 WDGTB0[7:7]=0x0 W[6:0]=0x7f |
| SR   | 0x40002c08 | 0x00000000 | EWIF[0:0]=0x0                                            |
+------+------------+------------+----------------------------------------------------------+
```
 - Get fields of RCC AHB3ENR
 ```
(gdb) svd get RCC AHB3ENR
+Registers+------------+------------+--------------------------------+
| name    | address    | value      | fields                         |
+---------+------------+------------+--------------------------------+
| AHB3ENR | 0x40023838 | 0x00000000 | FMCEN[0:0]=0x0 QSPIEN[1:1]=0x1 |
+---------+------------+------------+--------------------------------+
```
#### Set value
- Set register value
```
(gdb) svd set RCC AHB3ENR 0x0
```
- Set field of
```
(gdb) svd set RCC AHB3ENR QSPIEN 0x1
```
#### Dump value in file
 - Dump value of all registers to file
```
(gdb) svd dump <filename>
Print to file: <filename>
```
 - Dump value of ADC1 to file
```
(gdb) svd dump <filename> ADC1
Print to file: <filename>
```
## Authors
Ludovic Barre 1udovic.6arre@gmail.com

## License
This project is licensed under the GPL V2 License - see the [LICENSE.md](LICENSE.md) file for details
