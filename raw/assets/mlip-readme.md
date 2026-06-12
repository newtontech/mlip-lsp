# MLIP Ecosystem READMEs

Source: Multiple GitHub repositories, collected 2026-06-12

---

## 1. NequIP — E(3)-Equivariant Interatomic Potentials

Source: https://github.com/mir-group/nequip

NequIP is an open-source code for building E(3)-equivariant interatomic potentials.

### Installation
```bash
pip install nequip
```

### Key Features
- Compiled training and compiled inference
- Multi-GPU training via PyTorch DistributedDataParallel
- GPU kernel accelerations with OpenEquivariance and CuEquivariance
- ASE calculator integration and LAMMPS integration via `pair_nequip_allegro`
- Extension package architecture (e.g., Allegro)

### Training Workflow
NequIP uses YAML configuration files with Hydra-based configuration. Training data is provided in extended XYZ format.

### References
- Batzner et al., "E(3)-equivariant graph neural networks for data-efficient and accurate interatomic potentials", Nature Communications 13, 2453 (2022)
- Tan et al., "High-performance training and inference for deep equivariant interatomic potentials", arXiv:2504.16068

---

## 2. Allegro — Local Equivariant Representations

Source: https://github.com/mir-group/allegro

Allegro implements the Allegro E(3)-equivariant machine learning interatomic potential. It is an extension package for the NequIP framework.

### Installation
```bash
pip install nequip-allegro
```

### Key Hyperparameters (from tutorial.yaml)
```yaml
cutoff_radius: 5.0
chemical_symbols: [C, O, H]
model_type_names: ${chemical_symbols}

# Core hyperparameters
l_max: 1                    # max spherical harmonics order (1=fast, 2=accurate, 3=high)
num_layers: 2               # tensor product layers
num_scalar_features: 64     # scalar features (16,32,64,128,256)
num_tensor_features: 32     # tensor features (8,16,32,64)
parity: true                # include odd mirror parity features

# Training
training_module:
  _target_: nequip.train.EMALightningModule
  loss:
    _target_: nequip.train.EnergyForceLoss
    per_atom_energy: true
    coeffs:
      total_energy: 1.0
      forces: 1.0
  optimizer:
    _target_: torch.optim.Adam
    lr: 0.001
```

### LAMMPS Integration
LAMMPS plugin: `pair_allegro` from `mir-group/pair_nequip_allegro`, supports Kokkos acceleration, MPI, and parallel multi-GPU.

### Reference
- Musaelian et al., "Learning local equivariant representations for large-scale atomistic dynamics", Nature Communications 14, 579 (2023)

---

## 3. MACE — Higher Order Equivariant Message Passing

Source: https://github.com/acesuit/mace

MACE provides fast and accurate machine learning interatomic potentials with higher order equivariant message passing.

### Installation
```bash
pip install mace-torch
```

### Training Command
```bash
mace_run_train \
    --name="MACE_model" \
    --train_file="train.xyz" \
    --valid_fraction=0.05 \
    --test_file="test.xyz" \
    --config_type_weights='{"Default":1.0}' \
    --E0s='{1:-13.663, 6:-1029.28}' \
    --model="MACE" \
    --hidden_irreps='128x0e + 128x1o' \
    --r_max=5.0 \
    --batch_size=10 \
    --max_num_epochs=1500 \
    --stage_two \
    --start_stage_two=1200 \
    --ema --ema_decay=0.99 \
    --amsgrad \
    --restart_latest \
    --device=cuda
```

### Key Training Parameters
| Parameter | Description |
|-----------|-------------|
| `--model` | Model type: "MACE" or "ScaleShiftMACE" |
| `--hidden_irreps` | e.g., '128x0e + 128x1o', '256x0e' |
| `--r_max` | Cutoff radius |
| `--batch_size` | Training batch size |
| `--max_num_epochs` | Maximum training epochs |
| `--stage_two` | Increase energy weight in last ~20% |
| `--E0s` | Isolated atom energies or "average" |
| `--foundation_model` | Path to pre-trained model for fine-tuning |

