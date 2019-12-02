#!/usr/bin/env python
#
# Copyright 2019 Ludovic Barre <1udovic.6arre@gmail.com>
#
# This file is part of svd-tools.
#
# svd-tools is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# svd-tools is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with svd-tools.  If not, see <https://www.gnu.org/licenses/>.

import gdb
from terminaltables import AsciiTable
from cmsis_svd.parser import SVDParser
from textwrap import wrap

class GdbSvd(gdb.Command):
        """The CMSIS SVD (System View Description) inspector commands

        This allows easy access to all peripheral registers supported by the system
        in the GDB debug environment

        svd [filename] load an SVD file and to create the command for inspecting
        that object
        """
        def __init__(self):
                gdb.Command.__init__(self, "svd", gdb.COMMAND_DATA, gdb.COMPLETE_FILENAME, prefix = True)

        def invoke(self, arg, from_tty):
                try:
                        argv = gdb.string_to_argv(arg)                
                        if len(argv) != 1:
                                raise Exception("Invalide parameter")

                        pathfile = argv[0]
                        gdb.write("Svd Loading {} ".format(pathfile))
                        parser = SVDParser.for_xml_file(pathfile)
                        device = parser.get_device()
                        peripherals = dict((peripheral.name,peripheral) for peripheral in device.peripherals)
                        GdbSvdGetCmd(device, peripherals)
                        GdbSvdSetCmd(device, peripherals)
                        GdbSvdInfoCmd(device, peripherals)

                except Exception as inst:
                        gdb.write("\n{}\n".format(inst))
                        gdb.execute("help svd")
                except IOError:
                        gdb.write("\nFailed to load SVD file\n")
                else:
                        gdb.write("Done\n")

if __name__ == "__main__":
        GdbSvd()

