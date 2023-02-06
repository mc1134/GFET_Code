# ==================================================================================================================================================
# AUTHOR:            Morten Lidegaard, 2021.04.15
#                    Brash Product Development Inc.
#
# HW:                iMX8mm
# Linux:             Yocto Zeus?, Custom build kernel and image
#                    Linux ucm-imx8m-mini 5.4.24+gbabac00 #1 SMP PREEMPT Tue Apr 20 16:53:39 UTC 2021 aarch64 aarch64 aarch64 GNU/Linux
# Python version:    3.7.7
# Numpy version:     1.17.0
# SPIdev version:    python3-spidev
#
# ==================================================================================================================================================

from genericpath import exists
import time  # Time measureing and sleep
import datetime  # For filename creation
import spidev  # SPI interface
import array as arr  # Used for commands
import numpy  # Use this for data
import csv  # Writing/Reading files
import os  # For file-creation; For IO-pin control
import os.path  # For GPIO control - Testing
import sys  # For ADC value scaling
import threading  # HIGHER LEVEL THREADING: FOR RUNNING MULTIPLE THREADS
import numpy as np  # Processing of data
import openpyxl  # For excel files
from queue import Queue
import re #Regression search
import json
from os import path
import socket    

USE_FAKE_DATA = False # For generating fake Gate Voltages / Ids for testing without sensor

# CALIBRATION GAINS FOR ADC
# ADC_CALIBRATION_GAIN = 1.11262
# ADC_CALIBRATION_OFFSET = -0.055756889
# VOLTAGE_SCALE = 2.5
# FULL_SCALE_RESOLUTION = 8388608.0

# # SCALING FACTORs TO TRANSLATE CALIBRATED ADC VOLTAGE TO GATE VOLTAGE
# GATE_GAIN = (301 + 121)/301
# CURRENT_GAIN = 4990
# GATE_OFFSET = 0.019655897


# #CALIBRATION GAINS FOR TIA
# #y = 0.1371184370x3 - 0.2656584491x2 + 1.1644372463x - 0.0359382272
# TIA_GAIN_1 = 0.1371184370
# TIA_GAIN_2 = -0.2656584491
# TIA_GAIN_3 = 1.1644372463
# TIA_GAIN_4 = -0.0359382272


HELP_STRING = """
This is the standalone module for the GFET covid board project. The usage of the covid
board is as follows:
- Button 1: Runs a baseline.
- Button 2: Runs a sample.
- Button 3: Interrupts current process to return to idle state.
Here is the ideal workflow of the covid board usage:
1. User powers on the device. Device is in idle state when powered on - this script
   starts as a result of powering on the device.
2. User presses button 1. This gathers baseline data and takes approximately 80-100
   seconds.
3. After baseline completes, user inserts sample in the device.
4. User presses button 2. This gathers sampling data and also takes 80-100 seconds.
   a. Once the sampling completes, a quality control test is run on both data sets
      unknown to the user. This is to ensure that the readout is not a false +/-.
   b. If the data passes the quality control step, the dirac calculation is performed.
      The result will be displayed using the LEDs.
5. After interpreting the LED lights (see below), the user will press button 3 to
   return the board to an idle state.
"""

# SAMPLING PARAMETERS
SEC = 80  # was 5 TODO: # HOW LONG TO SAMPLE FOR
ADC_SAMPLING_RATE = 250  # DESIRED SAMPLING RATE FOR ADC


# =================================================================================
# THREAD VARIABLES
# =================================================================================
stop_sampling_process = False
running = True
ready_for_sample = False
mean_dirac_forward_sweep = 0
mean_dirac_reverse_sweep = 0


# =================================================================================
# LIMITS CONFIG
# =================================================================================
# LIMITS HARD CODED
# float(input("Enter upper limit of gate voltage to be scanned:"))
upp_lim = 1.25
# float(input("Enter lower limit of gate voltage to be scanned:"))
low_lim = -1.25


# =================================================================================
# SLOPE/PEAK DETECTION CONFIG
# =================================================================================
slope_range = 25  # t-n / if errors try 35
# WAS 8 #Number of sweeps to look for in each direction (MAX): 8 mean 16 intotal
secs = 16
fig_time_max = 80  # sec time frame of data
NN = 100000  # Array size for raw data


# =================================================================================
# GPIO CONFIG
# =================================================================================
GPIO_RESET = False  # Whether GPIOs should be re-exported
GPIO_PATH = "/sys/class/gpio"
GPIO_DIR_OUT = "in"
GPIO_VAL_HI = "1"
GPIO_VAL_LO = "0"

GPIO_CHAN_NUM_LED_RGB_RED = "149"       # RGB RED
GPIO_CHAN_NUM_LED_RGB_GREEN = "148"     # RGB GREEN
GPIO_CHAN_NUM_LED_RGB_BLUE = "147"      # RGB BLUE

GPIO_CHAN_NUM_LED_GREEN = "143"         # GREEN
GPIO_CHAN_NUM_LED_BLUE = "142"          # RED
GPIO_CHAN_NUM_LED_BLUE = "146"          # AMBER

# GPIO_CHAN_NUM_BUTTON1 = "48"           #BUTTON #1 !! DISABLED DUE TO CONFLICT IN DEVICE TREE!!
GPIO_CHAN_NUM_BUTTON2 = "72"  # BUTTON #2 NOT USED AT THE MOMENT
GPIO_CHAN_NUM_BUTTON3 = "106"  # BUTTON #3


# STRUCTURE OF THE OUTPUT FILE - IF CHANGED: CHANGE THE WRITE_TO_FILE ORDER AS WELL
raw_data_file_header = ['Time', 'd_time', 's_time', 'fs_time', 'Gate Voltage', 'Ids',
                        'raw_adc_binary_ch1', 'raw_adc_binary_ch2', 'raw_adc_voltage_ch1', 'raw_adc_voltage_ch2', 'Slope', 'Peak']
dirac_voltage_summary_file_header = ['Dirac Voltages', 'Sweep Type', 'Result']
# config_string = "" #FOR SAVING CONFIG FILE


# =================================================================================
# Enable SPI: /dev/spidev<bus>.<device>
# =================================================================================
bus = 0
device = 0
spi = spidev.SpiDev()
spi.open(bus, device)
# SETTINGS
spi.max_speed_hz = 10000000
spi.mode = 0b00
spi.cshigh = False


# =================================================================================
# MCP3561:
# =================================================================================
# SUPPORTS MODE: 0,0 and 1,1
#
# COMMAND BYTES
# =================================================================================
# CMD[7] CMD[6]          | CMD[5] CMD[4] CMD[3] CMD[2]           | CMD[1] CMD[0]
# Device Address Bits    | Register Address/Fast Command Bits    | Command Type Bits
# ---------------------------------------------------------------------------------
# Hard-coded in device   | Read or write address;                | Incremental Write
#                       | All registers can be read             | Incremental Read
#                       |                                       | Static Read
#                       |                                       | Fast command
#
# 2 bits: CMD[7] CMD[6] - Hard coded into device
mcp3562_internal_device_addr = 0b01


# SCAN MODE OR MUX MODE
# Scan mode: select multiple channels for a scan-cycle, or mux-mode for manually switching between channels
adc_scan_mode = False

# Scan mode: use continious, else one-shot
# Continuous Conversion mode or continuous conversion cycle in SCAN mode
CONV_MODE_CONTINIOUS = 0b11
# One-shot conversion or one-shot cycle in SCAN mode. It sets ADC_MODE[1:0] to ‘10’ (standby) at the end of the conversion or at the end of the conversion cycle in SCAN mode.
CONV_MODE_ONE_SHOT_STANDBY = 0b10
# One-shot conversion or one-shot cycle in SCAN mode. It sets ADC_MODE[1:0] to ‘0x’ (ADC Shutdown) at the end of the conversion or at the end of the conversion cycle in SCAN mode (default)
CONV_MODE_ONE_SHOT_SHUTDOWN = 0b00
conv_mode = CONV_MODE_ONE_SHOT_STANDBY

