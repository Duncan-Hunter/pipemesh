"""Base classes for cylindrical GMSH pieces.

Also contains useful functions for these classes.
"""
# pylint: disable=C0411
# pylint: disable=R0913
from pipemesh import gmsh
import numpy as np
from scipy.spatial.transform import Rotation

MODEL = gmsh.model
FACTORY = MODEL.occ
MESH = MODEL.mesh


def vec_angle(vec1, vec2):
    """Returns the angle between two numpy array vectors"""
    return np.arccos(
        np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)))


def proj(vec1, vec2):
    """
    Returns the component of vec1 along vec2

    Args:
        vec1, vec2: (np.array shape 3) xyz vector.
    """
    return np.dot(vec1, vec2) / np.linalg.norm(vec2)


def _rotate_inlet(vol_tag, in_direction, out_direction):
    """Rotates up facing inlet to face in_direction.

    Calculates the new outlet direction after it has been
    transformed.

    Args:
        vol_tag: dimtag tuple of volume being rotated.
        in_direction: xyz array direction to rotate the inlet to.
        out_direction: Direction the outlet is facing before
            rotation.

    Returns:
        new_out_direction: Direction outlet is facing after
            rotation as xyz array.
    """
    up_vector = np.array([0, 0, 1])
    # only have to rotate if its not facing up
    if np.allclose(in_direction, up_vector) is False:
        rotate_axis = np.cross(up_vector, in_direction)
        if np.allclose(rotate_axis, np.zeros(3)):
            rotate_axis = np.array([1, 0, 0])
        rotate_axis = rotate_axis / np.linalg.norm(rotate_axis)
        rotate_angle = vec_angle(in_direction, up_vector)
        FACTORY.rotate([vol_tag], *[0, 0, 0], *list(rotate_axis), rotate_angle)
        FACTORY.synchronize()
        rot_vec = rotate_angle * rotate_axis
        rot1 = Rotation.from_rotvec(rot_vec)
        new_out_direction = rot1.apply(out_direction)
    else:
        new_out_direction = out_direction
    return new_out_direction


def _rotate_outlet(vol_tag, out_direction, in_direction, new_out_direction):
    """Rotates outlet about in_direction to face out_direction.

        Projects new_out_direction and out_direction onto basis axes
        that are perpendicular to each other and in_direction. The
        angle between the projections is found, and the object is
        rotated.

        Args:
            vol_tag: dimtag tuple of volume being rotated.
            out_direction: xyz array, the direction that the outlet
                will face after being rotated.
            in_direction: xyz array, the direction that the inlet is
                facing, and the axis that the object will be rotated
                about.
            new_out_direction: xyz array, the direction that the outlet
                faces before being rotated.
                Returned from _rotate_inlet.
        """
    basis_1 = np.cross(
        out_direction, in_direction
    )  # basis vectors perpendicular to direction (rotation axis)
    basis_2 = np.cross(basis_1,
                       in_direction)  # and perpendicular to other basis
    # Before rotation projection.
    alpha = np.array(
        [proj(new_out_direction, basis_1),
         proj(new_out_direction, basis_2)])
    # After rotation projection.
    beta = np.array(
        [proj(out_direction, basis_1),
         proj(out_direction, basis_2)])
    # Find angle between two vectors in bases.
    rot2_angle = vec_angle(alpha, beta)
    cross = np.cross(new_out_direction, out_direction)
    if np.dot(in_direction, cross) > 0:
        rot2_angle *= -1
    FACTORY.rotate([vol_tag], *[0, 0, 0], *list(in_direction), -rot2_angle)
    FACTORY.synchronize()


class Surface():
    """Class representing a surface of a piece.

    Pieces are PipePieces, and are all cylindrical in nature,
    which is why the pieces have radius.
    """

    def __init__(self, dimtag, centre, direction, radius):
        """Inits the surface."""
        self.dimtag = dimtag
        self.centre = centre
        self.direction = np.array(direction)
        self.radius = radius

    def _update_direction(self, axis, angle):
        """Rotates the direction vector by angle about axis."""
        rotvec = Rotation.from_rotvec(angle * axis)
        self.direction = rotvec.apply(self.direction)

    def _update_centre(self):
        self.centre = FACTORY.getCenterOfMass(*self.dimtag)


