# ----------------------------------------------------------------------------
# Copyright (c) 2016-2020, UniFrac development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------
from warnings import warn
from functools import reduce
from operator import or_
from typing import Union

import numpy as np
import pandas as pd
import skbio
import h5py
from bp import BP
from skbio import TreeNode
from skbio.stats.distance._base import _build_results as _build_stat
from biom import Table

import unifrac as qsu
from unifrac._meta import CONSOLIDATIONS


def is_biom_v210(f, ids=None):
    import h5py
    if not h5py.is_hdf5(f):
        return False
    with h5py.File(f, 'r') as fp:
        if 'format-version' not in fp.attrs:
            return False

        version = fp.attrs.get('format-version', None)

        if version is None:
            return False

        if tuple(version) != (2, 1):
            return False

        if ids is not None:
            for idel in fp['sample/ids']:
                if isinstance(idel, bytes):
                    ids.append(idel.decode('ascii'))
                else:
                    ids.append(idel)

    return True


def is_newick(f):
    sniffer = skbio.io.format.newick.newick.sniffer_function
    return sniffer(f)[0]


def _validate(table, phylogeny, ids=None):
    if not is_biom_v210(table, ids):
        raise ValueError("Table does not appear to be a BIOM-Format v2.1")
    if not is_newick(phylogeny):
        raise ValueError("The phylogeny does not appear to be newick")


def _call_ssu(table, phylogeny, *args):
    if isinstance(table, Table) and isinstance(phylogeny, (TreeNode, BP)):
        return qsu.ssu_inmem(table, phylogeny, *args)
    elif isinstance(table, str) and isinstance(phylogeny, str):
        ids = []
        _validate(table, phylogeny, ids)
        return qsu.ssu_fast(table, phylogeny, ids, *args)
    else:
        table_type = type(table)
        tree_type = type(phylogeny)
        raise ValueError(f"table ('{table_type}') and tree ('{tree_type}') "
                         f"are incompatible with the library call")


def _call_ssu_to_file(table, phylogeny, *args):
    if isinstance(table, Table) and isinstance(phylogeny, (TreeNode, BP)):
        raise NotImplementedError("Direct to file support from in memory "
                                  "objects has not been implemented yet")
    elif isinstance(table, str) and isinstance(phylogeny, str):
        _validate(table, phylogeny)
        return qsu.ssu_to_file(table, phylogeny, *args)
    else:
        table_type = type(table)
        tree_type = type(phylogeny)
        raise ValueError(f"table ('{table_type}') and tree ('{tree_type}') "
                         f"are incompatible with the library call")


#
# Functions that compute Unifrac and return a memory object
#
def unweighted(table: Union[str, Table],
               phylogeny: Union[str, TreeNode, BP],
               threads: int = 1,
               variance_adjusted: bool = False,
               bypass_tips: bool = False,
               n_substeps: int = 1) -> skbio.DistanceMatrix:
    """Compute Unweighted UniFrac

    Parameters
    ----------
    table : str
        A filepath to a BIOM-Format 2.1 file.
    phylogeny : str
        A filepath to a Newick formatted tree.
    threads : int, optional
        Deprecated, no-op.
    variance_adjusted : bool, optional
        Adjust for varianace or not. Default is False.
    bypass_tips : bool, optional
        Bypass the tips of the tree in the computation. This reduces compute
        by about 50%, but is an approximation.
    n_substeps : int, optional
        Internally split the problem in substeps for reduced memory footprint.

    Returns
    -------
    skbio.DistanceMatrix
        The resulting distance matrix.

    Raises
    ------
    IOError
        If the tree file is not found
        If the table is not found
    ValueError
        If the table does not appear to be BIOM-Format v2.1.
        If the phylogeny does not appear to be in Newick format.

    Environment variables
    ---------------------
    OMP_NUM_THREADS
        Number of CPU cores to use. If not defined, use all detected cores.
    UNIFRAC_USE_GPU
        Enable or disable GPU offload. If not defined, autodetect.
    ACC_DEVICE_NUM
        The GPU to use. If not defined, the first GPU will be used.

    Notes
    -----
    Unweighted UniFrac was originally described in [1]_. Variance Adjusted
    UniFrac was originally described in [2]_, and while its application to
    Unweighted UniFrac was not described, factoring in the variance adjustment
    is still feasible and so it is exposed.

    References
    ----------
    .. [1] Lozupone, C. & Knight, R. UniFrac: a new phylogenetic method for
       comparing microbial communities. Appl. Environ. Microbiol. 71, 8228-8235
       (2005).
    .. [2] Chang, Q., Luan, Y. & Sun, F. Variance adjusted weighted UniFrac: a
       powerful beta diversity measure for comparing communities based on
       phylogeny. BMC Bioinformatics 12:118 (2011).
    """
    return _call_ssu(table, phylogeny, 'unweighted', variance_adjusted, 1.0,
                     bypass_tips, n_substeps)


def unweighted_fp64(table: Union[str, Table],
                    phylogeny: Union[str, TreeNode, BP],
                    threads: int = 1,
                    variance_adjusted: bool = False,
                    bypass_tips: bool = False,
                    n_substeps: int = 1) -> skbio.DistanceMatrix:
    """Compute Unweighted UniFrac using fp64 math

    Parameters
    ----------
    table : str
        A filepath to a BIOM-Format 2.1 file.
    phylogeny : str
        A filepath to a Newick formatted tree.
    threads : int, optional
        Deprecated, no-op.
    variance_adjusted : bool, optional
        Adjust for varianace or not. Default is False.
    bypass_tips : bool, optional
        Bypass the tips of the tree in the computation. This reduces compute
        by about 50%, but is an approximation.
    n_substeps : int, optional
        Internally split the problem in substeps for reduced memory footprint.

    Returns
    -------
    skbio.DistanceMatrix
        The resulting distance matrix.

    Raises
    ------
    IOError
        If the tree file is not found
        If the table is not found
    ValueError
        If the table does not appear to be BIOM-Format v2.1.
        If the phylogeny does not appear to be in Newick format.

    Environment variables
    ---------------------
    OMP_NUM_THREADS
        Number of CPU cores to use. If not defined, use all detected cores.
    UNIFRAC_USE_GPU
        Enable or disable GPU offload. If not defined, autodetect.
    ACC_DEVICE_NUM
        The GPU to use. If not defined, the first GPU will be used.

    Notes
    -----
    Unweighted UniFrac was originally described in [1]_. Variance Adjusted
    UniFrac was originally described in [2]_, and while its application to
    Unweighted UniFrac was not described, factoring in the variance adjustment
    is still feasible and so it is exposed.

    References
    ----------
    .. [1] Lozupone, C. & Knight, R. UniFrac: a new phylogenetic method for
       comparing microbial communities. Appl. Environ. Microbiol. 71, 8228-8235
       (2005).
    .. [2] Chang, Q., Luan, Y. & Sun, F. Variance adjusted weighted UniFrac: a
       powerful beta diversity measure for comparing communities based on
       phylogeny. BMC Bioinformatics 12:118 (2011).
    """
    return _call_ssu(table, phylogeny, 'unweighted_fp64', variance_adjusted,
                     1.0, bypass_tips, n_substeps)


def unweighted_fp32(table: Union[str, Table],
                    phylogeny: Union[str, TreeNode, BP],
                    threads: int = 1,
                    variance_adjusted: bool = False,
                    bypass_tips: bool = False,
                    n_substeps: int = 1) -> skbio.DistanceMatrix:
    """Compute Unweighted UniFrac using fp32 math

    Parameters
    ----------
    table : str
        A filepath to a BIOM-Format 2.1 file.
    phylogeny : str
        A filepath to a Newick formatted tree.
    threads : int, optional
        Deprecated, no-op.
    variance_adjusted : bool, optional
        Adjust for varianace or not. Default is False.
    bypass_tips : bool, optional
        Bypass the tips of the tree in the computation. This reduces compute
        by about 50%, but is an approximation.
    n_substeps : int, optional
        Internally split the problem in substeps for reduced memory footprint.

    Returns
    -------
    skbio.DistanceMatrix
        The resulting distance matrix.

    Raises
    ------
    IOError
        If the tree file is not found
        If the table is not found
    ValueError
        If the table does not appear to be BIOM-Format v2.1.
        If the phylogeny does not appear to be in Newick format.

    Environment variables
    ---------------------
    OMP_NUM_THREADS
        Number of CPU cores to use. If not defined, use all detected cores.
    UNIFRAC_USE_GPU
        Enable or disable GPU offload. If not defined, autodetect.
    ACC_DEVICE_NUM
        The GPU to use. If not defined, the first GPU will be used.

    Notes
    -----
    Unweighted UniFrac was originally described in [1]_. Variance Adjusted
    UniFrac was originally described in [2]_, and while its application to
    Unweighted UniFrac was not described, factoring in the variance adjustment
    is still feasible and so it is exposed.

    References
    ----------
    .. [1] Lozupone, C. & Knight, R. UniFrac: a new phylogenetic method for
       comparing microbial communities. Appl. Environ. Microbiol. 71, 8228-8235
       (2005).
    .. [2] Chang, Q., Luan, Y. & Sun, F. Variance adjusted weighted UniFrac: a
       powerful beta diversity measure for comparing communities based on
       phylogeny. BMC Bioinformatics 12:118 (2011).
    """
    return _call_ssu(table, phylogeny, 'unweighted_fp32', variance_adjusted,
                     1.0, bypass_tips, n_substeps)