# If One-shot, then standby, else conversion mode
ADC_MODE_CONVERSION_MODE = 0b11
ADC_MODE_STANDBY_MODE = 0b10
ADC_MODE_SHUTDOWN_MODE = 0b00
adc_mode = ADC_MODE_STANDBY_MODE


# 24 or 32 bit output (32 for scan mode)
ADC_OUTPUT_24bit = 0b00
ADC_OUTPUT_32bit = 0b11
adc_output_size = ADC_OUTPUT_24bit

# SCAN MODE SETTINGS
# DELAY BETWEEN CONVERSIONS
SCAN_MODE_DELAY_512 = 0b111  # 512 x DMCLK
SCAN_MODE_DELAY_256 = 0b110  # 256 x DMCLK
SCAN_MODE_DELAY_128 = 0b101  # 128 x DMCLK
SCAN_MODE_DELAY_64 = 0b100  # 64 x DMCLK
SCAN_MODE_DELAY_32 = 0b011  # 32 x DMCLK
SCAN_MODE_DELAY_16 = 0b010  # 16 x DMCLK
SCAN_MODE_DELAY_8 = 0b001  # 8 x DMCLK
SCAN_MODE_DELAY_0 = 0b000  # NO DELAY

scan_mode_delay = SCAN_MODE_DELAY_512

# ==========================================
# MCP3561: ADC MUX MODES:
# ==========================================
ADC_MUX_MODE1 = 0  # MUX DIFF V+ vs V-: CH0 vs CH1
ADC_MUX_MODE2 = 1  # MUX DIFF V+ vs V-: CH2 vs CH3

ADC_MUX_MODE3 = 2  # MUX V+ vs V-: CH0 vs AGND
ADC_MUX_MODE4 = 3  # MUX V+ vs V-: CH1 vs AGND
ADC_MUX_MODE5 = 4  # MUX V+ vs V-: CH2 vs AGND
ADC_MUX_MODE6 = 5  # MUX V+ vs V-: CH3 vs AGND

ADC_MUX_MODE7 = 6  # MUX V+ vs V-: Internal Temp P vs AGND - WORKS
ADC_MUX_MODE8 = 7  # MUX V+ vs V-: Internal Temp M vs AGND

ADC_MUX_MODE9 = 8  # MUX Vref+ vs Vref-

# SELECTED MODE - NOT USED IN SCAN MODE
mux_selection_1 = ADC_MUX_MODE4
mux_selection_2 = ADC_MUX_MODE5


mux_commands_index = [0b00000001,  # MUX DIFF V+ vs V-: CH0 vs CH1
                      0b00100011,  # MUX DIFF V+ vs V-: CH2 vs CH3

                      0b00001000,  # MUX V+ vs V-: CH0 vs AGND
                      0b00011100,  # MUX V+ vs V-: CH1 vs REFIN-
                      0b00101100,  # MUX V+ vs V-: CH2 vs REFIN-
                      0b00111000,  # MUX V+ vs V-: CH3 vs AGND

                      0b11101000,  # MUX V+ vs V-: Internal Temp P vs AGND
                      0b11011000,  # MUX V+ vs V-: Internal Temp M vs AGND

                      0b10111100,  # MUX Vref+ vs Vref-
                      ]

# =========================================
# MCP3561: CONFIG SETUP
# =========================================

# CLK SOURCE DEFINES:
# =========================================
CONFIG_CLK_EXT = 0
CONFIG_CLK_INT = 1
CONFIG_CLK_INT_W_OUTPUT = 2

# SELECT CLK SOURCE:
CONFIG_CLK_SEL = CONFIG_CLK_INT


# OSR SELECT
# =========================================
# VALID VALUES:
# CONFIG_OSR = 32
# CONFIG_OSR = 64
# CONFIG_OSR = 128
CONFIG_OSR = 256  # DEFAULT
# CONFIG_OSR = 512
# CONFIG_OSR = 1024
# CONFIG_OSR = 2048
# CONFIG_OSR = 4096
# CONFIG_OSR = 8192
# CONFIG_OSR = 16384
# CONFIG_OSR = 20480
# CONFIG_OSR = 24576
# CONFIG_OSR = 40960
# CONFIG_OSR = 49152
# CONFIG_OSR = 81920
# CONFIG_OSR = 98304


# =================================================================================
# MCP3561: REGISTERS AND COMANDS
# =================================================================================

# FAST COMMAND BITS: source: datasheet p60
# ADC Conversion Start/Restart Fast Command (overwrites ADC_MODE[1:0] = 11)
mcp3562_cmd_conversion_start = 0b1010
# ADC Standby Mode Fast Command (overwrites ADC_MODE[1:0] = 10)
mcp3562_cmd_standby = 0b1011
# ADC Shutdown Mode Fast Command (overwrites ADC_MODE[1:0] = 00)
mcp3562_cmd_shutdown = 0b1100
# Full Shutdown Mode Fast Command (overwrites CONFIG0[7:0] = 0x00)
mcp3562_cmd_full_shutdown = 0b1101
# Device Full Reset Fast Command (resets the entire register map to default value)
mcp3562_cmd_full_reset = 0b1110

# COMMAND TYPES: source: datasheet p60
mcp3562_cmd_type_inc_write = 0b10
mcp3562_cmd_type_inc_read = 0b11
mcp3562_cmd_type_static_read = 0b01
mcp3562_cmd_type_fast_cmd = 0b00

# INTERNAL REGISTER LIST
# Latest A/D conversion data output value (24 or 32 bits depending on DATA_FORMAT[1:0])
mcp3562_reg_adcdata = 0x0
# ADC Operating mode, Master Clock mode and Input Bias Current Source mode
mcp3562_reg_config0 = 0x1
mcp3562_reg_config1 = 0x2  # Prescale and OSR settings
# ADC boost and gain settings, auto-zeroing settings for analog multiplexer, voltage reference and ADC
mcp3562_reg_config2 = 0x3
mcp3562_reg_config3 = 0x4  # Conversion mode, data and CRC format settings; enable for CRC on communications, enable for digital offset and gain error calibrations
# IRQ Status bits and IRQ mode settings; enable for Fast commands and for conversion start pulse
mcp3562_reg_irq = 0x5
mcp3562_reg_mux = 0x6  # Analog multiplexer input selection (MUX mode only)
mcp3562_reg_scan = 0x7  # SCAN mode settings
mcp3562_reg_timer = 0x8  # Delay value for TIMER between scan cycles
mcp3562_reg_offsetcal = 0x9  # ADC digital offset calibration value
mcp3562_reg_gaincal = 0xA  # ADC digital gain calibration value
mcp3562_reg_lock = 0xD  # Password value for SPI Write mode locking
mcp3562_reg_crccfg = 0xF  # CRC checksum for device configuration


# MESSAGES/COMMANDS
# =========================================
# MESSAGES: WAIT FOR NEW DATA
msg1 = 0b00000000
msg1 |= mcp3562_internal_device_addr << 6
msg1 |= mcp3562_reg_irq << 2
msg1 |= mcp3562_cmd_type_static_read
msg_wait_for_data2 = [msg1, 0b00000000]

# MESSAGES: WAIT FOR NEW DATA FROM STATUS BITS - FASTER
msg1 = 0b00000000
msg1 |= mcp3562_internal_device_addr << 6
msg1 |= mcp3562_reg_irq << 2
msg1 |= mcp3562_cmd_type_static_read
msg_wait_for_data = [msg1]

# MESSAGES: READ DATA
msg1 = 0b00000000
msg1 |= mcp3562_internal_device_addr << 6
msg1 |= mcp3562_reg_adcdata << 2
msg1 |= mcp3562_cmd_type_static_read
if adc_output_size == ADC_OUTPUT_24bit:  # 24 bit
    msg_read_data = [msg1, 0b00000000, 0b00000000, 0b00000000]
else:  # 32 bit
    msg_read_data = [msg1, 0b00000000, 0b00000000, 0b00000000, 0b00000000]