class PipePiece():
    """Parent class of pieces.

    Pieces are GMSH objects that can be used in creating pipes.
    This class has common information that all pieces have, such as
    radius. It also has functions that all the classes use, such as the
    need to update centres of pieces after they have been transformed.
    """

    def __init__(self, radius, vol_tag, in_tag, out_tag, in_direction,
                 out_direction, lcar):
        """Stores the information of a created piece.

        Args:
            radius: (float) radius of the piece.
            vol_tag: (tuple, length 2) GMSH dimtag (dimension, tag)
                representing volume.
            in_tag: (tuple, length 2) GMSH dimtag representing in surface
            out_tag: (tuple, length 2) GMSH dimtag representing out surface
            in_direction: (np array, shape 3) xyz vector representing
                direction going in.
            out_direction: (np array, shape 3) xyz vector representing
                direction going out.
            lcar: (float) mesh size of the piece.
        """
        self.lcar = lcar
        self.vol_tag = vol_tag
        self.vol_centre = np.array(FACTORY.getCenterOfMass(*vol_tag))
        in_centre = np.array(FACTORY.getCenterOfMass(*in_tag))
        out_centre = FACTORY.getCenterOfMass(*out_tag)
        self.in_surface = Surface(in_tag, in_centre, in_direction, radius)
        self.out_surface = Surface(out_tag, out_centre, out_direction, radius)

    def _update_surfaces(self):
        """Updates the dimtag of surfaces after a transformation.

        This function is overriden for every piece, as the order
        in which surfaces are assigned tags is different for different
        pieces."""
        surfaces = MODEL.getBoundary([self.vol_tag], combined=False)
        self.in_surface.dimtag = surfaces[2]
        self.out_surface.dimtag = surfaces[1]

    def _update_centres(self):
        """Updates centres of surfaces after a transformation."""
        self._update_surfaces()
        self.vol_centre = np.array(FACTORY.getCenterOfMass(*self.vol_tag))
        self.in_surface._update_centre()
        self.out_surface._update_centre()

    def _update_directions(self, axis, angle):
        """Updates the direction of surfaces after a transformation."""
        self.out_surface._update_direction(axis, angle)
        self.in_surface._update_direction(axis, angle)


class Cylinder(PipePiece):
    """
    Class representing a GMSH cylinder with base at 0,0,0 facing upwards.
    """

    def __init__(self, length, radius, direction, lcar):
        """Creates the cylinder with GMSH.

        Args:
            length: (float) length of cylinder.
            radius: (float) radius of cylinder.
            direction: (list, length 3) xyz vector representing direction
                cylinder is facing.
            lcar: (float) mesh size for this piece.
        """
        self.length = length
        self.lcar = lcar
        vol_tag = (3, FACTORY.addCylinder(0, 0, 0, 0, 0, length, radius))
        FACTORY.synchronize()
        surfaces = MODEL.getBoundary([vol_tag], False)
        in_tag = surfaces[2]
        out_tag = surfaces[1]

        direction = np.array(direction)

        _rotate_inlet(vol_tag, direction, direction)

        super(Cylinder, self).__init__(radius, vol_tag, in_tag, out_tag,
                                       direction, direction, lcar)

    def _update_surfaces(self):
        """See base class."""
        surfaces = MODEL.getBoundary([self.vol_tag], combined=False)
        self.in_surface.dimtag = surfaces[2]
        self.out_surface.dimtag = surfaces[1]


