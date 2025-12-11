<div style="text-align: center;">
  <img src="https://www.uvlhub.io/static/img/logos/logo-light.svg" alt="Logo">
</div>

# uvlhub.io

Repository of feature models in UVL format integrated with Zenodo and flamapy following Open Science principles - Developed by DiversoLab

## Official documentation

You can consult the official documentation of the project at [docs.uvlhub.io](https://docs.uvlhub.io/)

## 🚀 PixelHub Installation and Setup with Docker

This guide details the steps to install and configure the PixelHub environment using Docker.

---

### 🛑 Prerequisite: Deactivate MariaDB Service

Before proceeding with the Docker installation, the MariaDB service **must be deactivated** to prevent port conflicts.

- To stop the MariaDB service:
  ```bash
  sudo systemctl stop MariaDB
  ```

---

### 🛠️ Installation Steps

Follow these steps to set up the environment:

1.  **Configure Environment Variables**
    - Copy the `.env` Docker example file to configure your local variables.
2.  **Navigate to Scripts Folder**
    - Change directory to the scripts folder:
      ```bash
      cd scripts/
      ```
3.  **Start the Environment**
    - Use the `docker-up.sh` script to install and configure the environment:
      ```bash
      sh docker-up.sh
      ```
4.  **Start the Environment**
    - Once the installation finish the application should be running at http://127.0.0.1:5000/ or http://172.21.0.5:5000/

5.  **Stop the Container**
    - To stop the running Docker container, use the `docker-down.sh` script:
      ```bash
      sh docker-down.sh
      ```

---

### 🧹 Cleaning Up Previous Configurations

**Important:** If you encounter previous container configurations due to lower versions of PixelHub, you can clean the Docker setup using this script:

- **To clean Docker configuration:**
  ```bash
  sh clean_docker.sh
  ```

## 📦 PixelHub Installation using Vagrant

This guide outlines the process for setting up the PixelHub environment using Vagrant.

---

### 🛠️ Installation Steps

Follow these steps to deploy the virtual machine (VM):

1.  **Configure Environment Variables**
    - Copy the configuration specified in the `vagrant .env` example file into your local `.env` file.
2.  **Access the Vagrant Folder**
    - Navigate to the Vagrant directory:
      ```bash
      cd vagrant/
      ```
3.  **Start the Installation**
    - Use the `vagrant up` command to initialize the VM and start the installation:
      ```bash
      vagrant up
      ```

4.  **Check Correct Installation**
    - Once the installation finish you should be able to load the aplication if you access http://localhost:5000/

5.  **Stop and Destroy the VM**
    - To stop and eliminate the created virtual machine, use the `vagrant destroy` command:
      ```bash
      vagrant destroy
      ```

---

### ⚠️ Common Issues and Troubleshooting

Encountering errors? Check these common solutions:

1.  **Secure Boot:**
    - Make sure you **deactivate Secure Boot** in your machine's BIOS before starting the process.
2.  **Missing Dependencies:**
    - You might need to install specific dependencies, such as VirtualBox, using the `requirements.txt` file.
3.  **Kernel Compilation Error (KVM):**
    - If you receive a kernel compilation error, you can often resolve this issue by unloading the corresponding KVM module:
      ```bash
      sudo rmmod kvm_{intel/amd}
      ```
      _(Select the module that better fits your computer, `kvm_intel` or `kvm_amd`.)_
