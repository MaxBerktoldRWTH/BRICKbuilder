import rdflib
from PyQt5.QtCore import Qt


class AppConfig:

    grid_size = 25
    canvas_width = 1_500
    canvas_height = 1_000

    frame_color = Qt.black
    frame_width = 2

    brick_ns = rdflib.Namespace("https://brickschema.org/schema/Brick#")
    ref_ns = rdflib.Namespace("https://brickschema.org/schema/Brick/ref#")
    bacnet_ns = rdflib.Namespace("http://data.ashrae.org/bacnet/2020#")

    building_ns = rdflib.Namespace("http://example.org/building/#")
    design_ns = rdflib.Namespace("http://example.org/design#")

    @classmethod
    def get_point_line_height(cls):
        return cls.canvas_height * 0.9

    @classmethod
    def set_size(cls, size):
        cls.size = size

