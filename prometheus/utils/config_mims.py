import os

RESOURCES_DIR = os.path.abspath(f"{os.path.dirname(__file__)}/../../resources/")
INTERACTION_DICT = {
    ("EMinus", "Hadrons"): "CC",
    ("MuMinus", "Hadrons"): "CC",
    ("TauMinus", "Hadrons"): "CC",
    ("EPlus", "Hadrons"): "CC",
    ("MuPlus", "Hadrons"): "CC",
    ("TauPlus", "Hadrons"): "CC",
    ("NuE", "Hadrons"): "NC",
    ("NuMu", "Hadrons"): "NC",
    ("NuTau", "Hadrons"): "NC",
    ("NuEBar", "Hadrons"): "NC",
    ("NuMuBar", "Hadrons"): "NC",
    ("NuTauBar", "Hadrons"): "NC",
}
EARTH_MODEL_DICT = {
    "gvd.geo": "PREM_gvd.dat",
    "icecube.geo": "PREM_south_pole.dat",
    "icecube_gen2.geo": "PREM_south_pole.dat",
    "icecube_upgrade.geo": "PREM_south_pole.dat",
    "orca.geo": "PREM_orca.dat",
    "arca.geo": "PREM_arca.dat",
    "pone.geo": "PREM_pone.dat",
    # The following options are used in case another file is provided
    "WATER": "PREM_water.dat",
    "ICE": "PREM_south_pole.dat",
}


def config_mims(config, detector) -> None:
    """Sets parameters of config so that they are consistent
    
    params
    ______
    config: Dictionary specifying the simulation configuration
    detector: Detector being used for the simulation. A lot of 
        the simulation parameters can be set off the geometry of 
        the detector.
    """
    # Set up injection stuff

    if detector.medium.name == "WATER":
        config.photon_propagator["name"] = "olympus"
    elif detector.medium.name == "ICE" and config.photon_propagator["name"] is None:
        config.photon_propagator["name"] = "PPC"

    if config.run["random_state_seed"] is None:
        config.run["random_state_seed"] = config.run["run_number"]

    output_prefix = os.path.abspath(f"{config.run['storage_prefix']}/{config.run['run_number']}")
    if config.run["outfile"] is None:
        config.run["outfile"] = (
            f"{output_prefix}_photons.parquet"
        )

    # Find which earth model we think we should be using
    earth_model_file = None
    base_geofile = os.path.basename(config.detector["geo_file"])
    if base_geofile in EARTH_MODEL_DICT.keys():
        earth_model_file = EARTH_MODEL_DICT[base_geofile]
    else:
        earth_model_file = EARTH_MODEL_DICT[detector.medium.name]

    injection_config_mims(
        config.injection[config.injection["name"]],
        detector,
        config.run["nevents"],
        config.run["random_state_seed"],
        output_prefix,
        earth_model_file
    )

    lepton_prop_config_mims(
        config.lepton_propagator,
        detector,
        earth_model_file
    )

    photon_prop_config_mims(
        config.photon_propagator,
        output_prefix
    )
    
    check_consistency(config)

def check_consistency(config: dict) -> None:

    # TODO check whether medium is knowable
    # TODO check if medium is consistent
    
    
    raise NotImplementedError
    #if (
    #    config["simulation"]["medium"] is not None and
    #    config["simulation"]["medium"].upper()!=detector.medium.name
    #):
    #    raise ValueError("Detector and lepton propagator have conflicting media")

def photon_prop_config_mims(config: dict, output_prefix: str) -> None:
    pass


def lepton_prop_config_mims(
    subconfig: dict, 
    detector, 
    earth_model_file: str
) -> None:
    
    subconfig["simulation"]["medium"] = detector.medium.name.capitalize()
    
    if subconfig["simulation"]["propagation_padding"] is None:
        subconfig["simulation"]["propagation_padding"] = detector.outer_radius
        if detector.medium.name=="WATER":
            subconfig["simulation"]["propagation_padding"] += 50
        else:
            subconfig["simulation"]["propagation_padding"] += 200

    if subconfig["paths"]["earth_model_location"] is None:
#        if earth_model_file is None:
#            earth_model_file = EARTH_MODEL_DICT[detector.medium.name]
        subconfig["paths"]["earth_model_location"] = (
            f"{RESOURCES_DIR}/earthparams/densities/{earth_model_file}"
        )

def injection_config_mims(
    subconfig: dict,
    detector,
    nevents: int,
    seed: int,
    output_prefix: str,
    earth_model_file: str
) -> None:

    if not subconfig["inject"]:
        del subconfig["simulation"]
        return

    if subconfig["paths"]["earth_model_location"] is None:
        #earth_model_file = EARTH_MODEL_DICT[detector.medium.name]
        subconfig["paths"]["earth_model_location"] = (
            os.path.abspath(f"{RESOURCES_DIR}/earthparams/densities/{earth_model_file}")
        )

    if subconfig["simulation"]["is_ranged"] is None:
        subconfig["simulation"]["is_ranged"] = False
        if subconfig["simulation"]["final_state_1"] in "MuMinus MuPlus".split():
            subconfig["simulation"]["is_ranged"] = True

    subconfig["simulation"]["nevents"] = nevents
    # Make sure seeding is consistent
    subconfig["simulation"]["random_state_seed"] = seed

    # Name the h5 file
    if subconfig["paths"]["injection_file"] is None:
        subconfig["paths"]["injection_file"] = (
            f"{output_prefix}_LI_output.h5"
        )
    # Name the lic file
    if subconfig["paths"]["lic_file"] is None:
        subconfig["paths"]["lic_file"] = (
            f"{output_prefix}_LI_config.lic"
        )

    from .geo_utils import get_endcap, get_injection_radius, get_volume
    # TODO we shouldn't set the scattering length like this
    is_ice = detector.medium.name == "ICE"
    # Set the endcap length
    if subconfig["simulation"]["endcap_length"] is None:
        endcap = get_endcap(detector.module_coords, is_ice)
        subconfig["simulation"]["endcap_length"] = endcap
    # Set the injection radius
    if subconfig["simulation"]["injection_radius"] is None:
        inj_radius = get_injection_radius(detector.module_coords, is_ice)
        subconfig["simulation"]["injection_radius"] = inj_radius
    # Set the cylinder radius and height
    cyl_radius, cyl_height = get_volume(detector.module_coords, is_ice)
    if subconfig["simulation"]["cylinder_radius"] is None:
        subconfig["simulation"]["cylinder_radius"] = cyl_radius
    if subconfig["simulation"]["cylinder_height"] is None:
        subconfig["simulation"]["cylinder_height"] = cyl_height

    # Set the interaction
    int_str = INTERACTION_DICT[(
        subconfig["simulation"]["final_state_1"],
        subconfig["simulation"]["final_state_2"]
    )]
    
    if int_str in "CC NC".split():
        # Set cross section spline paths
        nutype = "nubar"
        if (
            "Bar" in subconfig["simulation"]["final_state_1"] or \
            "Plus" in subconfig["simulation"]["final_state_1"]
        ):
            nutype = "nu"
        if subconfig["paths"]["diff_xsec"] is None:
            subconfig["paths"]["diff_xsec"] = (
                os.path.abspath(f"{subconfig['paths']['xsec_dir']}/dsdxdy_{nutype}_{int_str}_iso.fits")
            )
        if subconfig["paths"]["total_xsec"] is None:
            subconfig["paths"]["total_xsec"] = (
                os.path.abspath(f"{subconfig['paths']['xsec_dir']}/sigma_{nutype}_{int_str}_iso.fits")
            )
    else:
        # Glashow resonance xs is not set by splines
        del subconfig["paths"]["xsec_dir"]
        del subconfig["paths"]["diff_xsec"] 
        del subconfig["paths"]["total_xsec"] 
