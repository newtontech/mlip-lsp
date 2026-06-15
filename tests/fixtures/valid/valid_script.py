#!/usr/bin/env python3
"""Valid MLIP Python script for testing."""

from ase import Atoms
from ase.calculators.emt import EMT

# Create a simple structure
atoms = Atoms("Cu", [[0, 0, 0]], cell=[3.6, 3.6, 3.6])
atoms.calc = EMT()

# Run calculation
energy = atoms.get_potential_energy()
print(f"Energy: {energy} eV")