def weighted_normalized(table: Union[str, Table],
                        phylogeny: Union[str, TreeNode, BP],
                        threads: int = 1,
                        variance_adjusted: bool = False,
                        bypass_tips: bool = False,
                        n_substeps: int = 1) -> skbio.DistanceMatrix:
    """Compute weighted normalized UniFrac

    Parameters
    ----------
    table : str
        A filepath to a BIOM-Format 2.1 file.
    phylogeny : str
        A filepath to a Newick formatted tree.
    threads : int, optional
        Deprecated, no-op.
    variance_adjusted : bool, optional
        Adjust for varianace or not. Default is False.
    bypass_tips : bool, optional
        Bypass the tips of the tree in the computation. This reduces compute
        by about 50%, but is an approximation.
    n_substeps : int, optional
        Internally split the problem in substeps for reduced memory footprint.

    Returns
    -------
    skbio.DistanceMatrix
        The resulting distance matrix.

    Raises
    ------
    IOError
        If the tree file is not found
        If the table is not found
    ValueError
        If the table does not appear to be BIOM-Format v2.1.
        If the phylogeny does not appear to be in Newick format.

    Environment variables
    ---------------------
    OMP_NUM_THREADS
        Number of CPU cores to use. If not defined, use all detected cores.
    UNIFRAC_USE_GPU
        Enable or disable GPU offload. If not defined, autodetect.
    ACC_DEVICE_NUM
        The GPU to use. If not defined, the first GPU will be used.

    Notes
    -----
    Weighted UniFrac was originally described in [1]_. Variance Adjusted
    Weighted UniFrac was originally described in [2]_.

    References
    ----------
    .. [1] Lozupone, C. A., Hamady, M., Kelley, S. T. & Knight, R. Quantitative
       and qualitative beta diversity measures lead to different insights into
       factors that structure microbial communities. Appl. Environ. Microbiol.
       73, 1576-1585 (2007).
    .. [2] Chang, Q., Luan, Y. & Sun, F. Variance adjusted weighted UniFrac: a
       powerful beta diversity measure for comparing communities based on
       phylogeny. BMC Bioinformatics 12:118 (2011).
    """
    return _call_ssu(str(table), str(phylogeny), 'weighted_normalized',
                     variance_adjusted, 1.0, bypass_tips, n_substeps)


def weighted_normalized_fp64(table: Union[str, Table],
                             phylogeny: Union[str, TreeNode, BP],
                             threads: int = 1,
                             variance_adjusted: bool = False,
                             bypass_tips: bool = False,
                             n_substeps: int = 1
                             ) -> skbio.DistanceMatrix:
    """Compute weighted normalized UniFrac using fp64 math

    Parameters
    ----------
    table : str
        A filepath to a BIOM-Format 2.1 file.
    phylogeny : str
        A filepath to a Newick formatted tree.
    threads : int, optional
        Deprecated, no-op.
    variance_adjusted : bool, optional
        Adjust for varianace or not. Default is False.
    bypass_tips : bool, optional
        Bypass the tips of the tree in the computation. This reduces compute
        by about 50%, but is an approximation.
    n_substeps : int, optional
        Internally split the problem in substeps for reduced memory footprint.

    Returns
    -------
    skbio.DistanceMatrix
        The resulting distance matrix.

    Raises
    ------
    IOError
        If the tree file is not found
        If the table is not found
    ValueError
        If the table does not appear to be BIOM-Format v2.1.
        If the phylogeny does not appear to be in Newick format.

    Environment variables
    ---------------------
    OMP_NUM_THREADS
        Number of CPU cores to use. If not defined, use all detected cores.
    UNIFRAC_USE_GPU
        Enable or disable GPU offload. If not defined, autodetect.
    ACC_DEVICE_NUM
        The GPU to use. If not defined, the first GPU will be used.

    Notes
    -----
    Weighted UniFrac was originally described in [1]_. Variance Adjusted
    Weighted UniFrac was originally described in [2]_.

    References
    ----------
    .. [1] Lozupone, C. A., Hamady, M., Kelley, S. T. & Knight, R. Quantitative
       and qualitative beta diversity measures lead to different insights into
       factors that structure microbial communities. Appl. Environ. Microbiol.
       73, 1576-1585 (2007).
    .. [2] Chang, Q., Luan, Y. & Sun, F. Variance adjusted weighted UniFrac: a
       powerful beta diversity measure for comparing communities based on
       phylogeny. BMC Bioinformatics 12:118 (2011).
    """
    return _call_ssu(str(table), str(phylogeny), 'weighted_normalized_fp64',
                     variance_adjusted, 1.0, bypass_tips, n_substeps)


def weighted_normalized_fp32(table: Union[str, Table],
                             phylogeny: Union[str, TreeNode, BP],
                             threads: int = 1,
                             variance_adjusted: bool = False,
                             bypass_tips: bool = False,
                             n_substeps: int = 1
                             ) -> skbio.DistanceMatrix:
    """Compute weighted normalized UniFrac using fp32 math

    Parameters
    ----------
    table : str
        A filepath to a BIOM-Format 2.1 file.
    phylogeny : str
        A filepath to a Newick formatted tree.
    threads : int, optional
        Deprecated, no-op.
    variance_adjusted : bool, optional
        Adjust for varianace or not. Default is False.
    bypass_tips : bool, optional
        Bypass the tips of the tree in the computation. This reduces compute
        by about 50%, but is an approximation.
    n_substeps : int, optional
        Internally split the problem in substeps for reduced memory footprint.

    Returns
    -------
    skbio.DistanceMatrix
        The resulting distance matrix.

    Raises
    ------
    IOError
        If the tree file is not found
        If the table is not found
    ValueError
        If the table does not appear to be BIOM-Format v2.1.
        If the phylogeny does not appear to be in Newick format.

    Environment variables
    ---------------------
    OMP_NUM_THREADS
        Number of CPU cores to use. If not defined, use all detected cores.
    UNIFRAC_USE_GPU
        Enable or disable GPU offload. If not defined, autodetect.
    ACC_DEVICE_NUM
        The GPU to use. If not defined, the first GPU will be used.

    Notes
    -----
    Weighted UniFrac was originally described in [1]_. Variance Adjusted
    Weighted UniFrac was originally described in [2]_.

    References
    ----------
    .. [1] Lozupone, C. A., Hamady, M., Kelley, S. T. & Knight, R. Quantitative
       and qualitative beta diversity measures lead to different insights into
       factors that structure microbial communities. Appl. Environ. Microbiol.
       73, 1576-1585 (2007).
    .. [2] Chang, Q., Luan, Y. & Sun, F. Variance adjusted weighted UniFrac: a
       powerful beta diversity measure for comparing communities based on
       phylogeny. BMC Bioinformatics 12:118 (2011).
    """
    return _call_ssu(str(table), str(phylogeny), 'weighted_normalized_fp32',
                     variance_adjusted, 1.0, bypass_tips, n_substeps)


def weighted_unnormalized(table: Union[str, Table],
                          phylogeny: Union[str, TreeNode, BP],
                          threads: int = 1,
                          variance_adjusted: bool = False,
                          bypass_tips: bool = False,
                          n_substeps: int = 1) -> skbio.DistanceMatrix:
    # noqa
    """Compute weighted unnormalized UniFrac

    Parameters
    ----------
    table : str
        A filepath to a BIOM-Format 2.1 file.
    phylogeny : str
        A filepath to a Newick formatted tree.
    threads : int, optional
        Deprecated, no-op..
    variance_adjusted : bool, optional
        Adjust for varianace or not. Default is False.
    bypass_tips : bool, optional
        Bypass the tips of the tree in the computation. This reduces compute
        by about 50%, but is an approximation.
    n_substeps : int, optional
        Internally split the problem in substeps for reduced memory footprint.

    Returns
    -------
    skbio.DistanceMatrix
        The resulting distance matrix.

    Raises
    ------
    IOError
        If the tree file is not found
        If the table is not found
    ValueError
        If the table does not appear to be BIOM-Format v2.1.
        If the phylogeny does not appear to be in Newick format.

    Environment variables
    ---------------------
    OMP_NUM_THREADS
        Number of CPU cores to use. If not defined, use all detected cores.
    UNIFRAC_USE_GPU
        Enable or disable GPU offload. If not defined, autodetect.
    ACC_DEVICE_NUM
        The GPU to use. If not defined, the first GPU will be used.

    Notes
    -----
    Weighted UniFrac was originally described in [1]_. Variance Adjusted
    Weighted UniFrac was originally described in [2]_.

    References
    ----------
    .. [1] Lozupone, C. A., Hamady, M., Kelley, S. T. & Knight, R. Quantitative
       and qualitative beta diversity measures lead to different insights into
       factors that structure microbial communities. Appl. Environ. Microbiol.
       73, 1576-1585 (2007).
    .. [2] Chang, Q., Luan, Y. & Sun, F. Variance adjusted weighted UniFrac: a
       powerful beta diversity measure for comparing communities based on
       phylogeny. BMC Bioinformatics 12:118 (2011).
    """
    return _call_ssu(str(table), str(phylogeny), 'weighted_unnormalized',
                     variance_adjusted, 1.0, bypass_tips, n_substeps)


def weighted_unnormalized_fp64(table: Union[str, Table],
                               phylogeny: Union[str, TreeNode, BP],
                               threads: int = 1,
                               variance_adjusted: bool = False,
                               bypass_tips: bool = False,
                               n_substeps: int = 1
                               ) -> skbio.DistanceMatrix:
    # noqa
    """Compute weighted unnormalized UniFrac using fp64 math

    Parameters
    ----------
    table : str
        A filepath to a BIOM-Format 2.1 file.
    phylogeny : str
        A filepath to a Newick formatted tree.
    threads : int, optional
        TDeprecated, no-op..
    variance_adjusted : bool, optional
        Adjust for varianace or not. Default is False.
    bypass_tips : bool, optional
        Bypass the tips of the tree in the computation. This reduces compute
        by about 50%, but is an approximation.
    n_substeps : int, optional
        Internally split the problem in substeps for reduced memory footprint.

    Returns
    -------
    skbio.DistanceMatrix
        The resulting distance matrix.

    Raises
    ------
    IOError
        If the tree file is not found
        If the table is not found
    ValueError
        If the table does not appear to be BIOM-Format v2.1.
        If the phylogeny does not appear to be in Newick format.

    Environment variables
    ---------------------
    OMP_NUM_THREADS
        Number of CPU cores to use. If not defined, use all detected cores.
    UNIFRAC_USE_GPU
        Enable or disable GPU offload. If not defined, autodetect.
    ACC_DEVICE_NUM
        The GPU to use. If not defined, the first GPU will be used.

    Notes
    -----
    Weighted UniFrac was originally described in [1]_. Variance Adjusted
    Weighted UniFrac was originally described in [2]_.

    References
    ----------
    .. [1] Lozupone, C. A., Hamady, M., Kelley, S. T. & Knight, R. Quantitative
       and qualitative beta diversity measures lead to different insights into
       factors that structure microbial communities. Appl. Environ. Microbiol.
       73, 1576-1585 (2007).
    .. [2] Chang, Q., Luan, Y. & Sun, F. Variance adjusted weighted UniFrac: a
       powerful beta diversity measure for comparing communities based on
       phylogeny. BMC Bioinformatics 12:118 (2011).
    """
    return _call_ssu(str(table), str(phylogeny), 'weighted_unnormalized_fp64',
                     variance_adjusted, 1.0, bypass_tips, n_substeps)


