# This code is part of OpenFE and is licensed under the MIT license.
# For details, see https://github.com/OpenFreeEnergy/openfe


"""
Here I want to build the cmd tool for easy campaigner with RBFE. The output should be runnable with quickrun directly!
    So user experience would be:
        easy_campaign -l sdf_dir -p receptor.pdb -> Alchem network
        quickrun -i alchem_network

"""
import json
import os.path

import click
from typing import List
from openfecli.utils import write
from openfecli import OFECommandPlugin
from openfecli.parameters import MOL_DIR, PROTEIN, MAPPER, OUTPUT_DIR

# Todo: Make Params exchangeable - Lomap, Kartograf, etc.

def plan_rbfe_network_main(
    mapper, mapping_scorer, ligand_network_planner, small_molecules, solvent, protein
):
    from openfe.setup.alchemical_network_planner.easy_alchemical_network_planner import (
        RBFEAlchemicalNetworkPlanner,
    )

    ligand_network_planner_obj = ligand_network_planner(mappers=[mapper], scorer=mapping_scorer)
    campaigner = RBFEAlchemicalNetworkPlanner(
        ligand_network_planner=ligand_network_planner_obj,
    )
    alchemical_network = campaigner(
        ligands=small_molecules, solvent=solvent, receptor=protein
    )
    return alchemical_network

def plan_rbfe_network_output(alchemical_network, output):
    #Todo: this is an uggly peace of output code. it does not recognize overwriting! fix!
    an_dict = alchemical_network.to_dict()

    folder_path = output
    print(folder_path)
    base_name= os.path.basename(folder_path)

    if not os.path.isdir(folder_path):
        os.mkdir(folder_path)

    json.dump(an_dict, open(folder_path + "/" + base_name + ".json" , "w"))
    write("\t\t- " + base_name + ".json")

    transformation_dir = folder_path+"/transformations"
    if not os.path.isdir(transformation_dir):
        os.mkdir(transformation_dir)
    write("\t\t- " + transformation_dir)

    for transformation in alchemical_network.edges:
        out_path = transformation_dir+"/"+base_name+"_"+transformation.name+".json"
        transformation.dump(out_path)
        write("\t\t\t- " + base_name + "_" + transformation.name + ".json")


@click.command(
    "plan-rbfe-network", short_help="Run a planning session for relative binding free energies, saved as a JSON file"
)
@MOL_DIR.parameter(
    required=True, help=MOL_DIR.kwargs["help"] + " Any number of sdf paths."
)
@PROTEIN.parameter(
    multiple=False, required=True, default=None, help=PROTEIN.kwargs["help"]
)
@OUTPUT_DIR.parameter(
    help=OUTPUT_DIR.kwargs["help"] + " ",
    default="alchemicalNetwork"
)
@MAPPER.parameter(required=False, default="LomapAtomMapper")
def plan_rbfe_network(mol_dir: List[str], protein: str, output_dir: str, mapper: str):

    # INPUT
    write("Parsing in Files: ")
    write("\tGot input: ")

    small_molecules = MOL_DIR.get(mol_dir)
    write("\t\tSmall Molecules: " + " ".join([str(sm) for sm in small_molecules]))

    protein = PROTEIN.get(protein)
    write("\t\tProtein: " + str(protein))

    from gufe import SolventComponent
    solvent = SolventComponent()
    write("\t\tSolvent: " + str(solvent))
    write("")

    write("Using Options:")
    mapper_obj = MAPPER.get(mapper)()
    write("\tMapper: " + str(mapper_obj))

    from openfe.setup.atom_mapping.lomap_scorers import (
        default_lomap_score,
    )  # write nice parameter

    mapping_scorer = default_lomap_score
    write("\tMapping Scorer: " + str(mapping_scorer))

    from openfe.setup.ligand_network_planner import (
        MinimalSpanningNetworkPlanner
    )  # write nice parameter

    ligand_network_planner = MinimalSpanningNetworkPlanner()
    write("\tNetworker: " + str(ligand_network_planner))
    write("")

    # DO
    write("Planning RBFE-Campaign:")
    alchemical_network = plan_rbfe_network_main(
        mapper=mapper_obj,
        mapping_scorer=mapping_scorer,
        ligand_network_planner=ligand_network_planner,
        small_molecules=small_molecules,
        solvent=solvent,
        protein=protein,
    )
    write("\tDone")
    write("")

    # OUTPUT
    write("Output:")
    write("\tSaving to: " + str(output_dir)) #Todo: remove replace
    plan_rbfe_network_output(alchemical_network=alchemical_network, output=OUTPUT_DIR.get(output) )



PLUGIN = OFECommandPlugin(
    command=plan_rbfe_network, section="Setup", requires_ofe=(0, 3)
)
