"""utilsQAModulePlots

QA plots of a single cube, run by the QA handler (handlerQA.QAHandler)
on the imaging and postprocessed products.

These are ported from the "module" plots of the PHANGS-ALMA QA
pipeline (phangs_alma_qa_pipeline) written by Daizhong Liu:
    modules/imaging/imaging_plots.py
    modules/postprocess/postprocess_plots.py
The imaging and postprocess versions of each plot differ only in which
curves are drawn and in the unit labels, so each is ported here as one
function with a stage argument.

Every plot is saved together with the plotted arrays (see
utilsQA.save_qa_plot), so that the output can be compared numerically
with the original package.

This module is pure Python and does not require CASA.

Example:
    from phangsPipeline import utilsQAModulePlots as qamp

    qamp.plot_cube_statistics(
        infile='ngc1097_12m+7m+tp_co21_pbcorr_trimmed_k.fits',
        outfile_root='/path/to/qa/cube_statistics',
        stage='postprocess')
"""

import logging
import os
import warnings

import numpy as np
from astropy.io import fits

from . import utilsQA

logger = logging.getLogger(__name__)

# Stages handled by the plots in this module

QA_MODULE_STAGES = ['imaging', 'postprocess']


##############################################################
# Statistics
##############################################################

def compute_plane_statistics(data=None):
    """
    Compute basic statistics of one channel (or any array), using only
    the finite pixels.

    Ported from compute_statistics in Daizhong Liu's
    modules/{imaging,postprocess}/{imaging,postprocess}_utils.py,
    keeping only the fields used by the plots. The numpy calls are
    the same so that the numbers match exactly.

    Args:
        data (numpy.ndarray): Input array.

    Returns:
        dict: n_valid, mean, median, std, min, max. All NaN (and
        n_valid = 0) if there are no finite pixels.
    """

    if data is None:
        logger.error("Need data.")
        return (None)

    valid_data = data[np.isfinite(data)]

    if len(valid_data) == 0:
        stats = {
            'n_valid': 0,
            'mean': np.nan,
            'median': np.nan,
            'std': np.nan,
            'min': np.nan,
            'max': np.nan,
        }
        return (stats)

    # Note that "std" is the standard deviation about the mean. It is
    # labelled "RMS" in the original plots, and no mask is applied, so
    # it includes the line emission (QA port note, issue #5).

    stats = {
        'n_valid': len(valid_data),
        'mean': float(np.nanmean(valid_data)),
        'median': float(np.nanmedian(valid_data)),
        'std': float(np.nanstd(valid_data)),
        'min': float(np.nanmin(valid_data)),
        'max': float(np.nanmax(valid_data)),
    }

    return (stats)


def compute_cube_statistics(infile=None):
    """
    Compute the statistics of each channel of a 3D FITS cube.

    As in the original package, the data are read from the primary HDU,
    the number of channels is NAXIS3 and the channel index starts at 0.
    The cube is memory mapped and read one channel at a time.

    Args:
        infile (str): Name of the FITS cube.

    Returns:
        dict: channels, mean, median, std, min, max, each an array of
        length NAXIS3.
    """

    if infile is None:
        logger.error("Need an input file.")
        return (None)

    if not os.path.isfile(infile):
        logger.error("Input file not found: " + infile)
        return (None)

    stat_names = ['mean', 'median', 'std', 'min', 'max']

    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        with fits.open(infile, memmap=True) as hdulist:

            header = hdulist[0].header
            data = hdulist[0].data

            # The pipeline writes 3D cubes (exportfits with dropstokes
            # and dropdeg). The original code indexes data[ichan] for
            # ichan < NAXIS3, which only works for a 3D cube.

            if data is None or data.ndim != 3:
                raise ValueError("Expected a 3D cube in the primary HDU of " + infile)

            nchan = header.get('NAXIS3', 0)
            if nchan == 0:
                raise ValueError("No channels in cube " + infile)

            stats_dict = {}
            for this_name in stat_names:
                stats_dict[this_name] = []

            for ichan in range(nchan):
                this_plane = np.array(data[ichan])
                this_stats = compute_plane_statistics(this_plane)
                for this_name in stat_names:
                    stats_dict[this_name].append(this_stats[this_name])

    stats_dict['channels'] = np.arange(nchan)
    for this_name in stat_names:
        stats_dict[this_name] = np.array(stats_dict[this_name])

    return (stats_dict)


##############################################################
# Plots
##############################################################

