import cgi, cgitb
import json

################################################################################

def cgi_parse_query():

    form_data = cgi.FieldStorage()
    return(form_data)

################################################################################

def cgi_exit_on_error(shout):

    print("Content-Type: text")
    print()
    print(shout)
    exit()

################################################################################

def cgi_print_json_response(data):
    print('Content-Type: text')
    print()
    print(json.dumps(data, indent=4, sort_keys=True, default=str))
    exit()

################################################################################

