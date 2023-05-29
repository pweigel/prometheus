# -*- coding: utf-8 -*-
# prometheus.py
# Copyright (C) 2022 Christian Haack, Jeffrey Lazar, Stephan Meighen-Berger,
# Interface class to the package

import numpy as np
import awkward as ak
import pyarrow.parquet as pq
import os
import json
from typing import Union
from tqdm import tqdm
from time import time
from jax import random  # noqa: E402

from .utils import (
    config_mims, clean_config,
    UnknownInjectorError, UnknownLeptonPropagatorError,
    UnknownPhotonPropagatorError, NoInjectionError,
    InjectorNotImplementedError, CannotLoadDetectorError
)
from .config import Configuration
from .detector import Detector
from .injection import RegisteredInjectors, INJECTION_CONSTRUCTOR_DICT
from .lepton_propagation import (
    get_lepton_propagagtor,
    RegisteredLeptonPropagators
)
from .photon_propagation import (
    get_photon_propagator,
    RegisteredPhotonPropagators
)

os.environ["XLA_PYTHON_CLIENT_MEM_FRACTION"] = "0.5"

class PpcTmpdirExistsError(Exception):  # TODO: (Philip) This should be a util
    """Raised if PPC tmpdir exists and force not specified"""
    def __init__(self, path):
        self.message = f"{path} exists. Please remove it or specify force in the config"
        super().__init__(self.message)


