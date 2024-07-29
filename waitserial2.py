import serial
import time
from pynput import keyboard

# Serial port configuration
PORT = '/dev/ttyUSB0'
BAUD_RATE = 301

# Flag to indicate if the program should continue running
running = True

def on_press(key):
    global running
    if key == keyboard.Key.esc:  # ESC key
        print("Exiting...")
        running = False
        return False  # Stop listener

def main():
    global running

    print("Press 'Esc' to exit")

    # Start the keyboard listener
    listener = keyboard.Listener(on_press=on_press)
    listener.start()

    try:
        # Initialize serial connection
        ser = serial.Serial(
            PORT,
            BAUD_RATE,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=1
        )
        ser.flushInput()

        while running:
            # Check for incoming data
            if ser.in_waiting > 0:
                response = ser.read(ser.in_waiting)
                if response:
                    # Print hexadecimal representation of the data
                    hex_data = ' '.join(f'{byte:02x}' for byte in response)
                    print(f"Hex data: {hex_data}")

            # Add a small delay to prevent high CPU usage
            time.sleep(0.1)

    except Exception as e:
        print(f"Error: {e}")

    finally:
        # Close the serial connection
        ser.close()
        listener.stop()

if __name__ == "__main__":
    main()
