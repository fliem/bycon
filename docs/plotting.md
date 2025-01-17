---
title: Plotting
---

## `bycon` Plot functionality

Starting with version v1.0.30 (2023-04-14) the bycon package added the ability
to produce the typical _Progenetix_-style CNV histograms and CNV sample plots. 
These plots can both be generated by adding the respective `output=...` option to
standard Beacon queries or through use of the `bycon` package to visualize data
from local storage. Plotting from local `.pgxseg` ... file is possible but so far
we don't provide a ready-made for that.

### Plot types

#### CNV histograms - `/services/intervalFrequencies` with `output=histoplot`

CNV histograms can be generated either (fast) for one or multiple of the "collations" _i.e._
samples sharing a common code (diagnosis, technnique...) or identifier (cell line id, 
PMID ...), or as single histogram for the output of a Beacon query.

A complete list of collations can be retrieved through the `/services/collations/`
endpoint, e.g. [/services/collations?datasetIds=progenetix&output=text](http://progenetix.org/services/collations?datasetIds=progenetix&output=text).

Please note that the `datasetIds` parameter will fall back to the default parameter
if not indicated.

##### Examples

* [/services/intervalFrequencies/?filters=NCIT:C35562,NCIT:C3709&output=histoplot](http://progenetix.org/services/intervalFrequencies/?filters=NCIT:C35562,NCIT:C3709&output=histoplot)
    - a combination of 2 histograms
* [/services/intervalFrequencies/?filters=NCIT:C35562,NCIT:C3709&datasetIds=progenetix,cellz&output=histoplot](http://progenetix.org/services/intervalFrequencies/?filters=NCIT:C35562,NCIT:C3709&datasetIds=progenetix,cellz&output=histoplot)
    - a combination of 2 histograms
* [/services/intervalFrequencies/?filters=pgx:icdom-85003,pgx:icdom-81703,pgx:icdom-87003,pgx:icdom-87203,pgx:icdom-94003,pgx:icdom-95003,pgx:icdom-81403&plot_title=CNV+Comparison&plot_area_height=50&plot_axis_y_max=80&plot_label_y_values=50&output=histoplot](http://progenetix.org/services/intervalFrequencies/?filters=pgx:icdom-85003,pgx:icdom-81703,pgx:icdom-87003,pgx:icdom-87203,pgx:icdom-94003,pgx:icdom-95003,pgx:icdom-81403&plot_title=CNV+Comparison&plot_area_height=50&plot_axis_y_max=80&plot_label_y_values=50&output=histoplot)
    - a collations based example showing the use of some extra parameters such as
        * `plot_title`
        * `plot_area_height`
        * `plot_axis_y_max` & `plot_label_y_values`
* [/beacon/biosamples/?filters=pgx:icdom-95003&plotGeneSymbols=MYCN&output=histoplot&limit=1000](http://progenetix.org/beacon/biosamples/?filters=pgx:icdom-95003&plotGeneSymbols=MYCN&output=histoplot&limit=1000)
    - this example gets samples for ICD-O Morphology 95003/3 (a.k.a. `pgx:icdom-95003`)
    - limits the output to the first 1000 samples (`limit=1000`)
    - adds a label for the **MYCN** gene


#### CNV sample plots - `output=samplesplot`

##### Examples

* [/beacon/biosamples/?filters=pgx:icdom-95003&plot_filter_empty_samples=y&plotGeneSymbols=MYCN&output=samplesplot&limit=200](http://progenetix.org/beacon/biosamples/?filters=pgx:icdom-95003&plot_filter_empty_samples=y&plotGeneSymbols=MYCN&output=samplesplot&limit=200)
    - this example is based on the histoplot example above, with some modifications:
        * limits the output to 200 samples (`limit=200`)
        * removes samples w/o CNVs (`plot_filter_empty_samples=y`)

## Plot parameters

Plot parameters can be given both in `snake_case` and in the corresponding
`camelCase` format (`plot_area_width` or `plotAreaWidth`).


### Parameter definitions

``` yaml title="Plot parameters"
--8<-- "./bycon/config/plot_defaults.yaml"
```