import pygame
import os
import vgamepad
from enum import Enum
import keyboard

os.environ["SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS"] = "1"

pygame.init()


# This is a simple class that will help us print to the screen.
# It has nothing to do with the joysticks, just outputting the
# information.
class TextPrint:
    def __init__(self):
        self.reset()
        self.font = pygame.font.Font(None, 25)

    def tprint(self, screen, text):
        text_bitmap = self.font.render(text, True, (0, 0, 0))
        screen.blit(text_bitmap, (self.x, self.y))
        self.y += self.line_height

    def reset(self):
        self.x = 10
        self.y = 10
        self.line_height = 15

    def indent(self):
        self.x += 10

    def unindent(self):
        self.x -= 10

class IS_BUTTON(Enum):
    UP = 1
    DOWN = 2
    LEFT = 3
    RIGHT = 4
    L = 5
    M = 6
    H = 7
    S = 8
    GRAB = 9
    COLLAB = 10
    BURST = 11
    START = 12

class INPUT_TYPES(Enum):
    BUTTON = 1
    HAT = 2
    TRIGGER = 3


BUTTON_NAMES = {
    IS_BUTTON.UP: "UP",
    IS_BUTTON.DOWN: "DOWN",
    IS_BUTTON.LEFT: "LEFT",
    IS_BUTTON.RIGHT: "RIGHT",
    IS_BUTTON.L: "L",
    IS_BUTTON.M: "M",
    IS_BUTTON.H: "H",
    IS_BUTTON.S: "S",
    IS_BUTTON.GRAB: "GRAB",
    IS_BUTTON.COLLAB: "COLLAB",
    IS_BUTTON.BURST: "BURST",
    IS_BUTTON.START: "START"
}

AXIS_THRESHOLD = 0.5


def hatDirectionPressed(hat, direction):
    match direction:
        case IS_BUTTON.UP:
            return hat[1] == 1
        case IS_BUTTON.DOWN:
            return hat[1] == -1
        case IS_BUTTON.LEFT:
            return hat[0] == -1
        case IS_BUTTON.RIGHT:
            return hat[0] == 1


def axisThresholdMet(axis, threshold):
    return abs(axis) > threshold


def triggerThresholdMet(axis, threshold):
    return axis > threshold


JOYSTICKS = {}

def universalInterrupts(event):
    if event.type == pygame.QUIT:
        pygame.quit()
        exit(0)

    if event.type == pygame.JOYDEVICEADDED:
        #print(f"Joystick {event.instance_id} connected")
        initializer()
        return "New Controller Added"

    if event.type == pygame.JOYDEVICEREMOVED:
        print(f"Joystick {event.instance_id} disconnected")
        initializer()
        return "Controller Removed"

    if keyboard.is_pressed("r"):
        print("Reset button")
        return "Config Reset"

    return ""

def getEvents():
    events = []
    try:
        events = pygame.event.get()
    except:
        return []
    return events

def padSetup(player, screen, reason, text_print):
    print("push any button to select controller")
    joy = {}
    joyIndex = -999
    waiting = True
    while waiting:
        text_print.reset()
        text_print.tprint(screen, reason)
        text_print.tprint(screen, f"Push any button to select controller for P{player}")
        text_print.tprint(screen, f"{JOYSTICKS}")
        for event in getEvents():
            interrupted = universalInterrupts(event)
            if interrupted != "":
                return interrupted
            if event.type == pygame.JOYBUTTONDOWN:
                print("Joystick button pressed.")
                joyIndex = event.joy
                print(joyIndex)
                joy = pygame.joystick.Joystick(joyIndex)
                print(f"{joy.get_name()} being used as player {player}")
                waiting = False

        pygame.display.flip()
        screen.fill((255, 255, 255))

    mappings = {}
    for button in IS_BUTTON:
        print(f"map button for {BUTTON_NAMES[button]}")
        if joy.get_numhats() > 0 and button in [
            IS_BUTTON.UP, IS_BUTTON.DOWN, IS_BUTTON.LEFT, IS_BUTTON.RIGHT
        ]:
            mappings[button] = (INPUT_TYPES.HAT, button)
            continue

        waiting = True
        while waiting:
            text_print.reset()
            text_print.tprint(screen, reason)
            text_print.tprint(screen, f"{joy.get_name()} being used as P{player}")
            text_print.tprint(screen, f"map button for {BUTTON_NAMES[button]}")
            for event in getEvents():
                interrupted = universalInterrupts(event)
                if interrupted != "":
                    return interrupted
                if hasattr(event, "joy") and event.joy == joyIndex:
                    if event.type == pygame.JOYHATMOTION:
                        hat = joy.get_hat(0)
                        if hat == (0,0):
                            continue
                        print("Hat Motion pressed")
                        mappings[button] = (INPUT_TYPES.HAT, button)
                        waiting = False
                    elif event.type == pygame.JOYBUTTONDOWN:
                        print("Joystick button pressed.")
                        mappings[button] = (INPUT_TYPES.BUTTON, event.button)
                        waiting = False
                    elif event.type == pygame.JOYAXISMOTION and event.value > 0.99:
                        print("Axis Motion pressed")
                        axis_id = event.axis
                        if axis_id > 3:
                            # This is a trigger
                            mappings[button] = (INPUT_TYPES.TRIGGER, axis_id)
                            waiting = False
                        else:
                            # TODO: SUPPORT ANALOG STICKS
                            reason = "Analog Stick Not Supported Currently"
            pygame.display.flip()
            screen.fill((255, 255, 255))

    print(mappings)
    return mappings, joyIndex

