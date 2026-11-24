"""QAHandler

This module runs the quality assessment (QA) of the pipeline
products. It makes diagnostic plots from the imaging, postprocessed,
and derived products of each target, product and configuration, and
writes them to a subdirectory of qa_root (set in the master key).

The QA handler only reads existing products and does not change
them. It is run after the other pipeline stages, e.g. by setting
do_qa = True in the pipeline run script.

The QA plots are ported from the PHANGS-ALMA QA pipeline
(phangs_alma_qa_pipeline) written by Daizhong Liu, which includes
diagnostics derived from IDL code by Annie Hughes. Input file names
are built from the key files here, rather than found by matching
file name patterns as in the original package.

Output file names:
    {qa_root}/{target}/{stage}/{target}_{config}_{product}/{plot}.png
    {qa_root}/{target}/{stage}/{target}_{config}_{product}/{plot}.npz

where stage is one of 'imaging', 'postprocess' or 'derived', and the
.npz file holds the arrays that were plotted.

This module is pure Python and does not require CASA.

Example:
    $ ipython
    from phangsPipeline import handlerKeys as kh
    from phangsPipeline import handlerQA as qh
    this_kh = kh.KeyHandler(master_key = 'phangsalma_keys/master_key.txt')
    this_qh = qh.QAHandler(key_handler = this_kh)
    this_qh.set_targets(only = ['ngc1097'])
    this_qh.set_interf_configs(only = ['12m+7m'])
    this_qh.set_feather_configs(only = ['12m+7m+tp'])
    this_qh.set_line_products(only = ['co21'])
    this_qh.set_no_cont_products(no_cont = True)
    this_qh.loop_qa(do_all = True, imaging_method = 'tclean')

"""

import logging
import os

from . import handlerTemplate
from . import utilsFilenames
from . import utilsQAModulePlots

logger = logging.getLogger(__name__)


