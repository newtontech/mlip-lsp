# MLIP Training Scripts and Examples

Source: Multiple repositories, collected 2026-06-12

---

## 1. MACE Training Example

Source: https://github.com/acesuit/mace

### Basic Training
```bash
mace_run_train \
    --name="MACE_model" \
    --train_file="train.xyz" \
    --valid_fraction=0.05 \
    --test_file="test.xyz" \
    --config_type_weights='{"Default":1.0}' \
    --E0s='{1:-13.663181292231226, 6:-1029.2809654211628}' \
    --model="MACE" \
    --hidden_irreps='128x0e + 128x1o' \
    --r_max=5.0 \
    --batch_size=10 \
    --max_num_epochs=1500 \
    --stage_two \
    --start_stage_two=1200 \
    --ema \
    --ema_decay=0.99 \
    --amsgrad \
    --restart_latest \
    --device=cuda
```

### Fine-tuning Foundation Model
```bash
mace_run_train \
    --name="MACE_finetuned" \
    --foundation_model="small" \
    --train_file="train.xyz" \
    --valid_fraction=0.05 \
    --test_file="test.xyz" \
    --energy_weight=1.0 \
    --forces_weight=1.0 \
    --E0s="average" \
    --lr=0.01 \
    --scaling="rms_forces_scaling" \
    --batch_size=2 \
    --max_num_epochs=6 \
    --ema --ema_decay=0.99 \
    --amsgrad \
    --default_dtype="float32" \
    --device=cuda \
    --seed=3
```

### Evaluation
```bash
mace_eval_configs \
    --configs="your_configs.xyz" \
    --model="your_model.model" \
    --output="./your_output.xyz"
```

### ASE Calculator Usage
```python
from mace.calculators import mace_mp, mace_off
from ase import build
from ase.optimize import BFGS

atoms = build.molecule('H2O')
calc = mace_mp(model="medium", dispersion=False, default_dtype="float32", device='cuda')
atoms.calc = calc

# Run optimization
opt = BFGS(atoms)
opt.run(fmax=0.05)

print(atoms.get_potential_energy())
```

### Multi-GPU Training
```bash
# Using --distributed flag
mace_run_train \
    --name="MACE_multigpu" \
    --train_file="train.xyz" \
    --distributed \
    --device=cuda \
    ...
```

### Large Dataset Preprocessing
```bash
mkdir processed_data
python ./mace/scripts/preprocess_data.py \
    --train_file="/path/to/train_large.xyz" \
    --valid_fraction=0.05 \
    --test_file="/path/to/test_large.xyz" \
    --atomic_numbers="[1, 6, 7, 8, 9, 15, 16, 17, 35, 53]" \
    --r_max=4.5 \
    --h5_prefix="processed_data/" \
    --compute_statistics \
    --E0s="average" \
    --seed=123

# Then train on preprocessed data
python ./mace/scripts/run_train.py \
    --name="MACE_on_big_data" \
    --num_workers=16 \
    --train_file="./processed_data/train.h5" \
    --valid_file="./processed_data/valid.h5" \
    --test_dir="./processed_data" \
    --statistics_file="./processed_data/statistics.json" \
    --model="ScaleShiftMACE" \
    --num_interactions=2 \
    --num_channels=128 \
    --max_L=1 \
    --correlation=3 \
    --batch_size=32 \
    --max_num_epochs=100 \
    --device=cuda
```

---

## 2. MTP (MLIP-2) Training Example

Source: https://github.com/msg-byu/getting-started/blob/main/MTP.md

### Active Learning Cycle

```bash
# Step 1: Train initial potential
mlp train curr.mtp train.cfg --max-iter=500 \
    --trained-pot-name=curr.mtp \
    --curr-pot-name=curr.mtp \
    --stress-weight=5e-4 \
    --force-weight=5e-3

# Step 2: Calculate MaxVol grade
mlp calc-grade curr.mtp train.cfg train.cfg temp.cfg \
    --nbh-weight=0.0 \
    --energy-weight=1.0

# Step 3: Relax structures to find candidates
mlp relax mlip.ini \
    --force-tolerance=1e-3 \
    --stress-tolerance=1e-2 \
    --max-step=0.03 \
    --cfg-filename=catalog.cfg \
    --save-relaxed=relaxed.cfg \
    --save-unrelaxed=unrelaxed.cfg

# Step 4: Select structures for DFT calculation
# (Concatenate selected.cfg_* files first)
cat selected.cfg_* > selected.cfg

mlp select-add curr.mtp train.cfg selected.cfg diff.cfg \
    --select-threshold=3.0 \
    --nbh-weight=0.0 \
    --energy-weight=1.0 \
    --als-filename=state.als \
    --selected-filename=active_set.cfg

# Step 5: Run VASP on diff.cfg, add results to train.cfg
# Step 6: Repeat from Step 1
```

---

## 3. NequIP/Allegro Training Example

