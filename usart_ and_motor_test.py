import serial
import time
PORT = 'COM5' 
BAUD_RATE = 9600
try:
    ser = serial.Serial(PORT, BAUD_RATE, timeout=1)
    print(f"--- Connected to {PORT} at {BAUD_RATE} baud ---")

    while True:
         for i in range (0,180):
            msg = "A"+str(i).zfill(3)+str(i).zfill(3)+str(i).zfill(3)#to test the usart and mtors 
        # Send data (encoded to bytes)
            ser.write(msg.encode('utf-8'))
            time.sleep(0.02)
            print(msg)

except serial.SerialException as e:
    print(f"Error: Could not open port {PORT}. Is the Bluetooth paired and connected?")
except KeyboardInterrupt:
    print("\nExiting script...")
finally:
    if 'ser' in locals() and ser.is_open:
        ser.close()
