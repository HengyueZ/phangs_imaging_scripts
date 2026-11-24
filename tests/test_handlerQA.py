import importlib.util
import os

import numpy as np
import pytest

# Load the key writer directly, since importing the phangsPipelineTests package
# pulls in the full (slow, side-effectful) legacy test suite
_spec = importlib.util.spec_from_file_location(
    "minimal_key_writer",
    os.path.join(os.path.dirname(__file__), "..", "phangsPipelineTests", "minimal_key_writer.py"),
)
_mkw = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mkw)
MinimalKeyWriter = _mkw.MinimalKeyWriter

_TARGET = "testgal"
_CONFIG = "C1"
_PRODUCT = "co21"


def _write_keys(tmp_path, qa_root=None):
    """Write a minimal key set, optionally with a qa_root, and return the master key."""

    writer = MinimalKeyWriter(
        key_dir=tmp_path / "keys",
        data_dir=tmp_path / "data",
        ms_root=tmp_path / "uvdata",
    )
    master_key = writer.write_all(
        target=_TARGET,
        config=_CONFIG,
        product=_PRODUCT,
        ms_filename="missing.ms",
        restfreq_GHz=230.538,
        ra="12h00m00.0s",
        dec="-30d00m00.0s",
    )

    if qa_root is not None:
        with open(master_key, "a") as f:
            f.write(f"qa_root             {qa_root}/\n")

    return master_key


@pytest.fixture
def key_handler(tmp_path):
    """KeyHandler with qa_root set."""

    from phangsPipeline import handlerKeys as kh

    master_key = _write_keys(tmp_path, qa_root=tmp_path / "data" / "qa")

    cwd = os.getcwd()
    yield kh.KeyHandler(master_key=master_key)
    os.chdir(cwd)


@pytest.fixture
def key_handler_no_qa(tmp_path):
    """KeyHandler for a key set without qa_root, as for existing users."""

    from phangsPipeline import handlerKeys as kh

    master_key = _write_keys(tmp_path, qa_root=None)

    cwd = os.getcwd()
    yield kh.KeyHandler(master_key=master_key)
    os.chdir(cwd)


def _qa_handler(key_handler):
    """QAHandler selecting the single target, config and product."""

    from phangsPipeline.handlerQA import QAHandler

    qa_handler = QAHandler(key_handler=key_handler)
    qa_handler.set_targets(only=[_TARGET])
    qa_handler.set_interf_configs(only=[_CONFIG])
    qa_handler.set_line_products(only=[_PRODUCT])
    qa_handler.set_no_cont_products(True)

    return qa_handler


def test_key_handler_reads_qa_root(key_handler, tmp_path):
    """qa_root is read from the master key and gives a per-target directory."""

    qa_dir = key_handler.get_qa_dir_for_target(target=_TARGET)

    assert os.path.abspath(qa_dir) == str(tmp_path / "data" / "qa" / _TARGET)


def test_key_handler_without_qa_root(key_handler_no_qa):
    """A key set without qa_root still loads, and has no qa directory."""

    assert key_handler_no_qa._qa_root == ""
    assert key_handler_no_qa.get_qa_dir_for_target(target=_TARGET) is None


def test_make_missing_directories_qa(key_handler, tmp_path):
    """make_missing_directories(qa=True) creates the per-target qa directory."""

    key_handler.make_missing_directories(qa=True)

    assert os.path.isdir(tmp_path / "data" / "qa" / _TARGET)


