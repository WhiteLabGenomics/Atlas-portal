import argparse
import os
import sys
from enum import Enum
from unittest.mock import patch

from backend.cellguide.pipeline.canonical_marker_genes import get_canonical_marker_genes
from backend.cellguide.pipeline.computational_marker_genes import get_computational_marker_genes
from backend.cellguide.pipeline.constants import ASCTB_MASTER_SHEET_URL
from backend.cellguide.pipeline.metadata import get_cell_metadata, get_tissue_metadata
from backend.cellguide.pipeline.ontology_tree import get_ontology_tree_data
from backend.cellguide.pipeline.source_collections import get_source_collections_data
from backend.cellguide.pipeline.utils import output_json
from backend.wmg.data.utils import setup_retry_session
from tests.test_utils.mocks import (
    mock_bootstrap_rows_percentiles,
    mock_get_asctb_master_sheet,
    mock_get_collections_from_curation_endpoint,
    mock_get_datasets_from_curation_endpoint,
    mock_get_title_and_citation_from_doi,
)
from tests.unit.backend.wmg.fixtures.test_snapshot import load_realistic_test_snapshot
from tests.unit.cellguide_pipeline.constants import (
    ASCTB_MASTER_SHEET_FIXTURE_FILENAME,
    CANONICAL_MARKER_GENES_FIXTURE_FILENAME,
    CELLGUIDE_PIPELINE_FIXTURES_BASEPATH,
    CELLTYPE_METADATA_FIXTURE_FILENAME,
    CELLTYPE_ONTOLOGY_TREE_STATE_FIXTURE_FILENAME,
    COMPUTATIONAL_MARKER_GENES_FIXTURE_FILENAME,
    ONTOLOGY_GRAPH_FIXTURE_FILENAME,
    REFORMATTED_COMPUTATIONAL_MARKER_GENES_FIXTURE_FILENAME,
    SOURCE_COLLECTIONS_FIXTURE_FILENAME,
    TISSUE_METADATA_FIXTURE_FILENAME,
    TISSUE_ONTOLOGY_TREE_STATE_FIXTURE_FILENAME,
)

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)

TEST_SNAPSHOT = "realistic-test-snapshot"

CANONICAL_MARKER_GENE_TEST_TISSUES = ["heart", "blood"]

""" ################################# DANGER #######################################

Run this file if and only if you are confident there are no bugs in the CellGuide
pipeline.

Any and all unit test assertion errors prior to running this script must be expected
due to intended changes in the pipeline.

------------------------------------------------------------------------------------

This module generates the CellGuide data using the test snapshot stored in {TEST_SNAPSHOT}.
Requires an internet connection.

Run this script with the below command from the root directory of this repo:
```
python -m scripts.generate_cellguide_pipeline_test_fixtures --fixture-type <fixture_type>
```

If fixture type is not specified, all fixtures will be generated.
"""


class FixtureType(str, Enum):
    """Enum for fixture types"""

    ontology_graph = "ontology_graph"
    celltype_ontology_tree_state = "celltype_ontology_tree_state"
    tissue_ontology_tree_state = "tissue_ontology_tree_state"
    celltype_metadata = "celltype_metadata"
    tissue_metadata = "tissue_metadata"
    canonical_marker_genes = "canonical_marker_genes"
    computational_marker_genes = "computational_marker_genes"
    source_collections = "source_collections"
    all = "all"


