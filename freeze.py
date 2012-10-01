from bbfreeze import Freezer

f = Freezer(
    "dist-multiblob",
    includes = ("inspect", "zipfile", "ctypes.util")
    )
f.addScript("multiblob\\client.py")
f()
