import serial
import time

# Replace with your serial port and baud rate
PORT = '/dev/ttyUSB0'
BAUD_RATE = 300

def main():
    # Initialize serial connection
    ser = serial.Serial(PORT, BAUD_RATE, timeout=1)

    try:
        # Write an ASCII character (e.g., 'A') to the UART device
        ser.write(b'B')
        print("Sent: 'B'")

        # Wait briefly for the device to respond
        time.sleep(0.5)

        # Read response from the UART device
        if ser.in_waiting > 0:
            response = ser.read(ser.in_waiting)
            print(f"Received: {response.decode('ascii')}")
        else:
            print("No response received")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        # Close the serial connection
        ser.close()

if __name__ == "__main__":
    main()
