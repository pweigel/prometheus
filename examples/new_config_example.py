
import prometheus
from prometheus import Prometheus, Configuration

config_path = '../configs/test_muons.yaml'
config = Configuration().from_yaml(yaml_file=config_path)
config.detector['geo_file'] = '../resources/geofiles/icecube.geo'
# {RESOURCE_DIR}/geofiles/icecube.geo

promeeeethius = Prometheus(userconfig=config)
promeeeethius.sim()
del promeeeethius