def weighted_unnormalized_fp32(table: Union[str, Table],
                               phylogeny: Union[str, TreeNode, BP],
                               threads: int = 1,
                               variance_adjusted: bool = False,
                               bypass_tips: bool = False,
                               n_substeps: int = 1
                               ) -> skbio.DistanceMatrix:
    # noqa
    """Compute weighted unnormalized UniFrac using fp32 math

    Parameters
    ----------
    table : str
        A filepath to a BIOM-Format 2.1 file.
    phylogeny : str
        A filepath to a Newick formatted tree.
    threads : int, optional
        TDeprecated, no-op..
    variance_adjusted : bool, optional
        Adjust for varianace or not. Default is False.
    bypass_tips : bool, optional
        Bypass the tips of the tree in the computation. This reduces compute
        by about 50%, but is an approximation.
    n_substeps : int, optional
        Internally split the problem in substeps for reduced memory footprint.

    Returns
    -------
    skbio.DistanceMatrix
        The resulting distance matrix.

    Raises
    ------
    IOError
        If the tree file is not found
        If the table is not found
    ValueError
        If the table does not appear to be BIOM-Format v2.1.
        If the phylogeny does not appear to be in Newick format.

    Environment variables
    ---------------------
    OMP_NUM_THREADS
        Number of CPU cores to use. If not defined, use all detected cores.
    UNIFRAC_USE_GPU
        Enable or disable GPU offload. If not defined, autodetect.
    ACC_DEVICE_NUM
        The GPU to use. If not defined, the first GPU will be used.

    Notes
    -----
    Weighted UniFrac was originally described in [1]_. Variance Adjusted
    Weighted UniFrac was originally described in [2]_.

    References
    ----------
    .. [1] Lozupone, C. A., Hamady, M., Kelley, S. T. & Knight, R. Quantitative
       and qualitative beta diversity measures lead to different insights into
       factors that structure microbial communities. Appl. Environ. Microbiol.
       73, 1576-1585 (2007).
    .. [2] Chang, Q., Luan, Y. & Sun, F. Variance adjusted weighted UniFrac: a
       powerful beta diversity measure for comparing communities based on
       phylogeny. BMC Bioinformatics 12:118 (2011).
    """
    return _call_ssu(str(table), str(phylogeny), 'weighted_unnormalized_fp32',
                     variance_adjusted, 1.0, bypass_tips, n_substeps)


def generalized(table: Union[str, Table],
                phylogeny: Union[str, TreeNode, BP],
                threads: int = 1,
                alpha: float = 1.0,
                variance_adjusted: bool = False,
                bypass_tips: bool = False,
                n_substeps: int = 1) -> skbio.DistanceMatrix:
    """Compute Generalized UniFrac

    Parameters
    ----------
    table : str
        A filepath to a BIOM-Format 2.1 file.
    phylogeny : str
        A filepath to a Newick formatted tree.
    threads : int, optional
        Deprecated, no-op.
    alpha : float, optional
        The level of contribution of high abundance branches. Higher alpha
        increases the contribution of from high abundance branches while lower
        alpha reduces the contribution. Alpha was originally defined over the
        range [0, 1]. Default is 1.0.
    variance_adjusted : bool, optional
        Adjust for varianace or not. Default is False.
    bypass_tips : bool, optional
        Bypass the tips of the tree in the computation. This reduces compute
        by about 50%, but is an approximation.
    n_substeps : int, optional
        Internally split the problem in substeps for reduced memory footprint.

    Returns
    -------
    skbio.DistanceMatrix
        The resulting distance matrix.

    Raises
    ------
    IOError
        If the tree file is not found
        If the table is not found
    ValueError
        If the table does not appear to be BIOM-Format v2.1.
        If the phylogeny does not appear to be in Newick format.

    Environment variables
    ---------------------
    OMP_NUM_THREADS
        Number of CPU cores to use. If not defined, use all detected cores.
    UNIFRAC_USE_GPU
        Enable or disable GPU offload. If not defined, autodetect.
    ACC_DEVICE_NUM
        The GPU to use. If not defined, the first GPU will be used.

    Notes
    -----
    Generalized UniFrac was originally described in [1]_. Variance Adjusted
    UniFrac was originally described in [2]_, but was not described in as
    applied to Generalized UniFrac. It is feasible to do, so it is exposed
    here.

    An alpha of 1.0 is Weighted normalized UniFrac. An alpha of 0.0 is
    approximately Unweighted UniFrac, and is if the proportions are
    dichotomized.

    References
    ----------
    .. [1] Chen, J., Bittinger, K., Charlson, E. S., Hoffmann C., Lewis, J.,
       Wu, G. D., Collman R. G., Bushman, F. D. & Hongzhe L. Associating
       microbiome composition with environmental covariates using generalized
       UniFrac distances. Bioinformatics 28(16), 2106–2113 (2012).
    .. [2] Chang, Q., Luan, Y. & Sun, F. Variance adjusted weighted UniFrac: a
       powerful beta diversity measure for comparing communities based on
       phylogeny. BMC Bioinformatics 12:118 (2011).
    """
    if alpha == 1.0:
        warn("alpha of 1.0 is weighted-normalized UniFrac. "
             "Weighted-normalized is being used instead as it is more "
             "optimized.",
             Warning)
        return weighted_normalized(table, phylogeny, threads,
                                   variance_adjusted, bypass_tips, n_substeps)
    else:
        return _call_ssu(str(table), str(phylogeny), 'generalized',
                         variance_adjusted, alpha, bypass_tips, n_substeps)


def generalized_fp64(table: Union[str, Table],
                     phylogeny: Union[str, TreeNode, BP],
                     threads: int = 1,
                     alpha: float = 1.0,
                     variance_adjusted: bool = False,
                     bypass_tips: bool = False,
                     n_substeps: int = 1) -> skbio.DistanceMatrix:
    """Compute Generalized UniFrac using fp64 math

    Parameters
    ----------
    table : str
        A filepath to a BIOM-Format 2.1 file.
    phylogeny : str
        A filepath to a Newick formatted tree.
    threads : int, optional
        Deprecated, no-op.
    alpha : float, optional
        The level of contribution of high abundance branches. Higher alpha
        increases the contribution of from high abundance branches while lower
        alpha reduces the contribution. Alpha was originally defined over the
        range [0, 1]. Default is 1.0.
    variance_adjusted : bool, optional
        Adjust for varianace or not. Default is False.
    bypass_tips : bool, optional
        Bypass the tips of the tree in the computation. This reduces compute
        by about 50%, but is an approximation.
    n_substeps : int, optional
        Internally split the problem in substeps for reduced memory footprint.

    Returns
    -------
    skbio.DistanceMatrix
        The resulting distance matrix.

    Raises
    ------
    IOError
        If the tree file is not found
        If the table is not found
    ValueError
        If the table does not appear to be BIOM-Format v2.1.
        If the phylogeny does not appear to be in Newick format.

    Environment variables
    ---------------------
    OMP_NUM_THREADS
        Number of CPU cores to use. If not defined, use all detected cores.
    UNIFRAC_USE_GPU
        Enable or disable GPU offload. If not defined, autodetect.
    ACC_DEVICE_NUM
        The GPU to use. If not defined, the first GPU will be used.

    Notes
    -----
    Generalized UniFrac was originally described in [1]_. Variance Adjusted
    UniFrac was originally described in [2]_, but was not described in as
    applied to Generalized UniFrac. It is feasible to do, so it is exposed
    here.

    An alpha of 1.0 is Weighted normalized UniFrac. An alpha of 0.0 is
    approximately Unweighted UniFrac, and is if the proportions are
    dichotomized.

    References
    ----------
    .. [1] Chen, J., Bittinger, K., Charlson, E. S., Hoffmann C., Lewis, J.,
       Wu, G. D., Collman R. G., Bushman, F. D. & Hongzhe L. Associating
       microbiome composition with environmental covariates using generalized
       UniFrac distances. Bioinformatics 28(16), 2106–2113 (2012).
    .. [2] Chang, Q., Luan, Y. & Sun, F. Variance adjusted weighted UniFrac: a
       powerful beta diversity measure for comparing communities based on
       phylogeny. BMC Bioinformatics 12:118 (2011).
    """
    if alpha == 1.0:
        warn("alpha of 1.0 is weighted-normalized UniFrac. "
             "Weighted-normalized is being used instead as it is more "
             "optimized.",
             Warning)
        return weighted_normalized_fp64(table, phylogeny, threads,
                                        variance_adjusted, bypass_tips,
                                        n_substeps)
    else:
        return _call_ssu(str(table), str(phylogeny), 'generalized_fp64',
                         variance_adjusted, alpha, bypass_tips, n_substeps)