class GdbSvdCmd(gdb.Command):
        def __init__(self, device, peripherals):
                self.device = device
                self.peripherals = peripherals
                self.column_with = 100

        def complete(self, text, word):
                args = str(text).split(" ")
                nb_args = len(args)

                if nb_args == 1:
                        filt = filter(lambda x: x.upper().startswith(args[0].upper()), self.peripherals)
                        return filt
                
                periph_name = args[0].upper()
                periph = self.peripherals[periph_name]
                reg_names = [reg.name for reg in periph.registers]

                if nb_args == 2 and reg_names:
                        filt = filter(lambda x: x.upper().startswith(args[1].upper()), reg_names)
                        return filt

                reg_name =  args[1].upper()
                reg = [r for r in periph.registers if r.name == reg_name][0]
                field_names = [field.name for field in reg.fields]

                if nb_args == 3 and field_names:
                        filt = filter(lambda x: x.upper().startswith(args[2].upper()), field_names)
                        return filt

                return gdb.COMPLETE_NONE

        def get_registers_val(self, peripheral, registers):
                registers_val = []

                for reg in registers:
                        addr = peripheral.base_address + reg.address_offset
                        val = self.read(peripheral, reg)
                        if val is None:
                            fval = val
                            val = reg.access
                        else:
                            fval = self.get_fields_val(reg.fields, val)
                            val = "0x{:08x}".format(val)

                        addr = "0x{:08x}".format(addr)
                        registers_val += [{"name": reg.name,
                                           "addr": addr,
                                           "value": val,
                                           "fields": fval}]

                return registers_val

        def get_fields_val(self, fields, reg_values):
                fields_val = []

                for f in fields:
                        lsb = f.bit_offset
                        msb = f.bit_offset + f.bit_width - 1
                        fname = "{}[{}:{}]".format(f.name, msb, lsb)
                        fieldval = (reg_values >> lsb) & ((1 << f.bit_width) - 1)
                        fields_val += [{"name": fname, "value": fieldval}]
            
                return fields_val

        def print_desc(self, peripherals, registers = None, fields = None):
                table_show = []
              
                if fields is not None:
                    desc_title = "Fields"
                    table_show.append(["name", "[msb:lsb]", "access", "description"])
                    for f in fields:
                        mlsb = "[{}:{}]".format(f.bit_offset, f.bit_offset + f.bit_width - 1)
                        desc = '\n'.join(wrap(f.description, self.column_with))
                        table_show.append([f.name, mlsb, f.access, desc])
                elif registers is not None:
                    desc_title = "Registers"
                    table_show.append(["name", "address", "access", "description"])
                    for r in registers:
                        addr = r.parent.base_address + r.address_offset
                        desc = '\n'.join(wrap(r.description, self.column_with))
                        table_show.append([r.name, "{:#x}".format(addr), r.access, desc])
                elif peripherals is not None:
                    desc_title = "Peripherals"
                    table_show.append(["name", "base", "access", "description"])
                    for p in peripherals:
                        desc = '\n'.join(wrap(p.description, self.column_with))
                        table_show.append([p.name, "{:#x}".format(p.base_address), p.access, desc])

                desc_table = AsciiTable(table_show, title = desc_title)
                gdb.write("{}\n".format(desc_table.table))

        def print_registers(self, peripheral, registers):
                regs_table = []
                reg_val = []
                regs_table.append(["name", "address", "value", "fields"])

                reg_val += self.get_registers_val(peripheral, registers)
                
                for r in reg_val:
                    f_str = []
                    fields = r["fields"]
                    if fields is not None:
                        for f in fields:
                            if f["value"] > 0:
                                f_str.append("\033[94m{name}={value:#x}\033[0m".format(**f))
                            else:
                                f_str.append("{name}={value:#x}".format(**f))
                    
                    f_str = '\n'.join(wrap(" ".join(f_str), self.column_with))                  
                    regs_table.append([r["name"], r["addr"], r["value"], f_str])

                rval_table = AsciiTable(regs_table, title="Registers")
                
                gdb.write("{}\n".format(rval_table.table))


        def set_register(self, peripheral, register, value, field = None):
                val = value
                if field is not None:
                        max_val = ((1 << field.bit_width) - 1)
                        if value > max_val:
                                raise Exception("Invalid value, > max of field")

                        mask = max_val << field.bit_offset

                        #read register value with gdb
                        val = self.read(peripheral, register)
                        if val is None:
                                raise Exception("Register not readable")

                        val &= ~mask
                        val |= value << field.bit_offset

                # write val to target
                self.write(peripheral, register, val)

        def read(self, peripheral, register):
                """ Read register and return an integer
                """
                #access could be not defined for a register
                if register.access in [None, "read-only", "read-write", "read-writeOnce"]:
                        addr = peripheral.base_address + register.address_offset
                        cmd = "monitor mdw phys {:#x}".format(addr)
                        return int(gdb.execute(cmd, False, True).split(': ')[1], 16)
                else:
                        return None

        def write(self, peripheral, register, val):
                """ Write data to memory
                """
                if register.access in [None, "write-only", "read-write", "writeOnce", "read-writeOnce"]:
                        addr = peripheral.base_address + register.address_offset
                        cmd = "monitor mww phys {:#x} {:#x}".format(addr, val)
                        gdb.execute(cmd, False, True)
                else:
                        raise Exception("Register not writable")

