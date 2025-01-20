import subprocess

libraries_to_install = [
    "requests",
    "colorama",
    "paramiko",
    "tqdm",
    "psutil",
	"scapy",
	"pyotp",
]

for library in libraries_to_install:
    subprocess.call(["pip", "install", library])

print("Fatto!")