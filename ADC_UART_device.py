import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
import serial
import serial.tools.list_ports
import time
import csv
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import threading

# Global variables
running = False
start_time = None
data = []
ser = None
BAUD_RATE = 2404

# Function to handle the start of data acquisition
def start_acquisition():
    global running, start_time, data, ser

    start_time = None
    data = []
    running = True

    port = port_combobox.get()

    # Initialize serial connection
    ser = serial.Serial(
        port,
        BAUD_RATE,
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        timeout=1
    )
    ser.flushInput()
    ser.write(b'\xFF')  # Send initial start signal

    # Start the data acquisition thread
    threading.Thread(target=acquire_data).start()

def acquire_data():
    global running, start_time, data, ser

    while running:
        current_time = datetime.now()

        if start_time is None:
            start_time = current_time

        # Calculate time difference in seconds
        time_diff = (current_time - start_time).total_seconds()
        adc_values = [0, 0, 0]

        for i in range(3):
            while ser.in_waiting < 2:
                time.sleep(0.01)  # Wait for data to be available

            msb = ser.read(1)  # Read the most significant byte
            lsb = ser.read(1)  # Read the least significant byte

            if msb and lsb:
                adc_values[i] = (msb[0] << 8) | lsb[0]
                ser.write(b'\x02')  # Send acknowledgment byte

        data.append((time_diff, adc_values[0], adc_values[1], adc_values[2]))

        # Update the plot
        update_plot()

        # Add a small delay to prevent high CPU usage
        time.sleep(0.01)

def stop_acquisition():
    global running
    running = False
    if ser:
        ser.close()

def update_plot():
    if not running:
        return

    # Clear the plot
    ax.clear()

    # Get user inputs for voltage conversion and sample rate
    try:
        voltage_conversion = float(voltage_entry.get())
    except ValueError:
        voltage_conversion = 5.0  # Default value

    try:
        sample_rate = int(sample_entry.get())
    except ValueError:
        sample_rate = 10  # Default value

    # Plot the data
    time_data = [row[0] for i, row in enumerate(data) if i % sample_rate == 0]
    if var_ch0.get():
        ch0_data = [(row[1] / 1023.0) * voltage_conversion for i, row in enumerate(data) if i % sample_rate == 0]
        ax.plot(time_data, ch0_data, label='Channel 0')
    if var_ch1.get():
        ch1_data = [(row[2] / 1023.0) * voltage_conversion for i, row in enumerate(data) if i % sample_rate == 0]
        ax.plot(time_data, ch1_data, label='Channel 1')
    if var_ch2.get():
        ch2_data = [(row[3] / 1023.0) * voltage_conversion for i, row in enumerate(data) if i % sample_rate == 0]
        ax.plot(time_data, ch2_data, label='Channel 2')

    ax.legend()
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Voltage (V)')

    canvas.draw()

def save_data():
    if not data:
        return

    file_path = filedialog.asksaveasfilename(defaultextension=".csv")
    if not file_path:
        return

    try:
        sample_rate = int(sample_entry.get())
    except ValueError:
        sample_rate = 10  # Default value

    with open(file_path, 'w', newline='') as csvfile:
        fieldnames = ['Time (s)']
        if var_ch0.get():
            fieldnames.append('Channel 0 (V)')
        if var_ch1.get():
            fieldnames.append('Channel 1 (V)')
        if var_ch2.get():
            fieldnames.append('Channel 2 (V)')

        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        voltage_conversion = float(voltage_entry.get())

        for i, row in enumerate(data):
            if i % sample_rate == 0:
                row_dict = {'Time (s)': row[0]}
                if var_ch0.get():
                    row_dict['Channel 0 (V)'] = (row[1] / 1023.0) * voltage_conversion
                if var_ch1.get():
                    row_dict['Channel 1 (V)'] = (row[2] / 1023.0) * voltage_conversion
                if var_ch2.get():
                    row_dict['Channel 2 (V)'] = (row[3] / 1023.0) * voltage_conversion
                writer.writerow(row_dict)

def get_ports():
    ports = serial.tools.list_ports.comports()
    return [port.device for port in ports]

# Create the main window
root = tk.Tk()
root.title("ADC Data Acquisition")

# Create a frame for the controls
control_frame = ttk.Frame(root)
control_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

# COM port selection
ttk.Label(control_frame, text="COM Port:").pack(side=tk.LEFT)
port_combobox = ttk.Combobox(control_frame, values=get_ports(), state="readonly")
port_combobox.pack(side=tk.LEFT, padx=5)

# Start and Stop buttons
start_button = ttk.Button(control_frame, text="Start", command=start_acquisition)
start_button.pack(side=tk.LEFT, padx=5)
stop_button = ttk.Button(control_frame, text="Stop", command=stop_acquisition)
stop_button.pack(side=tk.LEFT, padx=5)

# Save Data button
save_button = ttk.Button(control_frame, text="Save Data", command=save_data)
save_button.pack(side=tk.LEFT, padx=5)

# Voltage conversion entry
ttk.Label(control_frame, text="Voltage Conversion (V):").pack(side=tk.LEFT)
voltage_entry = ttk.Entry(control_frame)
voltage_entry.insert(0, "5")
voltage_entry.pack(side=tk.LEFT, padx=5)

# Sampling rate entry
ttk.Label(control_frame, text="Sample every nth point:").pack(side=tk.LEFT)
sample_entry = ttk.Entry(control_frame)
sample_entry.insert(0, "10")
sample_entry.pack(side=tk.LEFT, padx=5)

# Checkbuttons for channels
var_ch0 = tk.BooleanVar(value=True)
var_ch1 = tk.BooleanVar(value=True)
var_ch2 = tk.BooleanVar(value=True)
ttk.Checkbutton(control_frame, text="Channel 0", variable=var_ch0).pack(side=tk.LEFT)
ttk.Checkbutton(control_frame, text="Channel 1", variable=var_ch1).pack(side=tk.LEFT)
ttk.Checkbutton(control_frame, text="Channel 2", variable=var_ch2).pack(side=tk.LEFT)

# Create the figure and axis for the plot
fig = Figure(figsize=(8, 6), dpi=100)
ax = fig.add_subplot(111)

# Create a canvas to embed the plot in the Tkinter window
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

# Create the Quit button
quit_button = ttk.Button(root, text="Quit", command=root.quit)
quit_button.pack(side=tk.BOTTOM, pady=5)

root.mainloop()
