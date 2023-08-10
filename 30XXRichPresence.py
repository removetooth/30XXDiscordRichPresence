""" Discord Rich Presence for 30XX, revision 1 (May not work outside of Windows 10)
    Had to make a small change because I did a stupid. Old script is broked for now. This should work fine.
    Run this at the same time as 30XX to have detailed info about your game appear in your profile!
    This is a .py file, which requires Python to run. 
    You can download & install Python from python.org or simply by typing "python" into command prompt.
    Once that's done, you can run this just by double-clicking on it! 
""" #- end of discord preview header -

# there are so many better ways to do this. this whole thing is terrible
# sorry for my messy, thrown-together code!

import ctypes, struct, time, sys, ast, urllib
from subprocess import check_output, CalledProcessError

try:
    import discord_rpc
except ImportError:
    print(
"""discord_rpc is missing!
if this is your first time running this, that's normal! thankfully, it's a (hopefully) easy fix that (hopefully) won't take too long. open command prompt and install it with:

py -m pip install discord-rpc.py

if that doesn't work, try this:

python -m pip install discord-rpc.py

and if ALL ELSE fails, paste this in:

""" + sys.executable.strip('w.exe') + """ -m pip install discord-rpc.py

then, while 30XX is open, try running this again!""")
    input("Press Enter to exit")
    sys.exit()