def set_config_bits():

    _config = arr.array('i')  # create empty array

    # CONFIG0: CLK-source - ONLY ENABLE ONE OF THESE
    # =========================================
    if CONFIG_CLK_SEL == CONFIG_CLK_EXT:
        _config.append(0b11000000 | conv_mode)  # CONFIG0: External clock
    elif CONFIG_CLK_SEL == CONFIG_CLK_INT_W_OUTPUT:
        # CONFIG0: Internal oscilator + OUTPUT AMCLK on pin: 4.55MHz ish (can be 3.33-6.66MHz)
        _config.append(0b11110000 | conv_mode)
    elif CONFIG_CLK_SEL == CONFIG_CLK_INT:
        # CONFIG0: Internal oscilator selected for testing only
        _config.append(0b11100000 | conv_mode)
    else:
        # CONFIG0: Internal oscilator selected for testing only
        _config.append(0b11100000 | conv_mode)
        print("CONFIG ERROR: CLK_SEL-VALUE IS NOT CORRECT!")

    # CONFIG1: OSR - ONLY ENABLE ONE OF THESE
    # =========================================
    if CONFIG_OSR == 32:
        _config.append(0b00000000)
    elif CONFIG_OSR == 64:
        _config.append(0b00000100)
    elif CONFIG_OSR == 128:
        _config.append(0b00001000)
    elif CONFIG_OSR == 256:
        _config.append(0b00001100)
    elif CONFIG_OSR == 512:
        _config.append(0b00010000)
    elif CONFIG_OSR == 1024:
        _config.append(0b00010100)
    elif CONFIG_OSR == 2048:
        _config.append(0b00011000)
    elif CONFIG_OSR == 4096:
        _config.append(0b00011100)
    elif CONFIG_OSR == 8192:
        _config.append(0b00100000)
    elif CONFIG_OSR == 16384:
        _config.append(0b00100100)
    elif CONFIG_OSR == 20480:
        _config.append(0b00101000)
    elif CONFIG_OSR == 24576:
        _config.append(0b00101100)
    elif CONFIG_OSR == 40960:
        _config.append(0b00110000)
    elif CONFIG_OSR == 49152:
        _config.append(0b00110100)
    elif CONFIG_OSR == 81920:
        _config.append(0b00111000)
    elif CONFIG_OSR == 98304:
        _config.append(0b00111100)
    else:
        _config.append(0b00001100)  # DEFAULT 256
        print("CONFIG ERROR: OSR-VALUE IS NOT CORRECT!")

    # CONFIG2: - ONLY ENABLE ONE OF THESE
    # =========================================
    # 0b10001111, #CONFIG2 DOUBLES CONVERSION TIME
    # 0b10001011, #CONFIG2 HALVES CONVERSION TIME BUT DOESN'T USE OFFSET CANCELLATION
    _config.append(0b10001011)  # CONFIG2

    # CONFIG3: - ONLY ENABLE ONE OF THESE
    # =========================================
    # 0b10000000, #CONFIG3 ONE-SHOT CONVERSION MODE - NOT USED
    # _config.append(0b11000000) #CONFIG3 CONTINIOUS CONVERSION MODE
    # CONFIG3 ONE SHOT CONVERSION MODE 24bit output
    _config.append(0b11000000 | (adc_output_size << 4))

    # IRQ REG: - ONLY ENABLE ONE OF THESE
    # =========================================
    # _config.append(0b00110111)  #IRQ: does not require pull-up in IRQ pin
    # IRQ: does not require pull-up in IRQ pin CONV-START-IRQ DISABLED
    # 0b00110110,  #IRQ: does not require pull-up in IRQ pin, DISABLE START-CONV-IRQ - NOT USED
    _config.append(0b00110110)

    # MUX REG: - ONLY ENABLE ONE OF THESE - NOT USED: USING SCAN MODE INSTEAD
    # =========================================
    _config.append(mux_commands_index[mux_selection_1])

    # ONLY ENABLE ONE OF THESE
    # SCAN REG - 24bit: if enabled, mux mode does not matter
    if(adc_scan_mode):
        _config.extend([(0b00000000 | (scan_mode_delay << 5)),
                        0b00000000, 0b00000110])  # CH1 + CH2
    else:
        # ALL ZEROS, SCAN MODE DISABLED
        _config.extend([0b00000000, 0b00000000, 0b00000000])

    # TIME = n * DMCLK, DMCLK = MCLK/4
    # ONLY ENABLE ONE OF THESE
    # TIMER REG - 24 bit: [NB: Seems to only work when in SCAN MODE]
    # 0b00000000, 0b00000000, 0b00000000, #NO DELAY BETWEEN SAMPLES
    # 0b00000000, 0b00000001, 0b01000000, # Approx 1000Hz, w. OSR 256, Int. XTAL
    # _config.extend([0b00000000, 0b00001100, 0b11000000]) #, #Approx 1000Hz, w. OSR 256, Ext XTAL: 10MHz
    # 0b11111111, 0b11111111, 0b11111111, #MAX DELAY BETWEEN SAMPLES

    # 32765 @ 20MHz = 0.00655sec between reads
    #_config.extend([0b00000000, 0b10000000, 0b00000000])

    # 5000 @ 20MHz = 0.001sec between reads
    #_config.extend([0b00000000, 0b00001100, 0b10001000])

    # 5000 @ 20MHz = 0.001sec between reads
    _config.extend([0b00000000, 0b00000000, 0b00000000])

    #_config.extend([0b00001010, 0b00000110, 0b10000000])

    return _config


def write_init_config():

    config = arr.array('i')  # create empty array

    # Sets the first address to write to - the addres will automatically increment after being written
    msg = 0b00000000
    msg |= mcp3562_internal_device_addr << 6
    # START ADDR, the rest will automatically follow due to auto increment of addr
    msg |= mcp3562_reg_config0 << 2
    msg |= mcp3562_cmd_type_inc_write

    #config_commands_inc_write[0] = msg
    #reply = spi.xfer2(config_commands_inc_write)
    config.append(msg)

    config_array = set_config_bits().tolist()
    config.extend(config_array)
    # print(config.tolist())
    reply = spi.xfer2(config.tolist())

    return 0


def start_conversion():
    msg = 0b00000000
    msg |= mcp3562_internal_device_addr << 6
    msg |= mcp3562_cmd_conversion_start << 2
    msg |= mcp3562_cmd_type_fast_cmd
    msg2 = [msg]
    reply = spi.xfer2(msg2)

# READ CONFIG REGISTERS