def generalized_fp32(table: Union[str, Table],
                     phylogeny: Union[str, TreeNode, BP],
                     threads: int = 1,
                     alpha: float = 1.0,
                     variance_adjusted: bool = False,
                     bypass_tips: bool = False,
                     n_substeps: int = 1) -> skbio.DistanceMatrix:
    """Compute Generalized UniFrac using fp32 math

    Parameters
    ----------
    table : str
        A filepath to a BIOM-Format 2.1 file.
    phylogeny : str
        A filepath to a Newick formatted tree.
    threads : int, optional
        Deprecated, no-op.
    alpha : float, optional
        The level of contribution of high abundance branches. Higher alpha
        increases the contribution of from high abundance branches while lower
        alpha reduces the contribution. Alpha was originally defined over the
        range [0, 1]. Default is 1.0.
    variance_adjusted : bool, optional
        Adjust for varianace or not. Default is False.
    bypass_tips : bool, optional
        Bypass the tips of the tree in the computation. This reduces compute
        by about 50%, but is an approximation.
    n_substeps : int, optional
        Internally split the problem in substeps for reduced memory footprint.

    Returns
    -------
    skbio.DistanceMatrix
        The resulting distance matrix.

    Raises
    ------
    IOError
        If the tree file is not found
        If the table is not found
    ValueError
        If the table does not appear to be BIOM-Format v2.1.
        If the phylogeny does not appear to be in Newick format.

    Environment variables
    ---------------------
    OMP_NUM_THREADS
        Number of CPU cores to use. If not defined, use all detected cores.
    UNIFRAC_USE_GPU
        Enable or disable GPU offload. If not defined, autodetect.
    ACC_DEVICE_NUM
        The GPU to use. If not defined, the first GPU will be used.

    Notes
    -----
    Generalized UniFrac was originally described in [1]_. Variance Adjusted
    UniFrac was originally described in [2]_, but was not described in as
    applied to Generalized UniFrac. It is feasible to do, so it is exposed
    here.

    An alpha of 1.0 is Weighted normalized UniFrac. An alpha of 0.0 is
    approximately Unweighted UniFrac, and is if the proportions are
    dichotomized.

    References
    ----------
    .. [1] Chen, J., Bittinger, K., Charlson, E. S., Hoffmann C., Lewis, J.,
       Wu, G. D., Collman R. G., Bushman, F. D. & Hongzhe L. Associating
       microbiome composition with environmental covariates using generalized
       UniFrac distances. Bioinformatics 28(16), 2106–2113 (2012).
    .. [2] Chang, Q., Luan, Y. & Sun, F. Variance adjusted weighted UniFrac: a
       powerful beta diversity measure for comparing communities based on
       phylogeny. BMC Bioinformatics 12:118 (2011).
    """
    if alpha == 1.0:
        warn("alpha of 1.0 is weighted-normalized UniFrac. "
             "Weighted-normalized is being used instead as it is more "
             "optimized.",
             Warning)
        return weighted_normalized_fp32(table, phylogeny, threads,
                                        variance_adjusted, bypass_tips,
                                        n_substeps)
    else:
        return _call_ssu(str(table), str(phylogeny), 'generalized_fp32',
                         variance_adjusted, alpha, bypass_tips, n_substeps)


METHODS = {'unweighted': unweighted,
           'weighted_normalized': weighted_normalized,
           'weighted_unnormalized': weighted_unnormalized,
           'generalized': generalized,
           'unweighted_fp64': unweighted_fp64,
           'weighted_normalized_fp64': weighted_normalized_fp64,
           'weighted_unnormalized_fp64': weighted_unnormalized_fp64,
           'generalized_fp64': generalized_fp64,
           'unweighted_fp32': unweighted_fp32,
           'weighted_normalized_fp32': weighted_normalized_fp32,
           'weighted_unnormalized_fp32': weighted_unnormalized_fp32,
           'generalized_fp32': generalized_fp32}


def meta(tables: tuple, phylogenies: tuple, weights: tuple = None,
         consolidation: str = None, method: str = None,
         threads: int = 1, variance_adjusted: bool = False,
         alpha: float = None, bypass_tips: bool = False,
         n_substeps: int = 1) -> \
         skbio.DistanceMatrix:
    """Compute meta UniFrac

    Parameters
    ----------
    tables : tuple of str
        Filepaths to BIOM-Format 2.1 files. This tuple is expected to be in
        index order with phylogenies.
    phylogenies : tuple of str
        Filepaths to Newick formatted trees. This tuple is expected to be in
        index order with tables.
    weights : tuple of float, optional
        The weight applied to each tree/table pair. This tuple is expected to
        be in index order with tables and phylogenies. Default is to weight
        each tree/table pair evenly.
    consolidation : str, optional
        The matrix consolidation method. The available choices are:
        'skipping_missing_matrices', 'missing_zero', 'missing_one',
        'skipping_missing_values'. The default is 'skipping_missing_values'.
    method : str
        The UniFrac method to use. The available choices are:
        'unweighted', 'unweighted_fp64', 'unweighted_fp32',
        'weighted_unnormalized', 'weighted_unnormalized_fp64',
        'weighted_unnormalized_fp32',
        'weighted_normalized', 'weighted_normalized_fp64',
        'weighted_normalized_fp32',
        'generalized', 'generalized_fp64' and 'generalized_fp32'.
    threads : int, optional
        TDeprecated, no-op.
    bypass_tips : bool, optional
        Bypass the tips of the tree in the computation. This reduces compute
        by about 50%, but is an approximation.
    alpha : float, optional
        The level of contribution of high abundance branches. Higher alpha
        increases the contribution of from high abundance branches while lower
        alpha reduces the contribution. Alpha was originally defined over the
        range [0, 1]. Default is 1.0
    variance_adjusted : bool, optional
        Adjust for varianace or not. Default is False.
    n_substeps : int, optional
        Internally split the problem in substeps for reduced memory footprint.

    Returns
    -------
    skbio.DistanceMatrix
        The resulting distance matrix.

    Raises
    ------
    IOError
        If the tree file is not found
        If the table is not found
    ValueError
        If the table does not appear to be BIOM-Format v2.1.
        If the phylogeny does not appear to be in Newick format.

    Environment variables
    ---------------------
    OMP_NUM_THREADS
        Number of CPU cores to use. If not defined, use all detected cores.
    UNIFRAC_USE_GPU
        Enable or disable GPU offload. If not defined, autodetect.
    ACC_DEVICE_NUM
        The GPU to use. If not defined, the first GPU will be used.

    Notes
    -----
    UniFrac can be adapted to account for multiple genes, as originally
    done in [1]_.

    Generalized UniFrac was originally described in [2]_. Variance Adjusted
    UniFrac was originally described in [3]_, but was not described in as
    applied to Generalized UniFrac. It is feasible to do, so it is exposed
    here.

    References
    ----------
    .. [1] Lozupone C. A., Hamady M., Cantarel B. L., Coutinho P. M.,
       Henrissat B., Gordon J. I. & Knight R. The convergence of carbohydrate
       active gene repertoires in human gut microbes. PNAS 105(39):15076-81
       (2008).
    .. [2] Chen, J., Bittinger, K., Charlson, E. S., Hoffmann C., Lewis, J.,
       Wu, G. D., Collman R. G., Bushman, F. D. & Hongzhe L. Associating
       microbiome composition with environmental covariates using generalized
       UniFrac distances. Bioinformatics 28(16), 2106–2113 (2012).
    .. [3] Chang, Q., Luan, Y. & Sun, F. Variance adjusted weighted UniFrac: a
       powerful beta diversity measure for comparing communities based on
       phylogeny. BMC Bioinformatics 12:118 (2011).
    """
    if not len(tables):
        raise ValueError("No tables specified.")

    if not len(phylogenies):
        raise ValueError("No trees specified.")

    if len(tables) != len(phylogenies):
        raise ValueError("Number of trees and tables must be the same.")

    if weights is None:
        weights = tuple(1 for _ in phylogenies)
    else:
        if len(weights) != len(phylogenies):
            raise ValueError("Number of weights does not match number of "
                             "trees and tables.")

    if method is None:
        raise ValueError("No method specified.")
    method_ = METHODS.get(method.replace('-', '_'))
    if method_ is None:
        raise ValueError("Method (%s) unrecognized. Available methods are: %s"
                         % (method, ', '.join(METHODS.keys())))

    if consolidation is None:
        consolidation = 'skipping_missing_values'
    consolidation_ = CONSOLIDATIONS.get(consolidation.replace('-', '_'))
    if consolidation_ is None:
        raise ValueError("Consolidation (%s) unrecognized. Available "
                         "consolidations are: %s"
                         % (consolidation, ', '.join(CONSOLIDATIONS.keys())))

    if alpha is not None and method_ is not generalized:
        raise ValueError("The alpha parameter can only be set when the method "
                         "is set as 'generalized', the selected method is "
                         "'%s'." % method)

    kwargs = {'n_substeps': n_substeps,
              'bypass_tips': bypass_tips,
              'variance_adjusted': variance_adjusted}
    if alpha is not None:
        kwargs['alpha'] = alpha

    weights = np.array(weights, float)/sum(weights)
    dms = [method_(table, tree, **kwargs) for table, tree in zip(tables,
                                                                 phylogenies)]
    all_ids = sorted(reduce(or_, [set(dm.ids) for dm in dms]))
    dm = consolidation_(dms, [dm.ids for dm in dms], weights, all_ids)

    return skbio.DistanceMatrix(dm, ids=all_ids)


#
# Functions that compute Unifrac and write into a file
#

def unweighted_to_file(table: str,
                       phylogeny: str,
                       out_filename: str,
                       pcoa_dims: int = 10,
                       threads: int = 1,
                       variance_adjusted: bool = False,
                       bypass_tips: bool = False,
                       format: str = "hdf5",
                       buf_dirname: str = "",
                       n_substeps: int = 1) -> str:
    """Compute Unweighted UniFrac and write to file

    Parameters
    ----------
    table : str
        A filepath to a BIOM-Format 2.1 file.
    phylogeny : str
        A filepath to a Newick formatted tree.
    out_filename : str
        A filepath to the output file.
    pcoa_dims : int, optional
        Number of dimensions to use for PCoA compute.
        if set to 0, no PCoA is computed.
        Defaults of 10.
    threads : int, optional
        Deprecated, no-op.
    variance_adjusted : bool, optional
        Adjust for varianace or not. Default is False.
    bypass_tips : bool, optional
        Bypass the tips of the tree in the computation. This reduces compute
        by about 50%, but is an approximation.
    format : str, optional
        Output format to use. Defaults to "hdf5".
    buf_dirname : str, optional
        If set, the directory where the disk buffer is hosted,
        can be used to reduce the amount of memory needed.
    n_substeps : int, optional
        Internally split the problem in substeps for reduced memory footprint.

    Returns
    -------
    str
        A filepath to the output file.

    Raises
    ------
    IOError
        If the tree file is not found
        If the table is not found
        If the output file cannot be created
    ValueError
        If the table does not appear to be BIOM-Format v2.1.
        If the phylogeny does not appear to be in Newick format.

    Environment variables
    ---------------------
    OMP_NUM_THREADS
        Number of CPU cores to use. If not defined, use all detected cores.
    UNIFRAC_USE_GPU
        Enable or disable GPU offload. If not defined, autodetect.
    ACC_DEVICE_NUM
        The GPU to use. If not defined, the first GPU will be used.

    Notes
    -----
    Unweighted UniFrac was originally described in [1]_. Variance Adjusted
    UniFrac was originally described in [2]_, and while its application to
    Unweighted UniFrac was not described, factoring in the variance adjustment
    is still feasible and so it is exposed.

    References
    ----------
    .. [1] Lozupone, C. & Knight, R. UniFrac: a new phylogenetic method for
       comparing microbial communities. Appl. Environ. Microbiol. 71, 8228-8235
       (2005).
    .. [2] Chang, Q., Luan, Y. & Sun, F. Variance adjusted weighted UniFrac: a
       powerful beta diversity measure for comparing communities based on
       phylogeny. BMC Bioinformatics 12:118 (2011).
    """
    return _call_ssu_to_file(table, phylogeny, out_filename,
                             'unweighted',
                             variance_adjusted, 1.0, bypass_tips, n_substeps,
                             format, pcoa_dims, buf_dirname)


