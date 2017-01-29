"""RGB Backend."""
from flask import Flask, Response, request
import json
from math import ceil, floor
import os
import pigpio
from time import sleep

app = Flask(__name__, static_url_path='', static_folder='public')
app.add_url_rule('/', 'root', lambda: app.send_static_file('index.html'))


class GpioPwm(object):
    MAX_VAL = 255
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
        self.last_r = GpioPwm.MAX_VAL
        self.last_g = GpioPwm.MAX_VAL
        self.last_b = GpioPwm.MAX_VAL
        self.state = 'off'

    def set_rgb(self, r_value, g_value, b_value, reset=True, do_fade=True):
        if reset and r_value == 0 and g_value == 0 and b_value == 0:
            self.last_r = GpioPwm.MAX_VAL
            self.last_g = GpioPwm.MAX_VAL
            self.last_b = GpioPwm.MAX_VAL
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
        time_period_secs = 0.02
        prev_r = None
        prev_g = None
        prev_b = None
        while prev_r != self.r or prev_g != self.g or prev_b != self.b:
            r_error = r_value - self.r
            g_error = g_value - self.g
            b_error = b_value - self.b
            r_next = round(self.r + get_gain(self.r) * r_error)
            g_next = round(self.g + get_gain(self.g) * g_error)
            b_next = round(self.b + get_gain(self.b) * b_error)

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

    def delta_color(self, color, delta):
        def limited_delta(v):
            return min(max(v + delta, 0), GpioPwm.MAX_VAL)
        if color == 'r':
            args = [limited_delta(self.r), self.g, self.b]
        elif color == 'g':
            args = [self.r, limited_delta(self.g), self.b]
        elif color == 'b':
            args = [self.r, self.g, limited_delta(self.b)]
        else:
            return '{}'
        self.set_rgb(*args)

    def scale_brightness(self, input_scale_factor):
        input_scale_factor = min(max(input_scale_factor, -0.9), 0.9)
        round_func = ceil
        if input_scale_factor < 0:
            round_func = floor
        min_val = min([self.r, self.g, self.b])
        max_val = max([self.r, self.g, self.b])
        if input_scale_factor < 0 and min_val == 0:
            return False
        if input_scale_factor > 0 and max_val == GpioPwm.MAX_VAL:
            return False
        scale_factor = float(1.0 + input_scale_factor)
        if max_val == 0:
            r_des = min(max(round_func(1 + scale_factor), 1), GpioPwm.MAX_VAL)
            g_des = min(max(round_func(1 + scale_factor), 1), GpioPwm.MAX_VAL)
            b_des = min(max(round_func(1 + scale_factor), 1), GpioPwm.MAX_VAL)
        else:
            r_des = min(max(round_func(self.r * scale_factor), 1), GpioPwm.MAX_VAL)
            g_des = min(max(round_func(self.g * scale_factor), 1), GpioPwm.MAX_VAL)
            b_des = min(max(round_func(self.b * scale_factor), 1), GpioPwm.MAX_VAL)
        self.fade_rgb(r_des, g_des, b_des)
        return True

    def _set_pin_value(self, color, value):
        pin = GpioPwm.rgb_to_pin[color]
        scaled_value = min([max([int(value), 0]), GpioPwm.MAX_VAL])
        self.pi.set_PWM_dutycycle(pin, scaled_value)


@app.route('/api/rgb', methods=['GET', 'PUT'])
def rgb_handler():
    global gpiopwm
    if request.method == 'GET':
        return make_rgb_response(gpiopwm.r, gpiopwm.g, gpiopwm.b)
    elif request.method == 'PUT':
        r = int(request.form.get('r', GpioPwm.MAX_VAL))
        g = int(request.form.get('g', GpioPwm.MAX_VAL))
        b = int(request.form.get('b', GpioPwm.MAX_VAL))
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


@app.route('/api/delta_color', methods=['PUT'])
def delta_color_handler():
    global gpiopwm
    color = request.form.get('color')
    delta = int(request.form.get('delta'))
    gpiopwm.delta_color(color, delta)
    msg = 'r: {}, g: {}, b: {}'.format(gpiopwm.r, gpiopwm.g, gpiopwm.b)
    return Response(
        json.dumps(msg),
        mimetype='application/json',
        headers={
            'Cache-Control': 'no-cache',
            'Access-Control-Allow-Origin': '*'
        }
    )


@app.route('/api/scale_brightness', methods=['PUT'])
def scale_brightness_handler():
    global gpiopwm
    scale = float(request.form.get('scale'))
    gpiopwm.scale_brightness(scale)
    msg = 'r: {}, g: {}, b: {}'.format(gpiopwm.r, gpiopwm.g, gpiopwm.b)
    return Response(
        json.dumps(msg),
        mimetype='application/json',
        headers={
            'Cache-Control': 'no-cache',
            'Access-Control-Allow-Origin': '*'
        }
    )


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


def make_rgb_response(r=GpioPwm.MAX_VAL, g=GpioPwm.MAX_VAL, b=GpioPwm.MAX_VAL):
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


# Use brightness value to determine operating point for gain schedule
def get_gain(v):
    return 0.1 + 0.3 * float(v) / GpioPwm.MAX_VAL


if __name__ == '__main__':
    global gpiopwn
    gpiopwm = GpioPwm()
    gpiopwm.set_rgb(0, 0, 0)
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 3000)))
