# 🦾 Polar Coordinate 2D Robotic Arm Writer

[![Platform](https://img.shields.io/badge/Platform-STM32-blue.svg)]()
[![Language](https://img.shields.io/badge/Language-Python%20%7C%20C-green.svg)]()
[![Hardware](https://img.shields.io/badge/Hardware-PWM%20Servos-orange.svg)]()
[![Libraries](https://img.shields.io/badge/Libraries-OpenCV%20%7C%20PySerial-red.svg)]()

A 2-dimensional robotic arm designed to act as an **automated writing machine**. Instead of standard X/Y gantries, this system utilizes **polar coordinates** and **inverse kinematics** to drive a multi-servo robotic arm — bridging computer vision on a host PC with low-level hardware control on an STM32 microcontroller.

---

## 🧭 Table of Contents

- [Project Overview](#-project-overview)
- [See it in Action](#-see-it-in-action)
- [The Math (Inverse Kinematics)](#-the-math-inverse-kinematics)
- [Software Architecture](#-software-architecture)
- [Firmware Deep Dive](#-firmware-deep-dive)
- [Setup & Installation](#-setup--installation)
  

---

## 📖 Project Overview

The writing machine takes a standard digital image, processes it to extract boundaries (contours), calculates the necessary inverse kinematics in real-time, and streams angular data to an STM32 microcontroller via a custom USART serial protocol.

**Key Features:**
- 🖼️ Automated image boundary detection using **OpenCV**
- 📐 Real-time **inverse kinematics** simulation
- ⚡ Hardware-level **PWM generation** on STM32 for jitter-free servo movement
- 🔄 **Interrupt-driven** serial communication for zero-delay coordinate parsing

---

## 🎥 See it in Action

**Simulation** — Python calculating paths and tracing boundaries:

<img width="400" alt="Simulation Screencast" src="https://github.com/user-attachments/assets/503035b1-7002-4cca-af6f-d6f27de53404" />

**Hardware** — STM32 driving the servos based on Python PySerial data:

<img width="400" alt="Hardware Demo" src="https://github.com/user-attachments/assets/a8fd8f33-ff75-4bba-940c-a3521f3440be" />

---

## 🧮 The Math (Inverse Kinematics)

<details>
<summary><strong>👉 Click to expand the Kinematics explanation</strong></summary>

<br>

The core logic converts a desired `(x, y)` coordinate on the drawing surface into the angles required by the two main links of the arm (`r1` and `r2`).

### Elbow Angle (φ)

The elbow angle is derived using the **Law of Cosines**:

$$\phi = 2\pi - \arccos\left(\frac{x^2 + y^2 - r1^2 - r2^2}{2 \cdot r1 \cdot r2}\right)$$

### Shoulder Angle (θ)

Once the elbow angle is known, the shoulder angle is calculated to ensure the end-effector reaches the target point:

$$\theta = \arctan2(y,\ x) - \arctan2\!\left(r2 \cdot \sin(\phi),\ r1 + r2 \cdot \cos(\phi)\right)$$

### Summary Table

| Variable | Description |
|----------|-------------|
| `r1` | Length of the upper arm link |
| `r2` | Length of the forearm link |
| `φ` (phi) | Elbow joint angle |
| `θ` (theta) | Shoulder joint angle |
| `(x, y)` | Target end-effector position |

</details>

---

## 💻 Software Architecture

The project is split into two environments working in tandem:

### 🐍 Python Application (Host PC)

The `main.ipynb` notebook handles all high-level processing:

1. **Image Processing** — Loads an image, applies an inverse binary threshold, and extracts contours using `cv2.findContours`.
2. **Kinematic Conversion** — Iterates through every contour point and calculates the required servo angles.
3. **Serial Transmission** — Formats computed angles into a strict **10-byte packet** (e.g., `A090045120`) and streams it over a COM port using `pyserial`.

#### Packet Format

```
A  [angle1 3-digit]  [angle2 3-digit]  [angle3 3-digit]
^   ^                 ^                 ^
|   Servo 1 (000–180) Servo 2 (000–180) Servo 3 (000–180)
Header byte 'A'
```

### ⚙️ STM32 Firmware (Device)

The microcontroller acts as the hardware driver using the **STM32 HAL** library:

| Component | Role |
|-----------|------|
| **Timer 1 (TIM1)** | Configured with prescaler/period to generate a precise **50 Hz PWM** signal on Channels 1, 2, and 3 |
| **USART1 Interrupts** | Continuously listens for incoming 10-byte packets; triggers `HAL_UART_RxCpltCallback` on reception |

---

## 🛠️ Firmware Deep Dive

The STM32 firmware relies on **hardware interrupts** to process serial data without blocking the main loop.

### 1. Initialization

PWM channels and the UART interrupt listener are started in the `USER CODE BEGIN 2` block:

```c
/* USER CODE BEGIN 2 */
HAL_TIM_PWM_Start(&htim1, TIM_CHANNEL_1);
HAL_TIM_PWM_Start(&htim1, TIM_CHANNEL_2);
HAL_TIM_PWM_Start(&htim1, TIM_CHANNEL_3);

// Start listening for 10-byte packets on USART1
HAL_UART_Receive_IT(&huart1, rx_data, 10);
/* USER CODE END 2 */
```

### 2. The Interrupt Callback

When a full 10-byte packet is received, the system verifies the `'A'` header, parses the three 3-digit angles from ASCII to integers, and pushes them to the servo function. Crucially, the interrupt is then **re-armed** for continuous streaming.

```c
void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart)
{
    if (huart->Instance == USART1)
    {
        // Verify header 'A' and toggle status LED
        if (rx_data[0] == 'A') {
            HAL_GPIO_TogglePin(GPIOC, GPIO_PIN_13);
        }

        // Parse angles from ASCII characters to integers
        int angle1 = (rx_data[1]-48)*100 + (rx_data[2]-48)*10 + (rx_data[3]-48);
        int angle2 = (rx_data[4]-48)*100 + (rx_data[5]-48)*10 + (rx_data[6]-48);
        int angle3 = (rx_data[7]-48)*100 + (rx_data[8]-48)*10 + (rx_data[9]-48);

        // Update motor positions
        setServoAngle(angle1, angle2, angle3);

        // Re-arm the interrupt (critical for continuous streaming)
        HAL_UART_Receive_IT(&huart1, rx_data, 10);
    }
}
```

### 3. PWM Generation

Standard servos require a pulse width between **1 ms** (0°) and **2 ms** (180°). The timer capture/compare registers are dynamically updated:

```c
void setServoAngle(int angle1, int angle2, int angle3)
{
    int minPulseWidth = 1000; // 1 ms
    int maxPulseWidth = 5000; // 2 ms (scaled to timer resolution)

    int pulse1 = ((angle1 * (maxPulseWidth - minPulseWidth)) / 180) + minPulseWidth;
    int pulse2 = ((angle2 * (maxPulseWidth - minPulseWidth)) / 180) + minPulseWidth;
    int pulse3 = ((angle3 * (maxPulseWidth - minPulseWidth)) / 180) + minPulseWidth;

    __HAL_TIM_SET_COMPARE(&htim1, TIM_CHANNEL_1, pulse1);
    __HAL_TIM_SET_COMPARE(&htim1, TIM_CHANNEL_2, pulse2);
    __HAL_TIM_SET_COMPARE(&htim1, TIM_CHANNEL_3, pulse3);
}
```

#### Pulse Width Mapping

| Angle | Pulse Width |
|-------|-------------|
| 0°    | 1 ms        |
| 90°   | 1.5 ms      |
| 180°  | 2 ms        |

---

## 🚀 Setup & Installation

### Hardware Requirements

- STM32 Development Board (e.g., STM32F103C8T6 "Blue Pill")
- 3× Standard Hobby Servos (5V, e.g., SG90 or MG996R)
- External 5V power supply for servos
- USB-to-UART adapter (if board lacks native USB serial)

> ⚠️ **Critical Warning:** Use an **external power supply** for the servos. Do **not** power them from the STM32 logic/power pins — the current draw will cause **brownouts** or permanently **damage the board**. Always ensure a **common ground** between the STM32 and the external supply.

### Wiring Diagram

```
  STM32          Servos (×3)
  ------         -----------
  PA8  ──────►  Servo 1 (Signal)
  PA9  ──────►  Servo 2 (Signal)
  PA10 ──────►  Servo 3 (Signal)
  GND  ──────►  Common GND (also connect external PSU GND here)

  External 5V PSU ──► Servo VCC (×3)
```

### Software Dependencies

```bash
# Python (Host PC)
pip install opencv-python pyserial numpy jupyter

# STM32 (Firmware)
# Use STM32CubeIDE with HAL libraries (included in CubeMX project)
```

### Quick Start

1. **Clone** this repository:
   ```bash
   git clone https://github.com/your-username/polar-arm-writer.git
   cd polar-arm-writer
   ```

2. **Flash** the firmware to your STM32 using **STM32CubeIDE** (`firmware/main.c`).

3. **Connect** the STM32 to your PC via USB/UART and note your COM port (e.g., `COM3` on Windows, `/dev/ttyUSB0` on Linux).

4. **Install** Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. **Open and run** `main.ipynb` in Jupyter:
   ```bash
   jupyter notebook main.ipynb
   ```

6. **Set** the correct COM port in the notebook:
   ```python
   SERIAL_PORT = "COM3"   # Windows
   # SERIAL_PORT = "/dev/ttyUSB0"  # Linux/macOS
   BAUD_RATE   = 115200
   ```

7. **Load** an image and run all cells to begin writing!

---


## 📜 License

This project is open source.

---

*Built with ❤️ using STM32 HAL, OpenCV, and PySerial.*
