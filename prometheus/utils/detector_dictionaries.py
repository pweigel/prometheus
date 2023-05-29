# -*- coding: utf-8 -*-
# detector_dictionaries.py
# Authors: David Kim
# Dicts for hebe_ui

# Vaules for default detectors
detectors = {
    '1': {
        'detector_name': 'IceCube',
        'file_path': '../hebe/data/icecube-geo',
        'injection_radius': 900,
        'endcap_length': 900,
        'cylinder_radius': 700,
        'cylinder_height': 1000,
        'medium': 'ice'
    },

    '2': {
        'detector_name': 'IceCube-Gen2',
        'file_path': '../hebe/data/icecube_gen2-geo',
        'injection_radius': 2100,
        'endcap_length': 1400,
        'cylinder_radius': 2000,
        'cylinder_height': 1700,
        'medium': 'ice'
    },

    '3': {
        'detector_name': 'P-ONE',
        'file_path': '../hebe/data/pone_triangle-geo',
        'injection_radius': 650,
        'endcap_length': 300,
        'cylinder_radius': 200,
        'cylinder_height': 1300,       
        'medium': 'water'
    },

    '4': {
        'detector_name': 'GVD',
        'file_path': '../hebe/data/gvd-geo',
        'injection_radius': 500,
        'endcap_length': 300,
        'cylinder_radius': 300,
        'cylinder_height': 900,       
        'medium': 'water'
    }
}

# Table of event & interaction types to final states
final_states = {
    'nue/cc':['EMinus','Hadrons'],
    'numu/cc':['MuMinus','Hadrons'],
    'nutau/cc':['TauMinus','Hadrons'],
    'nue/nc':['NuE','Hadrons'],
    'numu/nc':['NuMu','Hadrons'],
    'nutau/nc':['NuTau','Hadrons'],
    
    'nuebar/cc':['EPlus','Hadrons'],
    'numubar/cc':['MuPlus','Hadrons'],
    'nutaubar/cc':['TauPlus','Hadrons'],
    'nuebar/nc':['NuEBar','Hadrons'],
    'numubar/nc':['NuMuBar','Hadrons'],
    'nutaubar/nc':['NuTauBar','Hadrons'],
    
    'nuebar/hadron':['Hadrons','Hadrons'],
    'nuebar/e':['EMinus','NuEBar'],
    'nuebar/mu':['MuMinus','NuMuBar'],
    'nuebar/tau':['TauMinus','NuTauBar']
}

    

