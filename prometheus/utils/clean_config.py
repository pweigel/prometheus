
def clean_config(config: dict) -> None:
    """Removes extraneous fields from the config file

    params
    ______
    config: Configuration dictionary

    returns
    _______
    config: Configuration dictionary with unused fields removed
    """
    # TODO move the actual config up a level
    for x in ["injection", "lepton_propagator", "photon_propagator"]:
        keys = [key for key in config[x].keys() if key not in ["name", config[x]["name"], "photon_field_name"]]
        for key in keys:
            del config[x][key]
