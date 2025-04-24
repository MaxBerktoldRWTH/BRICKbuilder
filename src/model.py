import rdflib

import typing

from src.ontologies.namespaces import BRICK


def split_uri(uri: str | rdflib.URIRef) -> [str, str]:
    if isinstance(uri, rdflib.URIRef):
        uri = str(uri)

    if "#" in uri:
        return uri.split("#")

    if "/" in uri:
        return uri.split("/")

    raise ValueError(f"URI {uri} is not a valid URI")


def get_name(uri: str | rdflib.URIRef) -> str:
    return split_uri(uri)[-1]


def get_namespace(uri: str | rdflib.URIRef) -> str:
    return "/".join(split_uri(uri)[:-1])


class Entity:
    """Base class representing an entity from the Brick or REC ontology."""

    def __init__(
            self,
            uri_ref: rdflib.URIRef,
            svg_data: str,
            category: typing.List[str],
            port_pos: tuple = (25, 25),
    ):
        if not isinstance(uri_ref, rdflib.URIRef):
            raise TypeError(f"uri_ref must be rdflib.URIRef, not {type(uri_ref).__name__}")

        if not isinstance(svg_data, str):
            raise TypeError(f"svg_data must be str, not {type(svg_data).__name__}")

        if not isinstance(category, list) or not all(isinstance(item, str) for item in category):
            raise TypeError("category must be a list of strings")

        self.uri_ref = uri_ref
        self.svg_data = svg_data
        self.category = category
        self.port_pos = port_pos

    @property
    def name(self) -> str:
        return get_name(self.uri_ref)

    @property
    def namespace(self) -> str:
        return get_namespace(self.uri_ref)


class Point(Entity):

    def __init__(
            self,
            uri_ref: rdflib.URIRef,
            category: list
    ):

        super().__init__(
            uri_ref=uri_ref,
            svg_data="""
                    <svg width="25" height="50" xmlns="http://www.w3.org/2000/svg">
                        <rect width="25" height="50" x="0" y="0" fill="white" stroke="black" stroke-width="2"/> 
                    </svg>
                """,
            category=category,
            port_pos=(25 / 2, 25),
        )