def read_config(do_print):

    config_string = ""

    if do_print == True:
        print("\n========================================================")
        print("CONFIG")
        print("========================================================")
    config_string += ("CONFIG:\n")

    # READ CONFIG0 REG
    msg = 0b00000000
    msg |= mcp3562_internal_device_addr << 6
    msg |= mcp3562_reg_config0 << 2
    msg |= mcp3562_cmd_type_static_read
    msg2 = [msg, 0b00000000]
    reply = spi.xfer2(msg2)

    if do_print == True:
        print(" - CONFIG0:\t0b", format(reply[1], '08b'))
    config_string += (" - CONFIG0:\t0b"+format(reply[1], '08b')+"\n")

    # READ CONFIG1 REG
    msg = 0b00000000
    msg |= mcp3562_internal_device_addr << 6
    msg |= mcp3562_reg_config1 << 2
    msg |= mcp3562_cmd_type_static_read
    msg2 = [msg, 0b00000000]
    reply = spi.xfer2(msg2)

    if do_print == True:
        print(" - CONFIG1:\t0b", format(reply[1], '08b'))
    config_string += (" - CONFIG1:\t0b"+format(reply[1], '08b') + "\n")

    # READ CONFIG2 REG
    msg = 0b00000000
    msg |= mcp3562_internal_device_addr << 6
    msg |= mcp3562_reg_config2 << 2
    msg |= mcp3562_cmd_type_static_read
    msg2 = [msg, 0b00000000]
    reply = spi.xfer2(msg2)

    if do_print == True:
        print(" - CONFIG2:\t0b", format(reply[1], '08b'))
    config_string += (" - CONFIG2:\t0b"+format(reply[1], '08b') + "\n")

    # READ CONFIG3 REG
    msg = 0b00000000
    msg |= mcp3562_internal_device_addr << 6
    msg |= mcp3562_reg_config3 << 2
    msg |= mcp3562_cmd_type_static_read
    msg2 = [msg, 0b00000000]
    reply = spi.xfer2(msg2)

    if do_print == True:
        print(" - CONFIG3:\t0b", format(reply[1], '08b'))
    config_string += (" - CONFIG3:\t0b"+format(reply[1], '08b') + "\n")

    # READ IRQ REG
    msg = 0b00000000
    msg |= mcp3562_internal_device_addr << 6
    msg |= mcp3562_reg_irq << 2
    msg |= mcp3562_cmd_type_static_read
    msg2 = [msg, 0b00000000]
    reply = spi.xfer2(msg2)

    if do_print == True:
        print(" - IRQ-REG:\t0b", format(reply[1], '08b'))
    config_string += (" - IRQ-REG:\t0b"+format(reply[1], '08b') + "\n")

    # READ MUX REG
    msg = 0b00000000
    msg |= mcp3562_internal_device_addr << 6
    msg |= mcp3562_reg_mux << 2
    msg |= mcp3562_cmd_type_static_read
    msg2 = [msg, 0b00000000]
    reply = spi.xfer2(msg2)

    if do_print == True:
        print(" - MUX-REG:\t0b", format(reply[1], '08b'))
    config_string += (" - MUX-REG:\t0b"+format(reply[1], '08b') + "\n")

    # READ SCAN REG
    msg = 0b00000000
    msg |= mcp3562_internal_device_addr << 6
    msg |= mcp3562_reg_scan << 2
    msg |= mcp3562_cmd_type_static_read
    msg2 = [msg, 0b00000000, 0b00000000, 0b00000000]
    reply = spi.xfer2(msg2)

    if do_print == True:
        print(" - SCAN-REG:\t[23:16] 0b", format(reply[1], '08b'), "\t[15:8] 0b",
              format(reply[2], '08b'), "\t[7:0] 0b", format(reply[3], '08b'))
    config_string += (" - SCAN-REG:\t[23:16] 0b"+format(reply[1], '08b')+"\t[15:8] 0b"+format(
        reply[2], '08b')+"\t[7:0] 0b"+format(reply[3], '08b') + "\n")

    # READ TIMER REG
    msg = 0b00000000
    msg |= mcp3562_internal_device_addr << 6
    msg |= mcp3562_reg_timer << 2
    msg |= mcp3562_cmd_type_static_read
    msg2 = [msg, 0b00000000, 0b00000000, 0b00000000]
    reply = spi.xfer2(msg2)

    if do_print == True:
        print(" - TIMER-REG:\t[23:16] 0b", format(reply[1], '08b'), "\t[15:8] 0b",
              format(reply[2], '08b'), "\t[7:0] 0b", format(reply[3], '08b'))
    config_string += (" - TIMER-REG:\t[23:16] 0b"+format(reply[1], '08b')+"\t[15:8] 0b"+format(
        reply[2], '08b')+"\t[7:0] 0b"+format(reply[3], '08b') + "\n")

    # READ GAINCAL REG
    msg = 0b00000000
    msg |= mcp3562_internal_device_addr << 6
    msg |= mcp3562_reg_gaincal << 2
    msg |= mcp3562_cmd_type_static_read
    msg2 = [msg, 0b00000000, 0b00000000, 0b00000000]
    reply = spi.xfer2(msg2)

    if do_print == True:
        print(" - GAINCAL-REG:\t[23:16] 0b", format(reply[1], '08b'), "\t[15:8] 0b",
              format(reply[2], '08b'), "\t[7:0] 0b", format(reply[3], '08b'))
    config_string += (" - GAINCAL-REG:\t[23:16] 0b"+format(reply[1], '08b')+"\t[15:8] 0b"+format(
        reply[2], '08b')+"\t[7:0] 0b"+format(reply[3], '08b') + "\n")

    # READ LOCK REG
    msg = 0b00000000
    msg |= mcp3562_internal_device_addr << 6
    msg |= mcp3562_reg_lock << 2
    msg |= mcp3562_cmd_type_static_read
    msg2 = [msg, 0b00000000]
    reply = spi.xfer2(msg2)

    if do_print == True:
        print(" - LOCK-REG:\t0b", format(reply[1], '08b'))
    config_string += (" - LOCK-REG:\t0b"+format(reply[1], '08b') + "\n")

    # READ CRCCFG REG
    msg = 0b00000000
    msg |= mcp3562_internal_device_addr << 6
    msg |= mcp3562_reg_crccfg << 2
    msg |= mcp3562_cmd_type_static_read
    msg2 = [msg, 0b00000000, 0b00000000]
    reply = spi.xfer2(msg2)

    if do_print == True:
        print(" - CRCCFG-REG:\t[15:8] 0b", format(reply[1],
                                                  '08b'), "\t [7:0] 0b", format(reply[2], '08b'))
    config_string += (" - CRCCFG-REG:\t[15:8] 0b"+format(
        reply[1], '08b')+"\t [7:0] 0b"+format(reply[2], '08b') + "\n")

    # time.sleep(2)

    return config_string

# Read ADC values (32 bits) - Works


def read_adc_d_24():

    reply = spi.xfer2(msg_read_data)
    adc = (reply[1] << 16) + (reply[2] << 8) + (reply[3])

    return adc


# Check for new sample: works


def wait_for_data():

    reply = spi.xfer2(msg_wait_for_data)

    if (reply[0] & 0b00000100) >> 2 == 1:
        return True  # WAIT
    else:
        return False  # DATA READY

    reply = spi.xfer2(msg_wait_for_data2)


    if (reply[1] & 0b01000000) >> 6 == 1:
        # if (reply[0] & 0b00000100) > 0:
        return True  # WAIT
    else:
        return False  # DATA READY

# SET SCAN CHANNEL
# 24 bits register


def set_scan_reg():

    # repeat for all config bytes
    msg = 0b00000000
    msg |= mcp3562_internal_device_addr << 6
    msg |= mcp3562_reg_scan << 2
    msg |= mcp3562_cmd_type_inc_write

    # DELAY TIME = n * DMCLK, DMCLK = MCLK/4
    # if channel == 0:
    msg2 = [msg, 0b11100000, 0b00000000, 0b00000110]
    # elif channel == 1:
    #    msg2 = [msg, 0b00000000, 0b00000000, 0b00000010] #CH1 SINGLE
    # elif channel == 2:
    #    msg2 = [msg, 0b00000000, 0b00000000, 0b00000100] #CH2 SINGLE
    # elif channel == 3:
    #    msg2 = [msg, 0b00000000, 0b00000000, 0b00001000] #CH3 SINGLE
    # else:
    #    msg2 = [msg, 0b00000000, 0b00000000, 0b00000001] #CH0 SINGLE
    #print("CONFIG ERROR: SCAN CHANNEL WAS NOT SET CORRECTLY!")

    # msg2 = [msg, 0b00000000, 0b00010000, 0b00000000] #TEMP
    # msg2 = [msg, 0b00000000, 0b00000000, 0b00000001] #CH0 SINGLE
    # msg2 = [msg, 0b00000000, 0b00000000, 0b00000000] #SCAN MODE DISABLED

    reply = spi.xfer2(msg2)

    return 0

# MOVED TO write_init_config()
# 24 bits


def set_timer_reg():

    # repeat for all config bytes
    msg = 0b00000000
    msg |= mcp3562_internal_device_addr << 6
    msg |= mcp3562_reg_timer << 2
    msg |= mcp3562_cmd_type_inc_write
    msg2 = [msg, 0b00000000, 0b00000000, 0b00000000]
    #msg2 = [msg, 0b10000000, 0b00000000, 0b00000000]
    #msg2 = [msg, 0b11111111, 0b11111111, 0b11111111]
    reply = spi.xfer2(msg2)

    return 0

