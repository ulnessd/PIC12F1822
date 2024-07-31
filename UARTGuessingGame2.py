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

    # Prompt the user to enter the target number
    target_number = int(input("Enter the target number (0-255): "))

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

        # Send start signal to PIC
        ser.write(b'\x01')
        print("Sent start signal (0b00000001)")

        while running:
            # Check for incoming data
            if ser.in_waiting > 0:
                response = ser.read(1)
                if response:
                    guess = int.from_bytes(response, 'big')
                    print(f"PIC guessed: {guess}")

                    if guess == target_number:
                        print("PIC guessed it correctly!")
                        running = False
                    else:
                        # Prompt the user for feedback
                        feedback = input("Is the guess too low (B) or too high (A)? ").strip().upper()
                        if feedback == 'B':
                            ser.write(b'B')  # Send ASCII character 'B' if the guess is too low
                            print("Sent feedback: Guess too low (B)")
                        elif feedback == 'A':
                            ser.write(b'A')  # Send ASCII character 'A' if the guess is too high
                            print("Sent feedback: Guess too high (A)")

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
