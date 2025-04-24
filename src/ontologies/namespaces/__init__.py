import random
import string

from typing import Union, Tuple

import rdflib
from rdflib import Namespace, URIRef, Graph
from rdflib import RDF, RDFS, XSD, BRICK, SH
from src.ontologies.namespaces.qudt import QUDT, QUDTU, QUDTQK

BLDG = Namespace("http://example.org/building#")
S223 = Namespace("http://data.ashrae.org/standard223#")
REC = Namespace("https://w3id.org/rec#")
VISU = Namespace("http://example.org/visualization#")
BRICK_TAG = Namespace("https://brickschema.org/schema/BrickTag#")
BRICK_REF = Namespace("https://brickschema.org/schema/Brick/ref#")
BACNET = rdflib.Namespace("http://data.ashrae.org/bacnet/2020#")

__all__ = [
    "S223",
    "BRICK",
    "REC",
    "BRICK_REF",
    "VISU",
    "BLDG",
    "RDF",
    "SH",
    "RDFS",
    "XSD",
    "QUDT",
    "QUDTQK",
    "QUDTU",
    "bindings",

    "filter_by_namespace",
    "short_uuid",
    "replace_namespace",
    "bind_namespaces",
    "to_label",
    "to_uri",
    "split_uri",
]

bindings = {
    RDF: "rdf",
    RDFS: "rdfs",
    XSD: "xsd",
    S223: "s223",
    BRICK: "brick",
    BRICK_REF: "ref",
    BRICK_TAG: "tag",
    REC: "rec",
    BLDG: "bldg",
    VISU: "visu",
    QUDT: "qudt",
    QUDTQK: "qudtqk",
    QUDTU: "qudtu",
}


def replace_last_backslash(uri):

    index = uri.rfind("/")

    if index != -1:
        return uri[:index] + '#' + uri[index + 1:]

    return uri


def split_uri(uri: Union[rdflib.URIRef, str]) -> Union[Tuple[str, str], None]:

    uri = to_uri(uri)

    if uri is None:
        return None

    for sep in ['#', '/', ':']:
        index = uri.rfind(sep)
        if index != -1:
            namespace = uri[:index + 1]
            term = uri[index + 1:]
            return namespace, term

    raise ValueError(f"Invalid URI format: {uri}. No valid separator found.")


def find_abbreviation(uri):

    """Find the namespace of a given URI."""

    uri = str(uri)  # in case it's a URIRef

    for ns, short in bindings.items():
        if uri.startswith(str(ns)):
            return short

    return None


def to_uri(uri: Union[rdflib.URIRef, str, None]) -> Union[rdflib.URIRef, None]:

    if isinstance(uri, rdflib.URIRef):
        return uri
    elif isinstance(uri, str):
        return URIRef(uri)
    elif uri is None:
        return None

    raise TypeError(f"Invalid URI type: {type(uri)}. Expected rdflib.URIRef or str.")


def to_label(uri):
    """Converts a URI to a human-readable label."""

    if uri is None:
        return None

    ns, term = split_uri(uri)

    abbreviation = find_abbreviation(uri)

    if abbreviation is None:
        abbreviation = ns

    try:
        return abbreviation + '.' + term

    except TypeError:
        raise TypeError(f"Invalid URI format: {uri}.")


def short_uuid(length: int = 8):

    return ''.join(random.choices(string.ascii_letters, k=length))


def bind_namespaces(g: Graph):
    """Add a namespace prefix to a graph."""

    for namespace, prefix in bindings.items():
        g.bind(prefix, namespace)

    return g


def replace_namespace(g, oldns, newns):

    new_graph = Graph()

    for s, p, o in g:
        new_s = URIRef(str(s).replace(str(oldns), str(newns))) if isinstance(s, URIRef) and str(s).startswith(
            str(oldns)) else s
        new_p = URIRef(str(p).replace(str(oldns), str(newns))) if isinstance(p, URIRef) and str(p).startswith(
            str(oldns)) else p
        new_o = URIRef(str(o).replace(str(oldns), str(newns))) if isinstance(o, URIRef) and str(o).startswith(
            str(oldns)) else o

        new_graph.add((new_s, new_p, new_o))

    return new_graph


def filter_by_namespace(g, ns_to_keep: Namespace) -> Graph:

    filtered_graph = Graph()

    for s, p, o in g:
        if (str(s).startswith(str(ns_to_keep)) or
                str(p).startswith(str(ns_to_keep)) or
                str(o).startswith(str(ns_to_keep))):
            filtered_graph.add((s, p, o))

    filtered_graph = bind_namespaces(filtered_graph)

    return filtered_graph


if __name__ == "__main__":

    label = to_label(QUDT.degreeCelsius)

    print(label)

