# pipemesh
These tools use the GMSH-SDK (or GMSH API), available [here](http://gmsh.info/).

The documentation for pipemesh can be found [here](https://pipemesh.readthedocs.io/en/latest/).

## Installation
```python
python3 -m pip install --user pipemesh
```

Once completed, navigate to site-packages/pipemesh. Place the files libgmsh.so, libgmsh.so.4.3 and libgmsh.so.4.3.0, which can be downloaded from the GMSH website (link above).


### pieces.py
Contains classes (and some useful functions for said classes) which represent cylindrical GMSH objects. The classes store information of the object, such as the centre and direction of its faces, as well as functions to update the information when transformations are applied to them. This makes the information a little easier to access than using just the GMSH API. To use these individually start your file with:

```python
from pipemesh import pieces
model = gmsh.model
mesh = model.mesh
gmsh.initialize()
gmsh.option.setNumber("Mesh.CharacteristicLengthMax", 0.1)  # max mesh length
model.add("Example")  # optional, add a model name.
```

The available pieces to put in are:
* Cylinder
![cylinder](https://raw.githubusercontent.com/Duncan-Hunter/pipemesh/master/pipemesh/images/cylinder.png)
```python
piece = pieces.Cylinder(1, 0.5, [1,0,0], 0.1)
# Length, radius, direction, mesh size
```
* Cylinder with changing radius
![change_rad](https://raw.githubusercontent.com/Duncan-Hunter/pipemesh/master/pipemesh/images/change_radius.png)
```python
piece = pieces.ChangeRadius(2, 1.8, 0.3, 0.2, [1 ,0, 0], 0.1)
# length, change length, start radius, end radius, direction, mesh size
```
* Smooth bends
![bend](https://raw.githubusercontent.com/Duncan-Hunter/pipemesh/master/pipemesh/images/bend.png)
```python
piece = pieces.Curve(0.5, [1,0,-1], [0,1,0], 1, 0.2)
# radius of cylinder, in direction, out direction, bend radius, mesh size
```
* Mitered bends
![mitered](https://raw.githubusercontent.com/Duncan-Hunter/pipemesh/master/pipemesh/images/mitered.png)
```python
piece = pieces.Mitered(0.5, [0, 1, 0], [1, 0, 0], 0.2)
# radius of cylinder, in direction, out direction, mesh size
```
* T Junctions
![t_junc](https://raw.githubusercontent.com/Duncan-Hunter/pipemesh/master/pipemesh/images/t_junc.png)
```python
piece = pieces.TJunction(0.5, [1, 0, 0], [1, 1, -1], 0.1)
# radius, direction, t direction, mesh size
```

The mesh can be created and saved using:
```python
mesh.generate(3)
gmsh.option.setNumber("Mesh.Binary", 1)  # 1 for binary, 0 for ASCII
gmsh.write(filename.msh)  # .msh2 for legacy format
```

To view the mesh in the GMSH GUI, call
```python
gmsh.fltk.run()
```

To finish, and end use of gmsh, call
```python
gmsh.finalize()
```

As of yet, just using the pieces on their own is limited, as they do not have translate, or rotate functions, but if desired, the user can look into the GMSH-SDK and develop some, or use pipes (below) to generate pipe meshes.

### pipes.py
Using the pieces above and the Network class, pipes and pipe networks can be easily built. A Network is started with:
```python
from pipemesh import pipes
network = pipes.Network(1, 0.3, [1,0,0], 0.1)
```
Then added to using one of the following commands:
```python
network.add_cylinder(1, 0.1, out_number=1)
network.add_t_junction([-1,-1,0], 0.05)
network.add_curve([0,1,0], 0.5, 0.05)
network.add_mitered([0, 1, 0], 0.05, out_number=2)
```
Where out_number specifies which outlet of the pipe the piece will be added to. For more information on each function, the documentation is currently only within the files.

Examples:
* Chicane with mitered bends:
![chicane](https://raw.githubusercontent.com/Duncan-Hunter/pipemesh/master/pipemesh/images/network2.png)
```python
network = pipes.Network(1, 0.3, [1,0,0], 0.1)
network.add_cylinder(1, 0.1)
network.add_mitered([0,1,0], 0.1)
network.add_cylinder(1, 0.1)
network.add_mitered([1,0,0], 0.1)
network.add_cylinder(1, 0.1)
```
* Pipe with two junctions:
![network](https://raw.githubusercontent.com/Duncan-Hunter/pipemesh/master/pipemesh/images/network.png)
```python
network.add_t_junction([-1,1,0], 0.05)
network.add_t_junction([-1,-1,0], 0.05)
network.add_cylinder(1, 0.1, out_number=2)
network.add_curve([-1,0,0], 0.5, 0.05, out_number=3)
network.add_cylinder(1.5, 0.1, out_number=3)
```

Once the network is complete, you can fuse the objects together and create physical surfaces and volumes, and set the local mesh sizes. Information can be obtained and written to file. This is all done with one call.
```python
network.generate(filename="example", binary=False, write_info=False, mesh_format="msh2", write_xml=False run_gui=False)
```
Which will write the file "example.msh", as a msh2 binary file.


### Requirements for pipes.py:
- libgmsh.so, libgmsh.so.4.3, libgmsh.so.4.3.0 from the GMSH SDK.
- NumPy, SciPy