class Prometheus(object):
    """Class for unifying injection, energy loss calculation, and photon propagation"""
    def __init__(
        self,
        userconfig: Union[None, dict, str] = None,
        detector: Union[None, Detector] = None
    ) -> None:
        """Initializes the Prometheus class

        params
        ______
        userconfig: Configuration dictionary or path to yaml file 
            which specifies configuration
        detector: Detector to be used or path to geo file to load detector file.
            If this is left out, the path from the `userconfig["detector"]["geo file"]`
            be loaded

        raises
        ______
        UnknownInjectorError: If we don't know how to handle the injector the config
            is asking for
        UnknownLeptonPropagatorError: If we don't know how to handle the lepton
            propagator you are asking for
        UnknownPhotonPropagatorError: If we don't know how to handle the photon
            propagator you are asking for
        CannotLoadDetectorError: When no detector provided and no
            geo file path provided in config

        """
        self._start_timing_misc = time()
        if type(userconfig) == str:  # Path to yaml
            config = Configuration().from_yaml(userconfig)
        elif type(userconfig) == Configuration:
            config = userconfig

        if detector is None and config.detector["geo_file"] is None:
            raise CannotLoadDetectorError("No Detector provided and no geo file path given in config")

        if detector is None:
            from .detector import detector_from_geo
            detector = detector_from_geo(config.detector["geo_file"])

        self._detector = detector
        self._injection = None

        config_mims(config, self.detector)
        # clean_config(config)  # TODO: (Philip) Do we need to clean the config?
        
        LeptonPropagator = get_lepton_propagagtor(config.lepton_propagator["name"])
        import proposal as pp  # TODO: (Philip) Should this go somewhere else?
        pp.RandomGenerator.get().set_seed(config.run["random_state_seed"])

        self._lepton_propagator = LeptonPropagator(config.lepton_propagator)
        self._photon_propagator = get_photon_propagator(config.photon_propagator["name"])(
            self._lepton_propagator,
            self.detector,
            config.photon_propagator,
        )
        
        self._end_timing_misc = time()

    @property
    def detector(self):
        return self._detector

    @property
    def injection(self):
        #if self._injection is None:
        #    raise NoInjectionError("Injection has not been set!")
        return self._injection

    def inject(self):
        """Determines initial neutrino and final particle states according to config"""
        injection_config = config.injection
        if injection_config["inject"]:

            from .injection import INJECTOR_DICT
            if self._injector not in INJECTOR_DICT.keys():
                raise InjectorNotImplementedError(str(self._injector) + " is not a registered injector" )

            injection_config["simulation"]["random_state_seed"] = (
                config.run["random_state_seed"]
            )
            INJECTOR_DICT[self._injector](
                injection_config["paths"],
                injection_config["simulation"],
                detector_offset=self.detector.offset
            )
        self._injection = INJECTION_CONSTRUCTOR_DICT[self._injector](
            injection_config["paths"]["injection_file"]
        )

    # We should factor out generating losses and photon prop
    def propagate(self):
        """Calculates energy losses, generates photon yields, and propagates photons"""
        if config.photon_propagator["name"].lower() == "olympus":  # TODO: (Philip) Config should ensure lowercase names
            rstate = np.random.RandomState(config.run["random_state_seed"])
            rstate_jax = random.PRNGKey(config.run["random_state_seed"])
            # TODO this feels like it shouldn't be in the config
            config.photon_propagator["runtime"] = {  # TODO: (Philip) Fix spaces in config
                "random state": rstate,
                "random state jax": rstate_jax,
            }
        elif config.photon_propagator["name"].lower() == "ppc":  # TODO: (Philip) Combine this and PPC_CUDA?
            from glob import glob
            import shutil
            from .utils.clean_ppc_tmpdir import clean_ppc_tmpdir
            if (
                os.path.exists(config.photon_propagator["paths"]["ppc_tmpdir"]) and \
                not config.photon_propagator["paths"]["force"]
            ):
                raise PpcTmpdirExistsError(
                    config.photon_propagator["paths"]["ppc_tmpdir"]
                )
            os.mkdir(config.photon_propagator["paths"]["ppc_tmpdir"])
            fs = glob(f"{config.photon_propagator['paths']['ppctables']}/*")
            for f in fs:
                shutil.copy(f, config.photon_propagator["paths"]["ppc_tmpdir"])
        elif config.photon_propagator["name"].lower()=="ppc_cuda":
            from glob import glob
            import shutil
            from .utils.clean_ppc_tmpdir import clean_ppc_tmpdir
            if (
                os.path.exists(config.photon_propagator["paths"]["ppc_tmpdir"]) and \
                not config.photon_propagator["paths"]["force"]
            ):
                raise PpcTmpdirExistsError(
                    config.photon_propagator["paths"]["ppc_tmpdir"]
                )
            elif os.path.exists(cconfig.photon_propagator["paths"]["ppc_tmpdir"]):
                clean_ppc_tmpdir(config.photon_propagator["paths"]["ppc_tmpdir"])
            os.mkdir(config.photon_propagator["paths"]["ppc_tmpdir"])
            fs = glob(f"{config.photon_propagator['paths']['ppctables']}/*")
            for f in fs:
                shutil.copy(f, config.photon_propagator["paths"]["ppc_tmpdir"])

        if config.run["subset"] is not None:
            nevents = config.run["subset"]
        else:
            nevents = len(self.injection)

        with tqdm(enumerate(self.injection), total=len(self.injection)) as pbar:
            for idx, injection_event in pbar:
                if idx == nevents:
                    break
                for final_state in injection_event.final_states:
                    pbar.set_description(f"Propagating {final_state}")
                    self._photon_propagator.propagate(final_state)
        
        if config.photon_propagator["name"].lower()=="olympus":  # TODO: (Philip) Should the photon props have a cleanup method?
            config.photon_propagator["olympus"]["runtime"] = None
        elif config.photon_propagator["name"].lower()=="ppc":
            clean_ppc_tmpdir(config.photon_propagator['paths']['ppc_tmpdir'])
        elif config.photon_propagator["name"].lower()=="ppc_cuda":
            clean_ppc_tmpdir(config.photon_propagator['paths']['ppc_tmpdir'])

    def sim(self):
        """Performs injection of precipitating interaction, calculates energy losses,
        calculates photon yield, propagates photons, and save resultign photons"""
        if "runtime" in config.photon_propagator.keys():
            config.photon_propagator["runtime"] = None
        start_inj = time()
        self.inject()
        end_inj = time()
        start_prop = time()
        self.propagate()
        end_prop = time()
        start_out = time()
        self.construct_output()
        end_out = time()
        # Timing stuff
        # TODO: remove this? <-- (Philip) Debug info?
        self._timing_arr = np.array([
            self._end_timing_misc - self._start_timing_misc,
            end_inj - start_inj,
            end_prop - start_prop,
            end_out - start_out,
        ])

    def construct_output(self):
        """Constructs a parquet file with metadata from the generated files.
        Currently this still treats olympus and ppc output differently."""
        # sim_switch = config["photon propagator"]["name"]

        from .utils.serialization import serialize_particles_to_awkward, set_serialization_index
        set_serialization_index(self.injection)
        json_config = json.dumps(config)
        # builder = ak.ArrayBuilder()
        # with builder.record('config'):
        #     builder.field('config').append(json_config)
        # outarr = builder.snapshot()
        # outarr = ak.Record({"config": json_config})
        # outarr['mc_truth'] = self.injection.to_awkward()
        test_arr = serialize_particles_to_awkward(self.detector, self.injection)
        if test_arr is not None:
            outarr = ak.Array({
                'mc_truth': self.injection.to_awkward(),
                config.photon_propagator["photon_field_name"]: test_arr
            })
        else:
            outarr = ak.Array({
                'mc_truth': self.injection.to_awkward()
            })
        outfile = config["run"]['outfile']
        # Converting to pyarrow table
        outarr = ak.to_arrow_table(outarr)
        custom_meta_data_key = "config_prometheus"
        combined_meta = {custom_meta_data_key.encode() : json_config.encode()}
        outarr = outarr.replace_schema_metadata(combined_meta)
        pq.write_table(outarr, outfile)

    def __del__(self):
        """What to do when the Prometheus instance is deleted
        """
        print("I am melting.... AHHHHHH!!!!")

