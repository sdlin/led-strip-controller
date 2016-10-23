"""RGB Backend."""
from flask import Flask, Response, request
import json
import os
import pigpio
from time import sleep

app = Flask(__name__, static_url_path='', static_folder='public')
app.add_url_rule('/', 'root', lambda: app.send_static_file('index.html'))


class GpioPwm(object):
    rgb_to_pin = {
        'r': 3,
        'g': 4,
        'b': 2
    }

    def __init__(self):
        self.pi = pigpio.pi()
        self.r = 0
        self.g = 0
        self.b = 0
        self.last_r = 255
        self.last_g = 255
        self.last_b = 255
        self.state = 'off'

    def set_rgb(self, r_value, g_value, b_value, reset=True, do_fade=True):
        if reset and r_value == 0 and g_value == 0 and b_value == 0:
            self.last_r = 255
            self.last_g = 255
            self.last_b = 255
            self.state = 'off'
        elif self.state == 'off':
            self.state = 'on'
        if do_fade is True:
            self.fade_rgb(r_value, g_value, b_value)
        else:
            self.set_red(r_value)
            self.set_green(g_value)
            self.set_blue(b_value)

    def set_red(self, value):
        self._set_pin_value('r', value)
        self.r = value

    def set_green(self, value):
        self._set_pin_value('g', value)
        self.g = value

    def set_blue(self, value):
        self._set_pin_value('b', value)
        self.b = value

    def fade_rgb(self, r_value, g_value, b_value):
        time_period_secs = 0.03
        P = 0.4
        prev_r = None
        prev_g = None
        prev_b = None
        while prev_r != self.r or prev_g != self.g or prev_b != self.b:
            r_error = r_value - self.r
            g_error = g_value - self.g
            b_error = b_value - self.b
            r_next = round(self.r + P * r_error)
            g_next = round(self.g + P * g_error)
            b_next = round(self.b + P * b_error)

            prev_r = self.r
            prev_g = self.g
            prev_b = self.b

            self.set_red(r_next)
            self.set_green(g_next)
            self.set_blue(b_next)
            sleep(time_period_secs)

        self.set_red(r_value)
        self.set_green(g_value)
        self.set_blue(b_value)

    def turn_off(self):
        if self.state == 'off':
            return 1
        else:
            self.last_r = self.r
            self.last_g = self.g
            self.last_b = self.b
            self.set_rgb(0, 0, 0, False)
            self.state = 'off'
            return 0

    def turn_on(self):
        if self.state == 'on':
            return 1
        else:
            self.set_rgb(self.last_r, self.last_g, self.last_b)
            return 0

    def _set_pin_value(self, color, value):
        pin = GpioPwm.rgb_to_pin[color]
        scaled_value = min([max([int(value), 0]), 255])
        self.pi.set_PWM_dutycycle(pin, scaled_value)


@app.route('/api/rgb', methods=['GET', 'PUT'])
def rgb_handler():
    global gpiopwm
    if request.method == 'GET':
        return make_rgb_response(gpiopwm.r, gpiopwm.g, gpiopwm.b)
    elif request.method == 'PUT':
        r = int(request.form.get('r', 255))
        g = int(request.form.get('g', 255))
        b = int(request.form.get('b', 255))
        gpiopwm.set_rgb(r, g, b)

        msg = 'r: {}, g: {}, b: {}'.format(r, g, b)
        return Response(
            json.dumps(msg),
            mimetype='application/json',
            headers={
                'Cache-Control': 'no-cache',
                'Access-Control-Allow-Origin': '*'
            }
        )


@app.route('/api/simple_on', methods=['PUT', 'POST'])
def simple_on_handler():
    global gpiopwm
    return simple_closure_handler(gpiopwm.turn_on)


@app.route('/api/simple_off', methods=['PUT', 'POST'])
def simple_off_handler():
    global gpiopwm
    return simple_closure_handler(gpiopwm.turn_off)


def simple_closure_handler(func):
    ret = func()
    if ret == 0:
        msg = 'SUCCESS'
    else:
        msg = 'FAILURE'

    msg = 'STATUS: ' + msg
    return Response(
        json.dumps(msg),
        mimetype='application/json',
        headers={
            'Cache-Control': 'no-cache',
            'Access-Control-Allow-Origin': '*'
        }
    )


def make_rgb_response(r=255, g=255, b=255):
    """Return response."""
    return Response(
        json.dumps({'r': r, 'g': g, 'b': b}),
        mimetype='application/json',
        headers={
            'Cache-Control': 'no-cache',
            'Access-Control-Allow-Origin': '*'
        }
    )


def error(setpoint, current):
    return setpoint - current


if __name__ == '__main__':
    global gpiopwn
    gpiopwm = GpioPwm()
    gpiopwm.set_rgb(0, 0, 0)
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 3000)))
