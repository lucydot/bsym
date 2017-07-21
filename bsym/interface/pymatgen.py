from pymatgen.symmetry.analyzer import SpacegroupAnalyzer, SpacegroupOperations
from pymatgen.util.coord_utils import coord_list_mapping_pbc
from pymatgen import Lattice, Structure

from bsym import SpaceGroup, SymmetryOperation, ConfigurationSpace

def unique_symmetry_operations_as_vectors_from_structure( structure, verbose=False, subset=None ):
    """
    Uses `pymatgen`_ symmetry analysis to find the minimum complete set of symmetry operations for the space group of a structure.

    Args:
        structure (pymatgen ``Structure``): structure to be analysed.
        subset    (Optional [list]):        list of atom indices to be used for generating the symmetry operations.

    Returns:
        (list[list]): a list of lists, containing the symmetry operations as vector mappings.

    .. _pymatgen:
        http://pymatgen.org

    """
    symmetry_analyzer = SpacegroupAnalyzer( structure )
    if verbose:
        print( "The spacegroup for this structure is {}".format( symmetry_analyzer.get_space_group_symbol()) )
    symmetry_operations = symmetry_analyzer.get_symmetry_operations()
    mappings = []
    if subset:
        species_subset = [ spec for i,spec in enumerate( structure.species ) if i in subset]
        frac_coords_subset = [ coord for i, coord in enumerate( structure.frac_coords ) if i in subset ]
        mapping_structure = Structure( structure.lattice, species_subset, frac_coords_subset ) 
    else:
        mapping_structure = structure
    for symmop in symmetry_operations:
        new_structure = Structure( mapping_structure.lattice, mapping_structure.species, symmop.operate_multi( mapping_structure.frac_coords ) )
        new_mapping = [ x+1 for x in list( coord_list_mapping_pbc( new_structure.frac_coords, mapping_structure.frac_coords ) ) ]
        if new_mapping not in mappings:
            mappings.append( new_mapping )
    return mappings

def spacegroup_from_structure( structure, subset=None ):
    """
    Generates a ``SpaceGroup`` object from a `pymatgen` ``Structure``. 

    Args:
        structure (pymatgen ``Structure``): structure to be used to define the :any:`SpaceGroup`.
        subset    (Optional [list]):        list of atom indices to be used for generating the symmetry operations.

    Returns:
        a new :any:`SpaceGroup` instance
    """
    mappings = unique_symmetry_operations_as_vectors_from_structure( structure, subset=subset )
    symmetry_operations = [ SymmetryOperation.from_vector( m ) for m in mappings ]
    return SpaceGroup( symmetry_operations=symmetry_operations )

def unique_structure_substitutions( structure, to_substitute, site_distribution ):
    """
    Generate all symmetry-unique structures formed by substituting a set of sites in a structure.

    Args:
        structure (Structure): The parent structure.
        to_substitute (str): atom label for the sites to be substituted.
        site_distribution (dict): A dictionary that defines the number of each substituting element.

    Returns:
        (list[Structure]): A list of Structure objects for each unique substitution.
    """
    site_substitution_index = list( structure.indices_from_symbol( to_substitute ) )
    if len( site_substitution_index ) != sum( site_distribution.values() ):
        raise ValueError( "Number of sites from index does not match number from site distribution" )
    space_group = spacegroup_from_structure( structure, subset=site_substitution_index )
    config_space = ConfigurationSpace( objects=site_substitution_index, symmetry_group=space_group )
    numeric_site_distribution, numeric_site_mapping = parse_site_distribution( site_distribution )
    unique_configurations = config_space.unique_configurations( numeric_site_distribution )
    substituted_structures = []
    for c in unique_configurations:
        s = structure.copy()
        for j, k in enumerate( c.tolist() ):
            s.replace( site_substitution_index[j], numeric_site_mapping[k] )
        substituted_structures.append( s )
    return substituted_structures

def parse_site_distribution( site_distribution ):
    """
    Converts a site distribution using species labels into one using integer labels.

    Args:
        site_distribution (dict): e.g. `{ 'Mg': 1, 'Li': 3 }`

    Returns:
        numeric_site_distribution ( dict): e.g. `{ 1:1, 0:3 }`
        numeric_site_mapping (dict): e.g. `{ 1:'Mg', 0:'Li' }`
    """
    numeric_site_distribution = {}
    numeric_site_mapping = {}
    for i,k in enumerate( site_distribution.keys() ):
        numeric_site_distribution[i] = site_distribution[k]
        numeric_site_mapping[i] = k
    return numeric_site_distribution, numeric_site_mapping
    