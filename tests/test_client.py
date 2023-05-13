import requests
import json
import pytest

import subprocess
import time
import shlex

import yaml

from src.oai_nmdc_plugin import nmdc_client
from src.oai_nmdc_plugin.nmdc_client import NMDCClient


def test_client():
    client = NMDCClient()
    qb = nmdc_client.QueryBuilder()
    qb.add_condition(op="==", field="env_broad_scale", value="terrestrial ecosystem", table="biosample")
    qb.add_condition(op="==", field="omics_type", value="Proteomics", table="omics_processing")
    obj = client.search_study(qb.query)
    print(yaml.dump(obj))


def test_sample():
    client = NMDCClient()
    qb = nmdc_client.QueryBuilder()
    qb.add_condition(op="==", field="env_broad_scale", value="terrestrial ecosystem", table="biosample")
    qb.add_condition(op="==", field="omics_type", value="Proteomics", table="omics_processing")
    obj = client.search_study(qb.query)
    print(yaml.dump(obj))

def test_normalize():
    client = NMDCClient()
    qb = nmdc_client.QueryBuilder()
    qb.add_condition(op="==", field="env_broad_scale", value="terrestrial", table="biosample")
    qb.add_condition(op="==", field="omics_type", value="Proteomics", table="omics_processing")
    client.normalize_query(qb.query)
    print(yaml.dump(qb.query.dict()))
    assert qb.query.conditions[0].value == "terrestrial ecosystem"

if __name__ == "__main__":
    pytest.main()
