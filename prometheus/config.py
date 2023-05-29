# -*- coding: utf-8 -*-
# Name: config.py
# Copyright (C) 2022 Stephan Meighen-Berger
# Config file for the pr_dformat package.

from typing import Dict, Any
from collections import Mapping
import yaml
import os

from .injection import RegisteredInjectors
from .lepton_propagation import RegisteredLeptonPropagators
from .photon_propagation import RegisteredPhotonPropagators
from .utils import regularize_string

RESOURCES_DIR = os.path.abspath(f"{os.path.dirname(__file__)}/../resources/")

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
        
        self._LeptonPropagator
        
    def __setitem__(self, key, value) -> None:
        """
        Simple override to let the user know if a config
        key is being overwritten.
        """
        if key in self:
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
        return self['detector_config']
    
    @property
    def injection(self):
        name = self['injector']['name']
        return self['injector'][name].update(name=name) 
    
    @property
    def injector(self):
        return self.injection
    
    @property
    def lepton_propagator(self):
        name = self['lepton_propagator']['name']
        return self['lepton_propagator'][name].update(name=name)
    
    @property
    def photon_propagator(self):
        name = self['photon_propagator']['name']
        return self['photon_propagator'][name].update(name=name)
    
    @property
    def LeptonPropagator(self):
        # TODO: May not use this
        assert self._LeptonPropagator is not None, 'The lepton propagator has not been configured!'
        return self._LeptonPropagator
    
    def _load_lepton_propagator(self, name=None) -> None:
        # TODO: May not use this
        if name == 'old_proposal':
            from .lepton_propagation import OldProposalLeptonPropagator as LeptonPropagator
        else name == 'new_proposal':
            from .lepton_propagation import NewProposalLeptonPropagator as LeptonPropagator
        else:
            LeptonPropagator = None

        self._LeptonPropagator = LeptonPropagator

    def _get_proposal(self) -> str:
        """
        Check PROPOSAL version, set the proper config settings
        
        Returns
        -------
        Lepton propagator name 
        """
        import proposal as pp
        if int(pp.__version__.split('.')[0]) <= 6:
            name = 'old_proposal'
        else:
            name = 'new_proposal'
        
        self['lepton_propagator']['name'] = name
        self['lepton_propagator']['version'] = pp.__version__
                
        return name
    
    def _configure(self) -> None:
        """
        Check that the config is good and set a few things
        """
        injector_name = self['injector']['name']
        
        lepton_prop_name = self['lepton_propagator']['name']
        if lepton_prop_name is None:
            lepton_prop_name = self._get_proposal()  # This will set name/version
            
        photon_prop_name = self['photon_propagator']['name']
                
        if regularize_string(injector_name) not in RegisteredInjectors.list():
            raise UnknownInjectorError(injector_name + "is not supported as an injector!")

        if regularize_string(lepton_prop_name) not in RegisteredLeptonPropagators.list():
            raise UnknownLeptonPropagatorError(lepton_prop_name + "is not a known lepton propagator")

        if regularize_string(photon_prop_name) not in RegisteredPhotonPropagators.list():
            raise UnknownPhotonPropagatorError(photon_prop_name + " is not a known photon propagator")
    
    def from_yaml(self, yaml_file: str) -> ConfigClass:
        """ Update config with yaml file
        Parameters
        ----------
        yaml_file : str
            path to yaml file
        Returns
        -------
        None
        """
        yaml_config = yaml.load(open(yaml_file), Loader=yaml.SafeLoader)
        self.update(yaml_config)
        
        self._configure()  # TODO: (Philip) Perhaps the configure method should be a part of
                           #                an update method override...
        
        return self

    # TODO: Decide if this is going to be used
    def from_dict(self, user_dict: Dict[Any, Any]) -> ConfigClass:
        """ Creates a config from dictionary
        Parameters
        ----------
        user_dict : dic
            The user dictionary
        Returns
        -------
        None
        """
        raise NotImplementedError, 'This loading method is not yet implemented!'
    
        self.update(user_dict)
        return self

config = Configuration().from_yaml(yaml_file=f"{os.path.dirname(__file__)}/../configs/base.yaml")