# MOVED TO write_init_config() list
# NOT USED ANYMODE


def set_mux_mode(mux_selection):

    # Sets the first address to write to - the addres will automatically increment after being written
    msg = 0b00000000
    msg |= mcp3562_internal_device_addr << 6
    msg |= mcp3562_reg_mux << 2
    msg |= mcp3562_cmd_type_inc_write

    write_array = [msg, mux_commands_index[mux_selection]]

    reply = spi.xfer2(write_array)
    # if reply != 0
    #    return 1

    # TODO: READ CONFIG BACK TO CHECK SETUP

    return 0


def conv_raw_adc_to_voltage(adc_value,channel_name):

    # CONVERT TO STRING
    val_str = bin(adc_value)

    # 2'S COMPLEMENT CONVERSION
    bytes = 3
    val = int(val_str, 2)
    b = val.to_bytes(bytes, byteorder=sys.byteorder, signed=False)
    raw_adc_value = int.from_bytes(b, byteorder=sys.byteorder, signed=True)

    # SCALING TO VOLTAGE
    if channel_name == 'B':
        voltage = ADC_CALIBRATION_OFFSET + (ADC_CALIBRATION_GAIN*VOLTAGE_SCALE * raw_adc_value) / FULL_SCALE_RESOLUTION # TODO: SET refV in settings
    else:
        pre = (VOLTAGE_SCALE * raw_adc_value) / FULL_SCALE_RESOLUTION
        voltage = TIA_GAIN_1*pre*pre*pre + TIA_GAIN_2*pre*pre + TIA_GAIN_3*pre + TIA_GAIN_4

    return voltage


def check_internet():
    IPaddress=socket.gethostbyname(socket.gethostname())
    if IPaddress=="127.0.0.1":
        # Exit from script - send no connect message to remote script and exit
        print("[ERROR] Internet check: No Internet Connection Present\nSTOPPING")
        exit()
    else:
        print("Internet check: Connected to Internet")
        return IPaddress

# ================================================================================
# GPIO CONTROL : CANCEL THREAD, PRESS BUTTON #2 AND #3 when sampling to cancel
# ================================================================================
class cancelThread (threading.Thread):

    def __init__(self, threadID, name):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name

    def run(self):

        global stop_sampling_process

        while True:
            valueFile_button2 = open(GPIO_PATH+'/gpio'+GPIO_CHAN_NUM_BUTTON2+'/value', 'r')
            button_pressed2 = valueFile_button2.read(1)
            valueFile_button2.close()

            valueFile_button3 = open(GPIO_PATH+'/gpio'+GPIO_CHAN_NUM_BUTTON3+'/value', 'r')
            button_pressed3 = valueFile_button3.read(1)
            valueFile_button3.close()

            if(button_pressed2 == '0' and button_pressed3 == '0'):
                print("BOTH BUTTONS PRESSED in cancelthread...\n")
                stop_sampling_process = True

            time.sleep(1)
                


# ================================================================================
# GPIO CONTROL : BLUE LED THREAD, blinking while measureing
# ================================================================================
class ledThread (threading.Thread):

    def __init__(self, threadID, name, mode):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.sampling_mode = mode

    def run(self):

        global running
        global ready_for_sample

        while(running):
            if(self.sampling_mode == THREAD_SAMPLING_MODE_BASELINE):#BASELINE
                valueFile_LED_RGB_BLUE = open(GPIO_PATH+'/gpio'+GPIO_CHAN_NUM_LED_RGB_BLUE+'/value', 'w')
                time_start = time.time()
                while time.time()-time_start < SEC+2 and running:
                    valueFile_LED_RGB_BLUE.write(GPIO_VAL_HI)
                    valueFile_LED_RGB_BLUE.flush()
                    time.sleep(0.5)
                    valueFile_LED_RGB_BLUE.write(GPIO_VAL_LO)
                    valueFile_LED_RGB_BLUE.flush()
                    time.sleep(0.5)

                valueFile_LED_RGB_BLUE.close()

                #FINISHED SAMPLING OR CANCELLED BASELINE READ - EXIT THREAD
                return

            elif(self.sampling_mode == THREAD_SAMPLING_MODE_WAIT_FOR_SAMPLE):#SAMPLE
                valueFile_LED_RGB_GREEN = open(GPIO_PATH+'/gpio'+GPIO_CHAN_NUM_LED_RGB_GREEN+'/value', 'w')
                time_start = time.time()
                
                while running and not ready_for_sample: # time.time()-time_start < SEC+2: #TODO: HOW LONG TO WAIT FOR A SAMPLE???

                    valueFile_LED_RGB_GREEN.write(GPIO_VAL_HI)
                    valueFile_LED_RGB_GREEN.flush()
                    time.sleep(0.5)
                    valueFile_LED_RGB_GREEN.write(GPIO_VAL_LO)
                    valueFile_LED_RGB_GREEN.flush()
                    time.sleep(0.5)

                #TODO: MAKE SURE WE CLOSE THIS AGAIN
                valueFile_LED_RGB_GREEN.close()

                #FINISHED SAMPLING OR CANCELLED AFTER BASELINE READ - EXIT THREAD
                return

            else:#SAMPLE
                valueFile_LED_RGB_RED = open(GPIO_PATH+'/gpio'+GPIO_CHAN_NUM_LED_RGB_RED+'/value', 'w')
                time_start = time.time()
                while time.time()-time_start < SEC+2 and running:

                    valueFile_LED_RGB_RED.write(GPIO_VAL_HI)
                    valueFile_LED_RGB_RED.flush()
                    time.sleep(0.5)
                    valueFile_LED_RGB_RED.write(GPIO_VAL_LO)
                    valueFile_LED_RGB_RED.flush()
                    time.sleep(0.5)

                valueFile_LED_RGB_RED.close()

                #FINISHED SAMPLING OR CANCELLED BASELINE READ - EXIT THREAD
                return
    

        #TERMINATE THIS THREAD EARLY
        if not running:

            #SHUT OFF LEDS IF THREAD IS NOT RUNNING
            valueFile_LED_RGB_BLUE = open(GPIO_PATH+'/gpio'+GPIO_CHAN_NUM_LED_RGB_BLUE+'/value', 'w')
            valueFile_LED_RGB_BLUE.write(GPIO_VAL_LO)
            valueFile_LED_RGB_BLUE.flush()
            valueFile_LED_RGB_BLUE.close()

            valueFile_LED_RGB_GREEN = open(GPIO_PATH+'/gpio'+GPIO_CHAN_NUM_LED_RGB_GREEN+'/value', 'w')
            valueFile_LED_RGB_GREEN.write(GPIO_VAL_LO)
            valueFile_LED_RGB_GREEN.flush()
            valueFile_LED_RGB_GREEN.close()

            valueFile_LED_RGB_RED = open(GPIO_PATH+'/gpio'+GPIO_CHAN_NUM_LED_RGB_RED+'/value', 'w')
            valueFile_LED_RGB_RED.write(GPIO_VAL_LO)
            valueFile_LED_RGB_RED.flush()
            valueFile_LED_RGB_RED.close()
            return



