import shiftpi.shiftpi as shiftpi
import time
import RPi.GPIO as GPIO
import pygame
from threading import Thread
import MCP230XX as mcp_lib

pygame.init()
pygame.mixer.init()

print("setup of RPI")
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

left_joystick_up = 12
left_joystick_down = 13
right_joystick_up = 14 # labeled TXD on breakout
right_joystick_down = 15 # labeled RXD on breakout
start_button = 16

# Configure and set L298 pins
# Motor A, when in1, motor turns forward, when in2, motor turns backward, when in1=in2, brake
ena = 21
in1 = 20
in2 = 19
# Motor B
in3 = 6
in4 = 5
enb = 4
l298_inputs = [in1, in2, ena, in3, in4, enb]
for pin in l298_inputs:
  GPIO.setup(pin,GPIO.OUT)
  GPIO.output(pin, False)

left_dir = 0
right_dir = 0
left_speed = right_speed = 100

initial_freq = 1000

p1 = GPIO.PWM(ena,initial_freq)
p2 = GPIO.PWM(enb,initial_freq)

p1.start(right_speed)
p2.start(left_speed)

# Configure and set Shift Register Pins
shift_register_SER = 25
shift_register_RCLK = 26
shift_register_SRCLK = 27

print("setting pins")
# Set pins as input or output
GPIO.setup(left_joystick_up,GPIO.IN,pull_up_down=GPIO.PUD_UP)
GPIO.setup(left_joystick_down,GPIO.IN,pull_up_down=GPIO.PUD_UP)
GPIO.setup(right_joystick_up,GPIO.IN,pull_up_down=GPIO.PUD_UP)
GPIO.setup(right_joystick_down,GPIO.IN,pull_up_down=GPIO.PUD_UP)
GPIO.setup(start_button,GPIO.IN,pull_up_down=GPIO.PUD_UP)
shiftpi.pinsSetup(**{"ser": shift_register_SER, "rclk": shift_register_RCLK, "srclk": shift_register_SRCLK})

# Setting up LED configuration with shift registers
shiftpi.shiftRegisters(2)

# Light up all LEDs
shiftpi.digitalWrite(shiftpi.ALL, shiftpi.HIGH)

# Set up MCP23017 and configure inputs
MCP = mcp_lib.MCP230XX('MCP23017',0x20,'16bit')
for input in range(0,16):
    MCP.set_mode(input,'input')

standby = True
flashing = False

def motor_control():
    global left_dir
    global right_dir
    global left_speed
    global right_speed

    while True:
        if right_dir == 1:
            GPIO.output(in1, True)
            GPIO.output(in2, False)
        if left_dir == 1:
            GPIO.output(in3, True)
            GPIO.output(in4, False)
        if right_dir == -1:
            GPIO.output(in1, False)
            GPIO.output(in2, True)
        if left_dir == -1:
            GPIO.output(in3, False)
            GPIO.output(in4, True)

        if left_dir == 0 and right_dir == 1:
            # pwm.set_pwm(0, 0, int(initial_freq * 0.9))
            # pwm.set_pwm(1, 0, int(initial_freq * 1.1))
            p1.ChangeDutyCycle(right_speed)
            p2.ChangeDutyCycle(left_speed)
        elif left_dir == 1 and right_dir == 0:
            # pwm.set_pwm(0, 0, int(left_speed))
            # pwm.set_pwm(1, 0, int(initial_freq * 0.9))
            p1.ChangeDutyCycle(right_speed)
            p2.ChangeDutyCycle(left_speed)
        elif left_dir == 0 and right_dir == 0:
            GPIO.output(in1, False)
            GPIO.output(in2, False)
            GPIO.output(in3, False)
            GPIO.output(in4, False)
        else:
            # pwm.set_pwm(0, 0, int(initial_freq))
            # pwm.set_pwm(1, 0, int(initial_freq))
            p1.ChangeDutyCycle(right_speed)
            p2.ChangeDutyCycle(left_speed)

def standby_mode():
    print("start standby mode")
    global standby
    # Start background thread for LED routine
    led_background_thread = Thread(target=standby_led_routine)
    led_background_thread.daemon = True
    led_background_thread.start()

    # Start background thread for motor control
    motor_thread = Thread(target=motor_control)
    motor_thread.daemon = True
    motor_thread.start()

    channelA = pygame.mixer.Channel(1)
    startup = pygame.mixer.Sound("startup.ogg")
    channelA.set_volume(1.0)
    channelA.play(startup)

    # Uncomment these lines to bypass start button and wait 5 seconds instead
    # print("in standby")
    # time.sleep(5)
    # standby = False
    # start_new_game()

    print("in standby")
    while standby:

        input = GPIO.input(start_button)
        print("start button: " + str(input))
        if not input:
            standby = input
            print("start new game")
            start_new_game()
        standby = input
        time.sleep(0.05)


