# -*- coding: utf-8 -*-
# Name: config.py
# Copyright (C) 2022 Stephan Meighen-Berger
# Config file for the pr_dformat package.
from __future__ import annotations
from typing import Dict, Any
from collections.abc import Mapping
import yaml
import os

from .injection import RegisteredInjectors
from .lepton_propagation import RegisteredLeptonPropagators
from .photon_propagation import RegisteredPhotonPropagators
from .utils import regularize_string

RESOURCES_DIR = os.path.abspath(f"{os.path.dirname(__file__)}/../resources/")

# class TestConfiguration(dict):
#     # TODO: experimental
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
        
#         if 'name' in kwargs.keys():
#             self.name = kwargs['name']
            
#             if 'parent' in kwargs.keys():
#                 if kargs['parent'] is not None:
#                     self.parent = kwargs['parent']
#                     self.parent[self.name] = self

#     def __setitem__(self, key, value):
#         super().__setitem__(key, value)
        
#         if self.parent is not None:
#             self.parent[self.name].update({key: value})


class Configuration(dict):
    """ The configuration class. This is used
    by the package for all parameter settings. If something goes wrong
    its usually here.
    Parameters
    ----------
    config : dic
        The config dictionary
    Returns
    -------
    None
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self._warn_overwrite = True
        
    def __setitem__(self, key, value) -> None:
        """
        Simple override to let the user know if a config
        key is being overwritten.
        """
        if key in self and self._warn_overwrite:
            print('Overwriting key {}!'.format(key))

        super().__setitem__(key, value)
    
    @property
    def general(self):
        return self['general']
    
    @property
    def run(self):
        return self['run']

    @property
    def detector(self):
        return self['detector']
    
    @property
    def injection(self):
        return self['injection']
    
    @property
    def injector(self):
        return self.injection
    
    @property
    def lepton_propagator(self):
        return self['lepton_propagator']
    
    @property
    def photon_propagator(self):
        return self['photon_propagator']
    
    @property
    def LeptonPropagator(self):
        # TODO: May not use this
        assert self._LeptonPropagator is not None, 'The lepton propagator has not been configured!'
        return self._LeptonPropagator
    
    def _load_lepton_propagator(self, name=None) -> None:
        # TODO: May not use this
        if name == 'old_proposal':
            from .lepton_propagation import OldProposalLeptonPropagator as LeptonPropagator
        elif name == 'new_proposal':
            from .lepton_propagation import NewProposalLeptonPropagator as LeptonPropagator
        else:
            LeptonPropagator = None

        self._LeptonPropagator = LeptonPropagator

    def _get_proposal(self) -> (str, int):
        """
        Check PROPOSAL version, set the proper config settings
        
        Returns
        -------
        Lepton propagator name 
        """
        import proposal as pp
        version = int(pp.__version__.split('.')[0])
        if verion <= 6:
            name = 'old_proposal'
        else:
            name = 'new_proposal'

        return name, version
    
    def _configure(self, config: dict) -> None:
        """
        Check that the config is good and set a few things
        """
        
        # Copy the settings that don't require any special treatment
        for k, v in config.items():
            if k not in ['injector', 'lepton_propagator', 'photon_propagator']:
                self[k] = v

        injector_name = config['injection']['name']
        self['injection'] = config['injection'][injector_name]
        
        lepton_prop_name = config['lepton_propagator']['name']
        if lepton_prop_name is None:
            lepton_prop_name, lepton_prop_version = self._get_proposal()
        else:
            lepton_prop_version = None

        self['lepton_propagator'] = config['lepton_propagator'][lepton_prop_name]
        self['lepton_propagator']['version'] = lepton_prop_version  # Add PROPOSAL version
          
        photon_prop_name = config['photon_propagator']['name']
        self['photon_propagator'] = config['photon_propagator'][photon_prop_name]
        
        if regularize_string(injector_name) not in RegisteredInjectors.list():
            raise UnknownInjectorError(injector_name + "is not supported as an injector!")

        if regularize_string(lepton_prop_name) not in RegisteredLeptonPropagators.list():
            raise UnknownLeptonPropagatorError(lepton_prop_name + "is not a known lepton propagator!")

        if regularize_string(photon_prop_name) not in RegisteredPhotonPropagators.list():
            raise UnknownPhotonPropagatorError(photon_prop_name + " is not a known photon propagator!")
        
        # Update the subconfigs to include any parameters in the level above
        self['injection'].update(
            {k: v for k, v in config['injection'].items() if not isinstance(v, Mapping)})
        
        self['lepton_propagator'].update(
            {k: v for k, v in config['lepton_propagator'].items() if not isinstance(v, Mapping)})
        
        self['photon_propagator'].update(
            {k: v for k, v in config['photon_propagator'].items() if not isinstance(v, Mapping)})

        if 'warn_config_overwrite' in self.general.keys():
            self._warn_overwrite = self.general['warn_config_overwrite']
        
        
    def from_yaml(self, yaml_file: str) -> Configuration:
        """ Update config with yaml file
        Parameters
        ----------
        yaml_file : str
            path to yaml file
        Returns
        -------
        None
        """
        yaml_config = yaml.load(open(yaml_file, 'r'), Loader=yaml.SafeLoader)
        
        self._configure(yaml_config)  # TODO: (Philip) Maybe this should be an update override
        
        return self

    # TODO: Decide if this is going to be used
    def from_dict(self, user_dict: Dict[Any, Any]) -> Configuration:
        """ Creates a config from dictionary
        Parameters
        ----------
        user_dict : dic
            The user dictionary
        Returns
        -------
        None
        """
        raise NotImplementedError
    
        self.update(user_dict)
        return self

#TODO: (Philip) Remove?
# config = Configuration().from_yaml(yaml_file=f"{os.path.dirname(__file__)}/../configs/base.yaml")