def initializer():
    for i in range(pygame.joystick.get_count()):
        joy = pygame.joystick.Joystick(i)
        JOYSTICKS[joy.get_instance_id()] = joy
        print(f"Joystick {i} connected")

def updateVController(state, joy_id, screen, text_print, vJoy):
    if joy_id < 0:
        return
    joy = pygame.joystick.Joystick(joy_id)
    for button in IS_BUTTON:
        isPressed = resolveButton(state[button], joy)
        text_print.tprint(screen, f"{BUTTON_NAMES[button]} : {isPressed}")

    if resolveButton(state[IS_BUTTON.UP], joy):
        vJoy.press_button(vgamepad.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP)
    else:
        vJoy.release_button(vgamepad.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP)

    if resolveButton(state[IS_BUTTON.DOWN], joy):
        vJoy.press_button(vgamepad.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN)
    else:
        vJoy.release_button(vgamepad.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN)

    if resolveButton(state[IS_BUTTON.LEFT], joy):
        vJoy.press_button(vgamepad.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT)
    else:
        vJoy.release_button(vgamepad.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT)

    if resolveButton(state[IS_BUTTON.RIGHT], joy):
        vJoy.press_button(vgamepad.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT)
    else:
        vJoy.release_button(vgamepad.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT)

    if resolveButton(state[IS_BUTTON.L], joy):
        vJoy.press_button(vgamepad.XUSB_BUTTON.XUSB_GAMEPAD_X)
    else:
        vJoy.release_button(vgamepad.XUSB_BUTTON.XUSB_GAMEPAD_X)

    if resolveButton(state[IS_BUTTON.M], joy):
        vJoy.press_button(vgamepad.XUSB_BUTTON.XUSB_GAMEPAD_Y)
    else:
        vJoy.release_button(vgamepad.XUSB_BUTTON.XUSB_GAMEPAD_Y)

    if resolveButton(state[IS_BUTTON.H], joy):
        vJoy.press_button(vgamepad.XUSB_BUTTON.XUSB_GAMEPAD_B)
    else:
        vJoy.release_button(vgamepad.XUSB_BUTTON.XUSB_GAMEPAD_B)

    if resolveButton(state[IS_BUTTON.S], joy):
        vJoy.press_button(vgamepad.XUSB_BUTTON.XUSB_GAMEPAD_A)
    else:
        vJoy.release_button(vgamepad.XUSB_BUTTON.XUSB_GAMEPAD_A)

    if resolveButton(state[IS_BUTTON.GRAB], joy):
        vJoy.press_button(vgamepad.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER)
    else:
        vJoy.release_button(vgamepad.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER)

    if resolveButton(state[IS_BUTTON.GRAB], joy):
        vJoy.press_button(vgamepad.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER)
    else:
        vJoy.release_button(vgamepad.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER)

    if resolveButton(state[IS_BUTTON.COLLAB], joy):
        vJoy.press_button(vgamepad.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER)
    else:
        vJoy.release_button(vgamepad.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER)

    if resolveButton(state[IS_BUTTON.BURST], joy):
        vJoy.left_trigger(255)
    else:
        vJoy.left_trigger(0)

    if resolveButton(state[IS_BUTTON.START], joy):
        vJoy.press_button(vgamepad.XUSB_BUTTON.XUSB_GAMEPAD_START)
    else:
        vJoy.release_button(vgamepad.XUSB_BUTTON.XUSB_GAMEPAD_START)

    vJoy.update()


def resolveButton(tuple, joy):
    match tuple[0]:
        case INPUT_TYPES.BUTTON:
            return joy.get_button(tuple[1]) == 1
        case INPUT_TYPES.HAT:
            return hatDirectionPressed(joy.get_hat(0), tuple[1])
        case INPUT_TYPES.TRIGGER:
            return triggerThresholdMet(joy.get_axis(tuple[1]), 0)


def main():
    # Set the width and height of the screen (width, height), and name the window.
    screen = pygame.display.set_mode((500, 700))
    pygame.display.set_caption("Joystick example")

    # Used to manage how fast the screen updates.
    clock = pygame.time.Clock()

    # Get ready to print.
    text_print = TextPrint()

    initializer()

    state = "First Time Setup"
    p1Joy = -99
    p2Joy = -99
    p1Map = {}
    p2Map = {}

    p1VJoy = vgamepad.VX360Gamepad()
    p2VJoy = vgamepad.VX360Gamepad()
    while True:

        # Drawing step
        # First, clear the screen to white. Don't put other drawing commands
        # above this, or they will be erased with this command.
        screen.fill((255, 255, 255))
        text_print.reset()

        if pygame.joystick.get_count() < 4:
            p1Joy = -99
            p2Joy = -99
            text_print.tprint(screen, "waiting for 2 controllers")
        elif state != "":
            p1 = padSetup(1, screen, state, text_print)
            if not isinstance(p1, str):
                p1Map, p1Joy = p1
                p2 = padSetup(2, screen, state, text_print)
                if not isinstance(p2, str):
                    p2Map, p2Joy = p2
                    state = ""
                else:
                    state = p2
            else:
                state = p1
        else:
            updateVController(p1Map, p1Joy, screen, text_print, p1VJoy)
            updateVController(p2Map, p2Joy, screen, text_print, p2VJoy)

        # Go ahead and update the screen with what we've drawn.
        pygame.display.flip()

        # Limit to 30 frames per second.
        clock.tick(1000)

        for event in getEvents():
            state = universalInterrupts(event)


if __name__ == "__main__":
    main()
    # If you forget this line, the program will 'hang'
    # on exit if running from IDLE.
    pygame.quit()