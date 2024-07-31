import serial
import time
import random
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

    # Generate a random number between 0 and 255
    random_number = random.randint(0, 255)
    print(f"Random number generated: {random_number}")

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
        time.sleep(1.0)

        while running:
            # Check for incoming data
            if ser.in_waiting > 0:
                response = ser.read(1)
                if response:
                    guess = int.from_bytes(response, 'big')
                    print(f"Received guess: {guess}")

                    if guess == random_number:
                        print("You guessed it!")
                        running = False
                    elif guess < random_number:
                        time.sleep(1.0)
                        ser.write(b'\x00')  # Send 0b00000000 if the guess is too low
                        print("Sent feedback: Guess too low (0b00000000)")
                    else:
                        time.sleep(1.0)
                        ser.write(b'\x01')  # Send 0b00000001 if the guess is too high
                        print("Sent feedback: Guess too high (0b00000001)")

            # Add a small delay to prevent high CPU usage
            time.sleep(1.0)

    except Exception as e:
        print(f"Error: {e}")

    finally:
        # Close the serial connection
        ser.close()
        listener.stop()

if __name__ == "__main__":
    main()
