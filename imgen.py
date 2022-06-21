from skimage.io import imread, imsave
from skimage.viewer import ImageViewer
import numpy as np
import random

from numpy.polynomial import Polynomial

p = Polynomial.fromroots([(0.2, 0.2), (0.7, 15)])

res = p(np.linspace(0,1,num=10))


print(res)

exit()

H = 600
W = 400
C = 3

def scale_range(x, a, b):
    if x.max() - x.min() < 0.001:
        return np.ones_like(x) * (a + b) * 0.5
    return np.interp(x, (x.min(), x.max()), (a, b))

image = np.zeros((H, W, C))

def get_rand():
    return np.ones_like(image) * np.random.rand(3)
def get_x():
    return np.ones_like(image) * np.linspace(-1.0, 1.0, W).reshape(1, W, 1)
def get_y():
    return np.ones_like(image) * np.linspace(-1.0, 1.0, H).reshape(H, 1, 1)
def div_ab(a, b):
    return np.divide(a, np.maximum(np.abs(b), 0.001))
def div_ba(a, b):
    return np.divide(b, np.maximum(np.abs(a), 0.001))
def safe_log(x):
    return np.log(np.maximum(np.abs(x), 0.001))
def safe_arcsin(a):
    return np.arcsin(scale_range(a, -1.0, 1.0))
def safe_arccos(a):
    return np.arccos(scale_range(a, -1.0, 1.0))
def safe_power(a, b):
    return np.power(scale_range(a, 0.001, 1.0), scale_range(b, 0.001, 1.0))
def safe_sin(a):
    return np.sin(scale_range(a, -5, 5))
def safe_cos(a):
    return np.cos(scale_range(a, -5, 5))
def polynomial(x, y):
    pass

functions = [(0, get_rand), # -> [0,1]
             (0, get_x), # -> [0,1]
             (0, get_y), # -> [0,1]
             (1, safe_sin), # R -> [-1,1]
             (1, safe_cos), # R -> [-1,1]
             (1, safe_arcsin), # [-1,1] -> -pi/2, pi/2
             (1, safe_arccos),
            #  (1, safe_log), # R+ -> R
             (2, np.add), # [b1,e1], [b2,e2] -> [min(b1,b2), max(e1,e2)]
             (2, np.subtract), # [b1,e1], [b2,e2] -> [b1-e2, e1-b2]
             (2, np.multiply), # [b1,e1], [b2,e2] -> [min(_*_), max(_*_)]
            #  (2, div_ab), # [a1,a2], [b1, b2] -> [min(_/_), max(_/_)]
            #  (2, div_ba),
             (2, safe_power), # [a1,a2], [b1, b2] -> [a1^b1, a2^b2]
             ]
depthMin = 7
depthMax = 20

def buildImg(depth = 0):
    funcs = [f for f in functions if
                (f[0] > 0 and depth < depthMax) or
                (f[0] == 0 and depth >= depthMin)]
    nArgs, func = random.choice(funcs)
    args = [buildImg(depth + 1) for n in range(nArgs)]
    return func(*args)

with np.errstate(**{'divide': 'raise', 'over': 'raise', 'under': 'raise', 'invalid': 'raise'}):
    image = buildImg()

image = scale_range(image, 0, 255).astype(np.uint8)
imsave('test.png', image)
#image = imread('test.png')
# view = ImageViewer(image)
# view.show()