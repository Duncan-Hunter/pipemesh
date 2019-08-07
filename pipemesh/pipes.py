"""
Create pipes and pipe networks using the Network class.

See the Readme for more details.
"""

# pylint: disable=C0411
# pylint: disable=R0913
# pylint: disable=E1101

from pipemesh import pieces, gmsh
import os
import numpy as np
import xml.etree.ElementTree as ET

MODEL = gmsh.model
FACTORY = MODEL.occ
MESH = MODEL.mesh


def _round_0(values):
    """Rounds values less than 1e-8 to 0."""
    values = np.array(values)
    values[np.abs(values) < 1e-8] = 0
    return values


def _check_intersect(objects, tools):
    """
    Currently unused.

    Check if entities in tools intersect entities in objects.
    objects: (list) 1st group of entities
    tools: (list) 2nd group of entities

    returns: (bool) True if there is an intersection.
                    False if there is no intersection.
    """
    intersect = FACTORY.intersect(objects,
                                  tools,
                                  removeObject=False,
                                  removeTool=False)[0]
    if intersect:
        return True
    return False


class Network():
    """Represents a pipe or network of pipes.

    Pipes are built from an inlet in a sequential, modular fashion.
    When a junction is added, a new "out surface" is added, which
    can be added to. In this way, a network of pipes can be built.

    Once the pipe has been made, the functions below can be used:
    network._set_physical_groups()  # for IC-FERST
    network._set_mesh_sizes()  # enforces lcar
    network.write_info("info.csv")  # for you and IC-FERST

    Attributes:
        physical_in_out_surfaces: Dictionary of Physical surface tags
            to GMSH surface tags for inlets/outlets.
        phyiscal_no_slip: Dictionary of Physical surface tags for
            walls/outside of cylinder.
        physical_volume: Physical tag of the volume. Only available
            after generate.
    """

    def __init__(self, length, radius, direction, lcar):
        """
        Creates the inlet cylinder of a pipe.

        This is the beginning of a pipe, from which you can add more
        pieces. This piece has the inlet surface, and stores the
        geometrical information of the pipe, such as what direction
        the outlet is facing, where it is, and what the radius of the
        pipe is.

        Args:
        length: (float) length of piece.
        radius: (float) radius of pipe.
        direction: (list) Direction pipe will be facing in x, y, z
            vector format.
        lcar: (float) Mesh size of this piece.
        """
        gmsh.initialize()
        gmsh.option.setNumber("Mesh.CharacteristicLengthMax", lcar)

        direction = np.array(direction)
        piece = pieces.Cylinder(length, radius, direction, lcar)
        piece.in_surface.direction *= -1

        self.piece_list = [piece]
        self.in_surfaces = [piece.in_surface]
        self.out_surfaces = [piece.out_surface]

        self.vol_tag = None  # Overall vol_tag, only after fuse.
        # dictionary of physical dim tags
        # to surface objects, which has information
        self.physical_in_out_surfaces = {}
        self.physical_no_slip = {}
        self.physical_volume = None

    def _set_mesh_sizes(self):
        """Sets the mesh size for all pieces."""
        field_list = []
        for piece in self.piece_list:
            half_length = np.abs(
                np.linalg.norm(piece.in_surface.centre - piece.vol_centre))
            field_length = np.linalg.norm(
                np.array([half_length, piece.in_surface.radius]))
            point = FACTORY.addPoint(*list(piece.vol_centre),
                                     meshSize=piece.lcar)
            FACTORY.synchronize()
            dist_field = MESH.field.add("Distance")
            MESH.field.setNumbers(dist_field, "NodesList", [point])
            thresh_field = MESH.field.add("Threshold")
            MESH.field.setNumber(thresh_field, "IField", dist_field)
            MESH.field.setNumber(thresh_field, "LcMin", piece.lcar)
            MESH.field.setNumber(thresh_field, "LcMax", 0.3)
            MESH.field.setNumber(thresh_field, "DistMin", field_length)
            MESH.field.setNumber(thresh_field, "DistMax", 1.1 * field_length)
            field_list.append(thresh_field)
        min_field = MESH.field.add("Min")
        MESH.field.setNumbers(min_field, "FieldsList", field_list)
        MESH.field.setAsBackgroundMesh(min_field)

    def _out_number(self, out_number):
        """Checks validity of out_number and changes to index form."""
        if out_number > len(self.out_surfaces):
            raise ValueError("Out piece does not exist")
        if out_number <= 0:
            out_number = 0
        else:  # Number to index
            out_number -= 1
        return out_number

    def add_cylinder(self, length, lcar, out_number=0):
        """Adds a pipe to the Network at the outlet.

        Args:
            length: (float) length of pipe.
            lcar: (float) mesh size of piece.
            out_number: Out surface to add to. If <= 1, will add to the
                first out surface.
        """
        out_number = self._out_number(out_number)
        out_surface = self.out_surfaces[out_number]
        piece = pieces.Cylinder(length, out_surface.radius,
                                out_surface.direction, lcar)
        translate_vector = out_surface.centre - piece.in_surface.centre
        FACTORY.translate([piece.vol_tag], *list(translate_vector))
        FACTORY.synchronize()
        piece.update_centres()
        self.piece_list.append(piece)
        self.out_surfaces[out_number] = piece.out_surface

    def add_curve(self, new_direction, bend_radius, lcar, out_number=0):
        """Adds a curve to the Network at the outlet.

        Args:
            new_direction: (list) Direction pipe will be facing
                in x, y, z vector format.
                e.g. [0, 1, 0] faces positive y.
            bend_radius: (float) Radius of the bend.
            lcar: (float) Size of mesh in this piece.
            out_number: Out surface to add to. If <= 1, will add to the
                first out surface.

        Raises:
            ValueError: new_direction vector isn't right size.
                Bend radius isn't big enough.
        """
        # Check input
        out_number = self._out_number(out_number)
        out_surface = self.out_surfaces[out_number]
        if len(new_direction) > 3:
            raise ValueError("""Array given is too long (should be length 3,
                for x, y, z)""")
        if bend_radius < 1.1 * out_surface.radius:
            raise ValueError("""Bend of radius is not large enough""")
        piece = pieces.Curve(out_surface.radius, out_surface.direction,
                             new_direction, bend_radius, lcar)
        translate_vector = out_surface.centre - piece.in_surface.centre
        FACTORY.translate([piece.vol_tag], *list(translate_vector))
        FACTORY.synchronize()
        piece.update_centres()
        self.piece_list.append(piece)
        self.out_surfaces[out_number] = piece.out_surface

    def add_mitered(self, new_direction, lcar, out_number=0):
        """Adds a mitered bend to the Network at the outlet.

        A mitered bend is a sharp change in direction. Hard to
        simulate.

        Args:
            new_direction: (list, length 3) xyz vector representing
                the new direction of the pipe.
            lcar: (float) size of mesh of this piece.
            out_number: Out surface to add to. If <= 1, will add to the
                first out surface.
        """
        out_number = self._out_number(out_number)
        out_surface = self.out_surfaces[out_number]
        piece = pieces.Mitered(out_surface.radius, out_surface.direction,
                               new_direction, lcar)
        translate_vector = out_surface.centre - piece.in_surface.centre
        FACTORY.translate([piece.vol_tag], *list(translate_vector))
        FACTORY.synchronize()
        piece.update_centres()
        self.piece_list.append(piece)
        self.out_surfaces[out_number] = piece.out_surface

    def add_change_radius(self,
                          length,
                          new_radius,
                          change_length,
                          lcar,
                          out_number=0):
        """Adds a piece that changes the radius of the outlet.

        The piece is length long, and changes the Network radius to
        new_radius, over change_length, which controls how gentle the
        change is.

        Args:
            length: (float) Length of the piece.
            new_radius: (float) radius to change to.
            change_length: (float) Length that the change takes
                place over. Must be less than length and > 0.
            lcar: (float) mesh size for this piece.
            out_number: Out surface to add to. If <= 1, will add to the
                first out surface.

        Raises:
            ValueErrors: change_length is not between length and 0.
                If radius does not change.
        """
        out_number = self._out_number(out_number)
        out_surface = self.out_surfaces[out_number]
        if change_length >= length:
            raise ValueError('change_length must be less than length')
        if change_length < 0:
            raise ValueError('change_length must be greater than 0')
        if new_radius == out_surface.radius:
            raise ValueError("Radius is not different from old radius")
        piece = pieces.ChangeRadius(length, change_length, out_surface.radius,
                                    new_radius, out_surface.direction, lcar)
        translate_vector = out_surface.centre - piece.in_surface.centre
        FACTORY.translate([piece.vol_tag], *list(translate_vector))
        FACTORY.synchronize()
        piece.update_centres()
        self.piece_list.append(piece)
        self.out_surfaces[out_number] = piece.out_surface

    def add_t_junction(self, t_direction, lcar, t_radius=-1, out_number=0):
        """Adds a T junction to the Network at the outlet.

        This represents a pipe joining this pipe, creating a place to
        add a Network to this Network.

        Args:
            t_direction: (list, length 3) representing the direction
                that the joining pipe's inlet is facing.
            lcar: (float) mesh size for this piece.
            t_radius: radius of the piece joining the pipe. If <= 0, will
                default to radius of the pipe.
            out_number: Out surface to add to. If <= 1, will add to the
                first out surface.
        """

        out_number = self._out_number(out_number)
        out_surface = self.out_surfaces[out_number]

        if t_radius <= 0:
            t_radius = out_surface.radius

        piece = pieces.TJunction(out_surface.radius, t_radius,
                                 out_surface.direction, t_direction, lcar)
        translate_vector = out_surface.centre - piece.in_surface.centre
        FACTORY.translate([piece.vol_tag], *list(translate_vector))
        FACTORY.synchronize()
        piece.update_centres()
        self.piece_list.append(piece)
        self.out_surfaces.append(piece.t_surface)
        self.out_surfaces[out_number] = piece.out_surface

    def _fuse_objects(self):
        """Fuses separate objects in Network together.

        Returns
            no_slip: (list) The dimtags of in and out surfaces.
        """
        if len(self.piece_list) == 1:
            piece = self.piece_list[0]
            no_slip = [MODEL.getBoundary([piece.vol_tag], False)[0]]
            self.vol_tag = piece.vol_tag
            return no_slip

        if self.vol_tag:
            raise ValueError("Network already fused")

        vol_tags = [piece.vol_tag for piece in self.piece_list]

        if _check_intersect([vol_tags[0]], vol_tags[1:]):
            raise ValueError("Pieces overlap")

        out_dim_tags = FACTORY.fuse([vol_tags[0]], vol_tags[1:])[0]
        FACTORY.synchronize()
        self.vol_tag = out_dim_tags[0]
        for piece in self.piece_list:
            piece.vol_tag = None
        surfaces = MODEL.getBoundary([self.vol_tag], False)
        tot_in = len(self.in_surfaces)
        tot_out = len(self.out_surfaces)
        found_in = 0
        found_out = 0
        no_slip = []
        for surf in surfaces:
            added = False
            loc = np.array(FACTORY.getCenterOfMass(*surf))
            if found_in < tot_in:
                for in_surf in self.in_surfaces:
                    if np.allclose(loc, in_surf.centre):
                        in_surf.dimtag = surf
                        found_in += 1
                        added = True
            if found_out < tot_out and not added:
                for out_surf in self.out_surfaces:
                    if np.allclose(loc, out_surf.centre):
                        out_surf.dimtag = surf
                        found_out += 1
                        added = True
            if not added:
                no_slip.append(surf)
        return no_slip

    def _set_physical_groups(self):
        """Sets the physical groups of the network.

        Sets every surface to a physical surface, and the volume
        to a physical volume."""
        no_slip = self._fuse_objects()
        for dimtag in no_slip:
            phys_tag = MODEL.addPhysicalGroup(2, [dimtag[1]])
            self.physical_no_slip[phys_tag] = dimtag
        for surface in self.in_surfaces + self.out_surfaces:
            phys_tag = MODEL.addPhysicalGroup(2, [surface.dimtag[1]])
            self.physical_in_out_surfaces[phys_tag] = surface
        self.physical_volume = MODEL.addPhysicalGroup(3, [self.vol_tag[1]])

    def rotate_network(self, axis, angle):
        """Rotates the network from old_direction to new_direction.

        Args:
            axis: (array-like, shape (3,)) xyz vector representing the
                axis of rotation.
            angle: angle to rotate network about axis.
        """
        rot_axis = np.array(axis)
        dimtags = []
        for piece in self.piece_list:
            dimtags.append(piece.vol_tag)
        FACTORY.rotate(dimtags, 0, 0, 0, *list(rot_axis), angle)
        FACTORY.synchronize()
        for piece in self.piece_list:
            piece.update_centres()
            piece.update_directions(rot_axis, angle)

    def translate_network(self, vector):
        """Translates a network by vector.

        Args:
            vector: (list length 3) representing xyz vector to
                translate network by."""
        vector = np.array(vector)
        dimtags = []
        for piece in self.piece_list:
            dimtags.append(piece.vol_tag)
        FACTORY.translate(dimtags, *list(vector))
        FACTORY.synchronize()
        for piece in self.piece_list:
            piece.update_centres()

    def generate(self,
                 filename=None,
                 binary=False,
                 mesh_format='msh2',
                 write_info=False,
                 write_xml=False,
                 run_gui=False):
        """Generates mesh and saves if filename.

        Args:
            filename: (string) filename (without extension) to save as.
            binary: (Bool) Save mesh as binary or not. Default (False).
            mesh_format: (string) mesh format to save as. Default is
                msh2. To save as msh4, use 'msh4'.
            write_info: (Bool) write filename.txt with mesh
                mesh information (physical surfaces, locations
                and directions).
            write_xml: (Bool) write information in an xml file. Still
                under development.
            run_gui: (Bool) run the gmsh gui to view the mesh. May
                stop saving of information/meshes.
        """
        self._set_mesh_sizes()
        self._set_physical_groups()
        MESH.generate(3)
        if filename:
            if binary:
                gmsh.option.setNumber("Mesh.Binary", 1)
            else:
                gmsh.option.setNumber("Mesh.Binary", 0)
            name = filename + "." + mesh_format
            gmsh.write(name)
            os.rename(name, filename + ".msh")
        if write_info:
            self._write_info(filename + ".txt")
        if write_xml:
            self._write_xml(filename)
        if run_gui:
            gmsh.option.setNumber("General.Axes", 2)
            gmsh.option.setNumber("Mesh.SurfaceFaces", 1)
            gmsh.fltk.run()
        gmsh.finalize()

    def _write_info(self, fname):
        """Writes network info into file fname.

        Writes Inlet/Outlet physical surface numbers, centres, and outwards
        normals. Then writes details about cylinders.
        """
        with open(fname, 'w') as myfile:
            myfile.writelines("Physical Surface, Centre, Outward Direction")
            myfile.writelines("\nInOut Surfaces")
            for key, surf in self.physical_in_out_surfaces.items():
                myfile.writelines("\n{}\t{}\t{}".format(
                    key, _round_0(surf.centre), _round_0(surf.direction)))
            myfile.writelines("\nCylinder Surfaces")
            for key, dimtag in self.physical_no_slip.items():
                centre = np.array(FACTORY.getCenterOfMass(2, dimtag[1]))
                myfile.writelines("\n{}\t{}".format(key, centre))
            myfile.writelines("\nIntersection locations and directions")
            for piece in self.piece_list:
                myfile.writelines("\n{}\t{}".format(
                    np.array(piece.out_surface.centre),
                    piece.out_surface.direction))
                if hasattr(piece, 't_surface'):
                    myfile.writelines("\n{}\t{}".format(
                        np.array(piece.t_surface.centre),
                        piece.t_surface.direction))
            myfile.close()

    def _write_xml(self, fname):
        """Writes information as xml tree."""
        root = ET.Element('root')
        inlet_surfs = ET.SubElement(root, "inlet_surfaces")
        for key, surf in self.physical_in_out_surfaces.items():
            surf = ET.SubElement(inlet_surfs,
                                 "{}".format(key),
                                 attrib={
                                     "centre":
                                     np.array2string(np.array(surf.centre)),
                                     "outward_direction":
                                     np.array2string(np.array(surf.direction))
                                 })
        cyl_surfs = ET.SubElement(root, "cylinder_surfaces")
        for key, dimtag in self.physical_no_slip.items():
            centre = np.array2string(
                np.array(FACTORY.getCenterOfMass(2, dimtag[1])))
            surf = ET.SubElement(cyl_surfs,
                                 "{}".format(key),
                                 attrib={"centre": centre})
        volume = ET.SubElement(root, "volume")
        volume.text = str(self.vol_tag)
        ET.ElementTree(root).write(fname + ".xml", encoding='utf-8')
