# 🦾 Polar Coordinate 2D Robotic Arm Writer

[![Platform](https://img.shields.io/badge/Platform-STM32-blue.svg)]()
[![Language](https://img.shields.io/badge/Language-Python%20%7C%20C-green.svg)]()
[![Hardware](https://img.shields.io/badge/Hardware-PWM%20Servos-orange.svg)]()

This repository contains the software and firmware for a 2-dimensional robotic arm designed to act as an automated writing machine. Instead of standard X/Y gantries, this system utilizes polar coordinates and inverse kinematics to drive a multi-servo robotic arm, bridging computer vision with low-level hardware control.

---

## 🧭 Table of Contents
* [1. Project Overview](#-project-overview)
* [2. See it in Action](#-see-it-in-action)
* [3. The Math (Inverse Kinematics)](#-the-math-inverse-kinematics)
* [4. Software Architecture](#-software-architecture)
* [5. Setup & Installation](#-setup--installation)

---

## 📖 Project Overview

The writing machine takes a standard digital image, processes it to extract boundaries (contours), calculates the necessary inverse kinematics in real-time, and streams angular data to an STM32 microcontroller via a custom serial protocol. 

**Key Features:**
* Automated image boundary detection using OpenCV.
* Real-time inverse kinematics simulation.
* Hardware-level PWM generation on STM32 for jitter-free servo movement.

---

## 🎥 See it in Action
> **Simulation:** Python calculating paths and tracing boundaries.
![Simulation Demo](link-to-your-simulation.gif)

<img width="400" height="426" alt="Screencast from 2026-05-24 15-42-42" src="https://github.com/user-attachments/assets/503035b1-7002-4cca-af6f-d6f27de53404" />

> **Hardware:** STM32 driving the servos based on Python serial data.
![Hardware Demo](link-to-your-hardware.gif)
<img width="400" height="465" alt="demo" src="https://github.com/user-attachments/assets/a8fd8f33-ff75-4bba-940c-a3521f3440be" />

---

## 🧮 The Math (Inverse Kinematics)

<details>
<summary><strong>👉 Click to expand the Kinematics explanation</strong></summary>

<br>
The core logic relies on converting a desired (x, y) coordinate on the drawing surface into the angles required by the two main links of the arm (r1 and r2). 

The elbow angle (phi) is derived using the Law of Cosines:

$$\phi = 2\pi - \arccos\left(\frac{x^2 + y^2 - r1^2 - r2^2}{2 \cdot r1 \cdot r2}\right)$$

Once the elbow angle is known, the shoulder angle (theta) is calculated to ensure the end effector reaches the target point. 

</details>

---

## 💻 Software Architecture

The project is split into two environments working in tandem. 

<details>
<summary><strong>🐍 Python Application (Host PC)</strong></summary>

<br>
The `main.ipynb` script is responsible for high-level processing:
1. **Image Processing:** Loads an image, applies an inverse binary threshold, and extracts contours using `cv2.findContours`.
2. **Kinematic Conversion:** Iterates through every point and calculates servo angles.
3. **Serial Transmission:** Formats the computed angles into a strict 10-byte string format (e.g., `A090045120`) and pushes it via UART.

</details>

<details>
<summary><strong>⚙️ STM32 Firmware (Device)</strong></summary>

<br>
The microcontroller code relies on the STM32 HAL library:
* **Timer 1 (TIM1):** Configured with a prescaler and period to generate a 50Hz PWM signal on Channels 1, 2, and 3.
* **USART1 Interrupts:** When a full 10-byte packet is received, `HAL_UART_RxCpltCallback` triggers. It verifies the `'A'` header, parses the three 3-digit angles, maps them to RC servo pulse widths (1000 µs to 2000 µs), and updates the PWM registers.

</details>

---

## 🛠️ Setup & Installation

### Hardware Requirements
* STM32 Development Board
* 3x Standard Servos (5V)
* **Crucial:** External power supply for servos (Do not power directly from the STM32 logic pins).

### Quick Start
1. Clone this repository.
2. Flash the `main.c` firmware to your STM32 using STM32CubeIDE.
3. Connect the STM32 to your PC via USB/UART (Ensure Baud Rate is `9600`).
4. Install Python dependencies: `pip install opencv-python numpy pyserial`
5. Open `main.ipynb`, set your `PORT` to the correct COM port, and run the notebook.

---