def run_cellguide_pipeline(fixture_type: FixtureType):
    with load_realistic_test_snapshot(TEST_SNAPSHOT) as snapshot:
        # Get ontology tree data
        ontology_tree, ontology_tree_data = get_ontology_tree_data(snapshot=snapshot)

        if fixture_type in [FixtureType.ontology_graph, FixtureType.all]:
            output_json(
                ontology_tree_data.ontology_graph,
                f"{CELLGUIDE_PIPELINE_FIXTURES_BASEPATH}/{ONTOLOGY_GRAPH_FIXTURE_FILENAME}",
            )
            output_json(
                ontology_tree_data.all_states_per_cell_type,
                f"{CELLGUIDE_PIPELINE_FIXTURES_BASEPATH}/{CELLTYPE_ONTOLOGY_TREE_STATE_FIXTURE_FILENAME}",
            )
            output_json(
                ontology_tree_data.all_states_per_tissue,
                f"{CELLGUIDE_PIPELINE_FIXTURES_BASEPATH}/{TISSUE_ONTOLOGY_TREE_STATE_FIXTURE_FILENAME}",
            )

        if fixture_type in [FixtureType.celltype_metadata, FixtureType.all]:
            # Get cell metadata
            cell_metadata = get_cell_metadata(ontology_tree=ontology_tree)
            output_json(
                cell_metadata,
                f"{CELLGUIDE_PIPELINE_FIXTURES_BASEPATH}/{CELLTYPE_METADATA_FIXTURE_FILENAME}",
            )

        if fixture_type in [FixtureType.tissue_metadata, FixtureType.all]:
            # Get tissue metadata
            tissue_metadata = get_tissue_metadata(ontology_tree=ontology_tree)
            output_json(
                tissue_metadata,
                f"{CELLGUIDE_PIPELINE_FIXTURES_BASEPATH}/{TISSUE_METADATA_FIXTURE_FILENAME}",
            )

        if fixture_type in [FixtureType.canonical_marker_genes, FixtureType.all]:
            # output asct-b master sheet
            session = setup_retry_session()
            response = session.get(ASCTB_MASTER_SHEET_URL)
            if response.status_code != 200:
                raise Exception(f"Failed to retrieve ASCT-B master sheet from {ASCTB_MASTER_SHEET_URL}")

            data = response.json()
            data = {tissue: data[tissue] for tissue in CANONICAL_MARKER_GENE_TEST_TISSUES}
            output_json(data, f"{CELLGUIDE_PIPELINE_FIXTURES_BASEPATH}/{ASCTB_MASTER_SHEET_FIXTURE_FILENAME}")

            # Get canonical marker genes
            with patch(
                "backend.cellguide.pipeline.canonical_marker_genes.canonical_markers.get_asctb_master_sheet",
                new=mock_get_asctb_master_sheet,
            ), patch(
                "backend.cellguide.pipeline.canonical_marker_genes.canonical_markers.get_title_and_citation_from_doi",
                new=mock_get_title_and_citation_from_doi,
            ):
                canonical_marker_genes = get_canonical_marker_genes(snapshot=snapshot, ontology_tree=ontology_tree)
                output_json(
                    canonical_marker_genes,
                    f"{CELLGUIDE_PIPELINE_FIXTURES_BASEPATH}/{CANONICAL_MARKER_GENES_FIXTURE_FILENAME}",
                )

        if fixture_type in [FixtureType.source_collections, FixtureType.all]:
            # Get source data
            with patch(
                "backend.cellguide.pipeline.source_collections.source_collections_generator.get_datasets_from_discover_api",
                new=mock_get_datasets_from_curation_endpoint,
            ), patch(
                "backend.cellguide.pipeline.source_collections.source_collections_generator.get_collections_from_discover_api",
                new=mock_get_collections_from_curation_endpoint,
            ):
                source_collections = get_source_collections_data(ontology_tree=ontology_tree)
                output_json(
                    source_collections,
                    f"{CELLGUIDE_PIPELINE_FIXTURES_BASEPATH}/{SOURCE_COLLECTIONS_FIXTURE_FILENAME}",
                )

        if fixture_type in [FixtureType.computational_marker_genes, FixtureType.all]:
            # Get computational marker genes
            with patch(
                "backend.cellguide.pipeline.computational_marker_genes.computational_markers.bootstrap_rows_percentiles",
                new=mock_bootstrap_rows_percentiles,
            ):
                computational_marker_genes, reformatted_marker_genes = get_computational_marker_genes(
                    snapshot=snapshot, ontology_tree=ontology_tree
                )
                output_json(
                    computational_marker_genes,
                    f"{CELLGUIDE_PIPELINE_FIXTURES_BASEPATH}/{COMPUTATIONAL_MARKER_GENES_FIXTURE_FILENAME}",
                )
                output_json(
                    reformatted_marker_genes,
                    f"{CELLGUIDE_PIPELINE_FIXTURES_BASEPATH}/{REFORMATTED_COMPUTATIONAL_MARKER_GENES_FIXTURE_FILENAME}",
                )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--fixture_type",
        help="Type of fixture to generate",
        choices=[member.value for member in FixtureType],
        default="all",
    )
    args = parser.parse_args()

    run_cellguide_pipeline(FixtureType(args.fixture_type))
