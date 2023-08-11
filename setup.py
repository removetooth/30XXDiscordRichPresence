import cx_Freeze, sys, os

executables = [
    cx_Freeze.Executable(
        "30XXRichPresence.py",
        base=None,
        target_name = "RichPresence",
        icon = "icon.png"
        )
    ]

cx_Freeze.setup(
    name="30XXDiscordRichPresence",
    
    options={
        "build_exe": {

            "packages":[
                "discord_rpc",
                ],
            
            "optimize": 1,

            "excludes":[
               "asyncio",
               "concurrent",
               "curses",
               "distutils",
               "html",
               "lib2to3",
               "msizxcclib",
               "multiprocessing",
               "pkg_resources",
               "pydoc_data",
               "setuptools",
               "test",
               "tkinter",
               "unittest",
               "xml",
               "xmlrpc",
               "numpy"
               ]
            }
        },
                        
    executables = executables

    )