def test_fname_dict_tclean(key_handler):
    """tclean imaging file names follow export_imaging_to_fits."""

    fname_dict = _qa_handler(key_handler)._fname_dict(
        target=_TARGET, config=_CONFIG, product=_PRODUCT, imaging_method="tclean")

    assert fname_dict["imaging_cube"] == "testgal_C1_co21.fits"
    assert fname_dict["imaging_residual"] == "testgal_C1_co21_residual.fits"
    assert fname_dict["imaging_pb"] == "testgal_C1_co21_pb.fits"
    assert fname_dict["imaging_mask"] == "testgal_C1_co21_mask.fits"
    assert fname_dict["postprocess_cube"] == "testgal_C1_co21_pbcorr_trimmed_k.fits"
    assert fname_dict["postprocess_pb"] == "testgal_C1_co21_trimmed_pb.fits"
    assert fname_dict["derived_cube"] == "testgal_C1_co21.fits"
    assert fname_dict["derived_noise"] == "testgal_C1_co21_noise.fits"
    assert fname_dict["derived_strictmask"] == "testgal_C1_co21_strictmask.fits"
    assert fname_dict["derived_broadmask"] == "testgal_C1_co21_broadmask.fits"


def test_fname_dict_sdintimaging(key_handler):
    """sdintimaging imaging file names use the _joint_cube names (issue #3)."""

    fname_dict = _qa_handler(key_handler)._fname_dict(
        target=_TARGET, config=_CONFIG, product=_PRODUCT, imaging_method="sdintimaging")

    assert fname_dict["imaging_cube"] == "testgal_C1_co21_joint_cube.fits"
    assert fname_dict["imaging_residual"] == "testgal_C1_co21_joint_cube_residual.fits"
    assert fname_dict["imaging_pb"] == "testgal_C1_co21_joint_cube_pb.fits"
    assert fname_dict["imaging_mask"] == "testgal_C1_co21_joint_cube_mask.fits"

    # Postprocessed and derived names do not depend on the imaging method
    assert fname_dict["postprocess_cube"] == "testgal_C1_co21_pbcorr_trimmed_k.fits"
    assert fname_dict["derived_cube"] == "testgal_C1_co21.fits"


def test_loop_qa_missing_inputs(key_handler):
    """With no products on disk, every stage is recorded as skipped and nothing raises."""

    results = _qa_handler(key_handler).loop_qa(do_all=True)

    assert [r["stage"] for r in results] == ["imaging", "postprocess", "derived"]
    for r in results:
        assert r["status"] == "skipped"
        assert r["reason"].startswith("missing input")


def _write_test_cube(filename):
    """Write a small 3D cube (3 channels) with a NaN pixel and an all-NaN channel."""

    from astropy.io import fits

    data = np.arange(3 * 4 * 5, dtype=np.float32).reshape(3, 4, 5)
    data[0, 0, 0] = np.nan
    data[2] = np.nan
    fits.PrimaryHDU(data).writeto(filename, overwrite=True)

    return data


def test_loop_qa_found_input(key_handler):
    """With the main cube present, the checks run and write to the qa directory."""

    pytest.importorskip("matplotlib")

    imaging_dir = key_handler.get_imaging_dir_for_target(target=_TARGET)
    os.makedirs(imaging_dir, exist_ok=True)
    _write_test_cube(os.path.join(imaging_dir, "testgal_C1_co21.fits"))

    results = _qa_handler(key_handler).loop_qa(do_imaging=True)

    assert [(r["check"], r["status"]) for r in results] == [("cube_statistics", "done")]

    outdir = os.path.join(key_handler.get_qa_dir_for_target(target=_TARGET),
                          "imaging", "testgal_C1_co21")
    assert os.path.isfile(os.path.join(outdir, "cube_statistics.png"))
    with np.load(os.path.join(outdir, "cube_statistics.npz")) as npz:
        assert sorted(npz.files) == ["channels", "max", "mean", "median", "min", "std"]


def test_loop_qa_unreadable_input(key_handler):
    """An input file that cannot be read is recorded as failed, not raised."""

    postprocess_dir = key_handler.get_postprocess_dir_for_target(target=_TARGET)
    os.makedirs(postprocess_dir, exist_ok=True)
    open(os.path.join(postprocess_dir, "testgal_C1_co21_pbcorr_trimmed_k.fits"), "w").close()

    results = _qa_handler(key_handler).loop_qa(do_postprocess=True)

    assert [(r["check"], r["status"]) for r in results] == [("cube_statistics", "failed")]