class ChangeRadius(PipePiece):
    """Class representing a cylinder with a change in radius."""

    def __init__(self, length, change_length, in_radius, out_radius, direction,
                 lcar):
        """Inits the piece.

        Args:
            length: (float) length of piece.
            change_length: (float) length over which the change in
                radius takes place.
            in_radius: (float) radius of cylinder at "inlet".
            out_radius: (float) radius of cylinder at "outlet".
            direction: (list, length 3) xyz vector representing direction
                cylinder outlet is facing.
            lcar: (float) mesh size for this piece.
        """
        if change_length >= length:
            raise ValueError('change_length must be less than length')
        if change_length < 0:
            raise ValueError('change_length must be greater than 0')
        if out_radius > in_radius:
            vol_tag = (3, FACTORY.addCylinder(0, 0, 0, 0, 0, length,
                                              out_radius))
        else:
            vol_tag = (3, FACTORY.addCylinder(0, 0, 0, 0, 0, length,
                                              in_radius))
        FACTORY.synchronize()
        surfaces = MODEL.getBoundary([vol_tag], False)
        in_tag = surfaces[2]
        out_tag = surfaces[1]

        if out_radius > in_radius:
            lines = MODEL.getBoundary([in_tag], False, False)
            FACTORY.chamfer([vol_tag[1]], [lines[0][1]], [in_tag[1]],
                            [out_radius - in_radius, change_length])
            FACTORY.synchronize()
            self.increase = True
        else:
            lines = MODEL.getBoundary(out_tag, False, False)
            FACTORY.chamfer([vol_tag[1]], [lines[0][1]], [out_tag[1]],
                            [in_radius - out_radius, change_length])
            FACTORY.synchronize()
            self.increase = False

        direction = np.array(direction)

        _rotate_inlet(vol_tag, direction, direction)

        surfaces = MODEL.getBoundary([vol_tag], False)
        if self.increase:
            in_tag = surfaces[3]
            out_tag = surfaces[2]
        else:
            in_tag = surfaces[2]
            out_tag = surfaces[3]

        super(ChangeRadius, self).__init__(out_radius, vol_tag, in_tag,
                                           out_tag, direction, direction, lcar)

    def _update_surfaces(self):
        """See base class."""
        surfaces = MODEL.getBoundary([self.vol_tag], combined=False)
        if self.increase:
            self.in_surface.dimtag = surfaces[3]
            self.out_surface.dimtag = surfaces[2]
        else:
            self.in_surface.dimtag = surfaces[2]
            self.out_surface.dimtag = surfaces[3]


class Curve(PipePiece):
    """Class representing a GMSH curve by revolution."""

    def __init__(self, radius, in_direction, out_direction, bend_radius, lcar):
        """Inits the piece.

        Initially with inlet facing down, and outlet facing in x-plane.

        Args:
            radius: (float) radius of the pipe
            in_direction: (list, length 3) xyz vector representing
                direction going in.
            out_direction: (list, length 3) xyz vector representing
                direction going out.
            bend_radius: (float) radius of the bend of the curve.
            lcar: (float) mesh size for this piece.
        """
        in_tag = (2, FACTORY.addDisk(0, 0, 0, radius, radius))
        in_direction = np.array(in_direction)
        out_direction = np.array(out_direction)

        revolve_axis = [0, 1, 0]
        centre_of_rotation = [bend_radius, 0, 0]
        angle = vec_angle(in_direction, out_direction)
        # Revolve in x plane, bend with radius bend_radius
        revolve_tags = FACTORY.revolve([in_tag], *centre_of_rotation,
                                       *revolve_axis, angle)
        FACTORY.synchronize()

        vol_tag = revolve_tags[1]

        new_out_direction = np.array(
            [np.sin(np.pi - angle), 0,
             -np.cos(np.pi - angle)])  # direction out is currently facing
        # Rotate so in_direction faces right way "Rot1"
        new_out_direction = _rotate_inlet(vol_tag, in_direction,
                                          new_out_direction)
        # Rotate so out_direction faces right way "Rot2"
        _rotate_outlet(vol_tag, out_direction, in_direction, new_out_direction)

        surfaces = MODEL.getBoundary([vol_tag], False, True)
        out_tag = surfaces[2]
        in_tag = surfaces[1]
        super(Curve, self).__init__(radius, vol_tag, in_tag, out_tag,
                                    in_direction, out_direction, lcar)

        # FACTORY.synchronize()
    def _update_surfaces(self):
        """See base class."""
        surfaces = MODEL.getBoundary([self.vol_tag], combined=False)
        self.in_surface.dimtag = surfaces[1]
        self.out_surface.dimtag = surfaces[2]


