# MTP (Moment Tensor Potential) Documentation

Source: Multiple sources, collected 2026-06-12

---

## Overview

The MLIP package (Machine Learning Interatomic Potentials) implements Moment Tensor Potentials (MTP) with MPI and active learning. Developed at Skoltech by Alexander Shapeev, Evgeny Podryabinkin, and Ivan Novikov.

- Official site: https://mlip.skoltech.ru/
- Source code (MLIP-2): https://gitlab.com/ashapeev/mlip-2
- Main paper: Novikov et al., "The MLIP package: moment tensor potentials with MPI and active learning", Machine Learning: Science and Technology 2, 025002 (2021)
- arXiv: https://arxiv.org/abs/2007.08555

---

## CLI Commands (mlp)

The `mlp` executable is the main CLI tool for MTP operations.

### train — Train a potential

```bash
mlp train potential.mtp train.cfg [options]
```

**Common options:**
| Option | Description | Example |
|--------|-------------|---------|
| `--max-iter=<int>` | Maximum training iterations | `--max-iter=500` |
| `--trained-pot-name=<file>` | Output trained potential file | `--trained-pot-name=curr.mtp` |
| `--curr-pot-name=<file>` | Input (current) potential file | `--curr-pot-name=curr.mtp` |
| `--energy-weight=<double>` | Energy weight in loss function | `--energy-weight=1.0` |
| `--force-weight=<double>` | Force weight in loss function | `--force-weight=5e-3` |
| `--stress-weight=<double>` | Stress weight in loss function | `--stress-weight=5e-4` |
| `--nodes=<int>` | Number of MPI nodes | `--nodes=4` |

**Example:**
```bash
mlp train curr.mtp train.cfg --max-iter=500 --trained-opt-name=curr.mtp --curr-pot-name=curr.mtp --stress-weight=5e-4 --force-weight=5e-3
```

### calc-grade — Calculate MaxVol grade

```bash
mlp calc-grade curr.mtp train.cfg train.cfg temp.cfg --nbh-weight=0.0 --energy-weight=1.0
```

Calculates the MaxVol (MV) grade and creates the `state.als` file for active learning set storage.

### relax — Relax structures

```bash
mlp relax mlip.ini --force-tolerance=1e-3 --stress-tolerance=1e-2 --max-step=0.03 --cfg-filename=catalog.cfg --save-relaxed=relaxed.cfg --save-unrelaxed=unrelaxed.cfg
```

Attempts to relax structures to equilibrium. Structures that exceed the error tolerance are collected as preselected structures.

**Input files:**
- `mlip.ini` — configuration file
- `curr.mtp` — current potential
- `catalog.cfg` — structures to relax

**Output files:**
- `relaxed.cfg_*` — relaxed structures
- `unrelaxed.cfg_*` — unrelaxed structures
- `selected.cfg_*` — preselected structures for active learning

### select-add — Active learning selection

```bash
mlp select-add curr.mtp train.cfg selected.cfg diff.cfg --select-threshold=3.0 --nbh-weight=0.0 --energy-weight=1.0 --als-filename=state.als --selected-filename=active_set.cfg
```

Selects structures from `selected.cfg` to add to the training set based on MaxVol criterion.

**Common options:**
| Option | Description |
|--------|-------------|
| `--select-threshold=<double>` | Threshold for MaxVol selection |
| `--nbh-weight=<double>` | Neighborhood weight |
| `--energy-weight=<double>` | Energy weight |
| `--als-filename=<file>` | Active learning set file |
| `--selected-filename=<file>` | Output selected configurations |

---

## File Formats

### .mtp files
The `.mtp` file is the MTP potential file. Used both as input (current/existing potential) and output (trained potential). Contains the fitted parameters of the Moment Tensor Potential.

### .cfg files
The `.cfg` file is the internal MLIP configuration/training data format. Contains atomic structures with their ab initio-calculated energies, forces, and stresses.

### mlip.ini
Configuration file used by the `relax` command and other MLIP operations.

---

## Active Learning Workflow

1. **Initialize** with a small training set (`train.cfg`) and initial potential (`curr.mtp`)
2. **Train** the potential: `mlp train curr.mtp train.cfg`
3. **Calc-grade** to set up active learning: `mlp calc-grade curr.mtp train.cfg train.cfg temp.cfg`
4. **Relax** candidate structures: `mlp relax mlip.ini --cfg-filename=catalog.cfg`
5. **Select-add** new structures: `mlp select-add curr.mtp train.cfg selected.cfg diff.cfg`
6. **Run ab initio** calculations on selected structures
7. **Add** results to training set
8. **Repeat** from step 2

---

## MTP Mathematical Background

Moment Tensor Potentials use a systematic body-order expansion of the atomic environment. The key parameters controlling accuracy are:

| Parameter | Description |
|-----------|-------------|
| `levmax` | Maximum level (body order) of the MTP |
| `NQ` | Number of radial basis functions |

Higher `levmax` and `NQ` increase accuracy but also computational cost.

The MTP functional form is based on moment tensor descriptors that systematically capture many-body interactions while maintaining rotational and permutation invariance.

---

## Common Errors

### Training hangs forever
Happens with too few configurations — the error must decrease each iteration but overfitting prevents this. Resolved by expanding the training database.

### "Error reading .mtp file"
The specified MTP file does not exist in the current directory.

### Appending to output files
Running `relax` twice appends to existing `selected.cfg` files instead of overwriting. Delete output files before re-running.

---

## References

- Novikov, Gubaev, Podryabinkin, Shapeev. "The MLIP package: moment tensor potentials with MPI and active learning." Machine Learning: Science and Technology 2, 025002 (2021). arXiv:2007.08555
- Podryabinkin, Shapeev. "Active learning of linearly parametrized interatomic potentials." Computational Materials Science 140, 171-180 (2017)
- Shapeev. "Moment tensor potentials: a class of systematically improvable interatomic potentials." Multiscale Modeling & Simulation 14(3), 1153-1173 (2016)
