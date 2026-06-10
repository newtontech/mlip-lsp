"""Script missing ASE import."""

structure = build_bulk("Cu", "fcc", a=3.6)  # noqa: F821
print(structure)
