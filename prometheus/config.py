# -*- coding: utf-8 -*-
# Name: config.py
# Copyright (C) 2022 Stephan Meighen-Berger
# Config file for the pr_dformat package.

from typing import Dict, Any
import yaml
import os

RESOURCES_DIR = os.path.abspath(f"{os.path.dirname(__file__)}/../resources/")

class ConfigClass(dict):
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
    
    # TODO: Update this
    def from_yaml(self, yaml_file: str) -> None:
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
        
        return self

    # TODO: Update this
    def from_dict(self, user_dict: Dict[Any, Any]) -> None:
        """ Creates a config from dictionary
        Parameters
        ----------
        user_dict : dic
            The user dictionary
        Returns
        -------
        None
        """
        self.update(user_dict)
        return self
    
    @property
    def lepton_prop_config(self):
        pass
    

config = ConfigClass().from_yaml(yaml_file=f"{os.path.dirname(__file__)}/../configs/base.yaml")