class EntityLibrary:
    """Static collection of entity definitions from the Brick and REC ontologies."""

    valve = Entity(
        uri_ref=BRICK.Valve,
        svg_data="""
            <svg width="50" height="50" xmlns="http://www.w3.org/2000/svg">
              <path d="M 0, 10 L 0, 40 L 25, 25 Z" fill="white" stroke="black" stroke-width="1"/>
              <path d="M 50, 10 L 50, 40 L 25, 25 Z" fill="white" stroke="black" stroke-width="1"/>
            </svg>
        """,
        category=["BRICK", "Equipment"],
    )

    mixing_valve = Entity(
        uri_ref=BRICK.Bypass_Valve,
        svg_data="""
            <svg width="50" height="50" xmlns="http://www.w3.org/2000/svg">
              <path d="M 0, 10 L 0, 40 L 25, 25 Z" fill="white" stroke="black" stroke-width="1"/>
              <path d="M 50, 10 L 50, 40 L 25, 25 Z" fill="white" stroke="black" stroke-width="1"/>
              <path d="M 10, 50 L 40, 50 L 25, 25 Z" fill="white" stroke="black" stroke-width="1"/>
            </svg>
        """,
        category=["BRICK", "Equipment", "Valve"],
    )

    pump = Entity(
        uri_ref=BRICK.Pump,
        svg_data="""
            <svg width="50" height="50" xmlns="http://www.w3.org/2000/svg">
              <circle cx="25" cy="25" r="25" fill="white" stroke="black" stroke-width="1"/>
              <path d="M 25 0 L 50 25" stroke="black" stroke-width="1" fill="white"/>
              <path d="M 25 50 L 50 25" stroke="black" stroke-width="1" fill="white"/>
            </svg>
        """,
        category=["BRICK", "Equipment", "HVAC"],
    )

    fan = Entity(
        uri_ref=BRICK.Fan,
        svg_data="""
            <svg
               width="50"
               height="50"
               version="1.1"
               id="svg2"
               sodipodi:docname="fan.svg"
               inkscape:version="1.4 (86a8ad7, 2024-10-11)"
               xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"
               xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"
               xmlns="http://www.w3.org/2000/svg"
               xmlns:svg="http://www.w3.org/2000/svg">
              <defs
                 id="defs2" />
              <sodipodi:namedview
                 id="namedview2"
                 pagecolor="#ffffff"
                 bordercolor="#666666"
                 borderopacity="1.0"
                 inkscape:showpageshadow="2"
                 inkscape:pageopacity="0.0"
                 inkscape:pagecheckerboard="0"
                 inkscape:deskcolor="#d1d1d1"
                 showgrid="true"
                 inkscape:zoom="11.525841"
                 inkscape:cx="25.160855"
                 inkscape:cy="17.829502"
                 inkscape:window-width="1920"
                 inkscape:window-height="1017"
                 inkscape:window-x="-8"
                 inkscape:window-y="-8"
                 inkscape:window-maximized="1"
                 inkscape:current-layer="svg2">
                <inkscape:grid
                   id="grid2"
                   units="px"
                   originx="0"
                   originy="0"
                   spacingx="1"
                   spacingy="1"
                   empcolor="#0099e5"
                   empopacity="0.30196078"
                   color="#0099e5"
                   opacity="0.14901961"
                   empspacing="5"
                   enabled="true"
                   visible="true" />
              </sodipodi:namedview>
              <circle
                 cx="25"
                 cy="25"
                 r="25"
                 fill="white"
                 stroke="black"
                 stroke-width="1"
                 id="circle1" />
              <path
                 d="M 10,5 48,15"
                 stroke="#000000"
                 stroke-width="1"
                 fill="#ffffff"
                 id="path1"
                 sodipodi:nodetypes="cc" />
              <path
                 d="M 10,45 48,35"
                 stroke="#000000"
                 stroke-width="1"
                 fill="#ffffff"
                 id="path2"
                 sodipodi:nodetypes="cc" />
            </svg>

        """,
        category=["BRICK", "Equipment", "HVAC"],
    )

    radiator = Entity(
        uri_ref=BRICK.Radiator,
        svg_data="""
            <svg width="50" height="50" xmlns="http://www.w3.org/2000/svg">
              <circle cx="25" cy="25" r="25" fill="white" stroke="black" stroke-width="1"/>
              <circle cx="25" cy="25" r="20" fill="white" stroke="black" stroke-width="1"/>
            </svg>
        """,
        category=["BRICK", "Equipment", "HVAC", "Terminal Unit"],
        port_pos=(25, 25),
    )

    boiler = Entity(
        uri_ref=BRICK.Boiler,
        svg_data="""
        <svg
           width="50"
           height="80"
           version="1.1"
           id="svg2"
           sodipodi:docname="boiler.svg"
           inkscape:version="1.4 (86a8ad7, 2024-10-11)"
           xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"
           xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"
           xmlns="http://www.w3.org/2000/svg"
           xmlns:svg="http://www.w3.org/2000/svg">
          <defs
             id="defs2" />
          <sodipodi:namedview
             id="namedview2"
             pagecolor="#ffffff"
             bordercolor="#666666"
             borderopacity="1.0"
             inkscape:showpageshadow="2"
             inkscape:pageopacity="0.0"
             inkscape:pagecheckerboard="0"
             inkscape:deskcolor="#d1d1d1"
             showgrid="true"
             inkscape:zoom="8.15"
             inkscape:cx="15.337423"
             inkscape:cy="41.288344"
             inkscape:window-width="1920"
             inkscape:window-height="1017"
             inkscape:window-x="-8"
             inkscape:window-y="-8"
             inkscape:window-maximized="1"
             inkscape:current-layer="svg2">
            <inkscape:grid
               id="grid2"
               units="px"
               originx="0"
               originy="0"
               spacingx="1"
               spacingy="1"
               empcolor="#0099e5"
               empopacity="0.30196078"
               color="#0099e5"
               opacity="0.14901961"
               empspacing="5"
               enabled="true"
               visible="true" />
          </sodipodi:namedview>
          <g
             id="g31611"
             transform="matrix(2.3809472,0,0,2.3809472,60.714206,-250.80343)">
            <path
               style="fill:#ffffff;fill-opacity:1;stroke:#000000;stroke-width:1;stroke-linecap:square;stroke-miterlimit:4;stroke-dasharray:none;stroke-opacity:1"
               d="m -22.499998,135 c 0,4 4.999999,3.90667 7.499999,3.8889 2.499937,-0.0178 7.5000002,0.1111 7.5000002,-3.8889"
               id="path6724"
               sodipodi:nodetypes="csc" />
            <path
               style="fill:#ffffff;fill-opacity:1;stroke:#000000;stroke-width:1;stroke-linecap:square;stroke-miterlimit:4;stroke-dasharray:none;stroke-opacity:1"
               d="m -24.999999,110.5 c 0,-2.5 0,-5 10,-5 10.0000002,0 10.0000002,2.5 10.0000002,5 v 20 c 0,2.5 0,5 -10.0000002,5 -10,0 -10,-2.5 -10,-5 z"
               id="path5488"
               sodipodi:nodetypes="csssssc" />
            <path
               id="path5019"
               style="fill:#ffffff;stroke:#000000;stroke-width:0.94488;stroke-linecap:square"
               d="m -12.499999,113 a 2.5,2.5 0 0 1 -2.5,2.5 2.5,2.5 0 0 1 -2.5,-2.5 2.5,2.5 0 0 1 2.5,-2.5 2.5,2.5 0 0 1 2.5,2.5 z" />
            <path
               style="fill:none;fill-opacity:1;stroke:#000000;stroke-width:1;stroke-linecap:butt;stroke-miterlimit:4;stroke-dasharray:none;stroke-opacity:1"
               d="m -14.999999,113 1.5,-1.5"
               id="path7983"
               sodipodi:nodetypes="cc" />
            <g
               id="g9518"
               transform="translate(-5.9999988)"
               style="stroke-width:1;stroke-miterlimit:4;stroke-dasharray:none">
              <path
                 id="path8958"
                 style="display:inline;opacity:1;fill:none;stroke:#000000"
                 d="m -4,125 a 5,5 0 0 1 -5,5 5,5 0 0 1 -5,-5 5,5 0 0 1 5,-5 5,5 0 0 1 5,5 z" />
              <path
                 style="opacity:1;fill:#ac2b1c;fill-opacity:1;stroke:#000000;stroke-width:0.5;stroke-linecap:butt;stroke-linejoin:round;stroke-miterlimit:4;stroke-dasharray:none;stroke-opacity:1"
                 d="m -10.160875,128.77549 c 0,0 -1.750141,-1.27401 -1.831679,-2.6805 -0.137168,-2.36609 2.9262191,-4.86959 2.9262191,-4.86959 0,0 -0.446751,2.68051 0.4244131,3.70804 0.871164,1.02753 1.943367,-0.20104 1.943367,-0.20104 0,0 1.228565,1.38493 0.245713,2.76986 -0.982853,1.38493 -1.764666,1.38493 -1.764666,1.38493 0,0 0.335063,-0.53611 0.3574,-0.93818 0.02233,-0.40208 -0.3574,-0.75948 -0.3574,-0.75948 l -0.3619513,0.81884 c 0,0 -0.1182967,-0.0482 -0.4310217,-0.71832 -0.3127261,-0.67012 -0.2233761,-1.44077 -0.2233761,-1.44077 0,0 -0.9270091,0.96051 -1.0833711,1.63064 -0.156364,0.67012 0.156362,1.29557 0.156362,1.29557 z"
                 id="path9301"
                 sodipodi:nodetypes="cscscscsccscscc" />
            </g>
          </g>
        </svg>

        """,
        category=["BRICK", "Equipment", "HVAC"],
        port_pos=(25, 80),
    )

    Heating_Coil = Entity(
        uri_ref=BRICK.Heating_Coil,
        svg_data="""
        <svg
           width="50"
           height="100"
           version="1.1"
           id="svg2"
           sodipodi:docname="heating_coil.svg"
           inkscape:version="1.4 (86a8ad7, 2024-10-11)"
           xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"
           xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"
           xmlns="http://www.w3.org/2000/svg"
           xmlns:svg="http://www.w3.org/2000/svg">
          <defs
             id="defs2" />
          <sodipodi:namedview
             id="namedview2"
             pagecolor="#ffffff"
             bordercolor="#666666"
             borderopacity="1.0"
             inkscape:showpageshadow="2"
             inkscape:pageopacity="0.0"
             inkscape:pagecheckerboard="0"
             inkscape:deskcolor="#d1d1d1"
             showgrid="true"
             inkscape:zoom="5.7629203"
             inkscape:cx="3.2969396"
             inkscape:cy="60.819859"
             inkscape:window-width="1920"
             inkscape:window-height="1017"
             inkscape:window-x="-8"
             inkscape:window-y="-8"
             inkscape:window-maximized="1"
             inkscape:current-layer="svg2">
            <inkscape:grid
               id="grid2"
               units="px"
               originx="0"
               originy="0"
               spacingx="1"
               spacingy="1"
               empcolor="#0099e5"
               empopacity="0.30196078"
               color="#0099e5"
               opacity="0.14901961"
               empspacing="5"
               enabled="true"
               visible="true" />
          </sodipodi:namedview>
          <rect
             style="fill:white;stroke:#000000;stroke-width:1;stroke-opacity:1;stroke-dasharray:none"
             id="rect1"
             width="50"
             height="100"
             x="0"
             y="0"
             ry="0" />
          <path
             style="fill:none;stroke:#000000;stroke-width:1;stroke-opacity:1;stroke-dasharray:none"
             d="M 50,0 0,100"
             id="path3" />
        </svg>
        """,
        category=["BRICK", "Equipment", "HVAC", "HX", "Coil"],
        port_pos=(25, 50),
    )

    Cooling_Coil = Entity(
        uri_ref=BRICK.Cooling_Coil,
        svg_data="""
            <svg
               width="50"
               height="100"
               version="1.1"
               id="svg2"
               sodipodi:docname="heating_coil.svg"
               inkscape:version="1.4 (86a8ad7, 2024-10-11)"
               xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"
               xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"
               xmlns="http://www.w3.org/2000/svg"
               xmlns:svg="http://www.w3.org/2000/svg">
              <defs
                 id="defs2" />
              <sodipodi:namedview
                 id="namedview2"
                 pagecolor="#ffffff"
                 bordercolor="#666666"
                 borderopacity="1.0"
                 inkscape:showpageshadow="2"
                 inkscape:pageopacity="0.0"
                 inkscape:pagecheckerboard="0"
                 inkscape:deskcolor="#d1d1d1"
                 showgrid="true"
                 inkscape:zoom="5.7629203"
                 inkscape:cx="3.1234165"
                 inkscape:cy="60.819859"
                 inkscape:window-width="1920"
                 inkscape:window-height="1017"
                 inkscape:window-x="-8"
                 inkscape:window-y="-8"
                 inkscape:window-maximized="1"
                 inkscape:current-layer="svg2">
                <inkscape:grid
                   id="grid2"
                   units="px"
                   originx="0"
                   originy="0"
                   spacingx="1"
                   spacingy="1"
                   empcolor="#0099e5"
                   empopacity="0.30196078"
                   color="#0099e5"
                   opacity="0.14901961"
                   empspacing="5"
                   enabled="true"
                   visible="true" />
              </sodipodi:namedview>
              <rect
                 style="fill:white;stroke:#000000;stroke-width:1;stroke-opacity:1;stroke-dasharray:none"
                 id="rect1"
                 width="50"
                 height="100"
                 x="0"
                 y="0"
                 ry="0" />
              <path
                 style="fill:none;stroke:#000000;stroke-width:1;stroke-opacity:1;stroke-dasharray:none"
                 d="M 50,100 0,0"
                 id="path2" />
              <path
                 style="fill:none;stroke:#000000;stroke-width:1;stroke-opacity:1;stroke-dasharray:none"
                 d="M 50,0 0,100"
                 id="path3" />
            </svg>
        """,
        category=["BRICK", "Equipment", "HVAC", "HX", "Coil"],
        port_pos=(25, 50),
    )

    Heat_Exchanger = Entity(
        uri_ref=BRICK.Heat_Exchanger,
        svg_data="""
        <svg
           width="50"
           height="100"
           version="1.1"
           id="svg2"
           sodipodi:docname="heat_exchanger.svg"
           inkscape:version="1.4 (86a8ad7, 2024-10-11)"
           xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"
           xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"
           xmlns="http://www.w3.org/2000/svg"
           xmlns:svg="http://www.w3.org/2000/svg">
          <defs
             id="defs2" />
          <sodipodi:namedview
             id="namedview2"
             pagecolor="#ffffff"
             bordercolor="#666666"
             borderopacity="1.0"
             inkscape:showpageshadow="2"
             inkscape:pageopacity="0.0"
             inkscape:pagecheckerboard="0"
             inkscape:deskcolor="#d1d1d1"
             showgrid="true"
             inkscape:zoom="5.7629203"
             inkscape:cx="31.407688"
             inkscape:cy="65.157937"
             inkscape:window-width="1920"
             inkscape:window-height="1017"
             inkscape:window-x="-8"
             inkscape:window-y="-8"
             inkscape:window-maximized="1"
             inkscape:current-layer="svg2">
            <inkscape:grid
               id="grid2"
               units="px"
               originx="0"
               originy="0"
               spacingx="1"
               spacingy="1"
               empcolor="#0099e5"
               empopacity="0.30196078"
               color="#0099e5"
               opacity="0.14901961"
               empspacing="5"
               enabled="true"
               visible="true" />
          </sodipodi:namedview>
          <rect
             style="fill:white;stroke:#000000;stroke-width:1;stroke-opacity:1;stroke-dasharray:none"
             id="rect1"
             width="50"
             height="100"
             x="0"
             y="0"
             ry="0" />
          <path
             style="fill:none;stroke:#000000;stroke-width:1;stroke-opacity:1;stroke-dasharray:none"
             d="M 50,100 0,0"
             id="path2" />
          <path
             style="fill:none;stroke:#000000;stroke-width:1;stroke-dasharray:none;stroke-opacity:1"
             d="M 50,5 5,100"
             id="path3"
             sodipodi:nodetypes="cc" />
          <path
             style="fill:none;stroke:#000000;stroke-width:1;stroke-dasharray:none;stroke-opacity:1"
             d="M 45,0 0,95"
             id="path3-0"
             sodipodi:nodetypes="cc" />
        </svg>
        """,
        category=["BRICK", "Equipment", "HVAC"],
        port_pos=(25, 50),
    )

    Damper = Entity(
        uri_ref=BRICK.Damper,
        svg_data="""
        <svg
           width="50"
           height="100"
           version="1.1"
           id="svg2"
           sodipodi:docname="damper.svg"
           inkscape:version="1.4 (86a8ad7, 2024-10-11)"
           xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"
           xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"
           xmlns="http://www.w3.org/2000/svg"
           xmlns:svg="http://www.w3.org/2000/svg">
          <defs
             id="defs2" />
          <sodipodi:namedview
             id="namedview2"
             pagecolor="#ffffff"
             bordercolor="#666666"
             borderopacity="1.0"
             inkscape:showpageshadow="2"
             inkscape:pageopacity="0.0"
             inkscape:pagecheckerboard="0"
             inkscape:deskcolor="#d1d1d1"
             showgrid="true"
             inkscape:zoom="8.15"
             inkscape:cx="32.638037"
             inkscape:cy="48.282208"
             inkscape:window-width="1920"
             inkscape:window-height="1017"
             inkscape:window-x="-8"
             inkscape:window-y="-8"
             inkscape:window-maximized="1"
             inkscape:current-layer="svg2">
            <inkscape:grid
               id="grid2"
               units="px"
               originx="0"
               originy="0"
               spacingx="1"
               spacingy="1"
               empcolor="#0099e5"
               empopacity="0.30196078"
               color="#0099e5"
               opacity="0.14901961"
               empspacing="5"
               enabled="true"
               visible="true" />
          </sodipodi:namedview>
          <rect
             style="fill:white;stroke:#000000;stroke-width:1;stroke-opacity:1;stroke-dasharray:none"
             id="rect1"
             width="50"
             height="100"
             x="0"
             y="0"
             ry="0" />
          <path
             style="fill:none;stroke:#000000;stroke-width:1;stroke-dasharray:none;stroke-opacity:1"
             d="M 45,10 5,90"
             id="path3-0-0"
             sodipodi:nodetypes="cc" />
          <circle
             style="fill:#000000;fill-opacity:1;stroke:none"
             id="path1"
             cx="25"
             cy="50"
             r="3" />
        </svg>
        """,
        category=["BRICK", "Equipment", "HVAC"],
        port_pos=(25, 50),
    )

    point = Point(
        uri_ref=BRICK.Point,
        category=["BRICK"],
    )

    temperature_sensor = Point(
        uri_ref=BRICK.Temperature_Sensor,
        category=["BRICK", "Point", "Sensor"],
    )

    temperature_setpoint = Point(
        uri_ref=BRICK.Temperature_Setpoint,
        category=["BRICK", "Point", "Setpoint"],
    )

    Position_Sensor = Point(
        uri_ref=BRICK.Position_Sensor,
        category=["BRICK", "Point", "Sensor"],
    )

    Position_Setpoint = Point(
        uri_ref=BRICK.Position_Setpoint,
        category=["BRICK", "Point", "Setpoint"],
    )

    Room = Entity(
        uri_ref=rdflib.URIRef("https://doc.realestatecore.io/4.0/#Room"),
        svg_data="""
            <svg width="50" height="50" xmlns="http://www.w3.org/2000/svg">
                <rect width="50" height="50" x="0" y="0" fill="white" stroke="black" stroke-width="2"/> 
            </svg>
        """,
        category=["REC", "Space", "Room"],
        port_pos=(25, 25),
    )

    Zone = Entity(
        uri_ref=rdflib.URIRef("https://doc.realestatecore.io/4.0/#Zone"),
        svg_data="""
            <svg width="50" height="50" xmlns="http://www.w3.org/2000/svg">
                <rect width="50" height="50" x="0" y="0" fill="white" stroke="black" stroke-width="2"/> 
            </svg>
        """,
        category=["REC", "Space", "Zones"],
        port_pos=(25, 25),
    )

    HVACZone = Entity(
        uri_ref=rdflib.URIRef("https://doc.realestatecore.io/4.0/#HVAC_Zone"),
        svg_data="""
            <svg width="50" height="100" xmlns="http://www.w3.org/2000/svg">
                <rect width="50" height="100" x="0" y="0" fill="white" stroke="black" stroke-width="2"/> 
            </svg>
        """,
        category=["REC", "Space", "Zones"],
        port_pos=(25, 50),
    )

    level = Entity(
        uri_ref=rdflib.URIRef("https://doc.realestatecore.io/4.0/#Level"),
        svg_data="""
            <svg width="200" height="50" xmlns="http://www.w3.org/2000/svg">
                <rect width="200" height="50" x="0" y="0" fill="white" stroke="black" stroke-width="2"/> 
            </svg>
        """,
        category=["REC", "Space", "Levels"],
        port_pos=(100, 25),
    )

    @classmethod
    def get_all_entities(cls):
        return [cls.__dict__[item] for item in cls.__dict__ if isinstance(cls.__dict__[item], Entity)]

    @classmethod
    def find_entity_by_uri(cls, uri_ref: rdflib.URIRef) -> Entity:
        for entity in cls.get_all_entities():
            if str(entity.uri_ref) == str(uri_ref):
                return entity
        raise AttributeError(f"Entity not found for URI: {uri_ref}")



if __name__ == '__main__':

    for e in EntityLibrary.get_all_entities():
        print(e.uri_ref)