class QAHandler(handlerTemplate.HandlerTemplate):


    ############
    # __init__ #
    ############

    def __init__(
            self,
            key_handler=None,
            dry_run=False,
    ):
        """
        Class to make quality assessment (QA) plots from the imaging,
        postprocessed and derived products.
        """

        # inherit template class
        handlerTemplate.HandlerTemplate.__init__(self,
                                                 key_handler=key_handler,
                                                 dry_run=dry_run)

        # Record of what was run, skipped or failed
        self._qa_results = []

    ########################
    # Main processing loop #
    ########################

    def loop_qa(
            self,
            do_all: bool = False,
            do_imaging: bool = False,
            do_postprocess: bool = False,
            do_derived: bool = False,
            imaging_method: str = 'tclean',
            make_directories: bool = True,
            overwrite: bool = False,
    ):
        """
        Loops over the full set of targets, spectral products and
        configurations to make the QA plots. Toggle the pipeline stages
        to check using the do_XXX booleans. Stages are run in the
        order imaging, postprocess, derived.

        Args:
            do_all (bool, optional): If True, will run the QA for all
                stages. Defaults to False.
            do_imaging (bool, optional): If True, will run the QA on the
                imaging products. Defaults to False.
            do_postprocess (bool, optional): If True, will run the QA
                on the postprocessed products. Defaults to False.
            do_derived (bool, optional): If True, will run the QA on the
                derived products. Defaults to False.
            imaging_method (str, optional): Imaging method used to make
                the cubes, either 'tclean' or 'sdintimaging'. This sets
                the imaging file names and should match the value used
                in the imaging and postprocessing. Defaults to 'tclean'.
            make_directories (bool, optional): If True, will make the
                directories if they don't already exist. Defaults to True.
            overwrite (bool, optional): If True, will overwrite existing
                QA plots. Defaults to False.
        """

        if do_all:
            do_imaging = True
            do_postprocess = True
            do_derived = True

        # Error checking

        if len(self.get_targets()) == 0:
            logger.error("Need a target list.")
            return (None)

        if len(self.get_all_products()) == 0:
            logger.error("Need a products list.")
            return (None)

        if self._kh._qa_root is None or self._kh._qa_root == '':
            logger.error("The qa root directory has not been set.")
            logger.error("Please set qa_root in your master_key file to run the QA.")
            return (None)

        if imaging_method not in ['tclean', 'sdintimaging']:
            logger.error("imaging_method %s not recognised" % imaging_method)
            return (None)

        # If requested, make the directories

        if make_directories and not self._dry_run:
            self._kh.make_missing_directories(qa=True)

        # QA of the imaging products. These only exist for the
        # interferometric configurations.

        if do_imaging:

            for this_target, this_product, this_config in \
                    self.looper(do_targets=True, do_products=True, do_configs=True,
                                just_interf=True):

                self.task_qa_imaging(
                    target=this_target, config=this_config, product=this_product,
                    imaging_method=imaging_method, overwrite=overwrite)

        # QA of the postprocessed products.

        if do_postprocess:

            for this_target, this_product, this_config in \
                    self.looper(do_targets=True, do_products=True, do_configs=True):

                self.task_qa_postprocess(
                    target=this_target, config=this_config, product=this_product,
                    overwrite=overwrite)

        # QA of the derived products.

        if do_derived:

            for this_target, this_product, this_config in \
                    self.looper(do_targets=True, do_products=True, do_configs=True):

                self.task_qa_derived(
                    target=this_target, config=this_config, product=this_product,
                    overwrite=overwrite)

        # Report

        self._report_qa_results()

        return (self._qa_results)

    ###########################################
    # Defined file names for various products #
    ###########################################

    def _fname_dict(
            self,
            target=None,
            config=None,
            product=None,
            imaging_method='tclean',
    ):
        """
        Function to define the input file names used in the QA. These
        follow the names written by the imaging, postprocess and
        derived handlers.
        """

        # &%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%
        # Error checking
        # &%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%

        if target is None:
            raise Exception("Need a target.")
        if product is None:
            raise Exception("Need a product.")
        if config is None:
            raise Exception("Need a config.")

        # &%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%
        # Initialize
        # &%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%

        fname_dict = {}

        # Root of the output directory name for this target, config,
        # product combination

        fname_dict['qa_stem'] = utilsFilenames.get_cube_filename(
            target=target, config=config, product=product,
            casa=False).replace('.fits', '')

        # &%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%
        # Imaging products
        # &%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%

        # FITS names written by casaImagingRoutines.export_imaging_to_fits.
        # sdintimaging writes the joint cube as _joint_cube.fits,
        # _joint_cube_residual.fits, etc.

        if imaging_method == 'tclean':
            imaging_ext = ''
        elif imaging_method == 'sdintimaging':
            imaging_ext = 'joint_cube'
        else:
            logger.error('imaging_method %s not recognised' % imaging_method)
            raise Exception('imaging_method %s not recognised' % imaging_method)

        for tag in ['residual', 'pb', 'mask']:
            fname_dict['imaging_' + tag] = utilsFilenames.get_cube_filename(
                target=target, config=config, product=product,
                ext=imaging_ext + '_' + tag,
                casa=False)

        fname_dict['imaging_cube'] = utilsFilenames.get_cube_filename(
            target=target, config=config, product=product,
            ext=imaging_ext,
            casa=False)

        # &%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%
        # Postprocessed products
        # &%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%

        # FITS names written by handlerPostprocess

        fname_dict['postprocess_cube'] = utilsFilenames.get_cube_filename(
            target=target, config=config, product=product,
            ext='pbcorr_trimmed_k',
            casa=False)

        fname_dict['postprocess_pb'] = utilsFilenames.get_cube_filename(
            target=target, config=config, product=product,
            ext='trimmed_pb',
            casa=False)

        # &%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%
        # Derived products
        # &%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%

        # FITS names written by handlerDerived at the native
        # resolution

        fname_dict['derived_cube'] = utilsFilenames.get_cube_filename(
            target=target, config=config, product=product,
            casa=False)

        for tag in ['noise', 'strictmask', 'broadmask']:
            fname_dict['derived_' + tag] = utilsFilenames.get_cube_filename(
                target=target, config=config, product=product,
                ext=tag,
                casa=False)

        # &%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%
        # Return
        # &%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%

        return (fname_dict)

    def _get_qa_outdir(
            self,
            target=None,
            config=None,
            product=None,
            stage=None,
    ):
        """
        Return the QA output directory for a target, config, product
        and pipeline stage:

        {qa_root}/{target}/{stage}/{target}_{config}_{product}/
        """

        qa_dir = self._kh.get_qa_dir_for_target(target=target, changeto=False)
        if qa_dir is None:
            return (None)

        fname_dict = self._fname_dict(target=target, config=config, product=product)

        outdir = os.path.abspath(qa_dir) + '/' + stage + '/' + fname_dict['qa_stem'] + '/'

        return (outdir)

    ######################################
    # Record of what was run and skipped #
    ######################################

    def _record_qa_result(
            self,
            stage=None,
            target=None,
            config=None,
            product=None,
            check=None,
            status=None,
            reason='',
            outfile=None,
    ):
        """
        Append the outcome of one QA check to the results list.
        Status is 'done', 'skipped' or 'failed'.
        """

        result = {
            'stage': stage,
            'target': target,
            'config': config,
            'product': product,
            'check': check,
            'status': status,
            'reason': reason,
            'outfile': outfile,
        }
        self._qa_results.append(result)

        if status == 'done':
            logger.info("QA " + str(check) + ": done " + str(outfile))
        else:
            logger.warning("QA " + str(check) + ": " + str(status) + ": " + str(reason))

        return (None)

    def get_qa_results(self):
        """
        Return the list of QA results.
        """
        return (self._qa_results)

    def _report_qa_results(self):
        """
        Print a short summary of the QA results.
        """

        n_done = len([r for r in self._qa_results if r['status'] == 'done'])
        n_skipped = len([r for r in self._qa_results if r['status'] == 'skipped'])
        n_failed = len([r for r in self._qa_results if r['status'] == 'failed'])

        logger.info("")
        logger.info("&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&")
        logger.info("QA summary: " + str(n_done) + " done, " + str(n_skipped) +
                    " skipped, " + str(n_failed) + " failed.")
        logger.info("&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&")
        logger.info("")

        return (None)

    def _run_qa_check(
            self,
            stage=None,
            target=None,
            config=None,
            product=None,
            check=None,
            function=None,
            function_kwargs=None,
    ):
        """
        Run one QA check, catching any exception so that one failing
        check does not stop the loop. The function is called with the
        keyword arguments in function_kwargs and should return the
        name of the main output file, or None if nothing was made
        (recorded as failed).
        """

        if self._dry_run:
            self._record_qa_result(
                stage=stage, target=target, config=config, product=product,
                check=check, status='skipped', reason='dry run')
            return (None)

        try:
            if function_kwargs is None:
                function_kwargs = {}
            outfile = function(**function_kwargs)
        except Exception as e:
            logger.exception("QA check " + str(check) + " failed.")
            self._record_qa_result(
                stage=stage, target=target, config=config, product=product,
                check=check, status='failed', reason=repr(e))
            return (None)

        if outfile is None:
            self._record_qa_result(
                stage=stage, target=target, config=config, product=product,
                check=check, status='failed', reason='no output made, see log')
            return (None)

        self._record_qa_result(
            stage=stage, target=target, config=config, product=product,
            check=check, status='done', outfile=outfile)

        return (outfile)

    ##############################
    # QA for each pipeline stage #
    ##############################

    def _task_qa_stage(
            self,
            stage=None,
            target=None,
            config=None,
            product=None,
            input_file=None,
            indir=None,
    ):
        """
        Shared start of each stage's QA task: report, check that the
        main input file exists and return the output directory (or
        None if the QA for this stage should be skipped).
        """

        # Report

        logger.info("")
        logger.info("&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&")
        logger.info("Running " + stage + " QA for:")
        logger.info(str(target) + " , " + str(product) + " , " + str(config))
        logger.info("&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&%&")
        logger.info("")

        # Check input file existence

        if indir is None:
            self._record_qa_result(
                stage=stage, target=target, config=config, product=product,
                check='all', status='skipped', reason='no ' + stage + ' directory for target')
            return (None)

        indir = os.path.abspath(indir) + '/'

        if not os.path.isfile(indir + input_file):
            self._record_qa_result(
                stage=stage, target=target, config=config, product=product,
                check='all', status='skipped', reason='missing input ' + indir + input_file)
            return (None)

        logger.info("Input file: " + indir + input_file)

        # Output directory

        outdir = self._get_qa_outdir(
            target=target, config=config, product=product, stage=stage)
        if outdir is None:
            self._record_qa_result(
                stage=stage, target=target, config=config, product=product,
                check='all', status='skipped', reason='no qa directory for target')
            return (None)

        logger.info("Output directory: " + outdir)

        if not self._dry_run:
            if not os.path.isdir(outdir):
                os.makedirs(outdir)

        return (outdir)

    def task_qa_imaging(
            self,
            target=None,
            config=None,
            product=None,
            imaging_method='tclean',
            overwrite=False,
    ):
        """
        Run the QA on the imaging products for one target, config and
        product.
        """

        stage = 'imaging'

        # Generate file names

        indir = self._kh.get_imaging_dir_for_target(target=target, changeto=False)

        fname_dict = self._fname_dict(
            target=target, config=config, product=product,
            imaging_method=imaging_method)

        input_file = fname_dict['imaging_cube']

        outdir = self._task_qa_stage(
            stage=stage, target=target, config=config, product=product,
            input_file=input_file, indir=indir)
        if outdir is None:
            return (None)

        # Run the QA checks. Each ported plot adds a call to
        # self._run_qa_check here.

        # Per-channel statistics (issue #5)

        self._run_qa_check(
            stage=stage, target=target, config=config, product=product,
            check='cube_statistics',
            function=utilsQAModulePlots.plot_cube_statistics,
            function_kwargs={
                'infile': os.path.abspath(indir) + '/' + input_file,
                'outfile_root': outdir + 'cube_statistics',
                'stage': stage,
                'overwrite': overwrite,
            })

        return (None)

    def task_qa_postprocess(
            self,
            target=None,
            config=None,
            product=None,
            overwrite=False,
    ):
        """
        Run the QA on the postprocessed products for one target,
        config and product.
        """

        stage = 'postprocess'

        # Generate file names

        indir = self._kh.get_postprocess_dir_for_target(target=target, changeto=False)

        fname_dict = self._fname_dict(target=target, config=config, product=product)

        input_file = fname_dict['postprocess_cube']

        outdir = self._task_qa_stage(
            stage=stage, target=target, config=config, product=product,
            input_file=input_file, indir=indir)
        if outdir is None:
            return (None)

        # Run the QA checks. Each ported plot adds a call to
        # self._run_qa_check here.

        # Per-channel statistics (issue #5)

        self._run_qa_check(
            stage=stage, target=target, config=config, product=product,
            check='cube_statistics',
            function=utilsQAModulePlots.plot_cube_statistics,
            function_kwargs={
                'infile': os.path.abspath(indir) + '/' + input_file,
                'outfile_root': outdir + 'cube_statistics',
                'stage': stage,
                'overwrite': overwrite,
            })

        return (None)

    def task_qa_derived(
            self,
            target=None,
            config=None,
            product=None,
            overwrite=False,
    ):
        """
        Run the QA on the derived products for one target, config and
        product.
        """

        stage = 'derived'

        # Generate file names

        indir = self._kh.get_derived_dir_for_target(target=target, changeto=False)

        fname_dict = self._fname_dict(target=target, config=config, product=product)

        input_file = fname_dict['derived_cube']

        outdir = self._task_qa_stage(
            stage=stage, target=target, config=config, product=product,
            input_file=input_file, indir=indir)
        if outdir is None:
            return (None)

        # Run the QA checks. Each ported plot adds a call to
        # self._run_qa_check here.

        self._record_qa_result(
            stage=stage, target=target, config=config, product=product,
            check='all', status='skipped', reason='no derived QA checks implemented yet')

        return (None)
