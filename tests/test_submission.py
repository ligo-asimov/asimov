"""Tests of asimov's ability to run pipeline generation tools to produce submission files."""

import hashlib
import unittest
import shutil, os
from configparser import ConfigParser, NoOptionError
import git
import asimov.git
from asimov.olivaw import get_psds_rundir

PSD_LIST = {"L1": "tests/test_data/s000000xx/C01_offline/Prod0/ROQdata/0/BayesWave_PSD_L1/post/clean/glitch_median_PSD_forLI_L1.dat",
            "H1": "tests/test_data/s000000xx/C01_offline/Prod0/ROQdata/0/BayesWave_PSD_H1/post/clean/glitch_median_PSD_forLI_H1.dat",}

@unittest.skip("Deprecated class")
class LALInferenceTests(unittest.TestCase):
    """Test lalinference_pipe related jobs."""

    @classmethod
    def setUpClass(self):
        self.cwd = os.getcwd()
        git.Repo.init(self.cwd+"/tests/test_data/s000000xx/")


    @classmethod
    def tearDownClass(self):
        """Destroy all the products of this test."""
        shutil.rmtree(self.cwd+"/tests/test_data/s000000xx/.git")


    def setUp(self):
        self.repo = repo = asimov.git.EventRepo(self.cwd+"/tests/test_data/s000000xx")
        # self.sample_hashes = {
        #     "lalinference_dag": self._get_hash("test_data/sample_files/lalinference_1248617392-1248617397.dag")
        #     }
        self.repo.build_dag("C01_offline", "Prod0")
        os.chdir(self.cwd)

    def _get_hash(self, filename):
        with open(filename, "r") as handle:
            return hashlib.md5(handle.read().encode()).hexdigest()

    def _get_config_ini(self):
        """Fetch the generated config.ini file."""
        ini = ConfigParser()
        ini.optionxform=str
        ini.read(self.cwd+"/tests/test_data/s000000xx/C01_offline/Prod0/config.ini")
        return ini

    def test_lalinference_dag(self):
        """Check that a DAG is produced."""
        self.assertEqual(os.path.exists(self.cwd+"/tests/test_data/s000000xx/C01_offline/Prod0/lalinference_1248617392-1248617397.dag"), 1)

    def test_gpstime_insertion(self):
        """Check that the GPS time is picked-up from the time file."""
        ini = self._get_config_ini()
        start = float(ini.get("input", "gps-start-time"))
        end = float(ini.get("input", "gps-end-time"))
        with open("tests/test_data/s000000xx/C01_offline/s000000xx_gpsTime.txt", "r") as f:
            event_time = float(f.read())

        assert(start < event_time)
        assert(end > event_time)

    def test_paths(self):
        """Check that the paths are set correctly."""
        ini = self._get_config_ini()
        basedir = ini.get("paths", "basedir")
        self.assertEqual(basedir, self.cwd+"/tests/test_data/s000000xx/C01_offline/Prod0")

    def test_psd_fetch(self):
        """Check that PSDs can be found correctly."""
        from pathlib import Path
        
        for psd in PSD_LIST.values():
            Path(self.cwd+"/"+'/'.join(psd.split('/')[:-1])).mkdir(parents=True)
            with open(f"{self.cwd}/{psd}", "w") as f:
                f.write("")
        
        ini = self._get_config_ini()
        psds_dict = get_psds_rundir(self.cwd+"/tests/test_data/s000000xx/C01_offline/Prod0")
        for det, psd in psds_dict.items():
            self.assertEqual(psd, f"{self.cwd}/{PSD_LIST[det]}")

    def test_psd_insertion(self):
        """Check that PSDs are inserted into the ini file correctly."""
        from pathlib import Path
        for psd in PSD_LIST.values():
            Path(self.cwd+"/"+'/'.join(psd.split('/')[:-1])).mkdir(parents=True)
            Path(self.cwd+"/"+psd).touch()
        ini = self._get_config_ini()
        psds = get_psds_rundir(self.cwd+"/tests/test_data/s000000xx/C01_offline/Prod0")
        
        self.repo.build_dag("C01_offline", "Prod0", psds=psds, clobber_psd=True)
        os.chdir(self.cwd)
        ini = self._get_config_ini()

        for det, psd in psds.items():
            self.assertEqual(ini.get("engine", f"{det}-psd"), f"{self.cwd}/{PSD_LIST[det]}")

        
    def test_webdir(self):
        """Check that the web paths are set correctly."""
        ini = self._get_config_ini()
        self.assertEqual(self.repo.event, "s000000xx")
        webdir = ini.get("paths", "webdir")
        self.assertEqual(webdir,
                         os.path.join(os.path.expanduser("~"), *"public_html/LVC/projects/O3/C01/".split("/"), "s000000xx", "Prod0"))
        
    def test_bayeswave(self):
        """Check that Bayeswave is enabled."""
        ini = self._get_config_ini()
        assert(ini.has_option("condor", "bayeswave"))

    def test_bayeswave_disabled(self):
        """Check that Bayeswave is correctly disabled when PSDs provided."""
        psds = {"L1": "fake.txt", "H1": "fake.txt"}
        self.repo.build_dag("C01_offline", "Prod0", psds=psds, clobber_psd=True)
        os.chdir(self.cwd)
        ini = self._get_config_ini()
        assert(not ini.has_option("condor", "bayeswave"))

    def test_change_user(self):
        """Check that the ini is built for a specified accounting user."""
        self.repo.build_dag("C01_offline", "Prod0", user = "hermann.minkowski")
        os.chdir(self.cwd)
        ini = self._get_config_ini()
        self.assertEqual(ini.get("condor", "accounting_group_user"), "hermann.minkowski")
        
    def test_queue(self):
        """Check that the Queue is correctly set."""
        ini = self._get_config_ini()
        self.assertEqual(ini.get("condor", "queue"), "Priority_PE")

        
    def tearDown(self):
        shutil.rmtree("tests/test_data/s000000xx/C01_offline/Prod0/")
        
