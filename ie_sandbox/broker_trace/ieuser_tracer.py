from pydbg import *
from pydbg.defines import *
import ctypes
import struct
from broker_calls import *
import psutil


# shdocvwBroker object interface
shdocvw_offset = 0x12bd8
shdocvw_entry  = 121
shdocvw_names = get_shdocvw_calls_name()


# IERecoveryStore object interface
ierecovery_store_offset = 0xf4db0
ierecovery_store_entry = 36
ierecovery_store_names = get_ierecovery_store_calls_name()


# SettingsStore object interface
settingsstore_offset = 0x187c0c
settingsstore_entry = 9
settingsstore_names = get_settingsstore_calls_name()


# IEUserBroker object interface
ieuser_offset = 0x10ec78
ieuser_entry = 10
ieuser_names = get_ieuser_calls_name()


# stdidentity_unk object interface
stdidentity_unk_offset = 0x34810
stdidentity_unk_entry = 4
stdidentity_unk_names = get_stdidentity_unk_calls_name()


# ieaxinstall object interface
ieaxinstall_offset = 0x114450
ieaxinstall_entry = 4
ieaxinstall_names = get_ieaxinstall_calls_name()


# iereghelperbroker object interface
iereghelperbroker_offset = 0x11441c
iereghelperbroker_entry = 9
iereghelperbroker_names = get_iereghelperbroker_calls_name()


# iereghelperobject_cleanup object interface
iereghelperobject_cleanup_offset = 0x114440
iereghelperobject_cleanup_entry = 4
iereghelperobject_cleanup_names = get_iereghelperobject_cleanup_calls_name()


# iebrokerattach object interface
iebrokerattach_offset = 0x114460
iebrokerattach_entry = 4
iebrokerattach_names = get_iebrokerattach_calls_name()

# protectedmodeAPI object interface
protectedmodeAPI_offset = 0xe3d8
protectedmodeAPI_entry = 8
protectedmodeAPI_names = get_protectedmodeAPI_calls_name()


# Global variables for dll base address and dictionary function names
broker_global_names_hash = {}
ieframe_image_addr = 0
iertutil_image_addr = 0
ole32_image_addr = 0
broker_pid = 0
iface_list = []


# Define the breakpoint handler
def handler_breakpoint(pydbg):
    f = open("iface_log", "a")

    # ignore the first windows driven breakpoint.
    if pydbg.first_breakpoint:
        return DBG_CONTINUE
    
    if "CreateKnown" in broker_global_names_hash[pydbg.exception_address]:
        addr1 = pydbg.context.Esp + 8
        addr2 = pydbg.context.Esp + 12
        
        g1 = dump_guid(pydbg, addr1)
        g2 = dump_guid(pydbg, addr2)
        
        guid = (g1,g2)
        if guid not in iface_list:
            iface_list.append(guid)
            
            for i in g1:
                f.write("%x " %i)
            
            f.write(" -> ")
                
            for i in g2:
                f.write("%x " %i)

            f.write("\n")

        print "%s called from thread %d" % (broker_global_names_hash[pydbg.exception_address], pydbg.dbg.dwThreadId)

        print "%x:%x:%x:%x:%x:%x:%x:%x:%x:%x:%x" %(g1[0],g1[1],g1[2],g1[3],g1[4],g1[5],g1[6],g1[7],g1[8],g1[9],g1[10])
        print "%x:%x:%x:%x:%x:%x:%x:%x:%x:%x:%x" %(g2[0],g2[1],g2[2],g2[3],g2[4],g2[5],g2[6],g2[7],g2[8],g2[9],g2[10])


    return DBG_CONTINUE


def dump_guid(pydbg,address):
    ret = []
    p = pydbg.read_process_memory(address, 4)

    d1 = pydbg.read_process_memory(struct.unpack("<L", p)[0], 4)
    d2 = pydbg.read_process_memory(struct.unpack("<L", p)[0]+4, 2)
    d3 = pydbg.read_process_memory(struct.unpack("<L", p)[0]+6, 2)
    d4 = pydbg.read_process_memory(struct.unpack("<L", p)[0]+8, 8)

    ret.append(struct.unpack("<L", d1)[0])
    ret.append(struct.unpack("<H", d2)[0])
    ret.append(struct.unpack("<H", d3)[0])
    ret.append(struct.unpack("<B", d4[0])[0])
    ret.append(struct.unpack("<B", d4[1])[0])
    ret.append(struct.unpack("<B", d4[2])[0])
    ret.append(struct.unpack("<B", d4[3])[0])
    ret.append(struct.unpack("<B", d4[4])[0])
    ret.append(struct.unpack("<B", d4[5])[0])
    ret.append(struct.unpack("<B", d4[6])[0])
    ret.append(struct.unpack("<B", d4[7])[0])

    return ret


dbg = pydbg()
    
# register a breakpoint handler function.]
dbg.set_callback(EXCEPTION_BREAKPOINT, handler_breakpoint)

# find the broker process
for i in psutil.process_iter():
    try:
        if i.name == "iexplore.exe":
            if i.parent.name != "iexplore.exe":
                broker_pid = i.pid
    except:
        continue

try:
    dbg.attach(broker_pid)
except:
    print "Unable to attach.... aborting!"
    exit

# find the base address for ieframe.dll and iertutil.dll libraries
for n, addr in dbg.enumerate_modules():
    if n == "IEFRAME.dll":
        ieframe_image_addr = addr
    
    if n == "iertutil.dll":
        iertutil_image_addr = addr

    if n == "ole32.dll":
        ole32_image_addr = addr



# set a breakpoint in each entry of the interface and update the name dictionary
for i in range(0, ieuser_entry):
    # Ignore addref, queryInterface and release
    if i < 3:
        continue
    entry = dbg.read_process_memory(ieframe_image_addr + ieuser_offset + 4 * i, 4)
    entry = struct.unpack("<L", entry)[0]
    broker_global_names_hash.update({entry : ieuser_names[i]})
    dbg.bp_set(entry)


# Start the debug event handler
dbg.debug_event_loop()
