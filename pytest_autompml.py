from pipemesh.icferst import auto_mpml

options = auto_mpml.AutoMPML()


def test_1():
    """Tests if simulation name is changed."""
    before = options.sim_name[0].text
    assert (before == "3d_pipe")
    options.set_sim_name("test")
    after = options.sim_name[0].text
    assert (before != after)


def test_2():
    """Tests if src location is changed."""
    before = options.msh_options[1][0].attrib["file_name"]
    options.set_msh_options("test")
    after = options.msh_options[1][0].attrib["file_name"]
    assert (before != after)


def test_3():
    """Tests if dump period is changed."""
    before = options.io_options[1][0][0].text
    before_ids = options.io_options[2][0][0].text
    val = float(before) + 0.05
    options.set_io_options(val, [1, 2])
    after = options.io_options[1][0][0].text
    after_ids = options.io_options[2][0][0].text
    assert (float(after) > float(before))
    assert (after != before)


def test_4():
    """Tests if timestepping is changed."""
    t_step_before = options.timestepping[1][0].text
    ftime_before = options.timestepping[2][0].text
    options.set_timestepping(0.2, 0.006, CFL_no=2.0)
    t_step_after = options.timestepping[1][0].text
    ftime_after = options.timestepping[2][0].text
    assert (t_step_after != t_step_before)
    assert (ftime_after != ftime_before)


def test_5():
    """Tests if phase properties are changed."""
    d_before = options.material_phase[0][0][0][0].text
    v_before = options.material_phase[0][1][0][0][0][0][0][0].text
    options.set_material_properties(density=str(float(d_before)+1),
                                    viscosity=str(float(v_before)+0.001))
    d_after = options.material_phase[0][0][0][0].text
    v_after = options.material_phase[0][1][0][0][0][0][0][0].text
    assert(float(d_after) > float(d_before))
    assert(float(v_after) > float(v_before))


test_1()
test_2()
test_3()
test_4()
test_5()
