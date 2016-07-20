"""RGB Backend."""
from flask import Flask, Response, request
import json
import os
import pigpio

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

    def set_rgb(self, r_value, g_value, b_value):
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

if __name__ == '__main__':
    global gpiopwn
    gpiopwm = GpioPwm()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 3000)))