import os
import sys
import inspect
from ase.md.langevin import Langevin
from ase.md.verlet import VelocityVerlet
from ase.io import read
from ase.io.trajectory import Trajectory
from ase import units as u
from infretis.classes.formatter import FileIO, OutputFormatter
from infretis.core.core import create_external
from infretis.classes.orderparameter import create_orderparameter
from infretis.classes.engines.enginebase import EngineBase
import sys
from infretis.classes.engines.ase_external_engine import read_stuff, dump_stuff
import time
import tomli
import pathlib

# if idle for more than this nr. of seconds we shut down the engine
TIMEOUT = 600
START = "INFINITY_START"
SLEEP = 1.5

# read .toml settings
with open(sys.argv[1], "rb") as rfile:
    config = tomli.load(rfile)

# calc and orderfunction only need to be set up once
calc = create_external(config["engine"]["calculator_settings"], "ASE_calculator", [])
order_function = create_orderparameter(config)

# set exe_dir, e.g. worker0/
cwd = os.path.abspath(sys.argv[2])
wname = pathlib.Path(cwd).name
logger = open(f"{wname}_propagator.log", "a")
if not cwd:
    raise ValueError("No exe_dir specified!")
if not os.path.isdir(cwd):
    print(f"Did not find {cwd}/ dir, making it now.", file=logger, flush=True)
    os.mkdir(cwd)
# change directory
print(f"Changing dir to {cwd}")
os.chdir(cwd)

idle_time = 0

while True:
    # wait for start file to appear
    if not os.path.exists(START):
        time.sleep(SLEEP)
        print(f"{wname}: Sleeping ... now been idle for {idle_time} s", file=logger, flush=True)
        idle_time += SLEEP
        if idle_time >= TIMEOUT:
            print(f"{wname}: Idle time exceeded {TIMEOUT} seconds. Killing process.", file=logger, flush=True)
            logger.close()
            os._exit(1)
    else:
        print(f"{wname}: Found {START} file", file=logger, flush=True)
        # try to read start file
        while True:
            if not os.path.exists(START):
                print(f"{wname}: Now the START file is missing... Now idle for {idle_time}", file=logger, flush=True)
                time.sleep(SLEEP)
                idle_time += SLEEP
                if idle_time >= TIMEOUT:
                    print(f"{wname}: Idle time exceeded {TIMEOUT} seconds. Killing process.", file=logger, flush=True)
                    logger.close()
                    os._exit(1)
            else:
                with open(START, "r") as rfile:
                    line = rfile.readline()
                    spl = line.split()
                    if len(spl) != 6:
                        print(f"{wname}: STARTFILE_ERR not 6 columns in file; content is '{spl}'. Now idle for {idle_time} s", file=logger, flush=True)
                        time.sleep(SLEEP)
                        idle_time += SLEEP
                        if idle_time >= TIMEOUT:
                            print(f"{wname}: Idle time exceeded {TIMEOUT} seconds. Killing process.", file=logger, flush=True)
                            logger.close()
                            os._exit(1)
                    # finally escape the loop if we get 6 values
                    else:
                        print(f"{wname} " + line, file=logger, flush=True)
                        initial_conf, subcycles, traj_file, cwd, msg_file_name, input_path = line.split()
                        subcycles = int(subcycles)
                        break

        system = read_stuff("system", cwd)
        path = read_stuff("path", cwd)
        ens_set = read_stuff("ens_set", cwd)
        Integrator = read_stuff("Integrator", cwd)
        int_set = read_stuff("int_set", cwd)
        reverse = read_stuff("reverse", cwd)
        left = read_stuff("left", cwd)
        right = read_stuff("right", cwd)

        # create engine and order function
        atoms = read(initial_conf)
        if isinstance(atoms, list):
            atoms = atoms[0]

        msg_file = FileIO(
            msg_file_name, "a", OutputFormatter("MSG_File"), backup=False
        )
        msg_file.open()

        dyn = Integrator(atoms, **int_set)
        step_accepts_forces = None
        try:
            step_accepts_forces = "forces" in inspect.signature(dyn.step).parameters
        except (TypeError, ValueError):
            # Some callables do not expose signatures; detect support dynamically.
            pass
        traj = traj = Trajectory(traj_file, "w")
        step_nr = 0
        ekin = []
        vpot = []
        temp = []
        etot = []
        calc.calculate(atoms, properties=["energy", "forces"], system_changes=["positions", "numbers", "cell"])
        atoms.calc = calc
        t0 = time.time()
        # integrator step is taken at the end of every loop,
        # such that frame 0 is also written
        print(f"{wname}: Starting {subcycles*path.maxlen} steps", file=logger, flush=True)
        for i in range(subcycles * path.maxlen):
            #print(f"step {i} of {subcycles*path.maxlen}", file=logger, flush=True)
            energy = calc.results["energy"]
            forces = calc.results["forces"]
            stress = calc.results.get("stress", None)
            if (i) % (subcycles) == 0:
                ekin.append(calc.results.get("ekin", atoms.get_kinetic_energy()))
                vpot.append(calc.results["energy"])
                temp.append(calc.results.get("temp", atoms.get_temperature()))
                etot.append(ekin[-1] + vpot[-1])
                # NOTE: Writing atoms removes all results from
                # the calculator (and therefore atoms)!
                atoms.wrap()
                traj.write(atoms, forces=forces, energy=energy, stress=stress)
                system.pos = atoms.positions
                system.vel = atoms.get_velocities()
                system.box = atoms.cell.diagonal()
                order = order_function.calculate(system)
                msg_file.write(
                    f'{step_nr} {" ".join([str(j) for j in order])}'
                )
                snapshot = {
                    "order": order,
                    "config": (traj_file, step_nr),
                    "vel_rev": reverse,
                }
                phase_point = EngineBase.snapshot_to_system(system, snapshot)
                status, success, stop, add = EngineBase.add_to_path(
                    path, phase_point, left, right
                )

                if stop:
                    break
                step_nr += 1
            if step_accepts_forces is False:
                dyn.step()
            else:
                try:
                    dyn.step(forces=forces)
                    if step_accepts_forces is None:
                        step_accepts_forces = True
                except TypeError as err:
                    if "unexpected keyword argument 'forces'" in str(err):
                        dyn.step()
                        step_accepts_forces = False
                    else:
                        raise
        t1 = time.time()

        msg_file.write("# Propagation done.")
        msg_file.close()
        traj.close()
        path.update_energies(ekin, vpot, etot, temp)
        dump_stuff(["path"], [path], cwd)
        dump_stuff(["success","status"], [success, status], cwd)
        # avoid divide by zero err
        if step_nr == 0:
            step_nr += 1
        print(f"{wname}: propagation done {(t1-t0)/(step_nr)} s/step.", flush=True, file=logger)
        os.remove(START)
        idle_time = 0