class Mitered(PipePiece):
    """Class representing a mitered (sharp) pipe bend.

    Piece creation is done by masking (intersect) a cylinder with a
    chamfered box. The piece is then mirrored, rotated and fused.

    The piece is then rotated to face the direction of the outflow.
    It is then rotated about the direction of outflow to match the new direction
    """

    def __init__(self, radius, in_direction, out_direction, lcar):
        """Creates the GMSH piece.

        The inlet is facing up originally.

        Args:
            radius: (float) radius of the pipe.
            in_direction: (list, length 3) xyz vector representing
            direction going in.
            out_direction: (list, length 3) xyz vector representing
            direction going out.
            lcar: (float) mesh size for this piece.

        """
        in_direction = np.array(in_direction)
        out_direction = np.array(out_direction)  # clean up v's

        # Chamfer cylinder
        angle = vec_angle(out_direction, in_direction)
        height = 2.1 * radius * np.tan(angle / 2)
        new_out_direction = np.array(
            [np.sin(np.pi - angle), 0,
             -np.cos(np.pi - angle)])  # original outlet direction in xz plane
        cyl1 = (3, FACTORY.addCylinder(0, 0, 0, 0, 0, height,
                                       radius))  # create cylinder
        box1 = (3,
                FACTORY.addBox(-radius - 1, -radius, -1, 2 * radius + 1,
                               2 * radius, height + 1))  # create box
        FACTORY.synchronize()
        surface = MODEL.getBoundary([box1], False,
                                    False)[5]  # Top surface to chamfer from
        line = MODEL.getBoundary([surface], False, False)[2]  # -x line on top
        sdist = 2 * radius * np.tan(
            angle / 2)  # distances to chamfer to get correct angle
        #ldist = 2*radius*np.cos(angle/2)
        FACTORY.chamfer([box1[1]], [line[1]], [surface[1]],
                        [2 * radius, sdist])  # chamfer
        int_tag = FACTORY.intersect([box1],
                                    [cyl1])  # intersect (chamfer on cylinder)
        fuse = FACTORY.fuse([int_tag[0]], int_tag[1:])[0]  # fuse
        fuse2 = FACTORY.copy([fuse])  # create copy and mirror
        FACTORY.symmetrize([fuse2], 1, 0, 0, 0)
        FACTORY.synchronize()
        surface = MODEL.getBoundary([fuse2], False,
                                    False)[1]  # get center of rotation
        com = FACTORY.getCenterOfMass(*surface)
        FACTORY.rotate([fuse2], *com, 0, 1, 0,
                       -(np.pi - angle))  # rotate to create piece
        vol_tag = FACTORY.fuse([fuse], [fuse2],
                               removeObject=True,
                               removeTool=True)[0][0]  # fuse
        FACTORY.synchronize()

        surfaces = MODEL.getBoundary([vol_tag], False)
        in_tag = surfaces[3]  # bottom
        out_tag = surfaces[6]  # angled

        # Rot1: rotate object so inlet faces correct direction
        new_out_direction = _rotate_inlet(vol_tag, in_direction,
                                          new_out_direction)
        #Rot2
        _rotate_outlet(vol_tag, out_direction, in_direction, new_out_direction)
        super(Mitered, self).__init__(radius, vol_tag, in_tag, out_tag,
                                      in_direction, out_direction, lcar)

    def _update_surfaces(self):
        """See base class."""
        surfaces = MODEL.getBoundary([self.vol_tag], combined=False)
        self.in_surface.dimtag = surfaces[3]
        self.out_surface.dimtag = surfaces[6]


