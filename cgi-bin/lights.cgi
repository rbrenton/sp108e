#!/usr/bin/python2.7
import os
import re
import select
import simplejson as json
import socket
import sys
import time
import urllib

START_FLAG = '38'
END_FLAG = '83'

CMD_CUSTOM_EFFECT         = '02'
CMD_SPEED                 = '03'
CMD_MODE_AUTO             = '06'
CMD_CUSTOM_DELETE         = '07'
CMD_WHITE_BRIGHTNESS      = '08'
CMD_SYNC                  = '10'
CMD_SET_DEVICE_NAME       = '14'
CMD_SET_DEVICE_PASSWORD   = '16'
CMD_SET_IC_MODEL          = '1C'
CMD_GET_RECORD_NUM        = '20'
CMD_COLOR                 = '22'
CMD_CUSTOM_PREVIEW        = '24'
CMD_CHANGE_PAGE           = '25'
CMD_BRIGHTNESS            = '2A'
CMD_MODE_CHANGE           = '2C'
CMD_DOT_COUNT             = '2D'
CMD_SEC_COUNT             = '2E'
CMD_CHECK_DEVICE_IS_COOL  = '2F'
CMD_SET_RGB_SEQ           = '3C'
CMD_CUSTOM_RECODE         = '4C'
CMD_GET_DEVICE_NAME       = '77'
CMD_SET_DEVICE_TO_AP_MODE = '88'
CMD_TOGGLE_LAMP           = 'AA'
CMD_CHECK_DEVICE          = 'D5'

messages = []

class SP108E_Controller:

    def __init__(self):
        # Settings
        ip = '192.168.4.1'
        port = 8189

        #print "Connecting to %s:%s" % (ip, port)

        # Open connection.
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((ip, port))
        self.s.setblocking(0)

        self.device_name = self._sendrecv(CMD_GET_DEVICE_NAME, '000000') # \0SP108E_1f5e6f

        self.sync()


    def __get_bytes(self, data, mode):
        return (START_FLAG + data + mode + END_FLAG).decode('hex')


    def _sendrecv(self, cmd, data, delay = 0.0, debug = False):
        self._send(cmd, data, delay, debug)

        data = self._recv(debug)

        if debug == True:
            print ""

        return data


    def _send(self, cmd, data, delay = 0.0, debug = False):
        if debug == True:
            print "Sending: cmd %s data %s (%s)" % (cmd, data.decode('hex'), data)

        bytes = self.__get_bytes(data,cmd)

        if debug == True:
            print "Sending: %s" % bytes.encode('hex')

        self.s.send(bytes)

        if cmd == CMD_SET_DEVICE_NAME:
            delay = max(1.0, delay)
        elif cmd == CMD_BRIGHTNESS:
            delay = max(0.10, delay)
        elif cmd == CMD_SEC_COUNT:
            delay = max(2.0, delay)
        elif cmd == CMD_DOT_COUNT:
            delay = max(2.0, delay)
        elif cmd == CMD_COLOR:
            delay = max(0.02, delay)
        else:
            delay = max(0.05, delay)

        time.sleep(delay)


    def _recv(self, debug = False):
        if debug == True:
            print "Checking recv."

        data = ''
        ready = select.select([self.s], [], [], 1)

        if ready[0]:
            data = self.s.recv(4096)
            if debug == True:
                print "Response: %s (%s)" % (data, data.encode('hex'))
        else:
            if debug == True:
                print "No response.";

        return data


    def pulse(self):
        delay = 0.25
        self.setBrightness('40', delay)
        self.setBrightness('50', delay)
        self.setBrightness('40', delay)
        self.setBrightness('30', delay)
        self.setBrightness('20', delay)
        self.setBrightness('10', delay)
        self.setBrightness('20', delay)
        self.setBrightness(self.settings['brightness'], delay)


    def sync(self):

        # Check state.
        #self._sendrecv(CMD_CHECK_DEVICE, '000000', 0, True) # 0x010203040500
        #self._sendrecv(CMD_GET_RECORD_NUM, '000000', 0, True) # 0x03
        #self._sendrecv(CMD_CHECK_DEVICE_IS_COOL, '000000', 0, True) # 0x31 "1"
        #self._sendrecv(CMD_SYNC, '000000', 0, True) # 0x3801d001230200960006fefdfc0303ff83

        # Bytes.
        # 00 - 38 = START_FLAG
        # 01 - 01 = on/off (01/00)
        # 02 - d3 = pattern (cd=meteor, ce=breathing, cf=stack, d0=flow, d1=wave, d2=flash, d3=static, d4=catch-up, fa=off?)
        # 03 - 63 = speed (01-ff)
        # 04 - 20 = brightness
        # 05 - 02
        # 06 - 00
        # 07 - 96 = dot count
        # 08 - 00
        # 09 - 06 = sec count
        # 10 - ff = red
        # 11 - ff = green
        # 12 - ff = blue
        # 13 - 03
        # 14 - 03
        # 15 - ff
        # 16 - 83 = END_FLAG

        # 0x3801 db cc 80 0200960006 888888 0303ff83 pattern
        # 0x3801 d0 01 23 0200960006 fefdfc 0303ff83

        data = self._sendrecv(CMD_SYNC, '000000') # 0x3801d001230200960006fefdfc0303ff83

        settings = {}

        def fill(settings, key, value):
            settings[key] = value.encode('hex') # { 'raw': value, 'str': value.encode('hex') }

        fill(settings, 'power',      data[1])
        fill(settings, 'pattern',    data[2])
        fill(settings, 'speed',      data[3])
        fill(settings, 'brightness', data[4])
        fill(settings, 'dot_count',  data[6]+data[7])
        fill(settings, 'sec_count',  data[8]+data[9])
        fill(settings, 'red',        data[10])
        fill(settings, 'green',      data[11])
        fill(settings, 'blue',       data[12])
        fill(settings, 'sync',       data)

        self.settings = settings


    def setColor(self, value, delay = 0.0):
        messages.append('Setting COLOR to ' + value)
        self._send(CMD_COLOR, value, delay)


    def setBrightness(self, value, delay = 0.0):
        value = value.rjust(2, "0")
        messages.append('Setting BRIGHTNESS to ' + value)
        self._send(CMD_BRIGHTNESS, value + value + value, delay)

    def setPower(self, value, delay = 0.0):
        value = value.rjust(2, "0")
        messages.append('Setting TOGGLE_LAMP to ' + value)
        self._send(CMD_TOGGLE_LAMP, value + value + value, delay)

    def setMode(self, value, delay = 0.0):
        value = value.rjust(2, "0")
        messages.append('Setting MODE_CHANGE to ' + value)
        self._send(CMD_MODE_CHANGE, value + value + value, delay)

    def setSecCount(self, value, delay = 0.0):
        value = value.rjust(6, "0")
        messages.append('Setting SEC_COUNT to ' + value)
        value = value[4] + value[5] + value[2] + value[3] + value[0] + value[1]
        self._sendrecv(CMD_SEC_COUNT, value, delay, True)

    def setDotCount(self, value, delay = 0.0):
        value = value.rjust(6, "0")
        messages.append('Setting DOT_COUNT to ' + value)
        value = value[4] + value[5] + value[2] + value[3] + value[0] + value[1]
        self._send(CMD_DOT_COUNT, value, delay)

    def setSpeed(self, value, delay = 0.0):
        value = value.rjust(2, "0")
        messages.append('Setting SPEED to ' + value)
        self._send(CMD_SPEED, value + value + value, delay)