def unweighted_fp64_to_file(table: str,
                            phylogeny: str,
                            out_filename: str,
                            pcoa_dims: int = 10,
                            threads: int = 1,
                            variance_adjusted: bool = False,
                            bypass_tips: bool = False,
                            format: str = "hdf5",
                            buf_dirname: str = "",
                            n_substeps: int = 1) -> str:
    """Compute Unweighted UniFrac using fp64 math and write to file

    Parameters
    ----------
    table : str
        A filepath to a BIOM-Format 2.1 file.
    phylogeny : str
        A filepath to a Newick formatted tree.
    out_filename : str
        A filepath to the output file.
    pcoa_dims : int, optional
        Number of dimensions to use for PCoA compute.
        if set to 0, no PCoA is computed.
        Defaults of 10.
    threads : int, optional
        Deprecated, no-op.
    variance_adjusted : bool, optional
        Adjust for varianace or not. Default is False.
    bypass_tips : bool, optional
        Bypass the tips of the tree in the computation. This reduces compute
        by about 50%, but is an approximation.
    format : str, optional
        Output format to use. Defaults to "hdf5".
    buf_dirname : str, optional
        If set, the directory where the disk buffer is hosted,
        can be used to reduce the amount of memory needed.
    n_substeps : int, optional
        Internally split the problem in substeps for reduced memory footprint.

    Returns
    -------
    str
        A filepath to the output file.

    Raises
    ------
    IOError
        If the tree file is not found
        If the table is not found
        If the output file cannot be created
    ValueError
        If the table does not appear to be BIOM-Format v2.1.
        If the phylogeny does not appear to be in Newick format.

    Environment variables
    ---------------------
    OMP_NUM_THREADS
        Number of CPU cores to use. If not defined, use all detected cores.
    UNIFRAC_USE_GPU
        Enable or disable GPU offload. If not defined, autodetect.
    ACC_DEVICE_NUM
        The GPU to use. If not defined, the first GPU will be used.

    Notes
    -----
    Unweighted UniFrac was originally described in [1]_. Variance Adjusted
    UniFrac was originally described in [2]_, and while its application to
    Unweighted UniFrac was not described, factoring in the variance adjustment
    is still feasible and so it is exposed.

    References
    ----------
    .. [1] Lozupone, C. & Knight, R. UniFrac: a new phylogenetic method for
       comparing microbial communities. Appl. Environ. Microbiol. 71, 8228-8235
       (2005).
    .. [2] Chang, Q., Luan, Y. & Sun, F. Variance adjusted weighted UniFrac: a
       powerful beta diversity measure for comparing communities based on
       phylogeny. BMC Bioinformatics 12:118 (2011).
    """
    return _call_ssu_to_file(table, phylogeny, out_filename,
                             'unweighted_fp64',
                             variance_adjusted, 1.0, bypass_tips, n_substeps,
                             format, pcoa_dims, buf_dirname)


def unweighted_fp32_to_file(table: str,
                            phylogeny: str,
                            out_filename: str,
                            pcoa_dims: int = 10,
                            threads: int = 1,
                            variance_adjusted: bool = False,
                            bypass_tips: bool = False,
                            format: str = "hdf5",
                            buf_dirname: str = "",
                            n_substeps: int = 1) -> str:
    """Compute Unweighted UniFrac using fp32 math and write to file

    Parameters
    ----------
    table : str
        A filepath to a BIOM-Format 2.1 file.
    phylogeny : str
        A filepath to a Newick formatted tree.
    out_filename : str
        A filepath to the output file.
    pcoa_dims : int, optional
        Number of dimensions to use for PCoA compute.
        if set to 0, no PCoA is computed.
        Defaults of 10.
    threads : int, optional
        Deprecated, no-op.
    variance_adjusted : bool, optional
        Adjust for varianace or not. Default is False.
    bypass_tips : bool, optional
        Bypass the tips of the tree in the computation. This reduces compute
        by about 50%, but is an approximation.
    format : str, optional
        Output format to use. Defaults to "hdf5".
    buf_dirname : str, optional
        If set, the directory where the disk buffer is hosted,
        can be used to reduce the amount of memory needed.
    n_substeps : int, optional
        Internally split the problem in substeps for reduced memory footprint.

    Returns
    -------
    str
        A filepath to the output file.

    Raises
    ------
    IOError
        If the tree file is not found
        If the table is not found
        If the output file cannot be created
    ValueError
        If the table does not appear to be BIOM-Format v2.1.
        If the phylogeny does not appear to be in Newick format.

    Environment variables
    ---------------------
    OMP_NUM_THREADS
        Number of CPU cores to use. If not defined, use all detected cores.
    UNIFRAC_USE_GPU
        Enable or disable GPU offload. If not defined, autodetect.
    ACC_DEVICE_NUM
        The GPU to use. If not defined, the first GPU will be used.

    Notes
    -----
    Unweighted UniFrac was originally described in [1]_. Variance Adjusted
    UniFrac was originally described in [2]_, and while its application to
    Unweighted UniFrac was not described, factoring in the variance adjustment
    is still feasible and so it is exposed.

    References
    ----------
    .. [1] Lozupone, C. & Knight, R. UniFrac: a new phylogenetic method for
       comparing microbial communities. Appl. Environ. Microbiol. 71, 8228-8235
       (2005).
    .. [2] Chang, Q., Luan, Y. & Sun, F. Variance adjusted weighted UniFrac: a
       powerful beta diversity measure for comparing communities based on
       phylogeny. BMC Bioinformatics 12:118 (2011).
    """
    return _call_ssu_to_file(table, phylogeny, out_filename,
                             'unweighted_fp32',
                             variance_adjusted, 1.0, bypass_tips, n_substeps,
                             format, pcoa_dims, buf_dirname)


def weighted_normalized_to_file(table: str,
                                phylogeny: str,
                                out_filename: str,
                                pcoa_dims: int = 10,
                                threads: int = 1,
                                variance_adjusted: bool = False,
                                bypass_tips: bool = False,
                                format: str = "hdf5",
                                buf_dirname: str = "",
                                n_substeps: int = 1) -> str:
    """Compute weighted normalized UniFrac and write to file

    Parameters
    ----------
    table : str
        A filepath to a BIOM-Format 2.1 file.
    phylogeny : str
        A filepath to a Newick formatted tree.
    out_filename : str
        A filepath to the output file.
    pcoa_dims : int, optional
        Number of dimensions to use for PCoA compute.
        if set to 0, no PCoA is computed.
        Defaults of 10.
    threads : int, optional
        Deprecated, no-op.
    variance_adjusted : bool, optional
        Adjust for varianace or not. Default is False.
    bypass_tips : bool, optional
        Bypass the tips of the tree in the computation. This reduces compute
        by about 50%, but is an approximation.
    format : str, optional
        Output format to use. Defaults to "hdf5".
    buf_dirname : str, optional
        If set, the directory where the disk buffer is hosted,
        can be used to reduce the amount of memory needed.
    n_substeps : int, optional
        Internally split the problem in substeps for reduced memory footprint.

    Returns
    -------
    str
        A filepath to the output file.

    Raises
    ------
    IOError
        If the tree file is not found
        If the table is not found
        If the output file cannot be created
    ValueError
        If the table does not appear to be BIOM-Format v2.1.
        If the phylogeny does not appear to be in Newick format.

    Environment variables
    ---------------------
    OMP_NUM_THREADS
        Number of CPU cores to use. If not defined, use all detected cores.
    UNIFRAC_USE_GPU
        Enable or disable GPU offload. If not defined, autodetect.
    ACC_DEVICE_NUM
        The GPU to use. If not defined, the first GPU will be used.

    Notes
    -----
    Weighted UniFrac was originally described in [1]_. Variance Adjusted
    Weighted UniFrac was originally described in [2]_.

    References
    ----------
    .. [1] Lozupone, C. A., Hamady, M., Kelley, S. T. & Knight, R. Quantitative
       and qualitative beta diversity measures lead to different insights into
       factors that structure microbial communities. Appl. Environ. Microbiol.
       73, 1576-1585 (2007).
    .. [2] Chang, Q., Luan, Y. & Sun, F. Variance adjusted weighted UniFrac: a
       powerful beta diversity measure for comparing communities based on
       phylogeny. BMC Bioinformatics 12:118 (2011).
    """
    return _call_ssu_to_file(table, phylogeny, out_filename,
                             'weighted_normalized',
                             variance_adjusted, 1.0, bypass_tips, n_substeps,
                             format, pcoa_dims, buf_dirname)


