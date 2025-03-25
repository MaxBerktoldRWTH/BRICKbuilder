import rdflib


def to_uri(uri: str | rdflib.URIRef | None):

    if isinstance(uri, str):
        return rdflib.URIRef(uri)

    return uri


def to_literal(literal: str | int | float | rdflib.Literal | None):

    if isinstance(literal, (str, int, float)):
        return rdflib.Literal(literal)

    return literal

