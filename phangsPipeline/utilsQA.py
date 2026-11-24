"""utilsQA

Shared utility functions for the quality assessment (QA) handler
(handlerQA.QAHandler) and the QA plot modules.

Every QA plot is saved together with the arrays that were plotted, so
that the output can be compared numerically (e.g., against the
original QA package). The plot goes to {outfile_root}.png and the
arrays to {outfile_root}.npz.

The QA plots are ported from the PHANGS-ALMA QA pipeline
(phangs_alma_qa_pipeline) written by Daizhong Liu, which includes
diagnostics derived from IDL code by Annie Hughes.

This module is pure Python and does not require CASA.

Example:
    from phangsPipeline import utilsQA

    fig, ax = plt.subplots()
    ax.plot(channels, rms)
    utilsQA.save_qa_plot(
        fig=fig, outfile_root='/path/to/qa/cube_statistics',
        arrays={'channels': channels, 'rms': rms})
"""

import logging
import os

import numpy as np

logger = logging.getLogger(__name__)

# Plot resolution and matplotlib settings of the original package
# (COMMON_DPI and setup_matplotlib in Daizhong Liu's
# modules/*/*_plots.py). The original sets these globally; here they
# are applied with matplotlib.rc_context(QA_RCPARAMS) while each plot
# is made, so that the rest of the pipeline is not affected.

QA_DPI = 200

QA_RCPARAMS = {
    'axes.labelsize': '12',
    'axes.grid': True,
    'axes.formatter.useoffset': False,
    'xtick.direction': 'in',
    'ytick.direction': 'in',
    'xtick.minor.visible': True,
    'ytick.minor.visible': True,
    'xtick.labelsize': '8',
    'ytick.labelsize': '8',
    'xtick.top': True,
    'ytick.right': True,
    'grid.color': 'b0b0b0',
    'grid.linestyle': '--',
    'grid.linewidth': 0.25,
    'grid.alpha': 0.8,
    'legend.fontsize': '9',
    'legend.borderaxespad': 0.2,
}


##############################################################
# Output file names
##############################################################

def get_qa_plot_filenames(outfile_root=None):
    """
    Return the (png, npz) file names for a QA plot, given the root
    of the output file name, i.e. the full path without extension.
    """

    if outfile_root is None:
        logger.error("Need an output file root.")
        return (None, None)

    png_file = outfile_root + '.png'
    npz_file = outfile_root + '.npz'

    return (png_file, npz_file)


##############################################################
# Save plots together with the plotted arrays
##############################################################

def save_qa_plot(fig=None, outfile_root=None, arrays=None,
                 dpi=QA_DPI, overwrite=False):
    """
    Save a QA plot to {outfile_root}.png and the plotted arrays to
    {outfile_root}.npz. Closes the figure afterwards.

    Args:
        fig (matplotlib.figure.Figure): The figure to save.
        outfile_root (str): Full path of the output files, without
            extension.
        arrays (dict): Name -> array of everything that was plotted.
            Saved with numpy.savez, so each value must be convertible
            to a numpy array.
        dpi (int, optional): Resolution of the PNG. Defaults to
            QA_DPI (200, as in the original package).
        overwrite (bool, optional): If False and both output files
            already exist, do nothing. Defaults to False.

    Returns:
        bool: True if the files were written, False otherwise.
    """

    if fig is None:
        logger.error("Need a figure.")
        return (False)

    if arrays is None or len(arrays) == 0:
        logger.error("Need the plotted arrays. Every QA plot must save them.")
        return (False)

    png_file, npz_file = get_qa_plot_filenames(outfile_root=outfile_root)
    if png_file is None:
        return (False)

    if os.path.isfile(png_file) and os.path.isfile(npz_file) and not overwrite:
        logger.info("Found existing QA plot, not overwriting: " + png_file)
        return (False)

    outdir = os.path.dirname(png_file)
    if outdir != '' and not os.path.isdir(outdir):
        os.makedirs(outdir)

    fig.savefig(png_file, dpi=dpi, bbox_inches='tight')
    np.savez(npz_file, **arrays)

    # Close the figure to free memory when looping over many cubes

    import matplotlib.pyplot as plt
    plt.close(fig)

    logger.info("Wrote QA plot: " + png_file)
    logger.info("Wrote QA plot arrays: " + npz_file)

    return (True)
