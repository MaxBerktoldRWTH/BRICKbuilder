---
title: 'BRICKbuilder: A Graphical Interface for Semantic Building System Modeling'
tags:
  - building modeling
  - semantic web
  - ontology
  - Brick schema
  - building automation
  - smart buildings
authors:
  - name: Max Berktold
    affiliation: 1
  - name: Martin Rätz
    affiliation: 2
affiliations:
 - name: Institute for Energy Efficient Buildings and Indoor Climate, E.ON Energy Research Center, RWTH Aachen University, Aachen, Germany
   index: 1
date: 25 March 2025
bibliography: references.bib
---

# Summary

BRICKbuilder is a software application that provides a graphical user interface (GUI) for semantically designing building systems, bridging the gap between the power of ontologies and the practical needs of building professionals. It leverages the Brick and REC ontologies to facilitate the creation, visualization, and export of semantically rich models. This tool supports the development of semantic models, benefiting research and applications in building automation, energy management, and smart building technologies.

The core functionality includes:

- **Entity Modeling**: A library of pre-defined building system entities (e.g., equipment, sensors, spaces) based on Brick and REC, organized by category, allows users to drag and drop components onto a canvas. A properties panel enables customization of entity attributes and labels.
- **Semantic Relationships**: Users can visually connect entities, creating semantically meaningful relationships (e.g., 'hasPoint', 'feeds', 'isLocatedIn') defined by the Brick schema. The software offers intelligent assistance in selecting appropriate relationship types.
- **IFC Import**: Building layouts can be automatically imported from IFC files. The software extracts building, storey, and room information, creating a semantically linked spatial structure. This significantly reduces setup time.
- **Turtle Export**: Designs are exported as standard RDF Turtle (.ttl) files, ensuring compatibility with other semantic web tools and facilitating data sharing and reuse.
- **User-Friendly Interface**: The GUI comprises an entity browser, a design canvas, a property panel, a toolbar, and menus, providing a streamlined workflow.
- **Keyboard Shortcuts**: Extensive keyboard shortcuts enhance user efficiency and productivity.

BRICKbuilder is built upon the Brick and REC ontologies, allowing users to create models that are both visually intuitive and semantically precise. The software democratizes access to semantic modeling for building systems. By providing a visual representation of knowledge graphs, it overcomes the inherent complexity of raw ontological data, making it accessible to a wider range of users, including those without specialized expertise in semantic web technologies. This promotes collaboration and accelerates the adoption of ontology-based approaches in the building industry.

# Statement of Need

The building sector is a significant contributor to global energy consumption, and a substantial portion of this energy is used inefficiently due to suboptimal building operation. A root cause of this inefficiency lies in poor data management practices and the lack of robust, interoperable data models for representing building systems. Traditional building automation system (BAS) planning tools often rely on proprietary formats, hindering data exchange and integration across different systems and lifecycle stages (design, commissioning, operation). This "data silo" effect limits the potential for advanced analytics, optimization, and the development of truly smart buildings.

Semantic web technologies, specifically ontologies, offer a promising solution to these challenges. Ontologies provide a formal, machine-readable representation of knowledge, enabling interoperability, data integration, and reasoning capabilities. Several building-domain ontologies, such as Brick, REC, BOT, and SAREF, have gained traction in recent years, with Brick Schema emerging as a prominent choice within the research community. These ontologies provide a standardized vocabulary and structure for describing building components, systems, and their relationships.

However, a significant barrier to the widespread adoption of ontologies in building automation is the difficulty of *interpreting* and *working with* the resulting knowledge graphs. While ontologies excel at machine-readability, the raw data representations (e.g., Turtle files) are often challenging for humans to understand and manipulate, especially for those unfamiliar with semantic web technologies. This hinders collaboration, design review, and the overall usability of ontology-based approaches. BRICKbuilder directly addresses this critical gap by providing a user-friendly, visual interface for creating, editing, and understanding building system models based on ontologies like Brick and REC.

# Features

## Entity Modeling
BRICKbuilder provides a comprehensive, categorized library of building system entities based on the Brick and REC ontologies. Users can drag and drop these entities onto a canvas to create their designs. A properties panel allows users to view and modify entity attributes, labels, and other relevant information.

![Screenshot of the BRICKbuilder user interface.\label{fig:gui}](GUI.png)

## Semantic Relationships
The tool enables users to create semantically meaningful connections between entities, representing relationships defined by the Brick ontology (e.g., 'hasPoint', 'feeds', 'isLocatedIn'). The software provides visual cues for connection creation and automatically suggests appropriate relationship types. Users can manually adjust types and reverse directions. Custom routing paths are supported via adjustable joints.

## Design Management
Designs can be exported as RDF Turtle (.ttl) files, enabling interoperability. The software supports importing previously saved designs from Turtle files. The application can import building layouts directly from IFC files, automatically extracting buildings, levels, and rooms, and arranging them with semantic relationships.

## User Interface
The UI consists of:

- **Entity Browser**: Displays available entity types, organized by category.
- **Canvas**: The main area for creating and editing designs.
- **Property Panel**: Shows and allows editing of properties for selected items.
- **Toolbar**: Provides quick access to common tools.
- **Menus**: Offer access to file operations, editing functions, and view options.

## Keyboard Shortcuts
Shortcuts enhance efficiency: deleting items (Del), selecting all (Ctrl+A), rotating (R), copy/paste (Ctrl+C/V), toggling point visibility (P), zooming (Ctrl+scroll, +/-), panning (Middle mouse button), and exporting/importing (Ctrl+S/I). A help window ('H') displays all shortcuts.

# Acknowledgements

This work was supported by [Funding Source(s) and Grant Number(s)].

# References