class TJunction(PipePiece):
    """Class representing a T-junction in GMSH"""

    def __init__(self, radius, t_radius, direction, t_direction, lcar):
        """Inits the piece

        Creates a piece with the t_direction facing in the x-plane and
        inlet facing up.

        Args:
            radius: (float) radius of the pipe.
            t_radius: (float) radius of the joining pipe.
            direction: (list, length 3) xyz vector representing
                direction going in.
            t_direction: (list, length 3) xyz vector represeting the
                direction that the junction inlet faces.
            lcar: (float) mesh size for this piece.
        """
        if t_radius > radius:
            raise ValueError("t_radius cannot be bigger than radius")
        direction = np.array(direction)
        t_angle = vec_angle(direction, t_direction)
        if t_angle > np.pi/2:
            self.inv_surfs = True
            beta = abs(t_angle) - np.pi / 2
        else:
            self.inv_surfs = False
            beta = np.pi / 2 - abs(t_angle)

        height = radius * np.tan(beta) + radius / np.cos(beta)
        height_short = radius * abs(np.cos(beta))
        # Calculating height needed to emerge from merge

        in_tag = (3, FACTORY.addCylinder(0, 0, 0, 0, 0, 1.1 * height, radius))
        mid_tag = (3, FACTORY.addCylinder(0, 0, 0, 1.1 * height, 0, 0, t_radius))
        out_tag = (3, FACTORY.addCylinder(0, 0, 0, 0, 0, -1.1 * height_short,
                                          radius))

        FACTORY.rotate([mid_tag], 0, 0, 0, 0, 1, 0, -beta)
        FACTORY.synchronize()

        vol_tags = FACTORY.fuse([in_tag], [mid_tag, out_tag])[0]
        vol_tag = vol_tags[0]
        FACTORY.synchronize()

        surfaces = MODEL.getBoundary([vol_tag], False)

        if self.inv_surfs:
            FACTORY.rotate([vol_tag], 0,0,0, 1, 0, 0, np.pi)
            FACTORY.synchronize()
            mid_direction = np.array([np.cos(beta),0,-np.sin(beta)])
            in_tag = surfaces[3]
            out_tag = surfaces[5]
        else:
            mid_direction = np.array([np.cos(beta),0,np.sin(beta)])
            in_tag = surfaces[5]
            out_tag = surfaces[3]
        t_tag = surfaces[4]
        t_centre = FACTORY.getCenterOfMass(2, t_tag[1])

        mid_direction = _rotate_inlet(vol_tag, direction, mid_direction)

        _rotate_outlet(vol_tag, t_direction, direction, mid_direction)

        super(TJunction,
              self).__init__(radius, vol_tag, in_tag, out_tag,
                             direction, direction, lcar)

        self.t_surface = Surface(t_tag, t_centre, t_direction, t_radius)

    def _update_surfaces(self):
        """See base class."""
        surfaces = MODEL.getBoundary([self.vol_tag], combined=False)
        if self.inv_surfs:
            self.in_surface.dimtag = surfaces[3]
            self.out_surface.dimtag = surfaces[5]
        else:
            self.in_surface.dimtag = surfaces[5]
            self.out_surface.dimtag = surfaces[3]
        self.t_surface.dimtag = surfaces[4]

    def _update_centres(self):
        """See base class."""
        self.vol_centre = np.array(FACTORY.getCenterOfMass(*self.vol_tag))
        self.in_surface.centre = np.array(
            FACTORY.getCenterOfMass(*self.in_surface.dimtag))
        self.out_surface.centre = np.array(
            FACTORY.getCenterOfMass(*self.out_surface.dimtag))
        self.t_surface.centre = np.array(
            FACTORY.getCenterOfMass(*self.t_surface.dimtag))

    def _update_directions(self, axis, angle):
        """See base class."""
        self.out_surface._update_direction(axis, angle)
        self.in_surface._update_direction(axis, angle)
        self.t_surface._update_direction(axis, angle)
