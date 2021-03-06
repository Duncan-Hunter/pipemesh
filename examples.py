"""
Author: Duncan Hunter
"""
from pipemesh import pipes, pieces, gmsh
import os
import numpy as np

model = gmsh.model
factory = model.occ
mesh = model.mesh

fname = "junction"  # Can be changed

"""Pieces examples - uncomment one of the piece = commands and
the gmsh and mesh commands"""

# gmsh.initialize()
# gmsh.option.setNumber("Mesh.CharacteristicLengthMax", 0.1)
"""Piece classes"""
# piece = pieces.Cylinder(1, 0.5, [0,0,1], 0.1)
# piece = pieces.ChangeRadius(2,1.8, 0.3, 0.2, [1,0,0], 0.1)
# piece = pieces.Mitered(0.5, [1,0,0], [0,1,0], 0.2)
# piece = pieces.Curve(0.5, [1,0,-1], [0,1,0], 1, 0.2)
# piece = pieces.TJunction(0.5, 0.3, [1, 0,0], [-2,1, 0], 0.1)

# mesh.generate(3)
# gmsh.fltk.run()
# gmsh.finalize()

"""Network examples. Uncomment start network, a group of commands,
and generate."""
"""Start a network"""
# network = pipes.Network(0.5, 0.5, [0,0,-1], 0.1)

"""Create pipe with junctions"""
# network.add_t_junction([-3,1,0], 0.05, t_radius=0.2)
# network.add_t_junction([-1,-1,0], 0.05, t_radius=0.2)
# network.add_cylinder(1, 0.05, out_number=2)
# network.add_curve([-1,0,0], 0.5, 0.05, out_number=3)
# network.add_cylinder(1.5, 0.1, out_number=3)

"""Hufnagel (2016)"""
# r = 0.3
# network = wrapper.pipes.Network(0.2, r, [1,0,0], 0.1)
# network.add_cylinder(7*2*r, 0.1)
# network.add_curve([0, 0, -1], r/0.1, 0.1)
# network.add_cylinder(15*2*r, 0.1)

"""Chicane"""
# network.add_curve([0,-1,0], 0.4, 0.1)
# network.add_cylinder(5, 0.2)
# network.add_curve([0, 0, -1], 2, 0.1)
# network.add_cylinder(10,0.2)

"""U bend positive x to -x, through -y"""
#network.add_pipe(1, 0.2)
#network.add_curve([0, -1, 0], [0, -1, 0], 0.1)
#network.add_curve([-1, 0, 0], [-1, 0, 0], 0.1)
#network.add_pipe(1, 0.2)

"""U bend with changing radius"""
#network.change_radius(1, 0.4, 0.7)
#network.add_curve([0, -1, 0], [0, -1, 0], 0.1)
#network.add_curve([-1, 0, 0], [-1, 0, 0], 0.1)
#network.change_radius(1, 0.5, 0.2)

"""Sharp Chicane"""
# network.add_cylinder(0.2, 0.1)
# network.add_mitered([0,-1,0], 0.06)
# network.add_cylinder(0.4, 0.1)
# network.add_mitered([0,0,-1], 0.1)
# network.add_cylinder(0.2, 0.1)

"""Helix"""
# for i in range(3):
#     network.add_curve([0, 1, -0.25], 1, 0.1)
#     network.add_curve([-1, 0, -0.25], 1, 0.1)
#     network.add_curve([0, -1, -0.25], 1, 0.1)
#     network.add_curve([1, 0, -0.25], 1, 0.1)


# network.generate(filename=None, binary=False, write_info=False, write_xml=False, run_gui=True)