# ================================================================================
# SAMPLING THREAD
# ================================================================================
class samplingThread (threading.Thread):

    sampling_mode = 0
    filename_str = ""

    def __init__(self, threadID, name, mode, timestamp):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.sampling_mode = mode #BASELINE OR SAMPLING
        self.filename_str = timestamp

    def run(self):
        #   print ("Starting " + self.name)
        #   print_time(self.name, self.counter, 5)
        #   print ("Exiting " + self.name)

        # INITIATE ARRAYS
        # =============================================================

        # Required arrays:
        _adc_A = arr.array("i", [0]*NN)  # Raw adc data ch1
        _adc_B = arr.array("i", [0]*NN)  # raw ADC data ch2

        _voltage_A = arr.array("d", [0]*NN)  # voltage data ch1
        _voltage_B = arr.array("d", [0]*NN)  # voltage data ch2

        _time = arr.array("d", [0]*NN)  # Sys time - start_time

        # Delta time between sampling two data channels
        _d_time = arr.array("d", [0]*NN)

        # total sampling time incluting mux config, sampling and read data for 2x channels
        _s_time = arr.array("d", [0]*NN)

        _fs_time = arr.array("d", [0]*NN)  # Sampling f - desired at sampling frequency

        _slope = arr.array("i", [0]*NN)
        _peak = arr.array("i", [0]*NN)

        index_t = 0

        t_start = time.time()
        last_conv_time = time.time()

        global running
        global mean_dirac_forward_sweep
        global mean_dirac_reverse_sweep

    
        # START SAMPLING LOOP
        while (((t_start+SEC) > time.time()) or (index_t < SEC*ADC_SAMPLING_RATE)):  # Sample for x secs

            #TERMINATE THIS THREAD EARLY IF TEST IS CANCELLED
            if not running:
                return

            # WAIT TILL YOU ARE READY TO TAKE NEXT SAMPLE
            while (time.time() - last_conv_time < (1.0/ADC_SAMPLING_RATE)):
                m = 1

            _fs_time[index_t] = time.time() - last_conv_time
            last_conv_time = time.time()

            _time[index_t] = time.time() - t_start
            time_conv_start = time.time()  # START CONV
            set_mux_mode(mux_selection_1)
            start_conversion()

            while wait_for_data() == True:
                m = 1
            time_sample1_end = time.time()  # END CONV
            _adc_A[index_t] = read_adc_d_24()

            set_mux_mode(mux_selection_2)
            start_conversion()
            while wait_for_data() == True:
                m = 1
            time_sample2_end = time.time()  # END CONV
            _adc_B[index_t] = read_adc_d_24()

            if USE_FAKE_DATA:
                # Change Ids data
                gate_voltage_prev = 0
                gate_voltage = 4.096 + (conv_raw_adc_to_voltage(_adc_B[index_t],'B')-4.096)*1.332
                if index_t > 0:
                    gate_voltage_prev = 4.096 + (conv_raw_adc_to_voltage(_adc_B[index_t-1],'B')-4.096)*1.332
                    gate_voltage = 4.096 + (conv_raw_adc_to_voltage(_adc_B[index_t],'B')-4.096)*1.332
                    slope_for_fake_data = gate_voltage - gate_voltage_prev
                    if slope_for_fake_data >= 0:
                        fake_voltage_channel2 = 0.15 * (gate_voltage*gate_voltage) + .165
                        _voltage_A[index_t] = (fake_voltage_channel2)
                    else:
                        fake_voltage_channel2 = 0.15 * (gate_voltage*gate_voltage) + .15
                        _voltage_A[index_t] = (fake_voltage_channel2)


            time_conv_end = time.time()  # END CONV
            _s_time[index_t] = time_conv_end - time_conv_start

            _d_time[index_t] = time_sample2_end - time_sample1_end

            index_t += 1

        t_end = time.time()

        # =============================================================================
        # POST PROCESSING - FIND SECTIONS BETWEEN PEAKS ON TRIAGLE
        # =============================================================================

        #TERMINATE THIS THREAD EARLY IF TEST IS CANCELLED
        if not running:
            return

        os.system("echo 1 > /sys/class/gpio/gpio146/value")  # AMBER
        print("PROCESSING DATA...\n")

        forward_sections = [[0] * NN for i in range(secs)]
        reverse_sections = [[0] * NN for i in range(secs)]
        forward_sections_time = [[0] * NN for i in range(secs)]
        reverse_sections_time = [[0] * NN for i in range(secs)]
        forward_sections_used = [0]*secs
        reverse_sections_used = [0]*secs

        sec_used_counter_forward = 0
        sec_used_counter_reverse = 0
        section_index_forward = 0
        section_index_reverse = 0
        sec_data_index = 0

        # START AND END POINTS FOR SWEEPS
        start = []
        end = []
        sweep_type = []

        for i in range(index_t):

            #TERMINATE THIS THREAD EARLY IF TEST IS CANCELLED
            if not running:
                return

            # ALREADY POPULATED THIS DATA WHEN USING FAKE DATA
            if not  USE_FAKE_DATA:
                _voltage_A[i] = conv_raw_adc_to_voltage(_adc_A[i],'A')

            # CONVERT RAW ADC VALUES TO VOLTAGE
            _voltage_B[i] = conv_raw_adc_to_voltage(_adc_B[i],'B')

            # FIND SLOPE (+ or -) FOR TRIANGLE (CH2) (s =(y2-y1)/(x2-x1))
            if(i > slope_range):
                if (_voltage_B[i-slope_range] - _voltage_B[i]) / slope_range > 0:
                    _slope[i] = -1
                else:
                    _slope[i] = 1
            else:
                _slope[i] = 0

            # FIND PEAK
            if(i > slope_range):
                if((_slope[i] != _slope[i-1])):
                    if(_slope[i] == 1):
                        _peak[i] = -1  # NEGATIVE PEAK
                    else:
                        _peak[i] = 1  # POSITIVE PEAK
                else:
                    _peak[i] = 0
            else:
                _peak[i] = 0

        for i in range(index_t):  # _peak:

            #TERMINATE THIS THREAD EARLY IF TEST IS CANCELLED
            if not running:
                return

            if(i > slope_range+1):  # Skip the first peak at time = 0

                if(_peak[i] == 1):  # START OF REVERSE SWEEP (POSITIVE TO NEGATIVE V IN TRIAGLE)
                    i += 1
                    sec_data_index = 0
                    start.append(i)
                    sweep_type.append('REVERSE')

                    while _slope[i] == -1:  # _peak[i] == 0:
                        reverse_sections[section_index_reverse][sec_data_index] = _voltage_B[i]
                        reverse_sections_time[section_index_reverse][sec_data_index] = _time[i]
                        sec_data_index += 1
                        i += 1

                        if(i == NN):
                            break

                    end.append(i)
                    section_index_reverse += 1

                    if(i == NN):
                        break

                    # & sec_used_counter_reverse<4): #NEXT SECTION IS A FORWARD SWEEP, hence a full senction has been captured
                    if(_peak[i] == -1):
                        reverse_sections_used[sec_used_counter_reverse] = 1
                        sec_used_counter_reverse += 1

                    if(section_index_reverse == secs and section_index_forward == secs):
                        break

                elif(_peak[i] == -1):  # START OF FORWARD SWEEP (NEGATIVE TO POSITIVE V IN TRIAGLE)
                    i += 1
                    sec_data_index = 0
                    start.append(i)
                    sweep_type.append('FORWARD')

                    while _slope[i] == 1:  # _peak[i] == 0:
                        forward_sections[section_index_forward][sec_data_index] = _voltage_B[i]
                        forward_sections_time[section_index_forward][sec_data_index] = _time[i]
                        sec_data_index += 1
                        i += 1

                        if(i == NN):
                            break

                    end.append(i)
                    section_index_forward += 1

                    if(i == NN):
                        break

                    # & sec_used_counter_forward<4): #NEXT SECTION IS A REVERSE SWEEP, hence a full senction has been captured
                    if(_peak[i] == 1):
                        forward_sections_used[sec_used_counter_forward] = 1
                        sec_used_counter_forward += 1

                    if(section_index_forward == secs and section_index_reverse == secs):
                        break

        # Remove last as it is not used
        start.pop(len(start)-1)
        end.pop(len(end)-1)
        sweep_type.pop(len(sweep_type)-1)

        c = 0  # counter
        for i in range(len(start)-1-c):
            # 500: minimum range of sweeps - removed those that are under
            if (end[i-c] - start[i-c]) < 500:
                start.pop(i-c)
                end.pop(i-c)
                sweep_type.pop(i-c)
                c += 1

        # print("start", start)
        # print("end", end)

        # =============================================================================
        # POST PROCESSING : FITTING CURVE TO DATA
        # =============================================================================

        #TERMINATE THIS THREAD EARLY IF TEST IS CANCELLED
        if not running:
            return

        Vgate = np.ndarray(shape=(NN), dtype=float, order='F')
        Ids = np.ndarray(shape=(NN), dtype=float, order='F')

        for i in range(len(Vgate)):
            # CONVERT VOLTAGE AT ADC TO VOLTAGE AT GATE
            Vgate[i] = 4.0496 + (_voltage_B[i]-4.0496)*GATE_GAIN + GATE_OFFSET
            Ids[i] = _voltage_A[i]/CURRENT_GAIN  # Convert to current

            # print("Vgate[i]", Vgate[i], "\tIds[i]", Ids[i])

        Dirac = []
        dirac_forward_sweep = []
        dirac_reverse_sweep = []

        # Start fitting for each individual sweep
        for i in range(len(start)):

            # print(i)

            Vgate_prime = Vgate[start[i]:end[i]]
            Ids_prime = Ids[start[i]:end[i]]

            if not len(Vgate_prime):
                continue
            # Flip the data if its not monotonically increasing
            if (Vgate_prime[0] - Vgate_prime[-1]) > 0:
                Vgate_prime = np.flip(Vgate_prime)
                Ids_prime = np.flip(Ids_prime)

            Vgate_range = max(Vgate_prime) - min(Vgate_prime)

            min_idx = np.argmin(Ids_prime)

            fit_low = Vgate_prime[min_idx] - 0.25*Vgate_range
            fit_high = Vgate_prime[min_idx] + 0.25*Vgate_range

            idx_low = np.abs(Vgate_prime - fit_low).argmin()
            idx_high = np.abs(Vgate_prime - fit_high).argmin()
            # print(idx_low,idx_high)

            spl = np.poly1d(np.polyfit(
                Vgate_prime[idx_low:idx_high], Ids_prime[idx_low:idx_high], 9))

            xs = np.linspace(Vgate_prime[idx_low], Vgate_prime[idx_high], 4000)

            peak = xs[np.where(spl(xs) == min(spl(xs)))]

            Dirac = np.append(Dirac, peak[0])

            if sweep_type[i] == 'FORWARD':
                dirac_forward_sweep = np.append(dirac_forward_sweep, peak[0])
            else:
                dirac_reverse_sweep = np.append(dirac_reverse_sweep, peak[0])

        #MEAN
        mean_dirac_forward_sweep = np.mean(dirac_forward_sweep, axis=0)
        mean_dirac_reverse_sweep = np.mean(dirac_reverse_sweep, axis=0)

        #STD
        std_dirac_forward_sweep = np.std(dirac_forward_sweep, axis=0)
        std_dirac_reverse_sweep = np.std(dirac_reverse_sweep, axis=0)

        os.system("echo 0 > /sys/class/gpio/gpio146/value")  # AMBER
        os.system("echo 0 > /sys/class/gpio/gpio147/value")


