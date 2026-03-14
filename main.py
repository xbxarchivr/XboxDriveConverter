import wmi
import ctypes
import sys
import os
import subprocess
import string

XBOX_ONE_BOOT_SIGNATURE = bytes.fromhex('99cc')
PC_BOOT_SIGNATURE = bytes.fromhex('55aa')

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def assign_drive_letter(disk_number, partition, letter="Z"):
    diskpart_commands = f"""
    select disk {disk_number}
    select partition {partition}
    assign letter={letter}
    exit
    """
    result = subprocess.run(
        ["diskpart"],
        input=diskpart_commands,
        capture_output=True,
        text=True,
        shell=True
    )
    print(result.stdout)
    print(result.stderr)


def get_primary_partition(disk_number):
    result = subprocess.run(
        ["diskpart"],
        input=f"select disk {disk_number}\nlist partition\nexit",
        capture_output=True,
        text=True,
        shell=True
    )
    for line in result.stdout.splitlines():
        if "Primary" in line:
            parts = line.split()
            return int(parts[1])
    return None

def get_free_drive_letter():
    c = wmi.WMI()
    used = {d.DeviceID[0] for d in c.Win32_LogicalDisk()}
    available = [l for l in string.ascii_uppercase[3:] if l not in used]  # skip A, B, C
    return available

if not is_admin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit()

c = wmi.WMI()
drives = list(c.Win32_DiskDrive())  # store once
position = 0
for drive in drives:
    with open(drive.DeviceID, 'rb') as disk:
        mbr = disk.read(0x200) #mbr size duh

    if mbr[0x1fe:0x200] == PC_BOOT_SIGNATURE: # easy verification
        print("Mode: PC")
    else:
        print("Mode: XBOX")


    print(f"Position: {position}")
    print(f"DeviceID: {drive.DeviceID}")
    print(f"Model: {drive.Model}")
    print(f"Size: {int(drive.Size) / (1024**3):.2f} GB")
    print()
    position += 1

while True:
    try:
        selection = int(input("Enter disk position: "))
        break
    except ValueError:
        print("Enter a valid int!")

if selection >= position:
    input("Enter a valid position!")
    exit()

drive = drives[selection]

ver = input(f"Selected drive: {drive.Model}. Are you sure you want to continue? (Y/N): ")
if ver.lower() != "y":
    exit()

with open(drive.DeviceID, 'r+b') as disk:
    disk.seek(0)
    mbr = bytearray(disk.read(0x200))
    backup_path = os.path.expanduser("~\\mbrbackup.bin")

    with open(backup_path, "wb") as backup:
        backup.write(mbr)

    if mbr[0x1fe:0x200] == PC_BOOT_SIGNATURE: # easy verification
        ver2 = input("CONVERTING DRIVE TO XBOX MODE!!! ARE YOU SURE?? (Y/N):")
        if ver2.lower() != "y":
            exit()
        mbr[0x1fe] = XBOX_ONE_BOOT_SIGNATURE[0]
        mbr[0x1ff] = XBOX_ONE_BOOT_SIGNATURE[1]
    else:
        ver2 = input("CONVERTING DRIVE TO PC MODE!!! ARE YOU SURE?? (Y/N):")
        if ver2.lower() != "y":
                exit()
        mbr[0x1fe] = PC_BOOT_SIGNATURE[0]
        mbr[0x1ff] = PC_BOOT_SIGNATURE[1]


    disk.seek(0)
    disk.write(mbr)

print(f"Backup stored in: {os.path.expanduser('~\\mbrbackup.bin')}\n")
print("If u converted to xbox u can skip this step")
input("VERY IMPORTANT!!! Please check now if the disk appears mounted in disk management (Action -> Refresh), if it does exit this program. If it dosent press enter: ")

freeeee = get_free_drive_letter()
for i in freeeee:
    print(i, end=", ")

while True:
    drive_letter = input("\nPlease select a free disk. The available ones are listed above, must be one character: ").strip().upper()
    if drive_letter in freeeee:
        break
    print("Well get em next time")

assign_drive_letter(drive.Index, get_primary_partition(drive.Index), drive_letter)
input("DONE. Press any key to exit")