if __name__ == '__main__':

    class MODULEENTRY32(ctypes.Structure):
        _fields_ = [("dwSize", ctypes.c_long),
                    ("th32ModuleID", ctypes.c_long),
                    ("th32ProcessID", ctypes.c_long),
                    ("GlblcntUsage", ctypes.c_long),
                    ("ProccntUsage", ctypes.c_long),
                    ("modBaseAddr", ctypes.c_void_p), # apparently changing this to a pointer made Module32First not throw error 87 in 64-bit
                    ("modBaseSize", ctypes.c_long),
                    ("hModule", ctypes.c_void_p),
                    ("szModule", ctypes.c_char*256),
                    ("szExePath", ctypes.c_char*260)]

    # grabbed this off guidedhacking.com. idk how it works but it gets the job done
    def get_module_base_address(pid, moduleName):
        hModuleSnap = ctypes.c_void_p(0)
        me32 = MODULEENTRY32()
        me32.dwSize = ctypes.sizeof(MODULEENTRY32)
        hModuleSnap = ctypes.windll.kernel32.CreateToolhelp32Snapshot({32:0x08,64:0x18}[struct.calcsize("P")*8],pid)

        mod = ctypes.windll.kernel32.Module32First(hModuleSnap, ctypes.pointer(me32))
        
        if not mod:
            print("Error getting {} base address".format(moduleName), ctypes.windll.kernel32.GetLastError())
            ctypes.windll.kernel32.CloseHandle(hModuleSnap)
            return False
        while mod:
            if me32.szModule.decode() == moduleName:
                ctypes.windll.kernel32.CloseHandle(hModuleSnap)
                return me32.modBaseAddr
            else:
                mod = ctypes.windll.kernel32.Module32Next(hModuleSnap, ctypes.pointer(me32))
   
    def readyCallback(current_user):
        print('connected to discord RPC!')

    def disconnectedCallback(codeno, codemsg):
        print('Disconnected from Discord rich presence RPC. Code {}: {}'.format(
            codeno, codemsg
        ))

    def errorCallback(errno, errmsg):
        print('An error occurred! Error {}: {}'.format(
            errno, errmsg
        ))

    bytesRead = ctypes.c_ulonglong(0)
    buffer = (ctypes.c_byte * 4)()
    
    def readAddr(offset):
        ctypes.windll.kernel32.ReadProcessMemory(processHandle, ctypes.c_void_p(offset), buffer, len(buffer), ctypes.byref(bytesRead))
        return struct.unpack('i',buffer)[0]
    
    def statef(string):
        if type(string) == str:
            return string.format(
                mode=mode,
                level=level,
                levelname=levelname,
                levelthumb=levelthumb,
                charname=charname,
                charthumb=charthumb,
                hp=hp,
                maxhp=maxhp,
                starttime=str(runstarttime)
                )
        else:
            return None

    # Note: 'event_name': callback
    callbacks = {
        'ready': readyCallback,
        'disconnected': disconnectedCallback,
        'error': errorCallback,
    }
    
    print("30XX rich presence script r1\nfetching latest addresses...")
    tbl = ast.literal_eval(urllib.request.urlopen("http://69.164.206.130:3069/").read().decode())
    print(tbl["motd"])

    try:
        # kinda messy. results in a 109 for some reason.
        pid = int(check_output('tasklist /FI "IMAGENAME eq 30XX.exe" /FO LIST | findstr "PID:"',shell=True).decode().strip("\r\n").split("PID:          ")[1])
    except CalledProcessError:
        print("30XX doesn't seem to be running.")
        input("Press Enter to exit")
        sys.exit()
    
    processHandle = ctypes.windll.kernel32.OpenProcess(0x10, 0, pid)
    base_addr = get_module_base_address(pid, "30XX.exe") # you know, at this point i'm using ctypes so much that i might as well be using c. python is NOT the tool for the job

    print("PID: {} | Handle: {} | Base address: {}".format(pid, processHandle, hex(base_addr)))

    player_addr = readAddr(base_addr+tbl["player_pointer_offset"])
    
    discord_rpc.initialize('813814227328041010', callbacks=callbacks, log=False)
    
    runstarted = 0
    runstarttime = 0

    while b'30XX.exe' in check_output('tasklist',shell=True): # this is absolutely TERRIBLE but it's still the only way i could find to do this on windows
        mode_id = readAddr(base_addr+tbl["modes_offset"])
        mode = tbl["modes"].get(mode_id,0)
        level = readAddr(base_addr+tbl["level_offset"])
        levelname = tbl["themes"].get(readAddr(base_addr+tbl["themes_offset"]),["???","thumbs_ph"])[0]
        levelthumb = tbl["themes"].get(readAddr(base_addr+tbl["themes_offset"]),["???","thumbs_ph"])[1]
        charname = tbl["pl_characters"].get(readAddr(player_addr+tbl["pl_characters_offset"]),"???")
        charthumb = charname.lower()
        hp = str(int(readAddr(player_addr+tbl["pl_hp_offset"])/1000))
        maxhp = str(int(readAddr(player_addr+tbl["pl_maxhp_offset"])/1000))

        rpc_state = tbl["rpc_states"].get(level, tbl["rpc_states"]["default"])
        
        if rpc_state.get('in_run',0) == 0:
            if runstarted:
                runstarted = 0
        else:
            if not runstarted:
                runstarted = 1
                runstarttime = int(time.time())

        rpc_out = {
            'details': statef(rpc_state.get('details', None)),
            'state': statef(rpc_state.get('state', {}).get(mode_id,None)),
            'large_image_key': statef(rpc_state.get('large_image_key', {}).get(mode_id,None)),
            'large_image_text': statef(rpc_state.get('large_image_text', None)),
            'small_image_key': statef(rpc_state.get('small_image_key', None)),
            'small_image_text': statef(rpc_state.get('small_image_text', None)),
            'start_timestamp': statef(rpc_state.get('start_timestamp', None)),
            'end_timestamp': statef(rpc_state.get('end_timestamp', None))
        }

        [rpc_out.pop(i) for i in [j for j in rpc_out if rpc_out[j] == None]]
        
        discord_rpc.update_presence(**rpc_out)

        discord_rpc.update_connection()
        time.sleep(1)
        discord_rpc.run_callbacks()
        
    print("30XX no longer running, disconnecting")
    ctypes.windll.kernel32.CloseHandle(processHandle)
    discord_rpc.shutdown()
