# -*- coding: utf-8 -*-
# photonpropagator.py
# Copyright (C) 2022 Christian Haack, Jeffrey Lazar, Stephan Meighen-Berger,
# Interface class to the different photon propagators

# imports
import functools
import sys
import json
import numpy as np

from .hit import Hit
from ..config import config
from ..particle import Particle
from ..detector import Detector
from ..lepton_propagation import LeptonPropagator
from ..utils import serialize_to_f2k, PDG_to_f2k
from ..lepton_propagation import Loss

def _parse_ppc(ppc_f):
    res_result = [] # timing and module
    hits = []
    with open(ppc_f) as ppc_out:
        for line in ppc_out:
            if "HIT" in line: # Photon was seen
                l = line.split()
                '''(string number, dom number, time, wavelength, 
                dom zenith, dom azimuth, photon theta, photon azimuth)
                (N, n, ns, nm, radian, radian, radian, radian)
                '''
                hit = Hit(
                    int(l[1]), int(l[2]), float(l[3]), float(l[4]),
                    float(l[5]), float(l[6]), float(l[7]), float(l[8])
                )
                hits.append(hit)
    return hits

def _should_propagate(particle):
    if len(particle.losses) > 0:
        return True
    for child in particle.children:
        if len(child.losses) > 0:
            return True
    return False

def _ppc_sim(
    particle: Particle,
    det: Detector,
    lp: LeptonPropagator,
    ppc_config: dict
):
    """
    """
    geo_tmpfile = f"{ppc_config['paths']['ppctables']}/geo-f2k"
    ppc_file = f"{ppc_config['paths']['ppc_tmpfile']}_{str(particle)}"
    f2k_file = f"{ppc_config['paths']['f2k_tmpfile']}_{str(particle)}"
    command = f"{ppc_config['paths']['ppc_exe']} {ppc_config['simulation']['device']} < {f2k_file} > {ppc_file}"
    if ppc_config["simulation"]["supress_output"]:
        command += " 2>/dev/null"
    # TODO This could all be factored out into a LP step
    if abs(int(particle)) in [12, 14, 16]: # It's a neutrino
        return [], None
    # TODO put this in config
    r_inice = det.outer_radius + 1000
    if abs(int(particle)) in [11, 13, 15]: # It's a charged lepton
        lp.energy_losses(particle, det)
        for child in particle.children:
            # TODO put this in config
            if child.e > 1: # GeV
                _ppc_sim(child, det, lp, ppc_config)
    # All of these we consider as point depositions
    elif abs(int(particle))==111: # It's a neutral pion
        # TODO handle this correctl by converting to photons after prop
        return [], None
    elif abs(int(particle))==211: # It's a charged pion
        if np.linalg.norm(particle.position) <= r_inice:
            loss = Loss(int(particle), particle.e, particle.position)
            particle.add_loss(loss)
    elif abs(int(particle))==311: # It's a neutral kaon
        # TODO handle this correctl by converting to photons after prop
        return [], None
    elif int(particle)==-2000001006 or int(particle)==2212: # Hadrons
        if np.linalg.norm(particle.position) <= r_inice:
            loss = Loss(int(particle), particle.e, particle.position)
            particle.add_loss(loss)
    else:
        print(repr(particle))
        raise ValueError("Unrecognized particle")

    if not _should_propagate(particle):
        return [], None
    import os
    import subprocess
    serialize_to_f2k(particle, f2k_file)
    det.to_f2k(
        geo_tmpfile,
        serial_nos=[m.serial_no for m in det.modules]
    )
    tenv = os.environ.copy()
    tenv["PPCTABLESDIR"] = ppc_config["paths"]["ppctables"]

    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, env=tenv)
    process.wait()
    particle._hits = _parse_ppc(ppc_file)
    # Cleanup f2k_tmpfile
    # TODO maybe make this optional
    #os.remove(ppc_file)
    #os.remove(f2k_file)
    return None, None


