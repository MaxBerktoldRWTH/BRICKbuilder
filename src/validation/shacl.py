# src/validation/shacl_validator.py

import rdflib
from pyshacl import validate

SH = rdflib.Namespace("http://www.w3.org/ns/shacl#")


class ShaclValidationResult:
    def __init__(self, conforms: bool, report_graph: rdflib.Graph, report_text: str):
        self.conforms = conforms
        self.report_graph = report_graph
        self.report_text = report_text
        self.violations = self._extract_violations()

    def _extract_violations(self):
        """
        Extract validation result rows from the SHACL report graph.
        Returns a list of dictionaries for display in the GUI.
        """
        violations = []

        for result in self.report_graph.subjects(rdflib.RDF.type, SH.ValidationResult):
            severity = self.report_graph.value(result, SH.resultSeverity)
            focus_node = self.report_graph.value(result, SH.focusNode)
            result_path = self.report_graph.value(result, SH.resultPath)
            value = self.report_graph.value(result, SH.value)
            source_shape = self.report_graph.value(result, SH.sourceShape)
            message = self.report_graph.value(result, SH.resultMessage)

            violations.append({
                "severity": self._shorten(severity),
                "focus_node": str(focus_node) if focus_node else "",
                "path": str(result_path) if result_path else "",
                "value": str(value) if value else "",
                "source_shape": str(source_shape) if source_shape else "",
                "message": str(message) if message else "",
            })

        return violations

    @staticmethod
    def _shorten(value):
        if value is None:
            return ""

        value = str(value)

        if value == str(SH.Violation):
            return "Violation"
        if value == str(SH.Warning):
            return "Warning"
        if value == str(SH.Info):
            return "Info"

        return value


def validate_graph_with_shacl(
    data_graph: rdflib.Graph,
    shacl_file_path: str,
    inference: str = "rdfs",
    abort_on_first: bool = False,
    allow_warnings: bool = False,
    allow_infos: bool = False,
) -> ShaclValidationResult:
    """
    Validate an RDF data graph against a SHACL shapes graph loaded from a Turtle file.
    """
    shapes_graph = rdflib.Graph()
    shapes_graph.parse(shacl_file_path, format="turtle")

    conforms, report_graph, report_text = validate(
        data_graph=data_graph,
        shacl_graph=shapes_graph,
        inference=inference,
        abort_on_first=abort_on_first,
        allow_warnings=allow_warnings,
        allow_infos=allow_infos,
        meta_shacl=False,
        advanced=True,
        debug=False,
    )

    return ShaclValidationResult(
        conforms=conforms,
        report_graph=report_graph,
        report_text=report_text,
    )