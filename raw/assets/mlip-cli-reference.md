# MLIP CLI Reference

Source: Multiple MLIP packages, collected 2026-06-12

---

## 1. MLIP-2 / MTP CLI (mlp)

Source: https://gitlab.com/ashapeev/mlip-2

### Commands

| Command | Description |
|---------|-------------|
| `mlp train` | Train MTP on dataset |
| `mlp calc-grade` | Calculate MaxVol grade and setup active learning |
| `mlp relax` | Relax structures with current potential |
| `mlp select-add` | Select configurations for active learning |
| `mlp calculate-potential` | Calculate using trained potential |
| `mlp validate` | Validate potential on test set |

### Global Options
| Option | Description |
|--------|-------------|
| `--max-iter=<int>` | Maximum iterations |
| `--energy-weight=<double>` | Energy loss weight |
| `--force-weight=<double>` | Force loss weight |
| `--stress-weight=<double>` | Stress loss weight |
| `--nbh-weight=<double>` | Neighborhood weight |
| `--select-threshold=<double>` | MaxVol selection threshold |
| `--nodes=<int>` | MPI nodes for parallel training |
| `--curr-pot-name=<file>` | Current potential file |
| `--trained-pot-name=<file>` | Output potential file |
| `--als-filename=<file>` | Active learning set file |

---

## 2. MACE CLI

Source: https://github.com/acesuit/mace

### Commands

| Command | Description |
|---------|-------------|
| `mace_run_train` | Train a MACE model |
| `mace_eval_configs` | Evaluate model on configurations |
| `preprocess_data.py` | Preprocess large datasets |

### Training Arguments
| Argument | Default | Description |
|----------|---------|-------------|
| `--name` | "MACE_model" | Experiment name |
| `--train_file` | required | Training data (XYZ or HDF5) |
| `--test_file` | None | Test data file |
| `--valid_fraction` | 0.05 | Validation fraction if no valid_file |
| `--valid_file` | None | Validation data file |
| `--model` | "MACE" | Model architecture (MACE, ScaleShiftMACE) |
| `--hidden_irreps` | "128x0e" | Hidden irreps representation |
| `--num_channels` | None | Number of channels (alternative to hidden_irreps) |
| `--max_L` | None | Maximum L (alternative to hidden_irreps) |
| `--r_max` | 5.0 | Cutoff radius |
| `--batch_size` | 10 | Training batch size |
| `--max_num_epochs` | 1500 | Maximum training epochs |
| `--lr` | 0.001 | Learning rate |
| `--E0s` | None | Isolated atom energies (dict, "average", or "estimated") |
| `--stage_two` | False | Enable stage two training |
| `--start_stage_two` | 0.8*max_num_epochs | When to start stage two |
| `--ema` | False | Use exponential moving average |
| `--ema_decay` | 0.99 | EMA decay rate |
| `--amsgrad` | False | Use AMSGrad optimizer |
| `--device` | "cuda" | Device (cuda, cpu, mps) |
| `--default_dtype` | "float64" | Default data type |
| `--foundation_model` | None | Pre-trained model path for fine-tuning |
| `--distributed` | False | Enable multi-GPU training |
| `--config` | None | YAML config file path |
| `--restart_latest` | False | Restart from latest checkpoint |
| `--energy_weight` | 1.0 | Energy loss weight |
| `--forces_weight` | 1.0 | Forces loss weight |
| `--stress_weight` | 1.0 | Stress loss weight |
| `--scaling` | "rms_forces_scaling" | Energy scaling method |
| `--wandb` | False | Enable Weights & Biases logging |

### Eval Arguments
| Argument | Description |
|----------|-------------|
| `--configs` | Input XYZ file |
| `--model` | Model file path |
| `--output` | Output XYZ file |

---

## 3. DeePMD-kit CLI (dp)

Source: https://github.com/deepmodeling/deepmd-kit

### Commands

| Command | Description |
|---------|-------------|
| `dp train` | Train a Deep Potential model |
| `dp freeze` | Freeze model to .pb file |
| `dp test` | Test model performance |
| `dp compress` | Compress model for faster inference |
| `dp train-npt-tf` | Train NPT model |
| `dp model-devi` | Model deviation analysis |

### Training
```bash
dp train input.json           # Train from JSON config
dp train input.yaml           # Train from YAML config
dp train input.json -o output # Specify output directory
```

### Freeze and Compress
```bash
dp freeze                     # Freeze checkpoint to graph.pb
dp freeze -o custom.pb        # Custom output name
dp compress -i graph.pb       # Compress for inference
dp compress -i graph.pb -o compressed.pb
```

### Test
```bash
dp test -m graph.pb -s data/ -d results
dp test -m graph.pb -s data/ --detail-ranges
```

---

## 4. NequIP CLI

Source: https://github.com/mir-group/nequip

### Commands
```bash
nequip-train config.yaml          # Train a model
nequip-evaluate config.yaml       # Evaluate a trained model
nequip-deploy build config.yaml   # Deploy for LAMMPS
```

### Configuration
NequIP uses Hydra-based YAML configuration files. See Allegro tutorial.yaml for an example.

---

## 5. GPUMD / NEP CLI

Source: https://gpumd.org/

### NEP Training
```bash
nep   # reads nep.in automatically, requires train.xyz
```

### GPUMD Simulation
```bash
gpumd  # reads run.in automatically, requires xyz model file
```

### Key nep.in Parameters
See [mlip-input-format.md](mlip-input-format.md) for complete parameter reference.

---

## 6. ASE Integration (Common Across MLIPs)

Most MLIP frameworks provide ASE (Atomic Simulation Environment) calculator interfaces:

### MACE
```python
from mace.calculators import mace_mp, mace_off
calc = mace_mp(model="medium", device='cuda')
```

### DeePMD
```python
from deepmd.calculator import DP
calc = DP(model="graph.pb")
```

### NequIP
```python
from nequip.ase import NequIPCalculator
calc = NequIPCalculator.from_deployed_model("deployed_model.pth")
```

### Universal ASE Usage
```python
from ase import Atoms
atoms = Atoms('H2O', positions=[[0,0,0], [0,0,1], [0,1,0]])
atoms.calc = calc
print(atoms.get_potential_energy())
print(atoms.get_forces())
```

---

## 7. LAMMPS Integration

### MACE (via pair_mace)
```lammps
pair_style mace
pair_coeff * * /path/to/model.model
```

### DeePMD (via pair_deepmd)
```lammps
pair_style deepmd graph.pb
pair_coeff * *
```

### NequIP/Allegro (via pair_nequip_allegro)
```lammps
pair_style nequip/allegro
pair_coeff * * deployed_model.pth TYPE1 TYPE2 ...
```

### NEP (via GPUMD)
NEP potentials are used within GPUMD directly, not through LAMMPS.
```lammps
# In run.in:
potential nep.txt 5
```
