# wmg only includes data generated by assays that normalize for gene length
INCLUDED_ASSAYS = {
    "EFO:0010550": "sci-RNA-seq",
    "EFO:0009901": "10x 3' v1",
    "EFO:0011025": "10x 5' v1",
    "EFO:0009899": "10x 3' v2",
    "EFO:0009900": "10x 5' v2",
    "EFO:0009922": "10x 3' v3",
    "EFO:0030003": "10x 3' transcription profiling",
    "EFO:0030004": "10x 5' transcription profiling",
    "EFO:0008919": "Seq-Well",
    "EFO:0008995": "10x technology",
    "EFO:0008722": "Drop-seq",
    "EFO:0010010": "CEL-seq2",
}

CL_PINNED_CONFIG_URL = "https://raw.githubusercontent.com/chanzuckerberg/single-cell-curation/v3.1.3/cellxgene_schema_cli/cellxgene_schema/ontology_files/owl_info.yml"
CL_BASIC_OBO_NAME = "cl-basic.obo"
CL_BASIC_OWL_NAME = "cl-basic.owl"

WMG_PINNED_SCHEMA_VERSION = "3.1.0"
