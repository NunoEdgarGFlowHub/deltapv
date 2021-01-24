from jax import numpy as np, grad, vmap, jit
from functools import partial
import matplotlib.pyplot as plt

v = np.array([
    0.0, 0.02, 0.04, 0.060000000000000005, 0.08, 0.09999999999999999,
    0.12000000000000001, 0.14, 0.16, 0.18, 0.19999999999999998, 0.22,
    0.24000000000000002, 0.26, 0.28, 0.3, 0.32, 0.34, 0.36, 0.38,
    0.39999999999999997, 0.42000000000000004, 0.44, 0.45999999999999996,
    0.48000000000000004, 0.5, 0.52, 0.5399999999999999, 0.56, 0.58, 0.6, 0.62,
    0.64, 0.66, 0.68, 0.7000000000000001, 0.72, 0.7400000000000001, 0.76, 0.78,
    0.7999999999999999, 0.8200000000000001, 0.8400000000000001,
    0.8600000000000001, 0.88, 0.9, 0.9199999999999999, 0.94
])

j = np.array([
    0.01882799450659129, 0.01879856765176576, 0.018768580333567143,
    0.018738014811363984, 0.018706852356731047, 0.018675073222852775,
    0.018642656734894902, 0.018609580956954253, 0.018575822782358108,
    0.01854135782736367, 0.01850616015841796, 0.018470202397501235,
    0.01843345541902536, 0.01839588830382045, 0.018357468020730842,
    0.018318159501526814, 0.018277925065090066, 0.018236724477023198,
    0.018194514388699547, 0.018151248063680098, 0.018106874740686674,
    0.018061338905457577, 0.018014579077777513, 0.017966525886300575,
    0.017917099203650515, 0.01786620320549678, 0.017813718746720275,
    0.017759491266009782, 0.01770331267154145, 0.01764489408403717,
    0.017583825887487907, 0.01751951786925197, 0.017451107166260197,
    0.017377313529106132, 0.01729620637092025, 0.017204823920097177,
    0.017098539474066653, 0.016969987127703465, 0.016807200425042246,
    0.016590311609289348, 0.01628556057166174, 0.01583417006655876,
    0.015131262198710594, 0.013985205002644496, 0.01203822176066329,
    0.008610345694182748, 0.0023935909445044873, -0.009136607543454842
])


def quad(x):

    return np.array([x**2, x, 1])


def qspline(x, y):

    n = x.size
    M = np.zeros((3 * (n - 1), 3 * (n - 1)))
    z = np.zeros(3 * (n - 1))

    M = M.at[0, 0].set(1)
    z = z.at[1].set(y[0])

    for i in range(n - 1):
        M = M.at[3 * i + 1, 3 * i:3 * i + 3].set(quad(x[i]))
        z = z.at[3 * i + 1].set(y[i])

        M = M.at[3 * i + 2, 3 * i:3 * i + 3].set(quad(x[i + 1]))
        z = z.at[3 * i + 2].set(y[i + 1])

    for i in range(n - 2):
        M = M.at[3 * i + 3, 3 * i:3 * i + 6].set(
            np.array([2 * x[i + 1], 1, 0, -2 * x[i + 1], -1, 0]))

    coef = np.linalg.solve(M, z)
    a = coef[::3]
    b = coef[1::3]
    c = coef[2::3]

    return a, b, c


@jit
def predict(x, xp, coef):

    a, b, c = coef
    idx = np.clip(np.searchsorted(xp, x) - 1, 0)
    y = a[idx] * x**2 + b[idx] * x + c[idx]

    return y


def ascent(df, x0=0., lr=1., niter=100):

    x = x0
    for _ in range(niter):
        x = x + lr * df(x)

    return x


def calcPmax(v, j):
    p = v * j
    coef = qspline(v, p)
    fun = partial(predict, xp=v, coef=coef)
    dfun = grad(fun)

    vbest = ascent(dfun, x0=v[np.argmax(p)])
    pmax = fun(vbest)
    return pmax


if __name__ == "__main__":

    pmax = calcPmax(v, j)
    dpdj = grad(calcPmax, argnums=1)(v, j)

    dd = 1e-6
    dpdj_fd = np.zeros_like(j)
    for i in range(j.size):
        pmaxnew = calcPmax(v, j.at[i].add(dd))
        deriv = (pmaxnew - pmax) / dd
        dpdj_fd = dpdj_fd.at[i].set(deriv)

    plt.plot(v, dpdj, label="jax")
    plt.plot(v, dpdj_fd, label="fd")
    plt.legend()
    plt.show()