def weighted_normalized_fp64_to_file(table: str,
                                     phylogeny: str,
                                     out_filename: str,
                                     pcoa_dims: int = 10,
                                     threads: int = 1,
                                     variance_adjusted: bool = False,
                                     bypass_tips: bool = False,
                                     format: str = "hdf5",
                                     buf_dirname: str = "",
                                     n_substeps: int = 1) -> str:
    """Compute weighted normalized UniFrac using fp64 math and write to file

    Parameters
    ----------
    table : str
        A filepath to a BIOM-Format 2.1 file.
    phylogeny : str
        A filepath to a Newick formatted tree.
    out_filename : str
        A filepath to the output file.
    pcoa_dims : int, optional
        Number of dimensions to use for PCoA compute.
        if set to 0, no PCoA is computed.
        Defaults of 10.
    threads : int, optional
        Deprecated, no-op.
    variance_adjusted : bool, optional
        Adjust for varianace or not. Default is False.
    bypass_tips : bool, optional
        Bypass the tips of the tree in the computation. This reduces compute
        by about 50%, but is an approximation.
    format : str, optional
        Output format to use. Defaults to "hdf5".
    buf_dirname : str, optional
        If set, the directory where the disk buffer is hosted,
        can be used to reduce the amount of memory needed.
    n_substeps : int, optional
        Internally split the problem in substeps for reduced memory footprint.

    Returns
    -------
    str
        A filepath to the output file.

    Raises
    ------
    IOError
        If the tree file is not found
        If the table is not found
        If the output file cannot be created
    ValueError
        If the table does not appear to be BIOM-Format v2.1.
        If the phylogeny does not appear to be in Newick format.

    Environment variables
    ---------------------
    OMP_NUM_THREADS
        Number of CPU cores to use. If not defined, use all detected cores.
    UNIFRAC_USE_GPU
        Enable or disable GPU offload. If not defined, autodetect.
    ACC_DEVICE_NUM
        The GPU to use. If not defined, the first GPU will be used.

    Notes
    -----
    Weighted UniFrac was originally described in [1]_. Variance Adjusted
    Weighted UniFrac was originally described in [2]_.

    References
    ----------
    .. [1] Lozupone, C. A., Hamady, M., Kelley, S. T. & Knight, R. Quantitative
       and qualitative beta diversity measures lead to different insights into
       factors that structure microbial communities. Appl. Environ. Microbiol.
       73, 1576-1585 (2007).
    .. [2] Chang, Q., Luan, Y. & Sun, F. Variance adjusted weighted UniFrac: a
       powerful beta diversity measure for comparing communities based on
       phylogeny. BMC Bioinformatics 12:118 (2011).
    """
    return _call_ssu_to_file(table, phylogeny, out_filename,
                             'weighted_normalized_fp64',
                             variance_adjusted, 1.0, bypass_tips, n_substeps,
                             format, pcoa_dims, buf_dirname)


def weighted_normalized_fp32_to_file(table: str,
                                     phylogeny: str,
                                     out_filename: str,
                                     pcoa_dims: int = 10,
                                     threads: int = 1,
                                     variance_adjusted: bool = False,
                                     bypass_tips: bool = False,
                                     format: str = "hdf5",
                                     buf_dirname: str = "",
                                     n_substeps: int = 1) -> str:
    """Compute weighted normalized UniFrac using fp32 math and write to file

    Parameters
    ----------
    table : str
        A filepath to a BIOM-Format 2.1 file.
    phylogeny : str
        A filepath to a Newick formatted tree.
    out_filename : str
        A filepath to the output file.
    pcoa_dims : int, optional
        Number of dimensions to use for PCoA compute.
        if set to 0, no PCoA is computed.
        Defaults of 10.
    threads : int, optional
        Deprecated, no-op.
    variance_adjusted : bool, optional
        Adjust for varianace or not. Default is False.
    bypass_tips : bool, optional
        Bypass the tips of the tree in the computation. This reduces compute
        by about 50%, but is an approximation.
    format : str, optional
        Output format to use. Defaults to "hdf5".
    buf_dirname : str, optional
        If set, the directory where the disk buffer is hosted,
        can be used to reduce the amount of memory needed.
    n_substeps : int, optional
        Internally split the problem in substeps for reduced memory footprint.

    Returns
    -------
    str
        A filepath to the output file.

    Raises
    ------
    IOError
        If the tree file is not found
        If the table is not found
        If the output file cannot be created
    ValueError
        If the table does not appear to be BIOM-Format v2.1.
        If the phylogeny does not appear to be in Newick format.

    Environment variables
    ---------------------
    OMP_NUM_THREADS
        Number of CPU cores to use. If not defined, use all detected cores.
    UNIFRAC_USE_GPU
        Enable or disable GPU offload. If not defined, autodetect.
    ACC_DEVICE_NUM
        The GPU to use. If not defined, the first GPU will be used.

    Notes
    -----
    Weighted UniFrac was originally described in [1]_. Variance Adjusted
    Weighted UniFrac was originally described in [2]_.

    References
    ----------
    .. [1] Lozupone, C. A., Hamady, M., Kelley, S. T. & Knight, R. Quantitative
       and qualitative beta diversity measures lead to different insights into
       factors that structure microbial communities. Appl. Environ. Microbiol.
       73, 1576-1585 (2007).
    .. [2] Chang, Q., Luan, Y. & Sun, F. Variance adjusted weighted UniFrac: a
       powerful beta diversity measure for comparing communities based on
       phylogeny. BMC Bioinformatics 12:118 (2011).
    """
    return _call_ssu_to_file(table, phylogeny, out_filename,
                             'weighted_normalized_fp32',
                             variance_adjusted, 1.0, bypass_tips, n_substeps,
                             format, pcoa_dims, buf_dirname)


def weighted_unnormalized_to_file(table: str,
                                  phylogeny: str,
                                  out_filename: str,
                                  pcoa_dims: int = 10,
                                  threads: int = 1,
                                  variance_adjusted: bool = False,
                                  bypass_tips: bool = False,
                                  format: str = "hdf5",
                                  buf_dirname: str = "",
                                  n_substeps: int = 1) -> str:
    """Compute weighted unnormalized UniFrac and write it to file

    Parameters
    ----------
    table : str
        A filepath to a BIOM-Format 2.1 file.
    phylogeny : str
        A filepath to a Newick formatted tree.
    out_filename : str
        A filepath to the output file.
    pcoa_dims : int, optional
        Number of dimensions to use for PCoA compute.
        if set to 0, no PCoA is computed.
        Defaults of 10.
    threads : int, optional
        TDeprecated, no-op..
    variance_adjusted : bool, optional
        Adjust for varianace or not. Default is False.
    bypass_tips : bool, optional
        Bypass the tips of the tree in the computation. This reduces compute
        by about 50%, but is an approximation.
    format : str, optional
        Output format to use. Defaults to "hdf5".
    buf_dirname : str, optional
        If set, the directory where the disk buffer is hosted,
        can be used to reduce the amount of memory needed.
    n_substeps : int, optional
        Internally split the problem in substeps for reduced memory footprint.

    Returns
    -------
    str
        A filepath to the output file.

    Raises
    ------
    IOError
        If the tree file is not found
        If the table is not found
        If the output file cannot be created
    ValueError
        If the table does not appear to be BIOM-Format v2.1.
        If the phylogeny does not appear to be in Newick format.

    Environment variables
    ---------------------
    OMP_NUM_THREADS
        Number of CPU cores to use. If not defined, use all detected cores.
    UNIFRAC_USE_GPU
        Enable or disable GPU offload. If not defined, autodetect.
    ACC_DEVICE_NUM
        The GPU to use. If not defined, the first GPU will be used.

    Notes
    -----
    Weighted UniFrac was originally described in [1]_. Variance Adjusted
    Weighted UniFrac was originally described in [2]_.

    References
    ----------
    .. [1] Lozupone, C. A., Hamady, M., Kelley, S. T. & Knight, R. Quantitative
       and qualitative beta diversity measures lead to different insights into
       factors that structure microbial communities. Appl. Environ. Microbiol.
       73, 1576-1585 (2007).
    .. [2] Chang, Q., Luan, Y. & Sun, F. Variance adjusted weighted UniFrac: a
       powerful beta diversity measure for comparing communities based on
       phylogeny. BMC Bioinformatics 12:118 (2011).
    """
    return _call_ssu_to_file(table, phylogeny, out_filename,
                             'weighted_unnormalized',
                             variance_adjusted, 1.0, bypass_tips, n_substeps,
                             format, pcoa_dims, buf_dirname)


def weighted_unnormalized_fp64_to_file(table: str,
                                       phylogeny: str,
                                       out_filename: str,
                                       pcoa_dims: int = 10,
                                       threads: int = 1,
                                       variance_adjusted: bool = False,
                                       bypass_tips: bool = False,
                                       format: str = "hdf5",
                                       buf_dirname: str = "",
                                       n_substeps: int = 1) -> str:
    """Compute weighted unnormalized UniFrac using fp64 math and write to file

    Parameters
    ----------
    table : str
        A filepath to a BIOM-Format 2.1 file.
    phylogeny : str
        A filepath to a Newick formatted tree.
    out_filename : str
        A filepath to the output file.
    pcoa_dims : int, optional
        Number of dimensions to use for PCoA compute.
        if set to 0, no PCoA is computed.
        Defaults of 10.
    threads : int, optional
        TDeprecated, no-op..
    variance_adjusted : bool, optional
        Adjust for varianace or not. Default is False.
    bypass_tips : bool, optional
        Bypass the tips of the tree in the computation. This reduces compute
        by about 50%, but is an approximation.
    format : str, optional
        Output format to use. Defaults to "hdf5".
    buf_dirname : str, optional
        If set, the directory where the disk buffer is hosted,
        can be used to reduce the amount of memory needed.
    n_substeps : int, optional
        Internally split the problem in substeps for reduced memory footprint.

    Returns
    -------
    str
        A filepath to the output file.

    Raises
    ------
    IOError
        If the tree file is not found
        If the table is not found
        If the output file cannot be created
    ValueError
        If the table does not appear to be BIOM-Format v2.1.
        If the phylogeny does not appear to be in Newick format.

    Environment variables
    ---------------------
    OMP_NUM_THREADS
        Number of CPU cores to use. If not defined, use all detected cores.
    UNIFRAC_USE_GPU
        Enable or disable GPU offload. If not defined, autodetect.
    ACC_DEVICE_NUM
        The GPU to use. If not defined, the first GPU will be used.

    Notes
    -----
    Weighted UniFrac was originally described in [1]_. Variance Adjusted
    Weighted UniFrac was originally described in [2]_.

    References
    ----------
    .. [1] Lozupone, C. A., Hamady, M., Kelley, S. T. & Knight, R. Quantitative
       and qualitative beta diversity measures lead to different insights into
       factors that structure microbial communities. Appl. Environ. Microbiol.
       73, 1576-1585 (2007).
    .. [2] Chang, Q., Luan, Y. & Sun, F. Variance adjusted weighted UniFrac: a
       powerful beta diversity measure for comparing communities based on
       phylogeny. BMC Bioinformatics 12:118 (2011).
    """
    return _call_ssu_to_file(table, phylogeny, out_filename,
                             'weighted_unnormalized_fp64',
                             variance_adjusted, 1.0, bypass_tips, n_substeps,
                             format, pcoa_dims, buf_dirname)