def update_sys_time():
    try:
        import ntplib
        client = ntplib.NTPClient()
        response = client.request('pool.ntp.org')
        os.system('date ' + time.strftime('%m%d%H%M%Y.%S', time.localtime(response.tx_time)))
    except:
        print('[Update Sys Time] ERROR: Could not sync with time server.')
        return 1

    print('[Update Sys Time] OK.')
    return 0


##### Method for waiting for button press #####
BUTTON_PRESSED = "0"
BUTTON_CHECK_DELAY = 0.5 # seconds
def wait_for_button(button):
    while True:
        with open(f"{GPIO_PATH}/gpio{button}/value") as valueFile:
            if valueFile.read(1) == BUTTON_PRESSED:
                break
            time.sleep(BUTTON_CHECK_DELAY)



# ================================================================================
# MAIN
# ================================================================================
wifi_wait_counter = 1
baseline_mean_dirac_forward_sweep = 0
baseline_mean_dirac_reverse_sweep = 0
sample_mean_dirac_forward_sweep = 0
sample_mean_dirac_reverse_sweep = 0


# =====================================================================
# GET CALIB VALUES FROM FILE IF EXISTS, ELSE CREATE WITH DEFAULTS
# =====================================================================

#CHECK IF FILE EXISTS
calib_filename = "calib.json"

if(path.exists(calib_filename)):
    print("Calib file exists.")
else:
    print("Calib file does not exists. Creating file with default values.")
    data = {}
    data['ADC_CALIB'] = []
    data['ADC_CALIB'].append({

        # =====================================================================
        # DEFAULT VALUES TO ADD TO CALIB FILE IF IS DOESN'T EXISTS
        # NB: THESE WILL NOT OVERWRITE EXISTING VALUES IN CALIB.JSON IF IT ALREADY EXISTS! 
        # =====================================================================
        "ADC_CALIBRATION_GAIN": 1.11262,
        "ADC_CALIBRATION_OFFSET": -0.055756889,
        "VOLTAGE_SCALE": 2.5,
        "FULL_SCALE_RESOLUTION": 8388608.0,
        "GATE_GAIN": (301 + 121)/301, #1.40199335548,
        "CURRENT_GAIN": 4990,
        "GATE_OFFSET": 0.019655897,
        "TIA_GAIN_1": 0.1371184370,
        "TIA_GAIN_2": -0.2656584491,
        "TIA_GAIN_3": 1.1644372463,
        "TIA_GAIN_4": -0.0359382272
    })

    with open(calib_filename, 'w') as outfile:
        json.dump(data, outfile)

with open(calib_filename) as f:
    data = json.load(f)

#print(json.dumps(data, indent = 4, sort_keys=False))

# CALIBRATION GAINS FOR ADC
ADC_CALIBRATION_GAIN = data["ADC_CALIB"][0]["ADC_CALIBRATION_GAIN"]
ADC_CALIBRATION_OFFSET = data["ADC_CALIB"][0]["ADC_CALIBRATION_OFFSET"]
VOLTAGE_SCALE = data["ADC_CALIB"][0]["VOLTAGE_SCALE"]
FULL_SCALE_RESOLUTION = data["ADC_CALIB"][0]["FULL_SCALE_RESOLUTION"]

# SCALING FACTORs TO TRANSLATE CALIBRATED ADC VOLTAGE TO GATE VOLTAGE
GATE_GAIN = data["ADC_CALIB"][0]["GATE_GAIN"]
CURRENT_GAIN = data["ADC_CALIB"][0]["CURRENT_GAIN"]
GATE_OFFSET = data["ADC_CALIB"][0]["GATE_OFFSET"]

#CALIBRATION GAINS FOR TIA
#y = 0.1371184370x3 - 0.2656584491x2 + 1.1644372463x - 0.0359382272
TIA_GAIN_1 = data["ADC_CALIB"][0]["TIA_GAIN_1"]
TIA_GAIN_2 = data["ADC_CALIB"][0]["TIA_GAIN_2"]
TIA_GAIN_3 = data["ADC_CALIB"][0]["TIA_GAIN_3"]
TIA_GAIN_4 = data["ADC_CALIB"][0]["TIA_GAIN_4"]






