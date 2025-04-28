import os
from rdflib import Graph

__all__ = [
    "S223_GRAPH",
    "RDF_GRAPH",
    "OWL_GRAPH",
    "BRICK_GRAPH",
    "REC_GRAPH",
]


cur_dir = os.path.dirname(os.path.abspath(__file__))


def S223_GRAPH():
    return Graph().parse(cur_dir + r"\files\S223.ttl", format="turtle")


def BRICK_GRAPH():
    return Graph().parse(cur_dir + r"\files\BRICK.ttl", format="turtle")


def REC_GRAPH():
    return Graph().parse(cur_dir + r"\files\REC.ttl", format="turtle")


def RDF_GRAPH():
    return Graph().parse(cur_dir + r"\files\RDF.ttl", format="turtle")


def OWL_GRAPH():
    return Graph().parse(cur_dir + r"\files\OWL.ttl", format="turtle")