class PP(object):
    ''' interface class between the different photon propagators

    Parameters
    ----------
    lp : LeptonPropagator object
        A lepton propagation instance
    det : dictionary
        A detector dictionary
    '''
    def __init__(self, lp: LeptonPropagator, det: Detector):
        print('--------------------------------------------')
        print('Constructing the photon propagator')
        self.__lp = lp
        self.__det = det
        if config['photon propagator']['name'] == 'olympus':
            import sys
            # Import olympus specifics
            # TODO should we have this relative import stuff here ??
            sys.path.append('../')
            
            from olympus.event_generation.photon_propagation.norm_flow_photons import (  # noqa
                make_generate_norm_flow_photons
            )
            from olympus.event_generation.event_generation import (  # noqa: E402
                generate_cascade,
                generate_realistic_track,
                simulate_noise,
            )
            from olympus.event_generation.lightyield import make_realistic_cascade_source # noqa
            from olympus.event_generation.utils import sph_to_cart_jnp  # noqa: E402
            
            from hyperion.medium import medium_collections  # noqa: E402
            from hyperion.constants import Constants  # noqa: E402

            self._local_conf = config['photon propagator']['olympus']
            # Setting up proposal
            self._prop = self.__lp._new_proposal_setup()
            self._olympus_setup()
            self._sim = self._olympus_sim
        elif config['photon propagator']['name'] == 'PPC':
            # TODO add in event displays
            # self._plotting = plot_event
            # TODO make a function for propagating photons
            # TODO move plotting to a HEBE object
            self._sim = lambda particle: _ppc_sim(
                particle,
                self.__det,
                self.__lp,
                config["photon propagator"]["PPC"]
            )
        elif config['photon propagator']['name'] == 'PPC_CUDA':
            # TODO add in event displays
            #self._plotting = plot_event
            self._sim = lambda particle: _ppc_sim(
                    particle, 
                    self.__det,
                    self.__lp, 
                    config["photon propagator"]["PPC_CUDA"]
            )
            
        else:
            raise ValueError(
                'Unknown photon propagator! Check the config file'
            )
        print('--------------------------------------------')

    def _olympus_setup(self):
        # TODO I feel like we should move things out to a different file to avoid this importing mess
        # TODO this is bad :-(
        # sys.path.append(config['photon propagator']['location'])
        sys.path.append('../../')
        
        # TODO should these be moved inside the set up function
        from olympus.event_generation.photon_propagation.norm_flow_photons import (  # noqa
            make_generate_norm_flow_photons
        )
        
        from hyperion.medium import medium_collections  # noqa: E402
        ''' Sets up olympus.
        '''
        print('Using olympus')
        print('Setting up the medium')
        self._pprop_path = (
            self._local_conf['location'] + self._local_conf['photon model']
        )
        import json
        self._pprop_config = json.load(open(
            self._pprop_path))['photon_propagation']
        # The medium
        self._ref_ix_f, self._sca_a_f, self._sca_l_f = medium_collections[
            self._pprop_config['medium']
        ]
        print('Finished the medium')
        print('-------------------------------------------------------')
        print('Setting up the photon generator')
        if self._local_conf['files']:
            self._gen_ph = make_generate_norm_flow_photons(
                self._local_conf['location'] + self._local_conf['flow'],
                self._local_conf['location'] + self._local_conf['counts'],
                c_medium=self._c_medium_f(
                    self._local_conf['wavelength']) / 1E9
            )
        else:
            ValueError('Currently only file runs for olympus are supported!')
        print('Finished the photon generator')

    def _olympus_sim(self, particle):
        """ Utilizes olympus to propagate light for the injected object
        """
        from olympus.event_generation.lightyield import make_realistic_cascade_source # noqa
        from olympus.event_generation.utils import sph_to_cart_jnp  # noqa: E402
        from olympus.event_generation.event_generation import (  # noqa: E402
            generate_cascade,
            generate_realistic_track,
            simulate_noise,
        )
        injection_event = {
            "time": 0.,
            "theta": particle.theta,
            "phi": particle.phi,
            "pos": particle.position,
            "energy": particle.e,
            "particle_id": particle.pdg_code,
            'length': config['lepton propagator']['track length'],
        }
        event_dir = sph_to_cart_jnp(
            injection_event["theta"],
            injection_event["phi"]
        )
        injection_event["dir"] = event_dir
        # Tracks
        if injection_event['particle_id'] in config['particles'][
                'track particles']:
            res_event, res_record = (
                generate_realistic_track(
                    self.__det,
                    injection_event,
                    key=config['runtime']['random state jax'],
                    pprop_func=self._gen_ph,
                    proposal_prop=self._prop,
                    splitter=config['photon propagator']['olympus']['splitter']
                )
            )
        # Cascades
        else:
            import functools
            res_event, res_record = generate_cascade(
                self.__det,
                injection_event,
                seed = config['runtime']['random state jax'],
                converter_func = functools.partial(
                    make_realistic_cascade_source,
                    moliere_rand=True,
                    resolution=0.2),
                pprop_func=self._gen_ph,
                splitter=config['photon propagator']['olympus']['splitter']
            )
            if config['run']['noise']:
                res_event, _ = simulate_noise(self._det, res_event)
        return res_event, res_record

    def _c_medium_f(self, wl):
        """ Speed of light in medium for wl (nm)
        """
        from hyperion.constants import Constants  # noqa: E402
        return Constants.BaseConstants.c_vac / self._ref_ix_f(wl)
