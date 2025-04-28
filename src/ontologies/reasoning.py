import rdflib
from rdflib import Graph

import pyshacl
import reasonable
import owlrl
import time

from src.logging import Logger, LogLevel
from src.ontologies.namespaces import bind_namespaces


__all__ = [
    "reason_with_owlrl",
    "reason_with_reasonable",
]


logger = Logger(__name__, level=LogLevel.DEBUG)


def reason_with_owlrl(graph: Graph, new_graph: bool = False) -> Graph:
    """Loads ontology and instance data, performs reasoning, and saves the result."""

    if new_graph:
        reasoned_graph = rdflib.Graph() + graph
    else:
        reasoned_graph = graph

    logger.debug(f"The graph has {len(reasoned_graph)} triples. Starting reasoning process...")
    start_time = time.time()

    owlrl.DeductiveClosure(
        owlrl.OWLRL_Semantics,
        axiomatic_triples=True,
        datatype_axioms=True
    ).expand(reasoned_graph)

    end_time = time.time()
    logger.info(f"Reasoning time: {end_time - start_time:.2f} seconds")
    logger.debug(f"The graph has {len(reasoned_graph)} triples after reasoning.")

    return graph


def reason_with_reasonable(graph: Graph, new_graph: bool = False) -> Graph:

    reasoner = reasonable.PyReasoner()
    reasoner.from_graph(graph)

    logger.debug(f"The graph has {len(graph)} triples. Starting reasoning process...")
    start_time = time.time()
    triples = reasoner.reason()
    end_time = time.time()
    logger.info(f"Reasoning took {end_time - start_time:.2f} seconds and added {len(triples)} triples.")

    if new_graph:
        reasoned_graph = Graph()
    else:
        graph.remove((None, None, None))
        reasoned_graph = graph

    for triple in triples:
        reasoned_graph.add(triple)

    bind_namespaces(reasoned_graph)

    logger.debug(f"The graph has {len(reasoned_graph)} triples after reasoning.")

    return reasoned_graph


def validate_graph(data_graph: Graph, shacl_graph: Graph):
    """Validates the graph against SHACL constraints."""

    triples_before = len(data_graph)

    conforms, results_graph, results_text = pyshacl.validate(
        data_graph,
        shacl_graph=shacl_graph,
        inference='none',
        abort_on_first=False,
        meta_shacl=False,
        advanced=True,
        debug=False,
        iterate_rules=True,
    )

    triples_after = len(data_graph)

    logger.debug(f"Added {triples_after - triples_before} triples during validation.")

    results_graph.serialize(name='validation_report', format='turtle')

    if not conforms:
        logger.error(f"Validation failed:\n{results_text}")
    else:
        logger.info("Validation succeeded.")

    return conforms, results_graph, results_text


def infer_graph(data_graph: Graph, ont_graph: Graph, shacl_graph: Graph):
    """Validates the graph against SHACL constraints."""

    triples_before = len(data_graph)

    conforms, results_graph, results_text = pyshacl.validate(
        data_graph,
        ont_graph=ont_graph,
        shacl_graph=shacl_graph,

        inference='rdfs',  # 'rdfs', 'owlrl', 'none'
        debug=False,

        abort_on_first=False,
        allow_infos=True,
        allow_warnings=True,

        advanced=True,
        iterate_rules=True,
        inplace=True,
    )

    triples_after = len(data_graph)

    logger.debug(f"Added {triples_after - triples_before} triples during validation.")

    results_graph.serialize(name='validation_report', format='turtle')

    if not conforms:
        logger.error(f"Validation failed:\n{results_text}")
    else:
        logger.info("Validation succeeded.")

    return conforms, results_graph, results_text