# Patterns.
# 00 = rainbow
# 01 = multicolor chase
# 10 = meteor blue
# 20 = dot cyan
# 30 = line-follow yellow,green
# 40 = spread-close yellow
# 50 = long-chase
# 60 = short-chase
# 70 =
# 80 =
# 90 =
# a0 =
# b0 =
# c0 =
# cd = meteor
# ce = breathing
# cf = stack
# d0 = flow
# d1 = wave
# d2 = flash
# d3 = static
# d4 = catch-up
# db = custom1
# fa = off?

print "Content-Type: application/javascript"
print ""

ctrl = SP108E_Controller()

# url = 'http'
# try:
#     if os.environ["HTTPS"] == 'on':
#         url = url + 's'
# except:
#     pass
# url = url + '://' + os.environ["HTTP_HOST"] + ':' + os.environ["SERVER_PORT"] + os.environ["REQUEST_URI"]
# print "url=%s" % url

changes = False

try:

    state = re.findall('(?<=state=)([^&]*)(?=&)?', os.environ["REQUEST_URI"])
    state = state[0]
    state = urllib.unquote(state)
    state = re.sub("'", '"', state)

    js = json.loads(state)

    colorchanged = False
    for key, value in js.iteritems():
        if ctrl.settings[key] == value:
            continue

        if key == 'pattern':
            changes = True
            ctrl.setMode(value)
            pass
        if key == 'power':
            changes = True
            ctrl.setPower(value)
            pass
        if key == 'sec_count':
            changes = True
            ctrl.setSecCount(value)
            pass
        if key == 'dot_count':
            changes = True
            ctrl.setDotCount(value)
            pass
        if key == 'brightness':
            changes = True
            ctrl.setBrightness(value)
            pass
        if key == 'speed':
            changes = True
            ctrl.setSpeed(value)
            pass
        if key == 'red' or key == 'green' or key == 'blue':
            changes = True
            if colorchanged == False:
                colorchanged = True
                ctrl.setColor(js['red'] + js['green'] + js['blue'])
            pass

except:
    pass

if changes == True:
    ctrl.sync()

cur = {
  'settings': ctrl.settings,
  'messages': messages
}
