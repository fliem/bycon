import re, yaml
from pymongo import MongoClient
from pathlib import Path
from os import environ, pardir, path
import sys

from cgi_parsing import *
from bycon_helpers import hex_2_rgb
from export_file_generation import de_vrsify_variant

################################################################################

def _handover_add_stringified_plot_parameters(h_o_t, byc):

    if not "plot" in h_o_t:
        return ""

    p_p = get_plot_parameters({}, byc)
    p_p_l = []
    for ppk, ppv in p_p.items():
        if type(ppv) is list:
            p_p_l.append( f'{ppk}={ ",".join(map(str, (ppv))) }' )
            continue
        p_p_l.append( f'{ppk}={ppv}' )

    if len(p_p_l) < 1:
        return ""

    return f'&{"&".join(p_p_l)}'

################################################################################

def dataset_response_add_handovers(ds_id, byc):

    """podmd
    podmd"""

    b_h_o = [ ]
    if byc["include_handovers"] is not True:
        return b_h_o
    if not ds_id in byc["dataset_definitions"]:
        return b_h_o

    h_o_server = select_this_server(byc)    
    h_o_types = byc["handover_definitions"]["h->o_types"]
    ds_h_o = byc["dataset_definitions"][ ds_id ].get("handoverTypes", h_o_types.keys())

    for h_o_t, h_o_defs in h_o_types.items():

        # testing if this handover is active for the specified dataset      
        if not h_o_t in ds_h_o:
            continue

        for h_o_key, h_o in byc["dataset_results"][ds_id].items():

            if h_o["target_count"] < 1:
                continue

            accessid = h_o["id"]
            target_count =  h_o["target_count"]

            if h_o_key == h_o_types[ h_o_t ][ "h->o_key" ]:
                this_server = h_o_server
                if "remove_subdomain" in h_o_types[ h_o_t ]:
                    this_server = re.sub(r'\/\/\w+?\.(\w+?\.\w+?)$', r'//\1', this_server)
                h_o_r = {
                    "handover_type": h_o_defs.get("handoverType", {}),
                    "info": { "content_id": h_o_t},
                    "note": h_o_defs[ "note" ],
                    "url": "",
                    "pages": []
                }

                if "UCSClink" in h_o_t:
                    bed_file_name, ucsc_pos = _write_variants_bedfile(h_o, 0, 0, byc)
                    h_o_r.update( { "url": _handover_create_ext_url(this_server, h_o_defs, bed_file_name, ucsc_pos, byc ) } )
                else:
                    h_o_r.update( { "url": handover_create_url(this_server, h_o_defs, accessid, byc) } )

                # TODO: needs a new schema to accommodate this not as HACK ...
                # the phenopackets URL needs matched variants, which it wouldn't know about ...
                if "phenopackets" in h_o_t:
                    if "variants._id" in byc["dataset_results"][ds_id].keys():
                        h_o_r["url"] += "&variantsaccessid="+byc["dataset_results"][ds_id][ "variants._id" ][ "id" ]

                e_t = byc["response_entity"]["entity_type"]

                if e_t in h_o_defs["paginated_entities"]:

                    p_f = 0
                    p_t = p_f + byc["pagination"]["limit"]
                    p_s = 0

                    while p_f < target_count + 1:
                        if target_count < p_t:
                            p_t = target_count
                        l = "{}-{}".format(p_f + 1, p_t)
                        # no re-pagination of the results retrieved from the paginated query
                        # TODO: the bedfile part is wrong, since it paginates by the number of variants which
                        # may be incorrect if biosamples ... were called. have to change...
                        if "bedfile" in h_o_t:
                            bed_file_name, ucsc_pos = _write_variants_bedfile(h_o, p_f, p_t, byc)
                            u =  _handover_create_ext_url(this_server, h_o_defs, bed_file_name, ucsc_pos, byc )
                        else:
                            u = h_o_r["url"] + "&paginateResults=false&skip={}&limit={}".format(p_s, byc["pagination"]["limit"])
                        h_o_r["pages"].append( { "handover_type": {"id": h_o_defs["handoverType"][ "id" ], "label": l }, "url": u } )
                        p_s += 1
                        p_f += byc["pagination"]["limit"]
                        p_t = p_f + byc["pagination"]["limit"]

                    h_o_r["url"] += "&skip={}&limit={}".format(byc["pagination"]["skip"], byc["pagination"]["limit"])
                if "url" in h_o_r:
                    b_h_o.append( h_o_r )

    return b_h_o

################################################################################

def query_results_save_handovers(byc):

    if not "dataset_results" in byc:
        return False
    if byc["include_handovers"] is not True:
        return False

    for ds_id in byc["dataset_results"].keys():
        dataset_results_save_handovers(ds_id, byc)

    return True

################################################################################

def dataset_results_save_handovers(ds_id, byc):

    ho_client = MongoClient()
    ho_db = ho_client[ byc["config"]["services_db"] ]
    ho_coll = ho_db[ byc["config"][ "handover_coll" ] ]

    for h_o_k in byc["dataset_results"][ds_id].keys():
        
        h_o = byc["dataset_results"][ds_id][ h_o_k ]
        h_o_size = sys.getsizeof(h_o["target_values"])

        # print("Storage size for {}: {}Mb".format(h_o_k, h_o_size / 1000000))
        if h_o_size < 15000000:
            ho_coll.update_one( { "id": h_o["id"] }, { '$set': h_o }, upsert=True )

    ho_client.close()

    return True