def plot_cube_statistics(
        infile=None,
        outfile_root=None,
        stage=None,
        dpi=utilsQA.QA_DPI,
        overwrite=False,
):
    """
    Plot the mean, RMS and maximum of each channel of a cube against
    channel index, in a 2x2 figure.

    Ported from plot_cube_statistics in Daizhong Liu's
    modules/imaging/imaging_plots.py (stage = 'imaging') and
    modules/postprocess/postprocess_plots.py (stage = 'postprocess').
    The imaging version also plots the median and the minimum.

    Notes kept from the original (QA port, issue #5; not changed):
        - "RMS" is the standard deviation about the mean.
        - The unit labels are fixed per stage (Jy/beam for imaging, K
          for postprocess), not read from BUNIT.
        - The x-axis is channel index (from 0), not velocity.
        - No mask is applied, so in channels with line emission the
          "RMS" is not a noise estimate.

    Args:
        infile (str): Name of the FITS cube.
        outfile_root (str): Full path of the output files, without
            extension (e.g. {outdir}/cube_statistics).
        stage (str): 'imaging' or 'postprocess'.
        dpi (int, optional): Resolution of the PNG. Defaults to
            utilsQA.QA_DPI (200, as in the original package).
        overwrite (bool, optional): If False and the outputs already
            exist, do nothing. Defaults to False.

    Returns:
        str: Name of the PNG file, or None if nothing was made.

    Output files:
        {outfile_root}.png
        {outfile_root}.npz with channels, mean, std, max, and for the
        imaging stage also median and min.
    """

    if stage not in QA_MODULE_STAGES:
        logger.error("stage %s not recognised" % stage)
        return (None)

    png_file, npz_file = utilsQA.get_qa_plot_filenames(outfile_root=outfile_root)
    if png_file is None:
        return (None)

    # Check for existing output before reading the cube, which is slow
    # for large cubes.

    if os.path.isfile(png_file) and os.path.isfile(npz_file) and not overwrite:
        logger.info("Found existing statistics plot: " + png_file)
        return (png_file)

    stats_dict = compute_cube_statistics(infile=infile)
    if stats_dict is None:
        return (None)

    channels = stats_dict['channels']
    means = stats_dict['mean']
    medians = stats_dict['median']
    stds = stats_dict['std']
    maxs = stats_dict['max']
    mins = stats_dict['min']

    import matplotlib
    import matplotlib.pyplot as plt

    # Use the matplotlib settings of the original package for this
    # plot only

    with matplotlib.rc_context(utilsQA.QA_RCPARAMS):

        fig, axes = plt.subplots(2, 2, figsize=(12, 10))

        if stage == 'imaging':

            axes[0, 0].plot(channels, means, 'b-', label='Mean', linewidth=1)
            axes[0, 0].plot(channels, medians, 'g-', label='Median', linewidth=1)
            axes[0, 0].set_xlabel('Channel')
            axes[0, 0].set_ylabel('Flux (Jy/beam)')
            axes[0, 0].set_title('Mean/Median per Channel')
            axes[0, 0].legend()
            axes[0, 0].grid(True, alpha=0.3)

            axes[0, 1].plot(channels, stds, 'r-', label='Std Dev', linewidth=1)
            axes[0, 1].set_xlabel('Channel')
            axes[0, 1].set_ylabel('RMS (Jy/beam)')
            axes[0, 1].set_title('RMS per Channel')
            axes[0, 1].legend()
            axes[0, 1].grid(True, alpha=0.3)

            axes[1, 0].plot(channels, maxs, 'b-', label='Max', linewidth=1)
            axes[1, 0].plot(channels, mins, 'r-', label='Min', linewidth=1)
            axes[1, 0].set_xlabel('Channel')
            axes[1, 0].set_ylabel('Flux (Jy/beam)')
            axes[1, 0].set_title('Min/Max per Channel')
            axes[1, 0].legend()
            axes[1, 0].grid(True, alpha=0.3)

            axes[1, 1].semilogy(channels, np.abs(maxs), 'b-', label='|Max|', linewidth=1)
            axes[1, 1].semilogy(channels, stds, 'r-', label='RMS', linewidth=1)
            axes[1, 1].set_xlabel('Channel')
            axes[1, 1].set_ylabel('Flux (Jy/beam)')
            axes[1, 1].set_title('Peak/RMS per Channel (log)')
            axes[1, 1].legend()
            axes[1, 1].grid(True, alpha=0.3)

            arrays = {
                'channels': channels,
                'mean': means,
                'median': medians,
                'std': stds,
                'min': mins,
                'max': maxs,
            }

        if stage == 'postprocess':

            axes[0, 0].plot(channels, means, 'b-', linewidth=1)
            axes[0, 0].set_xlabel('Channel')
            axes[0, 0].set_ylabel('Mean (K)')
            axes[0, 0].set_title('Mean per Channel')
            axes[0, 0].grid(True, alpha=0.3)

            axes[0, 1].plot(channels, stds, 'r-', linewidth=1)
            axes[0, 1].set_xlabel('Channel')
            axes[0, 1].set_ylabel('RMS (K)')
            axes[0, 1].set_title('RMS per Channel')
            axes[0, 1].grid(True, alpha=0.3)

            axes[1, 0].plot(channels, maxs, 'b-', linewidth=1)
            axes[1, 0].set_xlabel('Channel')
            axes[1, 0].set_ylabel('Max (K)')
            axes[1, 0].set_title('Max per Channel')
            axes[1, 0].grid(True, alpha=0.3)

            axes[1, 1].semilogy(channels, np.abs(maxs), 'b-', label='|Max|', linewidth=1)
            axes[1, 1].semilogy(channels, stds, 'r-', label='RMS', linewidth=1)
            axes[1, 1].set_xlabel('Channel')
            axes[1, 1].set_ylabel('(K)')
            axes[1, 1].set_title('Peak/RMS (log)')
            axes[1, 1].legend()
            axes[1, 1].grid(True, alpha=0.3)

            arrays = {
                'channels': channels,
                'mean': means,
                'std': stds,
                'max': maxs,
            }

        fig.tight_layout()

        utilsQA.save_qa_plot(
            fig=fig, outfile_root=outfile_root, arrays=arrays,
            dpi=dpi, overwrite=True)

    return (png_file)