def weighted_unnormalized_fp32_to_file(table: str,
                                       phylogeny: str,
                                       out_filename: str,
                                       pcoa_dims: int = 10,
                                       threads: int = 1,
                                       variance_adjusted: bool = False,
                                       bypass_tips: bool = False,
                                       format: str = "hdf5",
                                       buf_dirname: str = "",
                                       n_substeps: int = 1) -> str:
    """Compute weighted unnormalized UniFrac using fp32 math and write to file

    Parameters
    ----------
    table : str
        A filepath to a BIOM-Format 2.1 file.
    phylogeny : str
        A filepath to a Newick formatted tree.
    out_filename : str
        A filepath to the output file.
    pcoa_dims : int, optional
        Number of dimensions to use for PCoA compute.
        if set to 0, no PCoA is computed.
        Defaults of 10.
    threads : int, optional
        TDeprecated, no-op..
    variance_adjusted : bool, optional
        Adjust for varianace or not. Default is False.
    bypass_tips : bool, optional
        Bypass the tips of the tree in the computation. This reduces compute
        by about 50%, but is an approximation.
    format : str, optional
        Output format to use. Defaults to "hdf5".
    buf_dirname : str, optional
        If set, the directory where the disk buffer is hosted,
        can be used to reduce the amount of memory needed.
    n_substeps : int, optional
        Internally split the problem in substeps for reduced memory footprint.

    Returns
    -------
    str
        A filepath to the output file.

    Raises
    ------
    IOError
        If the tree file is not found
        If the table is not found
        If the output file cannot be created
    ValueError
        If the table does not appear to be BIOM-Format v2.1.
        If the phylogeny does not appear to be in Newick format.

    Environment variables
    ---------------------
    OMP_NUM_THREADS
        Number of CPU cores to use. If not defined, use all detected cores.
    UNIFRAC_USE_GPU
        Enable or disable GPU offload. If not defined, autodetect.
    ACC_DEVICE_NUM
        The GPU to use. If not defined, the first GPU will be used.

    Notes
    -----
    Weighted UniFrac was originally described in [1]_. Variance Adjusted
    Weighted UniFrac was originally described in [2]_.

    References
    ----------
    .. [1] Lozupone, C. A., Hamady, M., Kelley, S. T. & Knight, R. Quantitative
       and qualitative beta diversity measures lead to different insights into
       factors that structure microbial communities. Appl. Environ. Microbiol.
       73, 1576-1585 (2007).
    .. [2] Chang, Q., Luan, Y. & Sun, F. Variance adjusted weighted UniFrac: a
       powerful beta diversity measure for comparing communities based on
       phylogeny. BMC Bioinformatics 12:118 (2011).
    """
    return _call_ssu_to_file(table, phylogeny, out_filename,
                             'weighted_unnormalized_fp32',
                             variance_adjusted, 1.0, bypass_tips, n_substeps,
                             format, pcoa_dims, buf_dirname)


def generalized_to_file(table: str,
                        phylogeny: str,
                        out_filename: str,
                        pcoa_dims: int = 10,
                        threads: int = 1,
                        alpha: float = 1.0,
                        variance_adjusted: bool = False,
                        bypass_tips: bool = False,
                        format: str = "hdf5",
                        buf_dirname: str = "",
                        n_substeps: int = 1) -> str:
    """Compute Generalized UniFrac and write to file

    Parameters
    ----------
    table : str
        A filepath to a BIOM-Format 2.1 file.
    phylogeny : str
        A filepath to a Newick formatted tree.
    out_filename : str
        A filepath to the output file.
    pcoa_dims : int, optional
        Number of dimensions to use for PCoA compute.
        if set to 0, no PCoA is computed.
        Defaults of 10.
    threads : int, optional
        TDeprecated, no-op.
    alpha : float, optional
        The level of contribution of high abundance branches. Higher alpha
        increases the contribution of from high abundance branches while lower
        alpha reduces the contribution. Alpha was originally defined over the
        range [0, 1]. Default is 1.0.
    variance_adjusted : bool, optional
        Adjust for varianace or not. Default is False.
    bypass_tips : bool, optional
        Bypass the tips of the tree in the computation. This reduces compute
        by about 50%, but is an approximation.
    format : str, optional
        Output format to use. Defaults to "hdf5".
    buf_dirname : str, optional
        If set, the directory where the disk buffer is hosted,
        can be used to reduce the amount of memory needed.
    n_substeps : int, optional
        Internally split the problem in substeps for reduced memory footprint.

    Returns
    -------
    str
        A filepath to the output file.

    Raises
    ------
    IOError
        If the tree file is not found
        If the table is not found
        If the output file cannot be created
    ValueError
        If the table does not appear to be BIOM-Format v2.1.
        If the phylogeny does not appear to be in Newick format.

    Environment variables
    ---------------------
    OMP_NUM_THREADS
        Number of CPU cores to use. If not defined, use all detected cores.
    UNIFRAC_USE_GPU
        Enable or disable GPU offload. If not defined, autodetect.
    ACC_DEVICE_NUM
        The GPU to use. If not defined, the first GPU will be used.

    Notes
    -----
    Generalized UniFrac was originally described in [1]_. Variance Adjusted
    UniFrac was originally described in [2]_, but was not described in as
    applied to Generalized UniFrac. It is feasible to do, so it is exposed
    here.

    An alpha of 1.0 is Weighted normalized UniFrac. An alpha of 0.0 is
    approximately Unweighted UniFrac, and is if the proportions are
    dichotomized.

    References
    ----------
    .. [1] Chen, J., Bittinger, K., Charlson, E. S., Hoffmann C., Lewis, J.,
       Wu, G. D., Collman R. G., Bushman, F. D. & Hongzhe L. Associating
       microbiome composition with environmental covariates using generalized
       UniFrac distances. Bioinformatics 28(16), 2106–2113 (2012).
    .. [2] Chang, Q., Luan, Y. & Sun, F. Variance adjusted weighted UniFrac: a
       powerful beta diversity measure for comparing communities based on
       phylogeny. BMC Bioinformatics 12:118 (2011).
    """
    if alpha == 1.0:
        warn("alpha of 1.0 is weighted-normalized UniFrac. "
             "Weighted-normalized is being used instead as it is more "
             "optimized.",
             Warning)
        return _call_ssu_to_file(table, phylogeny, out_filename,
                                 'weighted_normalized',
                                 variance_adjusted, alpha,
                                 bypass_tips, n_substeps,
                                 format, pcoa_dims, buf_dirname)
    else:
        return _call_ssu_to_file(table, phylogeny, out_filename,
                                 'generalized',
                                 variance_adjusted, alpha,
                                 bypass_tips, n_substeps,
                                 format, pcoa_dims, buf_dirname)


def generalized_fp64_to_file(table: str,
                             phylogeny: str,
                             out_filename: str,
                             pcoa_dims: int = 10,
                             threads: int = 1,
                             alpha: float = 1.0,
                             variance_adjusted: bool = False,
                             bypass_tips: bool = False,
                             format: str = "hdf5",
                             buf_dirname: str = "",
                             n_substeps: int = 1) -> str:
    """Compute Generalized UniFrac using fp64 math and write to file

    Parameters
    ----------
    table : str
        A filepath to a BIOM-Format 2.1 file.
    phylogeny : str
        A filepath to a Newick formatted tree.
    out_filename : str
        A filepath to the output file.
    pcoa_dims : int, optional
        Number of dimensions to use for PCoA compute.
        if set to 0, no PCoA is computed.
        Defaults of 10.
    threads : int, optional
        TDeprecated, no-op.
    alpha : float, optional
        The level of contribution of high abundance branches. Higher alpha
        increases the contribution of from high abundance branches while lower
        alpha reduces the contribution. Alpha was originally defined over the
        range [0, 1]. Default is 1.0.
    variance_adjusted : bool, optional
        Adjust for varianace or not. Default is False.
    bypass_tips : bool, optional
        Bypass the tips of the tree in the computation. This reduces compute
        by about 50%, but is an approximation.
    format : str, optional
        Output format to use. Defaults to "hdf5".
    buf_dirname : str, optional
        If set, the directory where the disk buffer is hosted,
        can be used to reduce the amount of memory needed.
    n_substeps : int, optional
        Internally split the problem in substeps for reduced memory footprint.

    Returns
    -------
    str
        A filepath to the output file.

    Raises
    ------
    IOError
        If the tree file is not found
        If the table is not found
        If the output file cannot be created
    ValueError
        If the table does not appear to be BIOM-Format v2.1.
        If the phylogeny does not appear to be in Newick format.

    Environment variables
    ---------------------
    OMP_NUM_THREADS
        Number of CPU cores to use. If not defined, use all detected cores.
    UNIFRAC_USE_GPU
        Enable or disable GPU offload. If not defined, autodetect.
    ACC_DEVICE_NUM
        The GPU to use. If not defined, the first GPU will be used.

    Notes
    -----
    Generalized UniFrac was originally described in [1]_. Variance Adjusted
    UniFrac was originally described in [2]_, but was not described in as
    applied to Generalized UniFrac. It is feasible to do, so it is exposed
    here.

    An alpha of 1.0 is Weighted normalized UniFrac. An alpha of 0.0 is
    approximately Unweighted UniFrac, and is if the proportions are
    dichotomized.

    References
    ----------
    .. [1] Chen, J., Bittinger, K., Charlson, E. S., Hoffmann C., Lewis, J.,
       Wu, G. D., Collman R. G., Bushman, F. D. & Hongzhe L. Associating
       microbiome composition with environmental covariates using generalized
       UniFrac distances. Bioinformatics 28(16), 2106–2113 (2012).
    .. [2] Chang, Q., Luan, Y. & Sun, F. Variance adjusted weighted UniFrac: a
       powerful beta diversity measure for comparing communities based on
       phylogeny. BMC Bioinformatics 12:118 (2011).
    """
    if alpha == 1.0:
        warn("alpha of 1.0 is weighted-normalized UniFrac. "
             "Weighted-normalized is being used instead as it is more "
             "optimized.",
             Warning)
        return _call_ssu_to_file(table, phylogeny, out_filename,
                                 'weighted_normalized_fp64',
                                 variance_adjusted, alpha,
                                 bypass_tips, n_substeps,
                                 format, pcoa_dims, buf_dirname)
    else:
        return _call_ssu_to_file(table, phylogeny, out_filename,
                                 'generalized_fp64',
                                 variance_adjusted, alpha,
                                 bypass_tips, n_substeps,
                                 format, pcoa_dims, buf_dirname)