################################################################################

def handover_create_url(h_o_server, h_o_defs, accessid, byc):

    if "script_path_web" in h_o_defs:
        server = h_o_server
        if "http" in h_o_defs["script_path_web"]:
            server = ""
        url = "{}{}?accessid={}".format(server, h_o_defs["script_path_web"], accessid)
        for p in ["method", "output", "requestedSchema"]:
            if p in h_o_defs:
                url += "&{}={}".format(p, h_o_defs[p])
        url += h_o_defs.get("url_opts", "")
        url += _handover_add_stringified_plot_parameters(h_o_defs.get("output", ""), byc)

        return url

    return ""

################################################################################

def _handover_create_ext_url(h_o_server, h_o_defs, bed_file_name, ucsc_pos, byc):

    local_paths = byc.get("local_paths")
    if not local_paths:
        return False

    if "ext_url" in h_o_defs:
        if "bedfile" in h_o_defs["handoverType"]["id"]:
            return("{}&position={}&hgt.customText={}{}/{}".format(h_o_defs["ext_url"], ucsc_pos, h_o_server, local_paths.get("server_tmp_dir_web", "/tmp"), bed_file_name))

    return False

################################################################################

def _write_variants_bedfile(h_o, p_f, p_t, byc):

    """podmd
    ##### Accepts

    * a Bycon `byc` object
    * a Bycon `h_o` handover object with its `target_values` representing `_id` 
    objects of a `variants` collection
        
    The function creates a basic BED file and returns its local path. A standard 
    use would be to create a link to this file and submit it as `hgt.customText` 
    parameter to the UCSC browser.

    ##### TODO

    * The creation of the different variant types is still rudimentary and has to be 
    expanded in lockstep with improving Beacon documentation and examples. The 
    definition of the types and their match patterns should also be moved to a 
    +separate configuration entry and subroutine.
    * evaluate to use "bedDetails" format

    podmd"""

    local_paths = byc.get("local_paths")
    if not local_paths:
        return False
    tmp_path = Path( path.join( *local_paths[ "server_tmp_dir_loc" ]) )
    if not tmp_path.is_dir():
        return False

    v_ret = 0
    v_max = 1000

    if len( h_o["target_values"] ) < 1:
        return()
    if not h_o["target_collection"] == "variants":
         return()
       
    ds_id = h_o["source_db"]
    accessid = h_o["id"]
    l = ""
    if p_t > 0:
        l = "_{}-{}".format(p_f + 1, p_t)
    else:
        p_t = v_max # only for the non-paginated ...

    bed_file_name = f'{accessid}{l}.bed'
    bed_file = Path( path.join( tmp_path, bed_file_name ) )

    vs = { "DUP": [ ], "DEL": [ ], "LOH": [ ], "SNV": [ ]}

    data_client = MongoClient( )
    data_db = data_client[ ds_id ]
    data_coll = data_db[ h_o["target_collection"] ]

    for v in data_coll.find( { h_o["target_key"]: { '$in': h_o["target_values"] } }).limit(p_t):

        v_ret += 1

        if p_t > 0:
            if v_ret > p_t:
                continue
            if v_ret <= p_f:
                continue
        
        # TODO: Just make this from the standard variant format
        v_d = de_vrsify_variant(v, byc)
        if v_d is False:
            continue

        v_d.update({"size": v_d["end"] - v_d["start"] })
        if "DUP" in v_d["variant_type"]:
            vs["DUP"].append(v_d)
        elif "DEL" in v_d["variant_type"]:
            vs["DEL"].append(v_d)
        elif "LOH" in v_d["variant_type"]:
            vs["LOH"].append(v_d)
        elif "SNV" in v_d["variant_type"]:
            vs["SNV"].append(v_d)
        else:
            continue

    b_f = open( bed_file, 'w' )
    pos = set()

    ucsc_chr = ""

    for vt in vs.keys():
        if len( vs[vt] ) > 0:
            try:
                vs[vt] = sorted(vs[vt], key=lambda k: k['size'], reverse=True)
            except:
                pass
            col_key = "plot_{}_color".format(vt.lower())
            col_hex = byc["plot_defaults"].get(col_key, "#666666")
            col_rgb = hex_2_rgb(col_hex)
            b_f.write("track name={} visibility=squish description=\"{} variants matching the query with {} overall returned\" color={},{},{}\n".format(vt, vt, v_ret, col_rgb[0], col_rgb[1], col_rgb[2] ) )
            b_f.write("#chrom\tchromStart\tchromEnd\tbiosampleId\n")
            for v in vs[vt]:
                ucsc_chr = "chr"+v["reference_name"]
                ucsc_min = int( v["start"] + 1 )
                ucsc_max = int( v["end"] )
                l = "{}\t{}\t{}\t{}\n".format( ucsc_chr, ucsc_min, ucsc_max, v["biosample_id"] )
                pos.add(ucsc_min)
                pos.add(ucsc_max)
                b_f.write( l )
 
    b_f.close()
    ucsc_range = sorted(pos)
    ucsc_pos = "{}:{}-{}".format(ucsc_chr, ucsc_range[0], ucsc_range[-1])

    return [bed_file_name, ucsc_pos]

################################################################################