Source: https://github.com/mir-group/allegro/blob/master/configs/tutorial.yaml

### Training with Allegro Model
```bash
# Using nequip CLI with Allegro model
nequip-train allegro_config.yaml
```

### Allegro Configuration (YAML)
```yaml
run: [train, test]

cutoff_radius: 5.0
chemical_symbols: [C, O, H]
model_type_names: ${chemical_symbols}

data:
  _target_: nequip.data.datamodule.sGDML_CCSD_DataModule
  dataset: aspirin
  data_source_dir: aspirin_data
  transforms:
    - _target_: nequip.data.transforms.NeighborListTransform
      r_max: ${cutoff_radius}
    - _target_: nequip.data.transforms.ChemicalSpeciesToAtomTypeMapper
      chemical_symbols: ${chemical_symbols}
  trainval_test_subset: [40, 10]
  train_val_split: [30, 10]
  seed: 123
  train_dataloader:
    _target_: torch.utils.data.DataLoader
    batch_size: 1
  val_dataloader:
    _target_: torch.utils.data.DataLoader
    batch_size: 5

trainer:
  _target_: lightning.Trainer
  max_epochs: 5
  check_val_every_n_epoch: 1
  log_every_n_steps: 5

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
  model:
    _target_: allegro.model.AllegroModel
    seed: 456
    model_dtype: float32
    type_names: ${model_type_names}
    r_max: ${cutoff_radius}
    l_max: 1
    num_layers: 2
    num_scalar_features: 64
    num_tensor_features: 32
    parity: true
```

---

## 4. NEP Training Example

Source: https://gpumd.org/nep/input_files/nep_in.html

### nep.in Configuration
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

### Running NEP Training
```bash
# Requires train.xyz (and optionally test.xyz)
nep  # reads nep.in automatically
```

### NEP with ZBL Repulsion
```
type        1 Si
version     4
zbl         1.0 2.0
cutoff      5 5
n_max       4 4
basis_size  8 8
l_max       4 2 0
neuron      30
batch       1000
population  50
generation  100000
```

### NEP for Prediction (Inference)
```
type        2 Te Pb
version     4
prediction  1
```

---

## 5. DeePMD-kit Training Example

Source: https://github.com/deepmodeling/deepmd-kit

### Input JSON Configuration
```json
{
  "model": {
    "type_map": ["C", "H", "O"],
    "descriptor": {
      "type": "se_e2_a",
      "sel": [16, 32, 16],
      "rcut_smth": 0.5,
      "rcut": 6.0,
      "neuron": [25, 50, 100],
      "resnet_dt": false,
      "axis_neuron": 16,
      "type_one_side": true
    },
    "fitting_net": {
      "type": "ener",
      "neuron": [240, 240, 240],
      "resnet_dt": true,
      "activation": "tanh"
    }
  },
  "learning_rate": {
    "type": "exp",
    "start_lr": 0.001,
    "stop_lr": 3.51e-8
  },
  "training": {
    "systems": ["data/"],
    "set_prefix": "set",
    "batch_size": 1,
    "numb_steps": 200000,
    "seed": 1
  }
}
```

### Training Commands
```bash
# Train
dp train input.json

# Freeze model
dp freeze -o graph.pb

# Compress model (4-15x speedup)
dp compress -i graph.pb -o graph-compressed.pb

# Test
dp test -m graph.pb -s data/ -d results
```

### Python Interface
```python
import deepmd.DeepPot as DP
import numpy as np

dp = DP('model.pb')
coord = np.array([...])  # atomic coordinates
atype = np.array([...])  # atom types
box = np.array([...])    # simulation box

e, f, v = dp.eval(coord, box, atype)
```

### Data Preparation with dpdata
```python
import dpdata

# Convert from VASP
system = dpdata.LabeledSystem('OUTCAR', fmt='vasp/outcar')
system.to('deepmd/npy', 'output_dir')

# Convert from LAMMPS
system = dpdata.LabeledSystem('dump.lammps', fmt='lammps/dump')
system.to('deepmd/npy', 'output_dir')
```

---

## 6. ACEpotentials.jl Training Example

Source: https://github.com/ACEsuit/ACEpotentials.jl

```julia
using ACEpotentials

# Read training data
data = read_extxyz("train.xyz")

# Define ACE model
model = ace1_model(
    species = [:Si, :C, :O],
    N = 3,              # correlation order (body order = N+1)
    maxdeg = 12,        # maximum polynomial degree
    rcut = 5.5,         # cutoff radius (Angstrom)
    r0 = 2.5            # typical nearest-neighbor distance
)

# Fit potential
results = fit!(model, data;
    energy_key = "dft_energy",
    force_key = "dft_force",
    weights = Dict(
        "default" => Dict("E" => 1.0, "F" => 1.0, "V" => 0.1)
    )
)

# Save and use
save_potential("ace_potential.json", results)
```