def generalized_fp32_to_file(table: str,
                             phylogeny: str,
                             out_filename: str,
                             pcoa_dims: int = 10,
                             threads: int = 1,
                             alpha: float = 1.0,
                             variance_adjusted: bool = False,
                             bypass_tips: bool = False,
                             format: str = "hdf5",
                             buf_dirname: str = "",
                             n_substeps: int = 1) -> str:
    """Compute Generalized UniFrac using fp32 math and write to file

    Parameters
    ----------
    table : str
        A filepath to a BIOM-Format 2.1 file.
    phylogeny : str
        A filepath to a Newick formatted tree.
    out_filename : str
        A filepath to the output file.
    pcoa_dims : int, optional
        Number of dimensions to use for PCoA compute.
        if set to 0, no PCoA is computed.
        Defaults of 10.
    threads : int, optional
        TDeprecated, no-op.
    alpha : float, optional
        The level of contribution of high abundance branches. Higher alpha
        increases the contribution of from high abundance branches while lower
        alpha reduces the contribution. Alpha was originally defined over the
        range [0, 1]. Default is 1.0.
    variance_adjusted : bool, optional
        Adjust for varianace or not. Default is False.
    bypass_tips : bool, optional
        Bypass the tips of the tree in the computation. This reduces compute
        by about 50%, but is an approximation.
    format : str, optional
        Output format to use. Defaults to "hdf5".
    buf_dirname : str, optional
        If set, the directory where the disk buffer is hosted,
        can be used to reduce the amount of memory needed.
    n_substeps : int, optional
        Internally split the problem in substeps for reduced memory footprint.

    Returns
    -------
    str
        A filepath to the output file.

    Raises
    ------
    IOError
        If the tree file is not found
        If the table is not found
        If the output file cannot be created
    ValueError
        If the table does not appear to be BIOM-Format v2.1.
        If the phylogeny does not appear to be in Newick format.

    Environment variables
    ---------------------
    OMP_NUM_THREADS
        Number of CPU cores to use. If not defined, use all detected cores.
    UNIFRAC_USE_GPU
        Enable or disable GPU offload. If not defined, autodetect.
    ACC_DEVICE_NUM
        The GPU to use. If not defined, the first GPU will be used.

    Notes
    -----
    Generalized UniFrac was originally described in [1]_. Variance Adjusted
    UniFrac was originally described in [2]_, but was not described in as
    applied to Generalized UniFrac. It is feasible to do, so it is exposed
    here.

    An alpha of 1.0 is Weighted normalized UniFrac. An alpha of 0.0 is
    approximately Unweighted UniFrac, and is if the proportions are
    dichotomized.

    References
    ----------
    .. [1] Chen, J., Bittinger, K., Charlson, E. S., Hoffmann C., Lewis, J.,
       Wu, G. D., Collman R. G., Bushman, F. D. & Hongzhe L. Associating
       microbiome composition with environmental covariates using generalized
       UniFrac distances. Bioinformatics 28(16), 2106–2113 (2012).
    .. [2] Chang, Q., Luan, Y. & Sun, F. Variance adjusted weighted UniFrac: a
       powerful beta diversity measure for comparing communities based on
       phylogeny. BMC Bioinformatics 12:118 (2011).
    """
    if alpha == 1.0:
        warn("alpha of 1.0 is weighted-normalized UniFrac. "
             "Weighted-normalized is being used instead as it is more "
             "optimized.",
             Warning)
        return _call_ssu_to_file(table, phylogeny, out_filename,
                                 'weighted_normalized_fp32',
                                 variance_adjusted, alpha,
                                 bypass_tips, n_substeps,
                                 format, pcoa_dims, buf_dirname)
    else:
        return _call_ssu_to_file(table, phylogeny, out_filename,
                                 'generalized_fp32',
                                 variance_adjusted, alpha,
                                 bypass_tips, n_substeps,
                                 format, pcoa_dims, buf_dirname)

#
# Functions that read Unifrac from hdf5 files
#


def h5unifrac(h5file: str) -> skbio.DistanceMatrix:
    """Read UniFrac from a hdf5 file

    Parameters
    ----------
    h5file : str
        A filepath to a hdf5 file.

    Returns
    -------
    skbio.DistanceMatrix
        The distance matrix.

    Raises
    ------
    OSError
        If the hdf5 file is not found
    KeyError
        If the hdf5 does not have the necessary fields

    References
    ----------
    .. [1] Lozupone, C. & Knight, R. UniFrac: a new phylogenetic method for
       comparing microbial communities. Appl. Environ. Microbiol. 71, 8228-8235
       (2005).
    .. [2] Chang, Q., Luan, Y. & Sun, F. Variance adjusted weighted UniFrac: a
       powerful beta diversity measure for comparing communities based on
       phylogeny. BMC Bioinformatics 12:118 (2011).
    """

    with h5py.File(h5file, "r") as f_u:
        dm = skbio.DistanceMatrix(
               f_u['matrix'][:, :],
               [c.decode('ascii') for c in f_u['order'][:]])

    return dm


def h5pcoa(h5file: str) -> skbio.OrdinationResults:
    """Read PCoA from a hdf5 file

    Parameters
    ----------
    h5file : str
        A filepath to a hdf5 file.

    Returns
    -------
    skbio.OrdinationResults
        The PCoA of the distance matrix

    Raises
    ------
    OSError
        If the hdf5 file is not found
    KeyError
        If the hdf5 does not have the necessary fields

    References
    ----------
    .. [1] Lozupone, C. & Knight, R. UniFrac: a new phylogenetic method for
       comparing microbial communities. Appl. Environ. Microbiol. 71, 8228-8235
       (2005).
    .. [2] Chang, Q., Luan, Y. & Sun, F. Variance adjusted weighted UniFrac: a
       powerful beta diversity measure for comparing communities based on
       phylogeny. BMC Bioinformatics 12:118 (2011).
    """

    with h5py.File(h5file, "r") as f_u:
        pcoa_method = f_u['pcoa_method'][0].decode('ascii')
        if 'FSVD' == pcoa_method:
            long_method_name = "Approximate Principal Coordinate Analysis" + \
                               " using FSVD"
        else:
            long_method_name = "Possibly Approximate Principal " + \
                               "Coordinate Analysis " + \
                               "using " + pcoa_method
        axis_labels = ["PC%d" % i for i in
                       range(1, len(f_u['pcoa_eigvals'][:]) + 1)]

        pc = skbio.OrdinationResults(
              short_method_name="PCoA",
              long_method_name=long_method_name,
              eigvals=pd.Series(f_u['pcoa_eigvals'][:], index=axis_labels),
              samples=pd.DataFrame(f_u['pcoa_samples'][:, :],
                                   index=[c.decode('ascii')
                                          for c in f_u['order'][:]],
                                   columns=axis_labels),
              proportion_explained=pd.Series(
                                     f_u['pcoa_proportion_explained'][:],
                                     index=axis_labels))

    return pc

def h5permanova(h5file: str) -> pd.Series:
    """Read first PERMANOVA statistical test from a hdf5 file

    Permutational Multivariate Analysis of Variance (PERMANOVA) is a
    non-parametric method that tests whether two or more groups of objects
    (e.g., samples) are significantly different based on a categorical factor.
    It is conceptually similar to ANOVA except that it operates on a distance
    matrix, which allows for multivariate analysis. PERMANOVA computes a
    pseudo-F statistic.

    Statistical significance is assessed via a permutation test. The assignment
    of objects to groups (`grouping`) is randomly permuted a number of times
    (controlled via `permutations`). A pseudo-F statistic is computed for each
    permutation and the p-value is the proportion of permuted pseudo-F
    statisics that are equal to or greater than the original (unpermuted)
    pseudo-F statistic.

    Parameters
    ----------
    h5file : str
        A filepath to a hdf5 file.

    Returns
    -------
    pandas.Series
        Results of the statistical test, including ``test statistic`` and
        ``p-value``.

    Raises
    ------
    OSError
        If the hdf5 file is not found
    KeyError
        If the hdf5 does not have the necessary fields

    References
    ----------
    .. [1] Anderson, Marti J. "A new method for non-parametric multivariate
       analysis of variance." Austral Ecology 26.1 (2001): 32-46.
    .. [2] http://cran.r-project.org/web/packages/vegan/index.html
    """

    found = False
    with h5py.File(h5file, "r") as f_u:
        methods = f_u['stat_methods'][:]
        test_names = f_u['stat_test_names'][:]
        values = f_u['stat_values'][:]
        pvalues = f_u['stat_pvalues'][:]
        n_permutations = f_u['stat_n_permutations'][:]
        num_groups = f_u['stat_n_groups'][:]
        
        sample_size = len(f_u['order'][:])

        n_stats = len(methods)

        for i in range(n_stats):
          if (methods[i]==b'PERMANOVA') and (test_names[i]==b'pseudo-F'):
            found = True
            pmn = _build_stat('PERMANOVA', 'pseudo-F', sample_size, num_groups[i],
                              values[i], pvalues[i], n_permutations[i])
            break

    if (not found):
      raise KeyError("Not found")

    return pmn
