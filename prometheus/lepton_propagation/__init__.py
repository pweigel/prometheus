from .loss import Loss
from .lepton_propagator import LeptonPropagator
from .registered_propagators import RegisteredPropagators as RegisteredLeptonPropagators

import proposal as pp

def get_lepton_propagagtor(name) -> LeptonPropagator:
    name = name.lower()
    major_version = int(pp.__version__.split(".")[0])
    if name == 'old_proposal':
        assert int(pp.__version__.split(".")[0]) <= 6, \
            'Found PROPOSAL major version {} not consistent with {}!'.format(major_version, name)
        from .old_proposal_lepton_propagator import OldProposalLeptonPropagator
        return OldProposalLeptonPropagator
    elif name == 'new_proposal':
        assert int(pp.__version__.split(".")[0]) >= 7, \
            'Found PROPOSAL major version {} not consistent with {}!'.format(major_version, name)
        from .new_proposal_lepton_propagator import NewProposalLeptonPropagator
        return NewProposalLeptonPropagator
    else:
        return None # TODO: Raise exception?