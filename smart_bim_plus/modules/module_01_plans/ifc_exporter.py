import uuid
import time
import tempfile
from typing import Dict, Any, List, Optional


class IFCExporter:
    """مصدر ملفات IFC — ينشئ نموذج BIM كامل"""

    def __init__(self):
        self.ifc_file = None
        self.project = None
        self.site = None
        self.building = None
        self.storeys = {}
        self.owner_history = None
        self.context = None

    def export(self, plan_data: Dict[str, Any], filepath: str,
               building_name: str = "NOVA Building",
               total_floors: int = 1):
        """تصدير المخطط إلى ملف IFC"""
        import ifcopenshell
        import ifcopenshell.guid

        self.ifc_file = ifcopenshell.file(schema="IFC4")
        self._create_header(building_name)
        self._create_project(building_name)
        self._create_site()
        self._create_building(building_name)

        floor_height = 3.0
        for floor_num in range(total_floors):
            storey = self._create_storey(floor_num, floor_height)
            self.storeys[floor_num] = storey

        target_floor = plan_data.get("floor_number", 0)
        storey = self.storeys.get(target_floor, list(self.storeys.values())[0])

        for room in plan_data.get("rooms", []):
            self._create_room_walls(room, storey, floor_height)

        for door in plan_data.get("doors", []):
            self._create_door(door, storey)

        for window in plan_data.get("windows", []):
            self._create_window(window, storey)

        pw = plan_data.get("plot_width", 20)
        pl = plan_data.get("plot_length", 25)
        for floor_num in range(total_floors):
            s = self.storeys.get(floor_num, storey)
            self._create_slab(pw, pl, s, floor_num * floor_height)

        self.ifc_file.write(filepath)

    def _guid(self) -> str:
        import ifcopenshell.guid
        return ifcopenshell.guid.new()

    def _create_header(self, name: str):
        self.ifc_file.wrapped_data.header.file_name.name = name
        self.ifc_file.wrapped_data.header.file_name.author = ["NOVA"]
        self.ifc_file.wrapped_data.header.file_name.organization = ["DSBA"]

    def _create_project(self, name: str):
        self.owner_history = self.ifc_file.create_entity(
            "IfcOwnerHistory",
            **{
                "OwningUser": self.ifc_file.create_entity(
                    "IfcPersonAndOrganization",
                    **{
                        "ThePerson": self.ifc_file.create_entity(
                            "IfcPerson",
                            FamilyName="DSBA",
                            GivenName="NOVA",
                        ),
                        "TheOrganization": self.ifc_file.create_entity(
                            "IfcOrganization",
                            Name="NOVA",
                        ),
                    }
                ),
                "OwningApplication": self.ifc_file.create_entity(
                    "IfcApplication",
                    **{
                        "ApplicationDeveloper": self.ifc_file.create_entity(
                            "IfcOrganization",
                            Name="NOVA",
                        ),
                        "Version": "1.0",
                        "ApplicationFullName": "NOVA DSBA",
                        "ApplicationIdentifier": "NOVA",
                    }
                ),
                "ChangeAction": "NOCHANGE",
                "CreationDate": int(time.time()),
            }
        )

        self.context = self.ifc_file.create_entity(
            "IfcGeometricRepresentationContext",
            ContextType="Model",
            CoordinateSpaceDimension=3,
            Precision=1.0e-05,
            WorldCoordinateSystem=self.ifc_file.create_entity(
                "IfcAxis2Placement3D",
                Location=self.ifc_file.create_entity(
                    "IfcCartesianPoint",
                    Coordinates=(0.0, 0.0, 0.0),
                ),
            ),
        )

        self.project = self.ifc_file.create_entity(
            "IfcProject",
            GlobalId=self._guid(),
            OwnerHistory=self.owner_history,
            Name=name,
            RepresentationContexts=[self.context],
            UnitsInContext=self._create_units(),
        )

    def _create_units(self):
        length = self.ifc_file.create_entity(
            "IfcSIUnit",
            UnitType="LENGTHUNIT",
            Name="METRE",
        )
        area = self.ifc_file.create_entity(
            "IfcSIUnit",
            UnitType="AREAUNIT",
            Name="SQUARE_METRE",
        )
        volume = self.ifc_file.create_entity(
            "IfcSIUnit",
            UnitType="VOLUMEUNIT",
            Name="CUBIC_METRE",
        )
        angle = self.ifc_file.create_entity(
            "IfcSIUnit",
            UnitType="PLANEANGLEUNIT",
            Name="RADIAN",
        )
        return self.ifc_file.create_entity(
            "IfcUnitAssignment",
            Units=[length, area, volume, angle],
        )

    def _create_site(self):
        self.site = self.ifc_file.create_entity(
            "IfcSite",
            GlobalId=self._guid(),
            OwnerHistory=self.owner_history,
            Name="Construction Site",
            CompositionType="ELEMENT",
        )
        self.ifc_file.create_entity(
            "IfcRelAggregates",
            GlobalId=self._guid(),
            OwnerHistory=self.owner_history,
            RelatingObject=self.project,
            RelatedObjects=[self.site],
        )

    def _create_building(self, name: str):
        self.building = self.ifc_file.create_entity(
            "IfcBuilding",
            GlobalId=self._guid(),
            OwnerHistory=self.owner_history,
            Name=name,
            CompositionType="ELEMENT",
        )
        self.ifc_file.create_entity(
            "IfcRelAggregates",
            GlobalId=self._guid(),
            OwnerHistory=self.owner_history,
            RelatingObject=self.site,
            RelatedObjects=[self.building],
        )

    def _create_storey(self, floor_num: int, floor_height: float):
        elevation = floor_num * floor_height
        storey = self.ifc_file.create_entity(
            "IfcBuildingStorey",
            GlobalId=self._guid(),
            OwnerHistory=self.owner_history,
            Name=f"Floor {floor_num}",
            CompositionType="ELEMENT",
            Elevation=elevation,
        )
        if not hasattr(self, '_storey_list'):
            self._storey_list = []
        self._storey_list.append(storey)

        self.ifc_file.create_entity(
            "IfcRelAggregates",
            GlobalId=self._guid(),
            OwnerHistory=self.owner_history,
            RelatingObject=self.building,
            RelatedObjects=[storey],
        )
        return storey

    def _create_placement(self, x: float = 0, y: float = 0, z: float = 0):
        point = self.ifc_file.create_entity(
            "IfcCartesianPoint",
            Coordinates=(float(x), float(y), float(z)),
        )
        axis2 = self.ifc_file.create_entity(
            "IfcAxis2Placement3D",
            Location=point,
        )
        return self.ifc_file.create_entity(
            "IfcLocalPlacement",
            RelativePlacement=axis2,
        )

    def _create_room_walls(self, room: Dict, storey, height: float = 3.0):
        px = room.get("position_x", 0)
        py = room.get("position_y", 0)
        rw = room.get("width", 4)
        rl = room.get("length", 4)
        thickness = 0.2

        wall_segments = [
            (px, py, px + rw, py),
            (px + rw, py, px + rw, py + rl),
            (px + rw, py + rl, px, py + rl),
            (px, py + rl, px, py),
        ]

        elements = []
        for sx, sy, ex, ey in wall_segments:
            wall = self._create_wall(sx, sy, ex, ey, height, thickness, storey)
            elements.append(wall)

        if elements:
            self.ifc_file.create_entity(
                "IfcRelContainedInSpatialStructure",
                GlobalId=self._guid(),
                OwnerHistory=self.owner_history,
                RelatingStructure=storey,
                RelatedElements=elements,
            )

    def _create_wall(self, x1, y1, x2, y2, height, thickness, storey):
        import math
        length = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
        angle = math.atan2(y2 - y1, x2 - x1)

        placement = self._create_placement(x1, y1, 0)

        direction = self.ifc_file.create_entity(
            "IfcDirection",
            DirectionRatios=(math.cos(angle), math.sin(angle), 0.0),
        )

        profile = self.ifc_file.create_entity(
            "IfcRectangleProfileDef",
            ProfileType="AREA",
            XDim=length,
            YDim=thickness,
        )

        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2

        extrusion_placement = self.ifc_file.create_entity(
            "IfcAxis2Placement3D",
            Location=self.ifc_file.create_entity(
                "IfcCartesianPoint",
                Coordinates=(mid_x, mid_y, 0.0),
            ),
        )

        solid = self.ifc_file.create_entity(
            "IfcExtrudedAreaSolid",
            SweptArea=profile,
            Position=extrusion_placement,
            ExtrudedDirection=self.ifc_file.create_entity(
                "IfcDirection",
                DirectionRatios=(0.0, 0.0, 1.0),
            ),
            Depth=height,
        )

        shape_rep = self.ifc_file.create_entity(
            "IfcShapeRepresentation",
            ContextOfItems=self.context,
            RepresentationIdentifier="Body",
            RepresentationType="SweptSolid",
            Items=[solid],
        )

        product_shape = self.ifc_file.create_entity(
            "IfcProductDefinitionShape",
            Representations=[shape_rep],
        )

        wall = self.ifc_file.create_entity(
            "IfcWall",
            GlobalId=self._guid(),
            OwnerHistory=self.owner_history,
            Name=f"Wall",
            ObjectPlacement=placement,
            Representation=product_shape,
        )
        return wall

    def _create_door(self, door_data: Dict, storey):
        pos = door_data.get("position", (0, 0))
        width = door_data.get("width", 0.9)
        height = 2.1
        placement = self._create_placement(pos[0], pos[1], 0)

        door = self.ifc_file.create_entity(
            "IfcDoor",
            GlobalId=self._guid(),
            OwnerHistory=self.owner_history,
            Name="Door",
            ObjectPlacement=placement,
            OverallHeight=height,
            OverallWidth=width,
        )

        self.ifc_file.create_entity(
            "IfcRelContainedInSpatialStructure",
            GlobalId=self._guid(),
            OwnerHistory=self.owner_history,
            RelatingStructure=storey,
            RelatedElements=[door],
        )
        return door

    def _create_window(self, window_data: Dict, storey):
        pos = window_data.get("position", (0, 0))
        width = window_data.get("width", 1.2)
        height = window_data.get("height", 1.2)
        sill = window_data.get("sill_height", 0.9)
        placement = self._create_placement(pos[0], pos[1], sill)

        window = self.ifc_file.create_entity(
            "IfcWindow",
            GlobalId=self._guid(),
            OwnerHistory=self.owner_history,
            Name="Window",
            ObjectPlacement=placement,
            OverallHeight=height,
            OverallWidth=width,
        )

        self.ifc_file.create_entity(
            "IfcRelContainedInSpatialStructure",
            GlobalId=self._guid(),
            OwnerHistory=self.owner_history,
            RelatingStructure=storey,
            RelatedElements=[window],
        )
        return window

    def _create_slab(self, width: float, length: float,
                     storey, elevation: float):
        thickness = 0.25
        placement = self._create_placement(0, 0, elevation - thickness)

        profile = self.ifc_file.create_entity(
            "IfcRectangleProfileDef",
            ProfileType="AREA",
            Position=self.ifc_file.create_entity(
                "IfcAxis2Placement2D",
                Location=self.ifc_file.create_entity(
                    "IfcCartesianPoint",
                    Coordinates=(width / 2, length / 2),
                ),
            ),
            XDim=width,
            YDim=length,
        )

        solid = self.ifc_file.create_entity(
            "IfcExtrudedAreaSolid",
            SweptArea=profile,
            Position=self.ifc_file.create_entity(
                "IfcAxis2Placement3D",
                Location=self.ifc_file.create_entity(
                    "IfcCartesianPoint",
                    Coordinates=(0.0, 0.0, 0.0),
                ),
            ),
            ExtrudedDirection=self.ifc_file.create_entity(
                "IfcDirection",
                DirectionRatios=(0.0, 0.0, 1.0),
            ),
            Depth=thickness,
        )

        shape = self.ifc_file.create_entity(
            "IfcShapeRepresentation",
            ContextOfItems=self.context,
            RepresentationIdentifier="Body",
            RepresentationType="SweptSolid",
            Items=[solid],
        )

        slab = self.ifc_file.create_entity(
            "IfcSlab",
            GlobalId=self._guid(),
            OwnerHistory=self.owner_history,
            Name=f"Slab",
            ObjectPlacement=placement,
            Representation=self.ifc_file.create_entity(
                "IfcProductDefinitionShape",
                Representations=[shape],
            ),
            PredefinedType="FLOOR",
        )

        self.ifc_file.create_entity(
            "IfcRelContainedInSpatialStructure",
            GlobalId=self._guid(),
            OwnerHistory=self.owner_history,
            RelatingStructure=storey,
            RelatedElements=[slab],
        )
