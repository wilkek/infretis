<h1 align="center">
Hunting Defects in Perovskites

Unveiling the molecular secrets with Path Sampling
</h1>

# Motivation
tba.
# The System
tba.
#Goals?

# Setting up the Software
We first need to install the required programs to run this exercise. This includes an MD Engine that can run our homemade ReaxFF forcefield ([AMS2023.2](https://www.scm.com/support/downloads/bug-fixes/)) for your molecule and the ∞RETIS software developed at the theoretical chemistry group at NTNU in Trondheim.

## Install AMS
We install a developement version of AMS2023. The bugfixed releases can be found [here](https://www.scm.com/support/downloads/bug-fixes/). You might need to change/update the version in the `wget` line. The credentials can be found [here](https://tue.topdesk.net/tas/public/ssp/content/detail/knowledgeitem?unid=1e2fac4ce2164be9872e3a0e59fc0f62). 
```bash
mkdir opt
cd opt/
wget --user uXXXXX --password XXXXXXXX https://downloads.scm.com/Downloads/beta/trunk.pc64_linux.intelmpi.r118896.0.1390.bin.tgz
tar zxvf *.bin.tgz
. ~/opt/ams2023.205.r118896/amsbashrc.sh
```
After download, create the autolicense with your own emailadress and check the install with `dirac info`

```bash
$AMSBIN/autolicense nogui -u uXXXXX -p XXXXXXXX -m "your@email.nl"
dirac info
```

The output should look like that:
```bash
SCM User ID: uXXXXX
 release: 2023.xxx
 .
 .
 .
LICENSE INFO READY

```


## Install ∞RETIS
Download and install mamba with the following commands (if you don't already have conda installed). Click the copy button on the box below and paste it into a terminal, and then do what is asked in the output on your screen (on Ubuntu, pressing down the mouse-wheel-button often works better for pasting than ctrl+V).
```bash
curl -L -O "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"
bash Miniforge3-$(uname)-$(uname -m).sh
```
Press enter and type yes everytime when prompted. Now close the terminal.

You should see `(base)` in the left of your terminal window after reopening if everything went successfully.

Then download and install the required python packages to run this exercise. Again copy-paste the code and do what is asked of you in the output.

```bash
mamba create --name molmod python==3.11 MDAnalysis tqdm
```
```bash
mamba activate molmod
cd ~/opt
git clone https://github.com/wilkek/infretis.git
cd infretis
git checkout ams
python -m pip install -e .
```

You should now see `(molmod)` in the left of your terminal. Whenever you open a new terminal, write `mamba activate molmod` to activate the required Python packages. Try it by opening a new terminal and running `python -c 'import MDAnalysis'` without activating the `molmod` environment. This should throw an error.

## Install PLAMS
AMS and ∞RETIS run in different python versions. We need to apply some tricks to work with both at the same time. First we need an external version of [PLAMS](https://www.scm.com/doc/Scripting/PLAMS/PLAMS.html), which is the AMS-internal python package. We install that by copying following lines to our terminal. Make sure, that the molmod environment is active.

```bash
cd ~/opt
git clone https://github.com/SCM-NV/PLAMS.git
cd PLAMS
git checkout oldparser
```
Now you probably get a `vim`-prompt. Just type `:wq` and hit `Enter`. Now you can continue with the next modifications: 
```bash
pip install py-ubjson
python -m pip uninstall plams
python -m pip install .
```
Now you have plams in your python3.11 stack. To make it work, you need to find the location of your `site-packages/scm/` folder. If you followed the instructions until here, you should be able to run the following lines:
```bash
cd ~/miniforge3/envs/molmod/lib/python3.11/site-packages/scm/ #if miniforge path is left standard
cp -r $AMSHOME/scripting/scm/input_parser/ .
```
The setup is done. You should test your install by running the following example simulation.

## Run the test

We will perform the test from the directory `~/opt/infretis/examples/ams/water_dimer/`. Get an overview of the folder structure and all the files we will be using by navigating to that directory and running
```bash
cd ~/opt/infretis/examples/ams/water_dimer/
ls *
```
Run the script with the command `bash runner`, but WATCH OUT! you are running on the Login-node. This is really just for testing purpose!!!
Your folder should now contain `amsworker`- and `worker`-directories
If everything works out, proceed with the slurm command:
```bash
sbatch srunner
```

