import ctypes
import argparse
import inspect
c_uint32 = ctypes.c_uint32

class PS_flavor3_Bics5(ctypes.LittleEndianStructure):
    _fields_ = [
            ("fmu", c_uint32,            2),
            ("plane", c_uint32,          1),
            ("fim", c_uint32,            2),
            ("diePageInBlk", c_uint32,   11),
            ("MB", c_uint32,             12),
            ("MD", c_uint32,             4),
        ]

class PS_flavor3_Bics6(ctypes.LittleEndianStructure):
    _fields_ = [
            ("fmu", c_uint32,            2),
            ("plane", c_uint32,          2),
            ("fim", c_uint32,            1),
            ("diePageInBlk", c_uint32,   13),
            ("MB", c_uint32,             10),
            ("MD", c_uint32,             4),
        ]

class vbaSlc_s_Bics6(ctypes.LittleEndianStructure):
    _fields_ = [
            ("fmu", c_uint32,            2),
            ("plane", c_uint32,          2),
            ("fim", c_uint32,            1),
            ("diePageInBlk", c_uint32,   13),
            ("block", c_uint32,          10),
            ("hFim", c_uint32,           1),
            ("dieInFim", c_uint32,       2),
            ("fim_high", c_uint32,       1),
        ]

class vbaTlc_s_Bics6(ctypes.LittleEndianStructure):
    _fields_ = [
            ("fmu", c_uint32,            2),
            ("plane", c_uint32,          2),
            ("fim", c_uint32,            1),
            ("diePageInBlk", c_uint32,   13),
            ("block", c_uint32,          10),
            ("hFim", c_uint32,           1),
            ("dieInFim", c_uint32,       2),
            ("fim_high", c_uint32,       1),
        ]

class vbaTlc_s_Bics8(ctypes.LittleEndianStructure):
    _fields_ = [
            ("fmu", c_uint32,            2),
            ("plane", c_uint32,          2),
            ("fim", c_uint32,            1),
            ("diePageInBlk", c_uint32,   12),
            ("block", c_uint32,          11),
            ("psId", c_uint32,           1),
            ("dieInFim", c_uint32,       3),
        ]

class flashAddressX3_t(ctypes.LittleEndianStructure):
    _fields_ = [
            ("fmu", c_uint32,            2),
            ("plane", c_uint32,          2),
            ("fim", c_uint32,            1),
            ("tlcpage", c_uint32,        2),
            ("stringNo", c_uint32,       3),
            ("wordLine", c_uint32,       8),
            ("phyBlock", c_uint32,       10),
            ("hFim", c_uint32,           1),
            ("dieInFim", c_uint32,       2),
            ("fim_high", c_uint32,       1),
        ]

class Flags(ctypes.Union):
    _fields_ = [("ps_bics5",  PS_flavor3_Bics5),
                ("ps_bics6",  PS_flavor3_Bics6),
                ("tlc_bics6", vbaTlc_s_Bics6),
                ("slc_bics6", vbaTlc_s_Bics6),
                ("tlc_bics8", vbaTlc_s_Bics8),
                ("flashAddressX3_t", flashAddressX3_t),
                ("asvba", c_uint32)]

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--reverse', type=str, required=False, help="Get VBA from block, dieInFim, page, fim, fmu, plane, psId")
    parser.add_argument('-v', '--vba', type=lambda x: int(x,0), required=False, help="input VBA address")
    varname,vartype = zip(*Flags._fields_[:-1])
    parser.add_argument('-t', '--type', type=str, required=True, help="Input support type : %s" % (list(varname)))
    parser.add_argument('-f', '--file', type=str, required=False, help="Input VBA List as txt file")
    args = parser.parse_args()
    
    if (args.file is not None): # print list
        with open(args.file,'r') as f:
            vbaes = f.readlines()
            flags = Flags()
            for vba in vbaes:
                _out = ''
                vba = int(vba.strip(),0)
                setattr(flags, "asvba", vba)
                vba_fields = getattr(flags, args.type)
                _out += 'VBA:0x%x ' % (vba)
                for i in inspect.getmembers(vba_fields):
                    # Ignores anything starting with underscore 
                    # (that is, private and protected attributes)
                    if not i[0].startswith('_'):
                        # Ignores methods
                        if not inspect.ismethod(i[1]):
                            #print("%-16s : %d" % (i[0],i[1]))
                            _out += '%s:%d ' % (i[0],i[1])
                print(_out)
            exit(0)
    else: # print only one
        flags = Flags()
        if (args.reverse is not None):
            _arguements = args.reverse.split()
            vba_fields = getattr(flags, args.type)

            type_idx = 0
            for i in inspect.getmembers(vba_fields):
                # Ignores anything starting with underscore 
                # (that is, private and protected attributes)
                if not i[0].startswith('_'):
                    # Ignores methods
                    if not inspect.ismethod(i[1]):
                        setattr(vba_fields,i[0],int(_arguements[type_idx],16) if '0x' in _arguements[type_idx] else int(_arguements[type_idx],10))
                        type_idx += 1
            vba_32_cast = getattr(flags, 'asvba')
            
            
            print('%-16s : 0x%x'%('VBA',vba_32_cast))            
            vba_fields = getattr(flags, args.type)            
            for i in inspect.getmembers(vba_fields):
                # Ignores anything starting with underscore 
                # (that is, private and protected attributes)
                if not i[0].startswith('_'):
                    # Ignores methods
                    if not inspect.ismethod(i[1]):
                        print("%-16s : %d (0x%x)" % (i[0],i[1],i[1]))            
        else:
            setattr(flags, "asvba", args.vba)
            vba_fields = getattr(flags, args.type)
            
            print("%-16s : 0x%x" % ("VBA", args.vba))
            for i in inspect.getmembers(vba_fields):
                # Ignores anything starting with underscore 
                # (that is, private and protected attributes)
                if not i[0].startswith('_'):
                    # Ignores methods
                    if not inspect.ismethod(i[1]):
                        print("%-16s : %d (0x%x)" % (i[0],i[1],i[1]))