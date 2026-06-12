# MLIP Input File Formats Reference

Source: Multiple repositories, collected 2026-06-12

---

## Overview

This document catalogs the input file formats used across MLIP (Machine Learning Interatomic Potentials) implementations. Each MLIP framework has its own configuration, training data, and model file formats.

---

## 1. NEP Configuration (nep.in)

Source: https://gpumd.org/nep/input_files/nep_in.html

The `nep.in` file specifies hyperparameters for training Neuroevolution Potential (NEP) models in GPUMD.

### File Format
- Blank lines and lines starting with `#` are ignored
- All parameter lines: `keyword parameter_1 parameter_2 ...`
- Keywords can appear in any order except `type_weight` must appear after `type`
- `type` is mandatory; all other keywords have defaults

### Complete Keyword Reference

| Keyword | Default | Description |
|---------|---------|-------------|
| `version` | 4 | NEP version (3 or 4) |
| `type` | *required* | Number of atom types and chemical species |
| `type_weight` | 1.0 for all | Force weights for different atom types |
| `model_type` | 0 | 0=potential, 1=dipole, 2=polarizability |
| `charge_mode` | - | Charge mode for potential model |
| `prediction` | - | Training or prediction (inference) mode |
| `zbl` | - | Outer cutoff for universal ZBL potential |
| `cutoff` | 8 4 | Radial and angular cutoffs |
| `n_max` | 4 4 | Size of radial and angular basis |
| `basis_size` | 8 8 | Number of radial and angular basis functions |
| `l_max` | 4 2 0 | Expansion order for angular terms |
| `neuron` | 30 | Number of neurons in hidden layer |
| `lambda_1` | - | L1 regularization weight |
| `lambda_2` | - | L2 regularization weight |
| `lambda_e` | 1.0 | Energy loss weight |
| `lambda_f` | 1.0 | Force loss weight |
| `lambda_v` | 0.1 | Virial loss weight |
| `lambda_q` | - | Charge loss weight |
| `lambda_z` | - | Dipole loss weight |
| `atomic_v` | - | Atomic or global virial fitting |
| `lambda_shear` | - | Shear stress loss weight |
| `force_delta` | - | Bias term for smaller force accuracy |
| `batch` | 1000 | Batch size for training |
| `population` | 50 | Population size for SNES algorithm |
| `generation` | 100000 | Number of SNES generations |
| `save_potential` | - | Save potential at intervals |
| `output_descriptor` | - | Output descriptor values |
| `fine_tune` | - | Fine-tune from existing model |

### Example nep.in
```
type        2 Te Pb
version     4
cutoff      8 4
n_max       4 4
basis_size  8 8
l_max       4 2 0
neuron      30
lambda_e    1.0
lambda_f    1.0
lambda_v    0.1
batch       1000
population  50
generation  100000
```

### NEP Training Data
- `train.xyz` — Training dataset in extended XYZ format
- `test.xyz` — Test dataset in extended XYZ format
- Output: `nep.txt` (trained model), `nep.restart` (restart file), `loss.out` (training log)

---

## 2. MTP Files (.mtp, .cfg)

Source: MLIP-2 package

### .mtp — Moment Tensor Potential File
Binary/text file containing fitted MTP parameters. Used as both input and output of the `mlp train` command.

### .cfg — MLIP Configuration/Training Data
Internal format for atomic structures with ab initio data. Contains:
- Atomic positions
- Energies
- Forces
- Stresses
- Lattice vectors

### mlip.ini — MLIP Configuration
INI-style configuration file used by `mlp relax` and other commands.

---

## 3. MACE Configuration

Source: https://github.com/acesuit/mace

### Training Data Format
Extended XYZ (`.xyz`) files with ASE-compatible info fields:
- `energy` — total energy
- `forces` — per-atom forces array
- `config_type` — configuration label (e.g., "Default", "IsolatedAtom")
- `config_stress_weight` — stress weight (0.0 to ignore)
- `virial` — stress/virial tensor

### CLI Arguments / YAML Configuration
MACE supports both command-line arguments and YAML config files:

```yaml
name: MACE_model
seed: 2024
train_file: train.xyz
valid_fraction: 0.05
test_file: test.xyz
config_type_weights:
  Default: 1.0
model: MACE
hidden_irreps: "128x0e + 128x1o"
r_max: 5.0
batch_size: 10
max_num_epochs: 1500
stage_two: yes
start_stage_two: 1200
ema: yes
ema_decay: 0.99
device: cuda
E0s:
  1: -13.663
  6: -1029.28
```

### Model Files
- `.model` — MACE model checkpoint
- `.pt` / `.pth` — PyTorch state dict

---

## 4. NequIP/Allegro Configuration

Source: https://github.com/mir-group/nequip

### YAML Configuration
NequIP uses Hydra-based YAML configuration:

```yaml
run: [train, test]

cutoff_radius: 5.0
chemical_symbols: [C, O, H]

data:
  _target_: nequip.data.datamodule.DataModule
  dataset: aspirin
  transforms:
    - _target_: nequip.data.transforms.NeighborListTransform
      r_max: ${cutoff_radius}
  train_dataloader:
    _target_: torch.utils.data.DataLoader
    batch_size: 1

trainer:
  _target_: lightning.Trainer
  max_epochs: 5

training_module:
  _target_: nequip.train.EMALightningModule
  loss:
    _target_: nequip.train.EnergyForceLoss
    per_atom_energy: true
  optimizer:
    _target_: torch.optim.Adam
    lr: 0.001
  model:
    _target_: allegro.model.AllegroModel  # or nequip.model.NequIPModel
```

---

## 5. DeePMD-kit Input Format

Source: https://github.com/deepmodeling/deepmd-kit

### Input Parameter File (JSON/YAML)
Controls model architecture and training hyperparameters:

```json
{
  "model": {
    "type_map": ["C", "H", "O"],
    "descriptor": {
      "type": "se_e2_a",
      "sel": [16, 32, 16],
      "rcut_smth": 0.5,
      "rcut": 6.0
    },
    "fitting_net": {
      "type": "ener",
      "neuron": [240, 240, 240],
      "activation": "tanh"
    }
  },
  "training": {
    "systems": ["data/"],
    "set_prefix": "set",
    "batch_size": 1,
    "numb_steps": 200000
  }
}
```

### Training Data Format
- **NumPy binary** (`.npy`) — arrays of coordinates, energies, forces, etc.
- **HDF5** (`.h5`/`.hdf5`) — hierarchical data format for large datasets

### Model File
- `.pb` — Frozen protocol buffer model file

### Data Conversion
`dpdata` converts from various formats:
```python
import dpdata
system = dpdata.LabeledSystem('VASP_DIR', fmt='vasp/poscar')
system.to('deepmd/npy', 'output_dir')
```

---

## 6. ACEpotentials.jl Input Format

Source: https://github.com/ACEsuit/ACEpotentials.jl

ACEpotentials uses Julia scripts for training. Data is read from extended XYZ files via ExtXYZ.jl.

```julia
using ACEpotentials

# Define basis
model = ace1_model(species = [:Si, :C],
                   N = 3,           # body order
                   maxdeg = 12,     # maximum degree
                   rcut = 5.5)      # cutoff radius

# Fit potential
data = read_extxyz("train.xyz")
potential = fit!(model, data;
                 energy_key = "dft_energy",
                 force_key = "dft_force",
                 weights = Dict("default" => Dict("E" => 1.0, "F" => 1.0)))
```

---

## 7. Common Structure File Formats

Used across all MLIP implementations for atomic structure input:

| Format | Extension | Description |
|--------|-----------|-------------|
| Extended XYZ | `.xyz` | Most common MLIP training data format |
| CIF | `.cif` | Crystallographic Information File |
| POSCAR/CONTCAR | - | VASP structure format |
| Lammps data | `.data` | LAMMPS input structure |
| ASE | various | ASE-compatible formats via `ase.io.read` |

### Extended XYZ Format
Standard format for MLIP training data, used by MACE, NequIP, ACE, NEP, and others:

```
N
lattice="a1x a1y a1z a2x a2y a2z a3x a3y a3z" properties=... energy=... config_type=...
element x y z fx fy fz
...
```

Where the first line is the atom count, second line contains metadata (lattice vectors, properties, energy, etc.), and subsequent lines list atom data.
