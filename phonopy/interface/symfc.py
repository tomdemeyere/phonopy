"""Symfc force constants calculator interface."""

# Copyright (C) 2024 Atsushi Togo
# All rights reserved.
#
# This file is part of phonopy.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# * Redistributions of source code must retain the above copyright
#   notice, this list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in
#   the documentation and/or other materials provided with the
#   distribution.
#
# * Neither the name of the phonopy project nor the names of its
#   contributors may be used to endorse or promote products derived
#   from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

from __future__ import annotations

from collections.abc import Sequence
from typing import Optional, Union

import numpy as np

from phonopy.structure.atoms import PhonopyAtoms
from phonopy.structure.cells import Primitive
from phonopy.structure.symmetry import Symmetry


def get_fc2(
    supercell: PhonopyAtoms,
    primitive: Primitive,
    displacements: np.ndarray,
    forces: np.ndarray,
    atom_list: Optional[Union[Sequence[int], np.ndarray]] = None,
    symmetry: Optional[Symmetry] = None,
    log_level: int = 0,
):
    """Calculate fc2 using symfc."""
    p2s_map = primitive.p2s_map
    is_compact_fc = atom_list is not None and (atom_list == p2s_map).all()
    fc2 = run_symfc(
        supercell,
        primitive,
        displacements,
        forces,
        is_compact_fc=is_compact_fc,
        symmetry=symmetry,
        log_level=log_level,
    )

    if not is_compact_fc and atom_list is not None:
        fc2 = np.array(fc2[atom_list], dtype="double", order="C")

    return fc2


def run_symfc(
    supercell: PhonopyAtoms,
    primitive: Primitive,
    displacements: np.ndarray,
    forces: np.ndarray,
    is_compact_fc: bool = False,
    symmetry: Optional[Symmetry] = None,
    log_level: int = 0,
):
    """Calculate force constants."""
    try:
        from symfc import Symfc
        from symfc.utils.utils import SymfcAtoms
    except ImportError:
        raise ImportError("Symfc python module was not found.")

    if log_level:
        print(
            "--------------------------------"
            " Symfc start "
            "-------------------------------"
        )
        print(
            "Symfc is a non-trivial force constants calculator. Please cite the paper:"
        )
        print("A. Seko and A. Togo, arXiv:2403.03588.")
        print("Symfc is developed at https://github.com/symfc/symfc.")

    symfc_supercell = SymfcAtoms(
        cell=supercell.cell,
        scaled_positions=supercell.scaled_positions,
        numbers=supercell.numbers,
    )
    symfc = Symfc(
        symfc_supercell,
        spacegroup_operations=symmetry.dataset,
        displacements=displacements,
        forces=forces,
    ).run(orders=[2], is_compact_fc=is_compact_fc)

    if log_level:
        print(
            "---------------------------------"
            " Symfc end "
            "--------------------------------"
        )

    if is_compact_fc:
        assert (symfc.p2s_map == primitive.p2s_map).all()
    return symfc.force_constants[2]
