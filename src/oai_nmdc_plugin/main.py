# The following code provides a thin wrapper around the NMDC API
# to provide a simple API for the OpenAI plugin to use. It uses FastAPI
# and is run on port 3434 by default.
import json
from enum import Enum
from typing import Any, Dict, List, Optional

import httpx
import yaml
from fastapi import FastAPI, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from os.path import abspath, dirname

from src.oai_nmdc_plugin import nmdc_client

app = FastAPI()

nmdc_client_obj = nmdc_client.NMDCClient()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# Serve static files needed for OpenAI plugin
app.mount("/.well-known", StaticFiles(directory = dirname(abspath(__file__)) + "/.well-known"), name="well-known")
app.mount("/static", StaticFiles(directory = dirname(abspath(__file__)) + "/static"), name="static")



#######################
### Search endpoint
#######################

# Define the models for search results
class SearchResultItem(BaseModel):
    id: str = Field(..., description="The NMDC identifier of the search result.")
    name: str = Field(..., description="The name of the sample or study.")

class SearchResultResponse(BaseModel):
    results: List[SearchResultItem] = Field(..., description="The list of search results.")


def _make_query(
            entity_type: str = "study",
            environment: Optional[str] = None,
            omics_type: Optional[str] = None,
            ) -> nmdc_client.Query:

    if entity_type == "study":
        api_url = nmdc_client.STUDY_SEARCH_URL
    elif entity_type == "biosample":
        api_url = nmdc_client.BIOSAMPLE_SEARCH_URL
    else:
        raise ValueError(f"Error: Invalid entity type: {entity_type}")

    qb = nmdc_client.QueryBuilder()
    if environment:
        qb.add_condition(op="==", field="env_broad_scale", value=environment, table="biosample")
    if omics_type:
        qb.add_condition(op="==", field="omics_type", value=omics_type, table="omics_processing")

    print(f"Query = {qb.query.dict()}")

    nmdc_client_obj.normalize_query(qb.query)

    print(f"Normalized = {qb.query.dict()}")

    print(yaml.dump(qb.query.dict()))

    return qb.query


def _results(response_json: dict):
    search_results = []
    for result in response_json.get("results", []):
        print(result)
        search_results.append(SearchResultItem(id=result.get("id"), name=result.get("name")))

    res = {"results": search_results}
    print(res)
    return res


@app.get("/study/search",
         response_model=SearchResultResponse,
         description="Search for microbiome studies",
         summary="Search for studies in NMDC",
         response_description="Search results for the given search parameters",
         operation_id="search_study")
async def search_study(environment: Optional[str] = Query(None, description="The type of environment, biome, or habitat."),
                       omics_type: Optional[str] = Query(None, description="The type of omics data. Valid categories are: Metagenome, Metatranscriptome, Proteomics, Metabolomics."),
                       ) -> SearchResultResponse:

    query = _make_query(entity_type="study", environment=environment, omics_type=omics_type)
    api_url = nmdc_client.STUDY_SEARCH_URL
    async with httpx.AsyncClient() as client:
        response = await client.post(api_url, data=json.dumps(query.dict()))

    response_json = response.json()
    return _results(response_json)


@app.get("/biosample/search",
         response_model=SearchResultResponse,
         description="Search for microbiome samples",
         summary="Search for sample in NMDC",
         response_description="List of samples matching the given search parameters",
         operation_id="search_sample")
async def search_biosample(environment: Optional[str] = Query(None, description="The type of environment, biome, or habitat."),
                       omics_type: Optional[str] = Query(None, description="The type of omics data. Valid categories are: Metagenome, Metatranscriptome, Proteomics, Metabolomics."),
                       ) -> SearchResultResponse:

    query = _make_query(entity_type="biosample", environment=environment, omics_type=omics_type)
    api_url = nmdc_client.BIOSAMPLE_SEARCH_URL
    async with httpx.AsyncClient() as client:
        response = await client.post(api_url, data=json.dumps(query.dict()))

    response_json = response.json()
    return _results(response_json)
