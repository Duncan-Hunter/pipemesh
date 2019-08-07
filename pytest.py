from pipemesh import pipes, pieces, gmsh
import os, sys
import numpy as np


def test1():
    """Tests if the msh file is correct.

    Generates a sideways network, then checks the version of the mesh
    file, then number of nodes, and the number of lines."""
    network = pipes.Network(
        1, 0.25, [1, 0, 0], 0.1
    )
    gmsh.model.mesh.generate(3)
    n_nodes = len(gmsh.model.mesh.getNodes()[0])
    assert(np.allclose(network.in_surfaces[0].centre, [0, 0, 0]))
    network.generate(filename="test")
    with open("test.msh", 'r') as testFile:
        content = testFile.readlines()
        assert(content[1][:3] == "2.2")
        assert(content[4][:3] == "{}".format(n_nodes))
        assert(len(content) == 1736)
    os.remove("test.msh")
    print("ASCII msh file working correctly.")


def test2():
    """Tests if binary msh file is correct."""
    network = pipes.Network(
        1, 0.25, [1, 0, 0], 0.1
    )
    gmsh.model.mesh.generate(3)
    n_nodes = len(gmsh.model.mesh.getNodes()[0])
    assert(np.allclose(network.in_surfaces[0].centre, [0, 0, 0]))
    network.generate(filename="test", binary=True)
    with open("test.msh", 'rb') as testFile:
        content = testFile.readlines()
        assert(content[1][:3] == b"2.2")
        assert(content[5][:3] == "{}".format(n_nodes).encode())
        assert(len(content) == 66)
    os.remove("test.msh")
    print("Binary msh file working correctly.")


def test3():
    """Tests if the mesh size is being changed."""
    network = pipes.Network(
        1, 0.25, [1, 0, 0], 0.2
    )
    network.add_cylinder(1, 0.1)
    gmsh.model.mesh.generate(3)
    n_nodes_before = len(gmsh.model.mesh.getNodes()[0])
    network.generate(filename="test", binary=False)
    with open("test.msh", 'r') as testFile:
        content = testFile.readlines()
        n_nodes_after = int(content[4][:3])
    os.remove("test.msh")
    assert(n_nodes_after > n_nodes_before)
    print("Mesh size set correctly.")


def test4():
    """Tests individual pieces."""
    gmsh.initialize()
    cyl = pieces.Cylinder(1, 0.5, [1, 0, 0], 0.1)
    assert(np.allclose(cyl.out_surface.centre, [1, 0, 0]))
    assert(np.allclose(cyl.in_surface.centre, [0, 0, 0]))
    gmsh.finalize()

    gmsh.initialize()
    change_radius = pieces.ChangeRadius(
        1, 0.8, 0.3, 0.2, [1, 0, 0], 0.1
    )
    assert(np.allclose(change_radius.out_surface.centre, [1, 0, 0]))
    assert(np.allclose(change_radius.in_surface.centre, [0, 0, 0]))
    gmsh.finalize()
    print("Indiviual pieces created correctly.")


test1()
test2()
test3()
test4()