def standby_led_routine():
    # Cycle through LEDs to entice the player
    while standby:
        delay = 300
        for each in range(0, 10):
            shiftpi.digitalWrite(each, shiftpi.HIGH)
            shiftpi.delay(delay)

            shiftpi.digitalWrite(each, shiftpi.LOW)
            shiftpi.delay(delay)

            if not standby:
                for each in range(0, 10):
                    shiftpi.digitalWrite(each, shiftpi.LOW)
                break

def winner_led_routine():
    global standby
    # Fun flashing light routine
    delay = 300
    while delay > 10:
        for each in range(0, 10):
            shiftpi.digitalWrite(each, shiftpi.HIGH)
            shiftpi.delay(delay)

            shiftpi.digitalWrite(each, shiftpi.LOW)
            shiftpi.delay(delay)
        delay = delay * 0.75

    # Turn off all LEDs and then enter standby mode
    for each in range(0, 10):
        shiftpi.digitalWrite(each, shiftpi.LOW)
    standby = True
    standby_mode()

def led_flash(led, delay):
    global flashing
    while flashing:
        shiftpi.digitalWrite(led, shiftpi.HIGH)
        shiftpi.delay(delay)

        shiftpi.digitalWrite(led, shiftpi.LOW)
        shiftpi.delay(delay)
#
# def left_joystick():
#     global left_dir
#     while True:
#         # Check if any of the joysticks are pressed
#         if GPIO.input(left_joystick_up) == GPIO.LOW:
#             # print('left joystick up')
#             left_dir = 1
#         if GPIO.input(left_joystick_down) == GPIO.LOW:
#             # print('left joystick down')
#             left_dir = -1
#
#         if GPIO.input(left_joystick_up) == GPIO.HIGH:
#             # print('left joystick up')
#             left_dir = 0
#         if GPIO.input(left_joystick_down) == GPIO.HIGH:
#             # print('left joystick down')
#             left_dir = 0
#
# def right_joystick():
#     global right_dir
#     while True:
#         if GPIO.input(right_joystick_up) == GPIO.LOW:
#             # print('right joystick up')
#             right_dir = 1
#         if GPIO.input(right_joystick_down) == GPIO.LOW:
#             # print('right joystick down')
#             right_dir = -1
#
#         if GPIO.input(right_joystick_up) == GPIO.HIGH:
#             # print('right joystick up')
#             right_dir = 0
#         if GPIO.input(right_joystick_down) == GPIO.HIGH:
#             # print('right joystick down')
#             right_dir = 0

def game_play(targetHole):
    print("trying to get into hole: " + str(targetHole + 1) + "!")
    global flashing
    global standby
    global left_dir
    global right_dir
    global left_speed
    global right_speed

    channelA = pygame.mixer.Channel(1)
    main_theme = pygame.mixer.Sound("mainTheme.ogg")
    channelA.set_volume(1.0)
    channelA.play(main_theme)

    flash_delay = 150
    flashing = True
    led_target_thread = Thread(target=led_flash, args=(targetHole, flash_delay))
    led_target_thread.daemon = True
    led_target_thread.start()

    # Initialize player to be in control
    player_control = True

    while player_control:
        if MCP.input(targetHole):
            print("ball went through hole: " + str(targetHole + 1) + "!")
            channelA = pygame.mixer.Channel(1)
            hole_success = pygame.mixer.Sound("holeSuccess.ogg")
            channelA.set_volume(1.0)
            channelA.play(hole_success)
            flashing = False
            targetHole += 1
            return targetHole

def start_new_game():
    print("starting new game")
    global flashing
    global standby
    global left_dir
    global right_dir
    global left_speed
    global right_speed

    # start game with first target hole
    new_targetHole = game_play(0)

    while True:
        # keep looping until target hole is winning hole

        if new_targetHole > 9:
            print("winner winner chicken dinner")
            winner_led_routine()
            break
        else:
            new_targetHole = game_play(new_targetHole)



        # left_js_thread = Thread(target=left_joystick)
        # left_js_thread.daemon = True
        # left_js_thread.start()
        #
        # right_js_thread = Thread(target=right_joystick)
        # right_js_thread.daemon = True
        # right_js_thread.start()









standby_mode()