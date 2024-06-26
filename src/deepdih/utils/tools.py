import numpy as np
from rdkit import Chem
from typing import List, Union, Tuple, Dict
from .topology import getRingAtoms


def regularize_aromaticity(mol: Chem.rdchem.Mol) -> bool:
    """
    Regularize Aromaticity for a rdkit.Mol object. Rings with exocyclic double bonds will not be set aromatic.
    """
    bInfo = {}
    for bond in mol.GetBonds():
        bInfo[(bond.GetBeginAtomIdx(), bond.GetEndAtomIdx())] = bond.GetBondType()
    mol.UpdatePropertyCache()
    for atom in mol.GetAtoms():
        if atom.GetSymbol() == "N" and atom.GetExplicitValence() == 4:
            atom.SetFormalCharge(1)
        elif atom.GetSymbol() == "O" and atom.GetExplicitValence() == 3:
            atom.SetFormalCharge(1)
        elif atom.GetSymbol() == "O" and atom.GetExplicitValence() == 1:
            atom.SetFormalCharge(-1)
    Chem.SanitizeMol(mol)
    rings = [tuple(r) for r in Chem.GetSymmSSSR(mol)]
    repairIdx = [False for _ in rings]
    patt = Chem.MolFromSmarts("[$([a]=[!R]):1]")
    for m in mol.GetSubstructMatches(patt):
        for i, r in enumerate(rings):
            if m[0] in r:
                repairIdx[i] = True
    repairAtomsIdx = []
    nonrepairAtomsIdx = []
    for i in range(len(rings)):
        if repairIdx[i]:
            repairAtomsIdx += list(rings[i])
        else:
            nonrepairAtomsIdx += list(rings[i])
    repairAtomsIdx = list(set(repairAtomsIdx) - set(nonrepairAtomsIdx))
    for atIdx in repairAtomsIdx:
        at = mol.GetAtomWithIdx(atIdx)
        at.SetIsAromatic(False)
        for bo in at.GetBonds():
            atIdx1, atIdx2 = bo.GetBeginAtomIdx(), bo.GetEndAtomIdx()
            if (atIdx1, atIdx2) in bInfo:
                btype = bInfo[(atIdx1, atIdx2)]
            else:
                btype = bInfo[(atIdx2, atIdx1)]
            bo.SetIsAromatic(False)
            bo.SetBondType(btype)
    return True


def write_sdf(rdmol: Union[Chem.rdchem.Mol, List[Chem.rdchem.Mol]], filename: str) -> None:
    """
    Write a RDKit molecule to a SDF file.

    Args:
        filename: The filename of the SDF file.
        rdmol: A RDKit molecule object or a list of RDKit molecule objects.
    """
    w = Chem.SDWriter(filename)
    if isinstance(rdmol, list):
        for m in rdmol:
            w.write(m)
    else:
        w.write(rdmol)
    w.close()


def read_sdf(filename: str) -> List[Chem.rdchem.Mol]:
    """
    Read a SDF file and return a list of RDKit molecule objects.

    Args:
        filename: The filename of the SDF file.

    Returns:
        A list of RDKit molecule objects.
    """
    suppl = Chem.SDMolSupplier(filename, sanitize=True, removeHs=False)
    return [x for x in suppl if x is not None]


def fix_aromatic(mol: Chem.rdchem.Mol):
    # set all atoms not on a ring to be non-aromatic
    all_ring_atoms = getRingAtoms(mol, join=True)
    for atom in mol.GetAtoms():
        if atom.GetIdx() not in all_ring_atoms:
            atom.SetIsAromatic(False)


def read_xyz_coords(filename):
    with open(filename, "r") as f:
        lines = f.readlines()
    
    coords = []
    pidx = 0
    while pidx < len(lines):
        natoms = int(lines[pidx])
        pidx += 2
        coords.append([])
        for _ in range(natoms):
            line = lines[pidx].split()
            coords[-1].append([float(x) for x in line[1:]])
            pidx += 1
    return np.array(coords)