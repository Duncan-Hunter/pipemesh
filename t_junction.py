from pipemesh import pieces, gmsh
import numpy as np

model = gmsh.model
factory = model.occ
mesh = model.mesh

fname = "junction"  # Can be changed

"""Pieces examples - uncomment one of the piece = commands and
the gmsh and mesh commands"""

gmsh.initialize()
gmsh.option.setNumber("Mesh.CharacteristicLengthMax", 0.5)

y_comp = np.sin(np.deg2rad(30))

piece = pieces.TJunction(4, 1, [0, 0, 1], [0, y_comp, 1], 0.5)

mesh.generate(3)

# gmsh.fltk.run()
gmsh.write("./t_junction.msh2")

gmsh.finalize()