try:
    os.system("echo 0 > /sys/class/gpio/gpio142/value")  # RED
    os.system("echo 1 > /sys/class/gpio/gpio143/value")  # GREEN - WIFI CONNECTED AND TIME UPDATED
    os.system("echo 0 > /sys/class/gpio/gpio146/value")  # AMBER

    os.system("echo 0 > /sys/class/gpio/gpio149/value")  # RGB RED
    os.system("echo 0 > /sys/class/gpio/gpio148/value")  # RGB GREEN
    os.system("echo 0 > /sys/class/gpio/gpio147/value")  # RGB BLUE


    # Write ADC config
    write_init_config()
    read_config(True)

    first_entry_in_sampling_loop = True

    # =====================================================================
    # SOCKET CONNECTION
    # =====================================================================

    HOST = server_ip #'192.168.1.14'#check_internet() ##'192.168.1.14' #check_internet()#'192.168.1.5' #list_devices_ip[0]   #'127.0.0.1'  # Standard loopback interface address (localhost)
    PORT = 65432                # Port to listen on (non-privileged ports are > 1023)
    #@time.sleep(5)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        conn, addr = s.accept()
        with conn:
            print('Connected by', addr)
            #while True:

            data = conn.recv(1024)
            print("data: "+str(data))
            #if not data:
            #    break

            conn.sendall(b"#START1 STARTED")
            

            # =====================================================================
            # MAIN LOOP
            # =====================================================================
            #while True:
            data = conn.recv(1024)
            print("data: "+str(data))
            
            
            #RESET MEAN VALUES USED IN SAMPLING LOOP
            mean_dirac_forward_sweep = 0
            mean_dirac_reverse_sweep = 0
            std_dirac_forward_sweep = 0
            std_dirac_reverse_sweep = 0
            baseline_mean_dirac_forward_sweep = 0
            baseline_mean_dirac_reverse_sweep = 0
            sample_mean_dirac_forward_sweep = 0
            sample_mean_dirac_reverse_sweep = 0


            #RESET BOOLEAN FOR MANAGING THREADS
            stop_sampling_process = False
            running = True
            ready_for_sample = False

            # PRESS BUTTON #2 TO START BASELINE SAMPLING
            # =============================================================

            conn.sendall(b"###WAITING FOR BUTTON 2###")

            while True:

                valueFile_button2 = open(
                    GPIO_PATH+'/gpio'+GPIO_CHAN_NUM_BUTTON2+'/value', 'r')
                button_pressed = valueFile_button2.read(1)
                valueFile_button2.close()

                if(button_pressed == '0'):
                    break  # continue to measurement

                time.sleep(0.5)

            # START BLUE LED THREAD
            # SOURCE: https://www.tutorialspoint.com/python3/python_multithreading.htm


            #DEFINES - MODE TO TOP SOMEWHERE
            THREAD_SAMPLING_MODE_BASELINE = 1
            THREAD_SAMPLING_MODE_SAMPLE = 2
            THREAD_SAMPLING_MODE_WAIT_FOR_SAMPLE = 3

            #FILE NAME FROM TIMESTAMP:
            if (use_default_filename):
                timestamp_filename = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            else:
                timestamp_filename = file_name
            thread_sampling = samplingThread(1, "Thread-Sampling", THREAD_SAMPLING_MODE_BASELINE, timestamp_filename) #BASE
            thread_led = ledThread(2, "Thread-LED", THREAD_SAMPLING_MODE_BASELINE)
            thread_cancel = cancelThread(3, "Thread-Cancel")


            print("BASELINE: FETCHING DATA...\n")
            
            conn.sendall(b"###BUTTON 2 PRESSED AND SAMPLING###")

            thread_sampling.start()
            thread_led.start()
            if first_entry_in_sampling_loop:
                thread_cancel.start()
                first_entry_in_sampling_loop = False


            #CHECK FOR CANCEL OPERATION WHILE SAMPLING BASELINE
            thread_running = thread_sampling.is_alive()
            while (thread_running):
                if stop_sampling_process:
                    running = False
                    print("CANCELLED TEST DURING BASELINE...\n")
                    conn.sendall(b"###CANCEL###")
                    break
                thread_running = thread_sampling.is_alive()
                time.sleep(0.5)

            #SOME SORT OF CHECK THAT BASELINE WAS OK
            #IF(BASELINE == OK)
                #CONTINUE
            #ELSE
                #STOP

            #WAIT FOR LED THREAD TO FINISH
            thread_led.join(600)

            baseline_mean_dirac_forward_sweep = mean_dirac_forward_sweep
            baseline_mean_dirac_reverse_sweep = mean_dirac_reverse_sweep
            baseline_std_dirac_forward_sweep = std_dirac_forward_sweep
            baseline_std_dirac_reverse_sweep = std_dirac_reverse_sweep

            if not stop_sampling_process:

                # WAIT FOR USER TO INSERT SAMPLE AND PRESS BUTTON 3
                thread_led = ledThread(2, "Thread-LED", THREAD_SAMPLING_MODE_WAIT_FOR_SAMPLE)#TODO: set last arg to mode: handle LEDS HERE!
                thread_led.start()
            
                # PRESS BUTTON #3 TO START SAMPLE SAMPLING
                # =============================================================
                
                print("\n========================================================")
                print("SYSTEM READY: Press Button #3 to start")
                print("========================================================")

                conn.sendall(b"###WAITING FOR BUTTON 3###")

                while True:

                    valueFile_button3 = open(GPIO_PATH+'/gpio'+GPIO_CHAN_NUM_BUTTON3+'/value', 'r')
                    button_pressed3 = valueFile_button3.read(1)
                    valueFile_button3.close()

                    #CHECK FOR CANCEL OPERATION WHILE SAMPLING BASELINE
                    thread_running = thread_led.is_alive()
                    if stop_sampling_process:
                        running = False
                        print("CANCELLED TEST WHILE WAITING FOR SAMPLE...\n")
                        conn.sendall(b"###CANCEL###")
                        break

                    #CONTINUE AFTER SAMPLE HAS BEEN INCERTED
                    elif(button_pressed3 == '0'):
                        #TRIGGER LED THREAD TO END
                        ready_for_sample = True

                        #WAIT FOR LED THREAD TO FINISH
                        thread_led.join(100)

                        break  # continue to measurement
                    time.sleep(0.5)

                if not stop_sampling_process:

                    #RESTART LED AND SAMPLING THREADS
                    thread_sampling = samplingThread(1, "Thread-Sampling", THREAD_SAMPLING_MODE_SAMPLE, timestamp_filename) 
                    thread_led = ledThread(2, "Thread-LED", THREAD_SAMPLING_MODE_SAMPLE)
                    print("SAMPLE: FETCHING DATA...\n")
                    
                    conn.sendall(b"###BUTTON 3 PRESSED AND SAMPLING###")

                    thread_sampling.start()
                    thread_led.start()
                    
                    thread_running = thread_sampling.is_alive()
                    while (thread_running):
                        if stop_sampling_process:
                            running = False
                            print("CANCELLED TEST DURING WHILE SAMPLE WAS BEING ANALYZED...\n")
                            conn.sendall(b"###CANCEL###")
                            break
                        thread_running = thread_sampling.is_alive()
                        time.sleep(0.5)
                    
                    sample_mean_dirac_forward_sweep = mean_dirac_forward_sweep
                    sample_mean_dirac_reverse_sweep = mean_dirac_reverse_sweep
                    sample_std_dirac_forward_sweep = std_dirac_forward_sweep
                    sample_std_dirac_reverse_sweep = std_dirac_reverse_sweep

                    delta_voltage_forward = sample_mean_dirac_forward_sweep - baseline_mean_dirac_forward_sweep
                    delta_voltage_reverse = sample_mean_dirac_reverse_sweep - baseline_mean_dirac_reverse_sweep
                    
                    #CHECK RESULT
                    if delta_voltage_forward > .140:
                        result = True
                    else:
                        result = False

            conn.sendall(b"###END PROCESS###")  

            #thread_sampling.join()
            thread_led.join()
            thread_cancel.join()
            conn.close() 
            exit()

        
      


finally:

    # CLOSE SPI ACCESS
    spi.close()

    os.system("echo 0 > /sys/class/gpio/gpio142/value")  # RED
    os.system("echo 0 > /sys/class/gpio/gpio143/value")  # GREEN
    os.system("echo 0 > /sys/class/gpio/gpio146/value")  # AMBER

    os.system("echo 0 > /sys/class/gpio/gpio149/value")  # RGB RED
    os.system("echo 0 > /sys/class/gpio/gpio148/value")  # RGB GREEN
    os.system("echo 0 > /sys/class/gpio/gpio147/value")  # RGB BLUE

    # CLOSE BUTTON AND LED GPIO FILES
    # valueFile_button3.close()
    # valueFile_LED_RGB_GREEN.close() #CLOSED IN THREAD
    # GPIO.cleanup()

    #print("###END PROCESS###")
