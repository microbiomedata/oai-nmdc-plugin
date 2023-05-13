import json
from typing import List, Optional, Collection

import httpx
import requests
from oaklib import BasicOntologyInterface, get_adapter
from oaklib.datamodels.search import SearchConfiguration
from oaklib.datamodels.search_datamodel import SearchProperty
from oaklib.datamodels.vocabulary import IS_A
from oaklib.interfaces import SearchInterface, OboGraphInterface
from oaklib.types import PRED_CURIE, CURIE
from oaklib.utilities.subsets.slimmer_utils import filter_redundant
from pydantic import BaseModel

BASE_URL = "https://data-dev.microbiomedata.org/api"
BIOSAMPLE_SEARCH_URL = f"{BASE_URL}/biosample/search?offset=0&limit=10"
STUDY_SEARCH_URL = f"{BASE_URL}/study/search?offset=0&limit=10"

ENV_BROAD_SCALE = "env_broad_scale"


class Condition(BaseModel):
    op: str
    field: str
    value: str
    table: str = "study"


class Query(BaseModel):
    conditions: List[Condition]


class QueryBuilder(BaseModel):
    query: Query = Query(conditions=[])


    def add_condition(self, op: str, field: str, value: str, table: str = "study"):
        condition = Condition(op=op, field=field, value=value, table=table)
        self.query.conditions.append(condition)
        return self


def filter_descendants(
    oi: OboGraphInterface, curies: Collection[CURIE], predicates: List[PRED_CURIE] = None
) -> List[CURIE]:
    return [curie for curie in curies if not is_descendant(oi, curie, curies, predicates)]


def is_descendant(
    oi: OboGraphInterface,
    curie: CURIE,
    curies: Collection[CURIE],
    predicates: List[PRED_CURIE] = None,
) -> bool:
    for candidate in curies:
        if candidate != curie:
            if curie in list(oi.descendants(candidate, predicates=predicates)):
                return True
    return False

class NMDCClient:

    _envo: Optional[BasicOntologyInterface] = None

    @property
    def envo(self) -> SearchInterface:
        if not self._envo:
            self._envo = get_adapter("sqlite:obo:envo")
        if not isinstance(self._envo, SearchInterface):
            raise Exception(f"Error: {self._envo} is not a SearchInterface")
        return self._envo


    def search_study(self, query: Query):
        api_url = STUDY_SEARCH_URL
        print(query.dict())
        resp = requests.post(api_url, data=json.dumps(query.dict()))
        if resp.status_code != 200:
            raise Exception(f"Error: {resp.status_code}: {resp.text}")
        return resp.json()


    def search_sample(self, query: Query):
        api_url = BIOSAMPLE_SEARCH_URL
        print(query.dict())
        resp = requests.post(api_url, data=json.dumps(query.dict()))
        if resp.status_code != 200:
            raise Exception(f"Error: {resp.status_code}: {resp.text}")
        return resp.json()


    def normalize_query(self, query: Query):
        # normalize the query
        # return the normalized query
        envo = self.envo
        configs = [
            SearchConfiguration(properties=[SearchProperty.LABEL]),
            SearchConfiguration(properties=[SearchProperty.ALIAS]),
            SearchConfiguration(is_partial=True, properties=[SearchProperty.ALIAS]),
                   ]
        tmap = {}
        for condition in query.conditions:
            if condition.field == "env_broad_scale":
                tmap[condition.value] = condition
        # ecosystems = set(list(envo.descendants("ENVO:01001110", [IS_A]))) # ecosystem
        ecosystems = set(list(envo.descendants("ENVO:00000428", [IS_A])))
        for term, condition in tmap.items():
            for config in configs:
                terms = list(envo.basic_search(term, config=config))
                filtered = ecosystems.intersection(terms)
                if len(filtered) > 0:
                    if not isinstance(envo, OboGraphInterface):
                        raise AssertionError(f"Error: {envo} is not an OboGraphInterface")
                    filtered = filter_descendants(envo, list(filtered), [IS_A])
                    condition.value = envo.label(filtered.pop())
                    if condition.value:
                        break


