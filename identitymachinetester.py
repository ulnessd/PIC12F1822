import serial
import time
from pynput import keyboard

# Serial port configuration
PORT = 'COM4'  # Update this to your serial port
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

        # Send initialization signal to PIC
        ser.write(b'\x01')
        print("Initialization signal sent...")
        time.sleep(1.0)

        while running:
            # Prompt user for state value
            state_value = input("Enter state value (0-3): ")
            if not state_value.isdigit() or int(state_value) < 0 or int(state_value) > 3:
                print("Invalid input. Please enter a value between 0 and 3.")
                continue

            state_value = int(state_value)
            ser.write(state_value.to_bytes(1, 'big'))
            print(f"Sent state value: {state_value}")

            # Wait for a response
            while running:
                if ser.in_waiting > 0:
                    response = ser.read(1)
                    if response:
                        response_value = int.from_bytes(response, 'big')
                        print(f"PIC response: {response_value}")
                        break

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
