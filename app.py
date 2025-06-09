# app.py
from flask import Flask, render_template
from flask_socketio import SocketIO, emit

import random
import math


# Required: pip install Flask Flask-SocketIO eventlet
# eventlet (or gevent) is needed for Flask-SocketIO's async operations in development
# For production, you'd use something like gunicorn with eventlet/gevent workers.

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_very_secret_key_please_change'  # IMPORTANT for sessions
socketio = SocketIO(app, async_mode='eventlet') # Using eventlet for async mode

# --- Shader Definitions ---
# You would typically load these from .glsl files in a real application
# For simplicity, they are defined as strings here.

# Shader Set 1 (Initial Shader)
vertex_shader = """
varying vec2 vUv; // Pass UV coordinates to the fragment shader
void main() {
    vUv = uv; // uv is a built-in attribute from Three.js geometry
    // gl_Position is the final clip space position of the vertex
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
}
"""

fragment_shader_1 = """
varying vec2 vUv;      // UV coordinates from vertex shader
uniform float u_time;  // A custom uniform for time-based animation

void main() {
    // Create a simple pattern based on time and UV coordinates
    // This will produce a red/yellowish pulsing pattern
    float colorR = 0.5 + 0.5 * sin(vUv.x * 10.0 + u_time * 2.0);
    float colorG = 0.5 + 0.5 * cos(vUv.y * 8.0 + u_time * 1.0);
    gl_FragColor = vec4(colorR, colorG, 0.2, 1.0); // R, G, B, Alpha
}
"""

# Shader Set 2 (Alternative Shader for Update Demonstration)

fragment_shader_2 = """
varying vec2 vUv;
uniform float u_time;

void main() {
    // Create a different pattern - e.g., blue/green waves
    float colorG = 0.5 + 0.5 * sin(vUv.x * 15.0 - u_time * 1.5 + vUv.y * 5.0);
    float colorB = 0.5 + 0.5 * cos(vUv.y * 12.0 + u_time * 2.5 - vUv.x * 3.0);
    gl_FragColor = vec4(0.1, colorG, colorB, 1.0);
}
"""

# --- Server State ---
shader_set_active = 1

# --- Flask Routes ---
@app.route('/')
def index():
    """Serves the main HTML page."""
    return render_template('index.html')

def get_x():
    return "(vUv.x * 2.0 - 1.0)"
def get_y():
    return "(vUv.y * 2.0 - 1.0)"
def get_t():
    period_sec = random.uniform(1.0, 5.0)
    period_offset = random.uniform(0.0, 1.0)
    return f"sin(TWO_PI * (u_time / {period_sec:.3f} + {period_offset:.3f}))"
def get_uniform():
    value = random.uniform(-1.0, 1.0)
    return f"{value:.3f}"
def get_normal():
    value = random.gauss(0.0, 0.3)  # this concentrates the values around 0
    return f"{value:.3f}"
def get_xy_rot():
    # generate random rotation
    angle = f"({get_uniform()} * TWO_PI)"
    x_rot = f"(({get_x()} * cos({angle}) - {get_y()} * sin({angle})))"
    y_rot = f"(({get_x()} * sin({angle}) + {get_y()} * cos({angle})))"
    return x_rot, y_rot
def modulate(x):
    modulation_amount = random.uniform(0.0, 0.3)
    return f"({x} + sin({get_t()}) * {modulation_amount})"
def get_norm(x, y):
    p = random.randrange(1, 3)
    return f"pow(pow(abs({x}), {p:.3f}) + pow(abs({y}), {p:.3f}), {1 / p:.3f})"
def polynomial():
    num_roots = random.randrange(1, 5)
    results = []
    for root in range(num_roots):
        x0, y0 = f"{modulate(get_normal())}", f"{modulate(get_normal())}"
        x, y = get_xy_rot()
        norm = get_norm(f'{x} - {x0}', f'{y} - {y0}')
        results.append(norm)
    result = ' * '.join(results)
    return f"(pow({result}, {1 / num_roots:.3f}) * 2.0 - 1.0)"
def repeated(x):
    period = random.uniform(1.0, 10.0)
    return f"sin({x} * HALF_PI * {period:.3f})"
def mix_cutoff():
    a = repeated(polynomial())
    b = repeated(polynomial())
    c = repeated(polynomial())
    return f"mix({b}, {a}, smoothstep({c} - 0.1, {c} + 0.1, {a}))"

def get_random_shader():
    
    func = mix_cutoff
    result = func()
    print(result)
    
    pp = [random.random() for _ in range(12)]
    
    fragment_shader = f"""
        const float PI = 3.14159265359;
        const float TWO_PI = PI * 2.0;
        const float HALF_PI = PI * 0.5;
    
        varying vec2 vUv;
        uniform float u_time;
        
        vec3 palette( in float t, in vec3 a, in vec3 b, in vec3 c, in vec3 d )
        {{
            return a + b*cos( 6.283185*(c*t+d) );
        }}

        void main() {{
            float result = {result} * 0.5 + 0.5;
            vec3 a = vec3({pp[0]},{pp[1]},{pp[2]});
            vec3 b = vec3({pp[3]},{pp[4]},{pp[5]});
            vec3 c = vec3({pp[6]},{pp[7]},{pp[8]});
            vec3 d = vec3({pp[9]},{pp[10]},{pp[11]});
            vec3 color = palette(result, a, b, c, d);
            gl_FragColor = vec4(color, 1.0);
        }}
    """
    
    return {
        'vertex': vertex_shader,
        'fragment': fragment_shader,
    }

# --- Socket.IO Event Handlers ---
@socketio.on('connect')
def handle_connect():
    """Handles new client connections."""
    client_sid = None # In Flask-SocketIO 5+, request.sid is not available directly here without a request context
                     # but we can still log the connection and emit.
    print(f'Client connected (SID will be known on specific events)')
    # Send the currently active shaders to the newly connected client
    emit('load_shaders', get_random_shader())

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('request_shader_update_from_client')
def handle_shader_update_request():
    """
    Handles a request from the client to switch to the next shader set.
    In a real app, this could be triggered by Python detecting a file change,
    or more complex logic.
    """
    global shader_set_active, current_shaders
    
    print('Shader update requested by client.')
    
    # Broadcast the new shader code to all connected clients
    socketio.emit('update_shaders', get_random_shader())
    print(f"Emitted 'update_shaders' with Shader Set {shader_set_active}")

if __name__ == '__main__':
    print("Flask app starting...")
    print("Please open http://127.0.0.1:5001 in your web browser.")
    print("Make sure you have a 'templates' folder with 'index.html' in it.")
    print("Required Python packages: Flask, Flask-SocketIO, eventlet")
    print("Install with: pip install Flask Flask-SocketIO eventlet")
    
    # socketio.run() is preferred for development as it uses Werkzeug's dev server
    # with Socket.IO capabilities (when using eventlet or gevent).
    socketio.run(app, host='0.0.0.0', port=5001, debug=True, use_reloader=True)
