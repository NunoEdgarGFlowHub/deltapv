from jaxpv import objects, scales, optical, sun, materials, solver, bcond, current, util
from jax import numpy as np, ops, lax, vmap
from typing import Callable, Tuple
import matplotlib.pyplot as plt
import logging

PVCell = objects.PVCell
PVDesign = objects.PVDesign
LightSource = objects.LightSource
Potentials = objects.Potentials
Array = util.Array
f64 = util.f64
i64 = util.i64


def create_design(dim_grid: Array) -> PVDesign:

    n = dim_grid.size
    grid = dim_grid / scales.units["grid"]
    init_params = {key: np.zeros(n) for key in PVDesign.__dataclass_fields__}
    init_params.update({"grid": grid})
    init_params.update({key: f64(0) for key in {"Snl", "Snr", "Spl", "Spr"}})

    return PVDesign(**init_params)


def add_material(cell: PVDesign, mat: materials.Material,
                 f: Callable[[f64], bool]) -> PVDesign:

    vf = vmap(f)
    idx = vf(cell.grid * scales.units["grid"])

    return objects.update(
        cell, **{
            param: np.where(idx, value / scales.units[param],
                            getattr(cell, param))
            for param, value in mat
        })


def contacts(cell: PVDesign, Snl: f64, Snr: f64, Spl: f64,
             Spr: f64) -> PVDesign:

    return objects.update(cell,
                          Snl=f64(Snl / scales.units["Snl"]),
                          Snr=f64(Snr / scales.units["Snr"]),
                          Spl=f64(Spl / scales.units["Spl"]),
                          Spr=f64(Spr / scales.units["Spr"]))


def single_pn_junction(cell: PVDesign, Nleft: f64, Nright: f64,
                       x: f64) -> PVDesign:

    idx = cell.grid * scales.units["grid"] <= x
    doping = np.where(idx, Nleft, Nright) / scales.units["Ndop"]

    return objects.update(cell, Ndop=doping)


def doping(cell: PVDesign, N: f64, f: Callable[[f64], bool]) -> PVDesign:

    vf = vmap(f)
    idx = vf(cell.grid * scales.units["grid"])
    doping = np.where(idx, N / scales.units["Ndop"], cell.Ndop)

    return objects.update(cell, Ndop=doping)


def incident_light(kind: str = "sun",
                   Lambda: Array = None,
                   P_in: Array = None) -> LightSource:

    if kind == "sun":
        return LightSource(Lambda=sun.Lambda_eff, P_in=sun.P_in_eff)

    if kind == "white":
        return LightSource(Lambda=np.linspace(4e2, 8e2, 100),
                           P_in=2e2 * np.ones(5, dtype=np.float64))

    if kind == "monochromatic":
        if Lambda is None:
            Lambda = np.array([4e2])
        return LightSource(Lambda=Lambda, P_in=np.array([1e3]))

    if kind == "user":
        assert Lambda is not None
        assert P_in is not None
        P_in = 1e3 * P_in / np.sum(P_in)
        return LightSource(Lambda=Lambda, P_in=P_in)


def init_cell(design: PVDesign, ls: LightSource) -> PVCell:

    G = optical.compute_G(design, ls)
    dgrid = np.diff(design.grid)
    params = design.__dict__.copy()
    params["dgrid"] = dgrid
    params.pop("grid")
    params["G"] = G

    return PVCell(**params)


def vincr(cell: PVCell, num_vals: i64 = 50) -> f64:

    phi_ini_left, phi_ini_right = bcond.boundary_phi(cell)
    incr_step = np.abs(phi_ini_right - phi_ini_left) / num_vals
    incr_sign = (-1)**(phi_ini_right > phi_ini_left)

    return incr_sign * incr_step


def equilibrium(design: PVDesign, ls: LightSource) -> Potentials:

    N = design.grid.size
    cell = init_cell(design, ls)

    logging.info("Solving equilibrium...")
    bound_eq = bcond.boundary_eq(cell)
    pot_ini = Potentials(
        np.linspace(bound_eq.phi0, bound_eq.phiL, cell.Eg.size), np.zeros(N),
        np.zeros(N))
    pot = solver.solve_eq(cell, bound_eq, pot_ini)

    return pot


def simulate(design: PVDesign, ls: LightSource) -> Array:

    pot_eq = equilibrium(design, ls)

    cell = init_cell(design, ls)
    pot = pot_eq
    currents = np.array([], dtype=f64)
    voltages = np.array([], dtype=f64)
    dv = vincr(cell)
    vstep = 0

    while vstep < 100:

        v = dv * vstep
        scaled_v = v * scales.energy
        logging.info(f"Solving for {scaled_v} V...")
        bound = bcond.boundary(cell, v)
        pot = solver.solve(cell, bound, pot)

        total_j = current.total_current(cell, pot)
        currents = np.append(currents, total_j)
        voltages = np.append(voltages, dv * vstep)
        vstep += 1

        if currents.size > 2:
            if (currents[-2] * currents[-1]) <= 0:
                break

    dim_currents = scales.current * currents
    dim_voltages = scales.energy * voltages

    pmax = np.max(dim_currents * dim_voltages) * 1e4  # W/cm^2 -> W/m2
    eff = pmax / np.sum(ls.P_in)

    results = {
        "cell": cell,
        "eq": pot_eq,
        "Voc": pot,
        "mpp": pmax,
        "eff": eff,
        "iv": (dim_voltages, dim_currents)
    }

    return results
