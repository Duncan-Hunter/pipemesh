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

    gmsh.initialize()
    curve = pieces.Curve(
        0.25, [1, 0, 0], [0, 0, 1], 1, 0.1
    )
    assert(np.allclose(curve.out_surface.centre, np.array([1, 0, 1])))
    assert(np.allclose(curve.in_surface.centre, np.array([0, 0, 0])))
    assert(np.allclose(curve.out_surface.direction, np.array([0, 0, 1])))
    assert(np.allclose(curve.in_surface.direction, np.array([1, 0, 0])))
    gmsh.finalize()

    gmsh.initialize()
    mitered = pieces.Mitered(
        0.25, [1, 1, 0], [0, 0, 1], 0.1
        )
    assert(np.allclose(mitered.in_surface.direction, np.array([1, 1, 0])))
    assert(np.allclose(mitered.out_surface.direction, np.array([0, 0, 1])))
    gmsh.finalize()

    gmsh.initialize()
    t_junc = pieces.TJunction(
        0.3, 0.3, [0, 0, 1], [1, 0, 0], 0.1
    )
    assert(np.allclose(t_junc.in_surface.direction, np.array([0, 0, 1])))
    assert(np.allclose(t_junc.t_surface.direction, np.array([1, 0, 0])))
    gmsh.finalize()
    print("Indiviual pieces created correctly.")


def test5():
    """Tests if network updates after rotation."""
    network = pipes.Network(
        1, 0.25, [1, 0, 0], 0.1
    )
    network.add_curve([0, 0, 1], 1, 0.1)
    network.rotate_network([0, 1, 0], -np.pi/2)
    network.generate(run_gui=False)
    assert(np.allclose(
        network.out_surfaces[0].direction, np.array([-1, 0, 0])
        ))
    assert(np.allclose(
        network.in_surfaces[0].direction, np.array([0, 0, -1])
        ))
    print("Rotate whole network works correctly.")


def test6():
    """Tests creation of velocities."""
    network = pipes.Network(
        1, 0.25, [1, 1, 1], 0.1
    )
    network.add_t_junction([1,0,0], 0.1)
    network.generate(run_gui=False)
    velos = network.get_velocities_reynolds([1, 3], 10000, 1000, 1e-3)
    assert(np.allclose(velos[1], np.array([-0.02, 0, 0])))
    velos_2 = network.get_velocities_vel_mag([1, 3], 0.02)
    assert(np.allclose(velos_2[1], np.array([-0.02, 0, 0])))
    print("Get velocities methods working correctly.")


def test7():
    """Tests get_ids methods."""
    network = pipes.Network(
        1, 0.25, [1, 1, 1], 0.1
    )
    network.add_t_junction([1, 0, 0], 0.1)
    network.generate(run_gui=False)
    inlet_phys_ids = np.array(network.get_inlet_outlet_phys_ids())
    assert(np.allclose(inlet_phys_ids, np.array([1, 2, 3])))
    cyl_phys_ids = network.get_cyl_phys_ids()
    assert(np.allclose(np.array([cyl_phys_ids]), np.array([4, 5, 6, 7])))
    print("Get IDs method working correctly.")

test1()
test2()
test3()
test4()
test5()
test6()
test7()
