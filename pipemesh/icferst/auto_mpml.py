"""
Edits a basic .mpml file with the AutoMPML class.

Create the class with options = AutoMPML. Then call
the set_methods to set options. Then use write to generate the file.
MPML files generated will only work with latest version of IC-FERST.
Contact author if you want support for older versions.
"""
import xml.etree.ElementTree as ET
import copy
import os
LOC = os.path.dirname(os.path.abspath(__file__))


class AutoMPML():
    def __init__(self):
        fname = LOC + "/3d_pipe_FEM.mpml"
        self.mpml_tree = ET.parse(fname)
        self.mpml_root = self.mpml_tree.getroot()

        self.sim_name = self.mpml_root[0]
        self.msh_options = self.mpml_root[2]
        self.io_options = self.mpml_root[4]
        self.timestepping = self.mpml_root[5]
        self.material_phase = self.mpml_root[6]
        self.mesh_adaptivity = self.mpml_root[7]

    def set_all(self,
                sim_name=None,
                msh_file="src/pipe",
                dump_period=0.1,
                dump_ids=[],
                finish_time=1,
                timestep=0.005,
                cfl_no=2.0,
                density=1e-3,
                viscosity=1e-3,
                inlet_phys_ids=[],
                inlet_velocities=[],
                outlet_phys_ids=[],
                cyl_phys_ids=[],
                min_mesh_size=0.01,
                max_mesh_size=0.5,
                max_no_nodes=3e5,
                t_adapt_delay=0.5,
                aspect_ratio=0.5):
        """Sets all of the options at once.

        See base functions for information on what each option sets."""
        self.set_sim_name(sim_name)
        self.set_msh_options(msh_file)
        self.set_io_options(dump_period, dump_ids)
        self.set_timestepping(finish_time, timestep, cfl_no)
        self.set_material_properties(density, viscosity)
        self.set_inlets(inlet_phys_ids, inlet_velocities)
        self.set_outlets(outlet_phys_ids)
        self.set_no_slip(cyl_phys_ids)
        self.set_mesh_adaptivity(min_mesh_size, max_mesh_size, max_no_nodes,
                                 t_adapt_delay, aspect_ratio)

    def set_sim_name(self, simname):
        """Sets the name of the simulation.

        Default is "3d_pipe".
        """
        self.sim_name[0].text = simname

    def set_msh_options(self, msh_file):
        """Sets the location of the msh_file.

        Default is src/pipe.
        Args:
            msh_file: (string) location .msh file is stored."""
        mesh = self.msh_options[1]
        mesh[0].attrib['file_name'] = msh_file

    def set_io_options(self, dump_period=0.1, dump_ids=[]):
        """Sets the input/output settings.

        Args:
            dump_period: How often to dump vtu files.
            dump_ids: Physical surfaces to record fluxes.
        """
        if dump_period < 0.1:
            print("Warning: dump period is less than maximum timestep.")
        dump_period = str(dump_period)
        dump_p = self.io_options[1][0][0]
        dump_p.text = str(dump_period)
        text = str(dump_ids[0])
        for i in dump_ids[1:]:
            text += " {}".format(i)
        dump_id = self.io_options[2][0][0]
        dump_id.attrib['shape'] = str(len(dump_ids))
        dump_id.text = text

    def set_timestepping(self, finish_time, timestep=0.005, cfl_no=2.0):
        """Sets the timestepping options.

        Args:
            finish_time: Time the simulations stops.
            timestep: Initial timestep.
            cfl_no: CFL number adaptive timestepping aims for.
        """
        tstep = self.timestepping[1][0]
        tstep.text = str(timestep)
        ftime = self.timestepping[2][0]
        ftime.text = str(finish_time)

        if cfl_no > 4:
            raise ValueError("CFL number too high")
        if cfl_no > 2:
            print("Warning: High CFL number")
        elif cfl_no <= 0:
            raise ValueError("CFL number too low")

        cfl = self.timestepping[3][0][0]
        cfl.text = str(cfl_no)

    def set_material_properties(self, density=1e3, viscosity=1e-3):
        """Sets the material phase properties.

        Args:
            density: density of the fluid.
            viscosity: viscosity of the fluid.
        """
        density_o = self.material_phase[0][0][0][0]
        density_o.text = str(density)
        viscosity_o = self.material_phase[0][1][0][0][0][0][0][0]
        viscosity_o.text = str(viscosity)

    def set_inlets(self, phys_ids, velocities):
        """Sets the properties for inlets.

        Args:
            phys_ids: (list of ints) physical ids of inlet surfaces.
            velocities: (list of xyz vector lists) velocities
                for respective physical ids. E.g. velocities[0] corresponds to
                phys_ids[0]. If not enough vectors are given, the first vector
                is used for all inlets.
        """

        def set_velo(i1_elem, i1_mom_elem, i1_ad_elem, phys_id, velocity):
            """eleme is boundary_conditions, name=inlet."""

            def set_vec_comp(elem, velo):
                for i in range(3):
                    elem[i][0][0].text = str(velo[i])

            i1_elem.attrib['name'] = "inlet_{}".format(phys_id)
            i1_elem[0][0].text = str(phys_id)
            set_vec_comp(i1_elem[1][1], velocity)

            i1_mom_elem.attrib['name'] = "inlet_{}_mom".format(phys_id)
            i1_mom_elem[0][0].text = str(phys_id)
            set_vec_comp(i1_mom_elem[1][0], velocity)

            i1_ad_elem.attrib['name'] = "inlet_{}_ad".format(phys_id)
            i1_ad_elem[0][0].text = str(phys_id)
            set_vec_comp(i1_ad_elem[1][1], velocity)

        velo = self.material_phase[2]

        n_inlets = len(phys_ids)
        set_velo(velo[0][2], velo[0][3], velo[0][4], phys_ids[0],
                 velocities[0])
        if n_inlets > 1:
            if len(velocities) < n_inlets:
                print(
                    "Not enough velocities given. Using first velocity for all inlets."
                )
                velocities = [velocities[0]] * n_inlets
            for phys_id, velocity in zip(phys_ids[1:], velocities[1:]):
                i1_copy = copy.deepcopy(velo[0][2])
                i1_mom_copy = copy.deepcopy(velo[0][3])
                i1_ad_copy = copy.deepcopy(velo[0][4])
                set_velo(i1_copy, i1_mom_copy, i1_ad_copy, phys_id, velocity)
                velo[0].append(i1_copy)
                velo[0].append(i1_mom_copy)
                velo[0].append(i1_ad_copy)

    def set_outlets(self, phys_ids):
        """Sets the outlet surfaces.

        Sets the physical surfaces phys_ids to 0 pressure.

        Args:
            phys_ids: The physical surfaces to set to 0 pressure.
        """
        pressure = self.material_phase[1]
        out_ids = pressure[0][2][0][0]
        out_ids.attrib['shape'] = str(len(phys_ids))
        text = str(phys_ids[0])
        for i in phys_ids[1:]:
            text += " {}".format(int(i))
        out_ids.text = text

    def set_no_slip(self, phys_ids):
        """Sets the no-slip boundary condition.

        Args:
            phys_ids: The physical surfaces to set to no-slip.
        """
        cyl_mom = self.material_phase[2][0][5]
        cyl_ns_visc = self.material_phase[2][0][6]
        cyl = self.material_phase[2][0][7]
        text = str(phys_ids[0])
        for i in phys_ids[1:]:
            text += " {}".format(int(i))

        for cond in [cyl_mom, cyl_ns_visc, cyl]:
            out_ids = cond[0][0]
            out_ids.attrib['shape'] = str(len(phys_ids))
            out_ids.text = text

    def set_mesh_adaptivity(self,
                            min_size=0.01,
                            max_size=0.5,
                            max_no_nodes=300000,
                            t_adapt_delay=0.5,
                            aspect_ratio=5):
        """Sets mesh adaptivity options.

        Args:
            min_size: Minimum mesh size.
            max_size: Maximum mesh size.
            max_no_nodes: Maximum number of nodes. 100,000 is ~16GB of memory.
            t_adapt_delay: Start adaptive meshing at this time.
            aspect_ratio: Limit the mesh shape to maximum this aspect ratio.
        """
        mnn = self.mesh_adaptivity[0][1][0]
        mnn.text = str(int(max_no_nodes))

        def ani_sym_matrix_text(value):
            text = "{} 0.0 0.0 0.0 {} 0.0 0.0 0.0 {}".format(
                value, value, value)
            return text

        min_s = self.mesh_adaptivity[0][3][0][0][0]
        min_s.text = ani_sym_matrix_text(min_size)
        max_s = self.mesh_adaptivity[0][4][0][0][0]
        max_s.text = ani_sym_matrix_text(max_size)
        asp_ratio = self.mesh_adaptivity[0][4][0]
        asp_ratio.text = str(aspect_ratio)
        t_a_d = self.mesh_adaptivity[0][5][0]
        t_a_d.text = str(t_adapt_delay)

    def write_mpml(self, fname):
        """Writes the settings to fname.mpml."""
        self.mpml_tree.write(fname + ".mpml", 'utf-8', xml_declaration=True)
