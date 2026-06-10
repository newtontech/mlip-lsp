"""ASE optimization script using MLIP model."""

from ase import Atoms
from ase.optimize import BFGS
from mlip import MLIPCalculator

structure = Atoms("H2", positions=[[0, 0, 0], [0, 0, 0.74]])
calc = MLIPCalculator(model="DPA3.1-3M")
structure.calc = calc
opt = BFGS(structure)
opt.run(fmax=0.01)
