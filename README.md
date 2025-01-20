# **Automated Verification System for CyberRange Assignments**  

## **Overview**  
This project provides an automated verification system for evaluating Assignments 1 and 2 of the "Cybersecurity" course by Professor Spognardi at Sapienza University of Rome. The system ensures compliance with predefined requirements on specific infrastructures using SSH access, configuration verification, and testing automation.  

---

## **Table of Contents**  
1. [Requirements](#requirements)  
2. [Installation and Setup](#installation-and-setup)  
3. [Usage](#usage)  
4. [Testing Environment Preparation](#testing-environment-preparation)  
5. [Launching the Verifier](#launching-the-verifier)  
6. [Troubleshooting](#troubleshooting)  

---

## **Requirements**  
Before setting up and running the verifier, ensure the following prerequisites are met:  

### **Software and Libraries**  
The following Python libraries are required:  
- `requests`  
- `colorama`  
- `paramiko`  
- `tqdm`  
- `psutil`  
- `pyotp`  

### **Infrastructure Requirements**  
- SSH access to all virtual hosts in the infrastructure.  
- An SSH key pair:  
  - Private key: `SSHKey`  
  - Public key: `SSHKey.pub`  
- A testing user (`tester`) configured on each host with the public SSH key.  
- OpenVPN access to the infrastructure.  
- Modified `/etc/ssh/sshd_config` to enable `PermitRootLogin yes`.  

---

## **Installation and Setup**  

### **Step 1: Clone the Repository**  
Clone the repository to your local machine:  
```bash  
git clone https://github.com/netsecuritylab/Automated-Verification-System.git  
cd Automated-Verification-System  
```  

### **Step 2: Install Required Libraries**  
Run the automated script to install dependencies:  
```bash  
python install_libraries.py  
```  
Alternatively, install the libraries manually using `pip`:  
```bash  
pip install requests colorama paramiko tqdm psutil pyotp  
```  

### **Step 3: Configure SSH Keys**  
Use the `Generator_SSH.py` script to generate and distribute SSH keys:  
```bash  
python Generator_SSH.py <option>  
```  
- `<option>` can be:  
  - `Generate`: Generate SSH keys in the working directory.  
  - `Publish`: Distribute keys to hosts specified in `device.json`.  
  - `All`: Perform both operations.  

### **Step 4: Configure Testing Users**  
Use the `UserGenerate.Script` to create testing users:  
```bash  
python UserGenerate.Script  
```  
This script:  
1. Creates a `tester` user on each host.  
2. Configures the SSH public key for `tester`.  
3. Sets up the key in both `root` and `tester` directories for SSH access.  

---

## **Testing Environment Preparation**  
1. Create directories for each ACME to be tested in the launcher’s folder. Example:  
   - `Testing_ACME01`, `Testing_ACME02`, etc.  
   Ensure the ACME number is zero-padded (e.g., `01`, `02` for numbers <10).  

2. Add configuration files to these directories:  
   - `.ovpn` files for VPN clients (`admin`, `operator`, `employee`).  

---

## **Launching the Verifier**  
Run the verifier using the `launcher.py` script:  
```bash  
python launcher.py <ACME>/<ACME_ALL> <Assignment> <TEST_ALL>  
```  

### **Parameters**  
- **`<ACME>`**: The ACME to test (e.g., `ACME01`).  
- **`<ACME_ALL>`**: Test all ACME directories.  
- **`<Assignment>`**: The assignment to verify (`Assignment1`, `Assignment2`, or abbreviations like `A1`, `A2`).  
- **`<TEST_ALL>`**: Optional. Launch all checks sequentially. Without this, a CLI menu for manual selection is displayed.  

### **Example Command**  
```bash  
python launcher.py ACME01 Assignment1 TEST_ALL  
```  

---

## **Troubleshooting**  
If issues arise, such as:  
- Firewall or VPN connectivity errors.  
- Missing responses from main infrastructure components.  

### **Steps to Resolve**  
1. Verify the network configuration and recheck all connection settings.  
2. Relaunch the verifier on the same ACME and assignment to rule out configuration errors.  

---

## **Report Generation**  
After execution, the verifier generates a report containing the test results. The report is saved in:  
- The respective ACME folder.  
- The main verifier directory.  

---  