def test_plot_cube_statistics_postprocess(tmp_path):
    """Per-channel stats match numpy on the finite pixels; postprocess saves 4 arrays."""

    pytest.importorskip("matplotlib")
    from phangsPipeline import utilsQAModulePlots

    infile = str(tmp_path / "cube.fits")
    data = _write_test_cube(infile)
    outfile_root = str(tmp_path / "qa" / "cube_statistics")

    png_file = utilsQAModulePlots.plot_cube_statistics(
        infile=infile, outfile_root=outfile_root, stage="postprocess")

    assert png_file == outfile_root + ".png"
    with np.load(outfile_root + ".npz") as npz:
        assert sorted(npz.files) == ["channels", "max", "mean", "std"]
        np.testing.assert_array_equal(npz["channels"], [0, 1, 2])
        plane = data[0][np.isfinite(data[0])]
        assert npz["mean"][0] == float(np.nanmean(plane))
        assert npz["std"][1] == float(np.nanstd(data[1]))
        # All-NaN channel gives NaN, not an error
        assert np.isnan(npz["max"][2])

    # Existing output is kept unless overwrite is set
    mtime = os.path.getmtime(outfile_root + ".npz")
    utilsQAModulePlots.plot_cube_statistics(
        infile=infile, outfile_root=outfile_root, stage="postprocess")
    assert os.path.getmtime(outfile_root + ".npz") == mtime


def test_plot_cube_statistics_rejects_4d(tmp_path):
    """A cube that is not 3D raises, so the handler records the check as failed."""

    from astropy.io import fits
    from phangsPipeline import utilsQAModulePlots

    infile = str(tmp_path / "cube4d.fits")
    fits.PrimaryHDU(np.zeros((1, 2, 3, 3), dtype=np.float32)).writeto(infile)

    with pytest.raises(ValueError):
        utilsQAModulePlots.compute_cube_statistics(infile=infile)


def test_loop_qa_without_qa_root(key_handler_no_qa):
    """Without qa_root, loop_qa reports an error and returns, rather than raising."""

    assert _qa_handler(key_handler_no_qa).loop_qa(do_all=True) is None


def test_run_qa_check_failure_does_not_raise(key_handler):
    """A failing check is recorded as failed, and the next check still runs."""

    def _failing_check():
        raise ValueError("broken")

    def _working_check():
        return "plot.png"

    qa_handler = _qa_handler(key_handler)
    qa_handler._run_qa_check(stage="imaging", target=_TARGET, config=_CONFIG,
                             product=_PRODUCT, check="failing", function=_failing_check)
    qa_handler._run_qa_check(stage="imaging", target=_TARGET, config=_CONFIG,
                             product=_PRODUCT, check="working", function=_working_check)

    results = qa_handler.get_qa_results()
    assert [r["status"] for r in results] == ["failed", "done"]


def test_save_qa_plot(tmp_path):
    """save_qa_plot writes the PNG and the plotted arrays together."""

    matplotlib = pytest.importorskip("matplotlib")
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from phangsPipeline import utilsQA

    channels = np.arange(5)
    rms = np.array([1.0, 2.0, np.nan, 4.0, 5.0])

    fig, ax = plt.subplots()
    ax.plot(channels, rms)

    outfile_root = str(tmp_path / "qa" / "cube_statistics")
    assert utilsQA.save_qa_plot(fig=fig, outfile_root=outfile_root,
                                arrays={"channels": channels, "rms": rms})

    assert os.path.isfile(outfile_root + ".png")
    saved = np.load(outfile_root + ".npz")
    assert np.array_equal(saved["channels"], channels)
    assert np.array_equal(saved["rms"], rms, equal_nan=True)

    # Existing output is not overwritten by default
    fig, ax = plt.subplots()
    assert not utilsQA.save_qa_plot(fig=fig, outfile_root=outfile_root,
                                    arrays={"channels": channels})