### YAML Configuration Support
```yaml
name: nacl
seed: 2024
train_file: train.xyz
stage_two: yes
start_stage_two: 1200
max_num_epochs: 1500
device: cpu
test_file: test.xyz
```

### ASE Integration
```python
from mace.calculators import mace_mp, mace_off
from ase import build

atoms = build.molecule('H2O')
calc = mace_mp(model="medium", default_dtype="float32", device='cuda')
atoms.calc = calc
print(atoms.get_potential_energy())
```

### Pre-trained Foundation Models
| Model | Elements | Dataset | Target |
|-------|----------|---------|--------|
| MACE-MP-0a | 89 | MPTrj | Materials |
| MACE-OFF23 | 10 | SPICE v1 | Organic Chemistry |
| MACE-OMAT-0 | 89 | OMAT | Materials |
| MACE-MH-0/1 | 89 | OMAT/OMOL/OC20/MATPES | Cross-domain |

### Reference
- Batatia et al., NeurIPS 2022

---

## 4. DeePMD-kit — Deep Potential Models

Source: https://github.com/deepmodeling/deepmd-kit

DeePMD-kit is a Python/C++ package for building deep learning-based interatomic potential energy and force field models.

### Installation
```bash
curl -fsSL https://dp1s.deepmodeling.com | bash
# or
pip install deepmd-kit
```

### CLI Usage
```bash
dp --help
```

### File Formats
| Format | Extension | Purpose |
|--------|-----------|---------|
| Model file | `.pb` | Frozen TensorFlow/protocol buffer model |
| Input data | `.npy` | NumPy binary format |
| Input data | `.h5`/`.hdf5` | HDF5 format |
| Parameters | `.json`/`.yaml` | Training configuration |

### Python Interface
```python
import deepmd.DeepPot as DP
dp = DP('model.pb')
```

### Data Conversion
`dpdata` tool converts from VASP, LAMMPS, etc. to DeePMD-kit format.

### Key Features
- Multiple backends: TensorFlow, PyTorch, JAX, Paddle
- Interfaces with LAMMPS, i-PI, AMBER, CP2K, GROMACS, OpenMM, ABACUS
- MPI and GPU support
- Model compression (4-15x speedup)
- Deep Potential series: DeepPot-SE, DPA-1, DPA-2, DPA-3

### References
- Wang et al., Computer Physics Communications 228, 178-184 (2018)
- Zeng et al., J. Chem. Phys. 159, 054801 (2023)
- Zeng et al., J. Chem. Theory Comput. 21, 4375-4385 (2025)

---

## 5. ACE.jl / ACEpotentials.jl — Atomic Cluster Expansion

Source: https://github.com/ACEsuit/ACE.jl (unmaintained, moved to ACEpotentials.jl)
Source: https://github.com/ACEsuit/ACEpotentials.jl

ACEpotentials.jl facilitates the creation and use of atomic cluster expansion (ACE) interatomic potentials in Julia.

### Key Dependencies
- Polynomials4ML.jl — basic kernels for embeddings and tensors
- EquivariantModels.jl — equivariant model building
- ACEfit.jl — unified interface to regression algorithms
- AtomsBase.jl — community interface for atomic structures
- ExtXYZ.jl — reading/writing extended XYZ format
- Molly.jl — molecular dynamics in Julia

### References
- Drautz, Phys. Rev. B 99, 014104 (2019)
- Dusson et al., J. Comp. Phys. 454, 110946 (2022)
- Witt et al., J. Chem. Phys. 159, 164101 (2023)

### License
Academic Software License v1.0 (ASL) for most parts, MIT for some components.

---

## 6. MALA — Materials Learning Algorithms

Source: https://github.com/mala-project/mala

MALA is a data-driven framework to generate surrogate models of density functional theory (DFT) calculations based on machine learning.

### Key Features
- Replaces DFT calculations with ML surrogate models
- Open-source, modular pipeline
- Integrates with Quantum ESPRESSO

### Resources
- Documentation: https://mala-project.github.io/mala/
- Tutorial: https://github.com/mala-project/mala_tutorial
- Paper: Computer Physics Communications (2025)

---
