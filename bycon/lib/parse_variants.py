import cgi, cgitb
import re, yaml
import logging
import sys

from .cgi_utils import *

################################################################################

def parse_variants(byc):

    variant_pars = { }
    v_p_defs = byc["variant_definitions"]["parameters"]

    for p_k in v_p_defs.keys():
        v_default = None
        if "default" in v_p_defs[ p_k ]:
            v_default = v_p_defs[ p_k ][ "default" ]
        if "array" in v_p_defs[ p_k ]["type"]:
            variant_pars[ p_k ] = form_return_listvalue( byc["form_data"], p_k )
        else:
            variant_pars[ p_k ] = byc["form_data"].getvalue(p_k, v_default)

        if not variant_pars[ p_k ]:
            del( variant_pars[ p_k ] )

    # for debugging
    if "args" in byc:
        args = byc["args"]
        if "test" in args:
            if args.test:
                variant_pars = byc["service_info"][ "sampleAlleleRequests" ][0]
        if "cytobands" in args:
            if args.cytobands:
                variant_pars[ "cytoBands" ] = args.cytobands
        if "chrobases" in args:
            if args.chrobases:
                variant_pars[ "chroBases" ] = args.chrobases
        if "genome" in args:
            if args.genome:
                variant_pars[ "assemblyId" ] = args.genome

    # value checks
    v_p_c = { }

    for p_k in variant_pars.keys():
        if not p_k in v_p_defs.keys():
            continue
        v_p = variant_pars[ p_k ]
        if "array" in v_p_defs[ p_k ]["type"]:
            v_l = [ ]
            for v in v_p:
                if re.compile( v_p_defs[ p_k ][ "items" ][ "pattern" ] ).match( str( v ) ):
                    if "integer" in v_p_defs[ p_k ][ "items" ][ "type" ]:
                        v = int( v )
                    v_l.append( v )
            v_p_c[ p_k ] = sorted( v_l )
        else:
            if re.compile( v_p_defs[ p_k ][ "pattern" ] ).match( str( v_p ) ):
                if "integer" in v_p_defs[ p_k ][ "type" ]:
                    v_p = int( v_p )
                v_p_c[ p_k ] = v_p

    # # TODO: this is meant to accommodate the "<end" interbase matches; 
    # # should probably be more systematic
    # for k in [ "start", "end" ]:
    #     if k in v_p_c:
    #         if len(v_p_c[ k ]) == 1:
    #             v_p_c[ k ].append( v_p_c[ k ][0] + 1 )

    byc.update( { "variant_pars": v_p_c } )

    return byc

################################################################################

def get_variant_request_type(byc):
    """podmd
    This method guesses the type of variant request, based on the complete
    fulfillment of the required parameters (all of `all_of`, at least one of
    `one_of`).
    In case of multiple types the one with most matched parameters is prefered.
    This may be changed to using a pre-defined request type and using this as
    completeness check only.
    podmd"""

    variant_request_type = "no correct variant request"

    v_pars = byc["variant_pars"]
    v_p_defs = byc["variant_definitions"]["parameters"]
    g_v_defs = byc["variant_definitions"]["BeaconRequestTypes"]["g_variant"]

    brts = byc["variant_definitions"]["request_types"]
    brts_k = brts.keys()
    
    # HACK: setting to range request if start and end with one value
    if "start" in v_pars and "end" in v_pars:
        if len(v_pars[ "start" ]) == 1:
            if len(v_pars[ "end" ]) == 1:
                brts_k = [ "variantRangeRequest" ]

    vrt_matches = [ ]

    for vrt in brts_k:
        matched_par_no = 0
        needed_par_no = 0
        if "one_of" in brts[vrt]:
            needed_par_no = 1
            for one_of in brts[vrt][ "one_of" ]:
                if one_of in v_pars:
                    needed_par_no = 0
                    continue
        needed_par_no += len( brts[vrt][ "all_of" ] )

        for required in brts[vrt][ "all_of" ]:
            if required in v_pars:
                matched_par_no += 1
        
        # print("{} {} of {}".format(vrt, matched_par_no, needed_par_no))

        if matched_par_no >= needed_par_no:
            vrt_matches.append( { "type": vrt, "par_no": matched_par_no } )

    if len(vrt_matches) > 0:
        vrt_matches = sorted(vrt_matches, key=lambda k: k['par_no'], reverse=True)
        variant_request_type = vrt_matches[0]["type"]

    byc.update( { "variant_request_type": variant_request_type } )

    return byc

################################################################################

def create_variantAlleleRequest_query(variant_request_type, variant_pars):

    """podmd
 
    podmd"""

    if variant_request_type != "variantAlleleRequest":
        return

    # TODO: Regexes for ref or alt with wildcard characters

    v_q_p = [
        { "reference_name": variant_pars[ "referenceName" ] },
        { "start": int(variant_pars[ "start" ][0]) }
    ]
    for p in [ "referenceBases", "alternateBases" ]:
        if not variant_pars[ p ] == "N":
            p_n = p.replace("Bases", "_bases")
            if "N" in variant_pars[ p ]:
                rb = variant_pars[ p ].replace("N", ".")
                v_q_p.append( { p_n: { '$regex': rb } } )
            else:
                 v_q_p.append( { p_n: variant_pars[ p ] } )
        
    variant_query = { "$and": v_q_p}

    return variant_query

################################################################################

def create_variantCNVrequest_query(variant_request_type, variant_pars):

    if not variant_request_type in [ "variantCNVrequest" ]:
        return

    variant_query = { "$and": [
        { "reference_name": variant_pars[ "referenceName" ] },
        { "start": { "$lt": variant_pars[ "start" ][-1] } },
        { "end": { "$gte": variant_pars[ "end" ][0] } },
        { "start": { "$gte": variant_pars[ "start" ][0] } },
        { "end": { "$lt": variant_pars[ "end" ][-1] } },
        create_and_or_query_for_parameter("variantType", "variant_type", "$or", variant_pars)
    ]}

    return variant_query

################################################################################

def create_variantRangeRequest_query(variant_request_type, variant_pars):

    # TODO
    if variant_request_type != "variantRangeRequest":
        return

    v_q_l = [
        { "reference_name": variant_pars[ "referenceName" ] },
        { "start": { "$lt": int(variant_pars[ "end" ][-1]) } },
        { "end": { "$gt": int(variant_pars[ "start" ][0]) } }
    ]

    if "variantType" in variant_pars:
        v_q_l.append( create_and_or_query_for_parameter("variantType", "variant_type", "$or", variant_pars) )
    elif "alternateBases" in variant_pars:
        # the N wildcard stands for any length alt bases so can be ignored
        if not variant_pars[ "alternateBases" ] == "N":
            v_q_l.append( { "alternate_bases": variant_pars[ "alternateBases" ] } )

    variant_query = { "$and": v_q_l }

    return variant_query

################################################################################

def create_and_or_query_for_list(logic, q_list):

    if not isinstance(q_list, list):
        return q_list

    if not q_list:
        return [ ]

    if len(q_list) > 1:
        return { logic: q_list }

    return q_list[0]

################################################################################

def create_and_or_query_for_parameter(par, qpar, logic, q_pars):

    if not isinstance(q_pars[ par ], list):
        return { qpar: q_pars[ par ] }

    if not q_pars[ par ][0]:
        return { }

    if len(q_pars[ par ]) > 1:
        v_t_l = [ ]
        for v_t in q_pars[ par ]:
            v_t_l.append( { qpar: v_t } )
        return { logic: v_t_l }

    return { qpar: q_pars[ par ][0] }


################################################################################