# sub commands
class GdbSvdGetCmd(GdbSvdCmd):
        """Get register(s) value(s): svd get [peripheral] [register]
        """
        def __init__(self, device, peripherals):
                GdbSvdCmd.__init__(self, device, peripherals)
                gdb.Command.__init__(self, "svd get", gdb.COMMAND_DATA)

        def complete(self, text, word):
                args = str(text).split(" ")
                if len(args) > 2:
                        return gdb.COMPLETE_NONE

                return GdbSvdCmd.complete(self, text, word)

        def invoke(self, arg, from_tty):
                args = str(arg).split(" ")
                if len(args) > 2:
                        gdb.write("Invalide parameter\n")
                        gdb.execute("help svd get")
                        return

                try:
                        periph_name = args[0].upper()
                        periph = self.peripherals[periph_name]
                except:
                        gdb.write("Invalid peripheral name\n")
                        GdbSvdCmd.print_desc(self, self.device.peripherals, None, None)
                        return
                
                try:            
                        regs = periph.registers

                        if len(args) == 2:
                                reg_name = args[1].upper()
                                regs = [[r for r in regs if r.name == reg_name][0]]

                        GdbSvdCmd.print_registers(self, periph, regs)

                except Exception as inst:
                        gdb.write("{}\n".format(inst))
                except:
                        gdb.write("Error cannot get the value\n")

class GdbSvdSetCmd(GdbSvdCmd):
        """Set register value: svd set <peripheral> <register> [field] <value>
        """
        def __init__(self, device, peripherals):
                GdbSvdCmd.__init__(self, device, peripherals)
                gdb.Command.__init__(self, "svd set", gdb.COMMAND_DATA)

        def complete(self, text, word):
                args = str(text).split(" ")
                if len(args) > 3:
                        return gdb.COMPLETE_NONE

                return GdbSvdCmd.complete(self, text, word)
        
        def invoke(self, arg, from_tty):
                args = str(arg).split(" ")
    
                try:
                        periph_name = args[0].upper()
                        periph = self.peripherals[periph_name]
                except:
                        gdb.write("Invalid peripheral name\n")
                        GdbSvdCmd.print_desc(self, self.device.peripherals, None, None)
                        return
                
                if len(args) < 3 or len(args) > 4:
                        gdb.write("Invalide parameter\n")
                        gdb.execute("help svd set")
                        return

                try:
                        reg_name =  args[1].upper()
                        reg = [r for r in periph.registers if r.name == reg_name][0]
                        field = None
                        if len(args) == 4:
                                field_name = args[2].upper()
                                field = [f for f in reg.fields if f.name == field_name][0]
                                value = int(args[3], 16)
                        else:
                                value = int(args[2], 16)
                        
                        GdbSvdCmd.set_register(self, periph, reg, value, field)

                except Exception as inst:
                        gdb.write("{}\n".format(inst))
                
                except:
                        gdb.write("Error cannot set the value\n")

class GdbSvdInfoCmd(GdbSvdCmd):
        """Info on Peripheral|register|field: svd info <peripheral> [register] [field]
        """
        def __init__(self, device, peripherals):
                GdbSvdCmd.__init__(self, device, peripherals)
                gdb.Command.__init__(self, "svd info", gdb.COMMAND_DATA)
        
        def complete(self, text, word):
                args = str(text).split(" ")
                if len(args) > 3:
                        return gdb.COMPLETE_NONE

                return GdbSvdCmd.complete(self, text, word)

        def invoke(self, arg, from_tty):
                args = str(arg).split(" ")

                if len(args) < 1 or len(args) > 3:
                        gdb.write("Invalide parameter\n")
                        gdb.execute("help svd info")
                        return
                
                try:
                        periph_name = args[0].upper()
                        periphs = list(filter(lambda x: x.name.startswith(periph_name), self.device.peripherals))
                        regs = fields = None

                        if len(args) >= 2:
                            per = [ per for per in periphs if per.name == periph_name ][0]
                            reg_name =  args[1].upper()
                            regs = list(filter(lambda x: x.name.startswith(reg_name), per.registers))

                        if len(args) >= 3:
                            reg = [ reg for reg in regs if reg.name == reg_name ][0]
                            field_name = args[2].upper()
                            fields = list(filter(lambda x: x.name.startswith(field_name), reg.fields))

                        GdbSvdCmd.print_desc(self, periphs, regs, fields)

                except:
                        gdb.write("Error cannot get info\n")

