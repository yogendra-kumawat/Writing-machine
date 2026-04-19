import serial
import time
PORT = 'COM5' 
BAUD_RATE = 9600
try:
    ser = serial.Serial(PORT, BAUD_RATE, timeout=1)
    print(f"--- Connected to {PORT} at {BAUD_RATE} baud ---")
    print("Type characters to send to STM32 (Ctrl+C to exit)\n")

    # Start a background thread to listen for incoming data
    # thread = threading.Thread(target=read_from_port, args=(ser,), daemon=True)
    # thread.start()

    while True:
        # Get user input
        for i in range (0,180):
            j=i
        
            k=i
            msg = "A"+str(i).zfill(3)+str(j).zfill(3)+str(k).zfill(3)
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