from skimage.io import imread, imsave
from skimage.viewer import ImageViewer
import numpy as np
import random
import inspect
import scipy
import matplotlib as mpl

H = 1080
W = 1920
C = 3


def scale_range(x, a, b):
    if x.max() - x.min() < 0.001:
        return np.ones_like(x) * (a + b) * 0.5
    # use quantiles to ignore outliers
    x_min = np.quantile(x, 0.05)
    x_max = np.quantile(x, 0.95)
    x = np.clip(x, x_min, x_max)
    return np.interp(x, (x_min, x_max), (a, b))

image = np.zeros((H, W))

def get_rand():
    return np.ones_like(image) * random.random()
def get_x():
    return np.ones_like(image) * np.linspace(0.1, 0.9, W).reshape(1, W)
def get_y():
    return np.ones_like(image) * np.linspace(0.1, 0.9, H).reshape(H, 1)
def div_ab(a, b):
    return np.divide(a, np.maximum(np.abs(b), 0.001))
def safe_log(x):
    return scale_range(np.log(scale_range(x, 0.5, 2.0)), 0, 1)
def safe_arcsin(a):
    return np.arcsin(scale_range(a, -1.0, 1.0))
def safe_arccos(a):
    return np.arccos(scale_range(a, -1.0, 1.0))
def safe_power(a, b):
    res = np.power(scale_range(a, 0.5, 2.0), scale_range(b, 0.5, 2.0))
    return scale_range(res, 0, 1)
def safe_sin(a):
    return np.sin(scale_range(a, -5, 5))
def safe_cos(a):
    return np.cos(scale_range(a, -5, 5))
def sincos(a):
    if np.random.randint(0, 2) == 1:
        r = safe_sin(a)
    else:
        r = safe_cos(a)
    return scale_range(a, 0, 1)
def polynomial(x, y):
    r = np.ones_like(image)
    p = random.randrange(-2, 3)
    for root in range(random.randrange(3, 7)):
        x0, y0 = random.uniform(0.1, 0.9), random.uniform(0.1, 0.9)
        if p == 0:
            r *= (np.abs(x - x0) + np.abs(y - y0))
        else:
            r *= (np.abs(x - x0)**p + np.abs(y - y0)**p)**(1/p)
    return scale_range(r, 0, 1)
def poly_root():
    return polynomial(get_x(), get_y())
def convolve(x):
    conv_size = 5
    template = np.random.random_sample(size=(conv_size, conv_size))
    convolved = scipy.signal.convolve(x, template, mode='valid')
    padded = np.pad(convolved, pad_width=conv_size // 2, mode='edge')
    return scale_range(padded, 0, 1)
def mix(a, b):
    return (a + b) / 2
def mirror(x):
    cutoff = random.random()
    return (x < cutoff) * (cutoff - x) + (x > cutoff) * x 
def gradient(a):
    dx, dy = np.gradient(a)
    if np.random.randint(0, 2) == 1:
        grad = dx
    else:
        grad = dy
    return scale_range(grad, 0, 1)
def stack(c, a, b):
    cutoff = random.random()
    return (c < cutoff) * a + (c > cutoff) * b

functions = [
    get_rand,
    poly_root,
    sincos,
    polynomial,
    convolve,
    mirror,
    safe_power,
    mix,
    gradient,
    safe_log,
    stack,
]

def num_args(func):
    return len(inspect.signature(func).parameters)

depthMin = 4
depthMax = 10

def buildImg(depth = 0):
    funcs = [f for f in functions if
                (num_args(f) > 0 and depth < depthMax) or
                (num_args(f) == 0 and depth >= depthMin)]
    func = random.choice(funcs)
    args = [buildImg(depth + 1) for n in range(num_args(func))]
    return func(*args)

with np.errstate(**{'divide': 'raise', 'over': 'raise', 'under': 'raise', 'invalid': 'raise'}):
    image = buildImg()

available_colormaps = list(mpl.colormaps.keys())
colormap_name = random.choice(available_colormaps)
#colormap_name = 'hsv'
print(f'colormap: {colormap_name}')
colormap = mpl.cm.get_cmap(colormap_name)

image = colormap(scale_range(image, 0, 1))[:,:,0:3]
image = (image * 255).astype(np.uint8)
imsave('test.png', image)
#image = imread('test.png')
# view = ImageViewer(image)
# view.show()