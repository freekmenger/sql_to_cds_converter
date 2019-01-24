import sys
import pdb
import pandas as pd
import codecs
import re

def read_txt(i_filename):
    ''' 
    i_filename: the directory and filename of the excel file that will be read
    Returns all the lines in a list, split by the create command. 
    So one list item per table that should be created.
    '''
    #Open the filename. Sometimes errors may occur when the encoding is different
    #Works with .sql files, but might also work with plain .txt files
    file = codecs.open(i_filename,"r","utf-16")
    lines = []
    tables = []
    keymark = 0
    keys = []
    ctable = ""
    i = 0
    #Looping through the lines of the file
    for line in file:
        line = line.replace(", ",",")
        #split each line by item, seperated by space
        lineitems = line.split()
        items = []
        #Removing brackets from the items
        for item in lineitems:
            items.append(item.replace("[", "").replace("]", ""))
        #When the CREATE statement was found a new table is defined
        if items != []:
            if items[0] == "CREATE":
                if len(lines) != 0:
                    #adding the previous "lines" to the tables array
                    tables.append(lines)
                lines = []
                keymark = 0
                #getting the table name from the third item (sql: create table [tablename])
                ctable = items[2].split('.')[len(items[2].split('.'))-1].replace("(","")
                lines.append(ctable)
                i = 0
        #Try to extract the field, it has to be of any of the following types:
        #nvarchar, shorttext, nclob, text, varbinary, blob, integer, int (not into), bigint,
        #decimal, double, daydate, date, secondtime, time, seconddate, longdate, timestamp, 
        #alphanum, smallint, tinyint, smalldecimal, real, varchar, clob, binary, st_point, 
        #st_geometry, datetime, bit or char
        try:
            if (items[1][0:8].upper() == "NVARCHAR" or items[1][0:9].upper() == "SHORTTEXT" or 
               items[1][0:5].upper() == "NCLOB" or items[1][0:4].upper() == "TEXT" or 
               items[1][0:9].upper() == "VARBINARY" or items[1][0:4].upper() == "BLOB" or 
               items[1][0:7].upper() == "INTEGER" or 
               (items[1][0:3].upper() == "INT" and items[1][0:4].upper() != "INTO") or 
               items[1][0:6].upper() == "BIGINT" or items[1][0:12].upper() == "DECIMAL(p,s)" or 
               items[1][0:7].upper() == "DECIMAL" or items[1][0:6].upper() == "DOUBLE" or 
               items[1][0:7].upper() == "DAYDATE" or items[1][0:4].upper() == "DATE" or 
               items[1][0:10].upper() == "SECONDTIME" or items[1][0:4].upper() == "TIME" or 
               items[1][0:10].upper() == "SECONDDATE" or items[1][0:8].upper() == "LONGDATE" or 
               items[1][0:9].upper() == "TIMESTAMP" or items[1][0:8].upper() == "ALPHANUM" or 
               items[1][0:8].upper() == "SMALLINT" or items[1][0:7].upper() == "TINYINT" or 
               items[1][0:12].upper() == "SMALLDECIMAL" or items[1][0:4].upper() == "REAL" or 
               items[1][0:7].upper() == "VARCHAR" or items[1][0:4].upper() == "CLOB" or 
               items[1][0:6].upper() == "BINARY" or items[1][0:8].upper() == "ST_POINT" or 
               items[1][0:11].upper() == "ST_GEOMETRY" or items[1][0:8].upper() == "DATETIME"
               or items[1][0:3].upper() == "BIT" or items[1][0:4].upper() == "CHAR"):
                for idx, txt in enumerate(items):
                    #checking if the field is also a key
                    if txt == "KEY"and items[idx-1] == "PRIMARY":
                        #append the key to the keys array
                        keys.append([ctable,items[0]])
                #add the item to the lines array
                lines.append(items)
                i += 1
        except IndexError:
            #Empty lines will fail the index check
            pass
        try:
            if items[0] == "CONSTRAINT" and items[2] == "PRIMARY":
                #indicating the next line will contain a key
                keymark = 1
            elif keymark == 1 and (items[1] == "ASC" or items[1] == "DESC"):
                #append the key to the keys array
                keys.append([ctable,items[0]])
        except IndexError:
            #Empty lines will fail the index check
            pass
    if i != 0:
        #adding the last lines array to the tables array
        tables.append(lines)
    file.close()
    #Return the tables and keys array
    return (tables, keys)


class TableObject(object):
    ''' 
    TableObject: a TableObject that has differentfields
    '''
    def __init__(self, name, context):
        #create a TableObject with empty fieldlist, name and context (output table)
        self.fields = []
        self.name = name
        self.context = context
    def addField(self, fieldname, keyfield, nullfield, generated, fieldtype, decimaltype, length):
        #append field to fieldlist
        self.fields.append([fieldname.upper(), keyfield, nullfield, generated, fieldtype, decimaltype, length])
    def getContext(self):
        #return context field
        return self.context
    def genCDSOutput(self):
        #generate the CDS output text
        resulttext = "  entity " + str(self.name) + "\n"
        resulttext += "  {\n"
        for field in self.fields:
            if field[1] == 'X':
                resulttext += "    key " + str(field[0]) + "  :  "
            else:
                resulttext += "    " + str(field[0]) + "  :  "
            if field[5] == 'X':
                resulttext += str(field[4]) + "(" + str(field[6]) + ")"+ str(field[2]) + str(field[3]) + ";\n"
            else:
                resulttext += str(field[4]) + str(field[2]) + str(field[3]) + ";\n"
        resulttext += "  };\n"
        return resulttext
    def genAuthOutput(self):
        #generate authorization tables
        authtext = "\n      {\n"
        authtext += '        "name":"'+ str(self.name) + '",\n'
        authtext += '        "type":"TABLE",\n'
        authtext += '        "privileges":[ "SELECT" ]\n'
        authtext += '      }'
        return authtext
    def genAuthOutputG(self):
        #generate authorization tables
        authtext = "\n      {\n"
        authtext += '        "name":"'+ str(self.name) + '",\n'
        authtext += '        "type":"TABLE",\n'
        authtext += '        "privileges_with_grant_option":[ "SELECT" ]\n'
        authtext += '      }'
        return authtext
    def genSynonyms(self):
        #generate synonyms
        syntext = '  "'+str(self.name)+'": {\n'
        syntext += '  	"target": {\n'
        syntext += '      "object": "'+str(self.name)+'",\n'
        syntext += '      "schema": "HDB_STG_1"\n'
        syntext += '    }\n'
        syntext += '  }'
        return syntext


def generate_outputOO(i_sql, i_keys, i_outputdir):
    ''' 
    i_sql: the sql statement to create a table
    i_keys: list of keys per table
    i_outputdir: directory and filename of output file
    For each item a cds artifact code will be generated with 
    the corresponding datatypes. Finally the code will generate
    a file.
    Returns OK if the file was generated
    '''
    lines = []
    tables = []
    #Looping through the sql statements (the filtered array created earlier)
    for sql in i_sql:
        if len(sql)>=2:
            #the context is a way to group several tables together in one cds file
            #here it is just made to be 'XX', but if there is some other logic 
            #from the name that can place it in the right group, change that here.
            #for example:
            #context = find_context(str(sql[0]))
            context = 'XX'
            #Create the tableObject
            CurrentTable = TableObject(str(sql[0]),context)
            #Getting keys from keys array for this table
            ckeys = [ x for x in i_keys if sql[0] in x ]
            #Looping over fields
            for field in sql[1:len(sql)]:
                nullfield = ""
                generated = ""
                for idx, txt in enumerate(field):
                    #check if field is nullable
                    if txt == "NULL" and field[idx-1] == "NOT":
                        nullfield = " not null"
                    #check if the field is identity insert (column numbering to be generated by database)
                    if txt[0:8] == "IDENTITY":
                        generated = " generated always as identity ( start with 1 increment by 1 )"      			
                key = ""
                #check if field is a key from the key array
                for key in ckeys:
                    if field[0] == key[1]:
                        key = "X"
                        nullfield = ""
                #check if the field starts with S_PK_ => then it's also a key
                if key == "" and field[0][0:5].upper() == "S_PK_":
                    key = "X"
                #check if the opening parenthesis occurs, then it's a field that has a length specification,
                #the name and length is then split from the field
                if "(" in field[1]:
                    decimaltype = "X"
                    #find the corresponding cds datatype
                    fieldtype = translate_datatypes(field[1].split("(")[0].upper())
                    #find the length
                    length = field[1].split("(")[1].replace(")","")
                else:
                    decimaltype = ""
                    length = ""
                    #find the corresponding cds datatype
                    fieldtype = translate_datatypes(field[1].upper())
                #add the field to the CurrentTable object
                CurrentTable.addField(str(field[0]), key, nullfield, generated, fieldtype, decimaltype, length)
            #append the currentTable object to the tables array
            tables.append(CurrentTable)
    #Sort the tables by name
    tables_srt = sorted(tables, key=lambda tableobject: tableobject.context)
    #Generate the output file, one file for each context
    create_files(i_outputdir, tables_srt)


def find_context(i_objectname):
    '''
    i_tablename: name of the table that will be used to derive context
    this functions identifies the context - two letter abbreviation.
    if it cannot be found, use xx
    '''
    if i_objectname[0:2] == "WS":
        context = "WS"
    elif i_objectname[0:6] == "STG_PI":
        context = "PI"
    elif i_objectname[0:6] == "STG_EU":
        context = "EU"
    elif i_objectname[0:6] == "STG_EV":
        context = "EV"
    elif i_objectname[0:6] == "STG_GR":
        context = "GR"
    elif i_objectname[0:6] == "STG_ME":
        context = "ME"
    elif i_objectname[0:6] == "STG_OR":
        context = "OR"
    elif i_objectname[0:6] == "STG_PR":
        context = "PR"
    elif i_objectname[0:6] == "STG_SF":
        context = "Sf"
    elif i_objectname[0:6] == "STG_SI":
        context = "SI"
    elif i_objectname[0:6] == "STG_AG":
        context = "AG"
    elif i_objectname[0:6] == "STG_CR":
        context = "CR"
    elif i_objectname[0:6] == "STG_FE":
        context = "FE"
    elif i_objectname[0:6] == "STG_KV":
        context = "KV"
    else:
        context = "XX"
    return context


def create_files(i_outputdir, tables_srt):
    '''
    i_outputdir: contains directory of target files
    tables_srt: table objects
    that will generate a file with table settings
    Returns OK if the files were generated
    This function will create one file for each array,
    , one file containing all synonyms and
    one file containing authorizations (external_access) and
    one file containing authorizations with grant option 
    (external_access_g). 
    '''
    
    authtext = '{\n'
    authtext += '  "role": {\n'
    authtext += '    "name": "HDB_STG::external_access",\n'
    authtext += '    "object_privileges": ['
    authtextG = '{\n'
    authtextG += '  "role": {\n'
    authtextG += '    "name": "HDB_STG::external_access_g#",\n'
    authtextG += '    "object_privileges": ['
    syntext = "{\n"
    resulttext = ""
    lastContext = ""
    if len(tables_srt) > 0:
        for table in tables_srt:
            if table.context != lastContext and lastContext != "" and resulttext != "":
                #new context, writing the file
                i_filename = i_outputdir + "\\" + lastContext.lower() + "_tables.hdbcds"
                file = open(i_filename, "w+")
                file.write(resulttext)
                resulttext = ""
            resulttext += table.genCDSOutput()
            authtext += table.genAuthOutput()+","
            authtextG += table.genAuthOutputG() +","
            syntext += table.genSynonyms() +",\n"
            lastContext = table.context
        if table.context != "" and resulttext != "":
            #last context, writing the file
            i_filename = i_outputdir + "\\" + table.context.lower() + "_tables.hdbcds"
            file = open(i_filename, "w+")
            file.write(resulttext)
        #writing authorizationfiles
        #remark: authorizations can also be granted on schema level
        authtext = authtext[0:len(authtext)-1]
        authtext += "\n    ]\n"
        authtext += "  }\n"
        authtext += "}"
        i_filename = i_outputdir + "\external_access.hdbrole"
        file = open(i_filename, "w+")
        file.write(authtext)
        authtextG = authtextG[0:len(authtextG)-1]
        authtextG += "\n    ]\n"
        authtextG += "  }\n"
        authtextG += "}"    
        i_filename = i_outputdir + "\external_access_g.hdbrole"
        file = open(i_filename, "w+")
        file.write(authtextG)    
        syntext = syntext[0:len(syntext)-2]+"\n}"
        i_filename = i_outputdir + "\synonyms.hdbsynonym"
        file = open(i_filename, "w+")
        file.write(syntext)
    else:
        print("no tables found in source")


def translate_datatypes(i_type):
    ''' 
    i_type: SQL datatype
    converts SQL datatypes to CDS datatypes
    Returns CDS datatype
    '''
    switcher = {
        'NVARCHAR': 'String',
        'SHORTTEXT': 'String',
        'NCLOB': 'LargeString',
        'TEXT': 'LargeString',
        'VARBINARY': 'Binary',
        'BLOB': 'LargeBinary',
        'INTEGER': 'Integer',
        'INT': 'Integer',
        'BIGINT': 'Integer64',
        'DECIMAL': 'Decimal',
        'DOUBLE': 'BinaryFloat',
        'DAYDATE': 'LocalDate',
        'DATE': 'LocalDate',
        'SECONDTIME': 'LocalTime',
        'TIME': 'LocalTime',
        'SECONDDATE': 'UTCDateTime',
        'LONGDATE': 'UTCTimestamp',
        'TIMESTAMP': 'UTCTimestamp',
        'ALPHANUM': 'hana.ALPHANUM',
        'SMALLINT': 'Integer',
        'TINYINT': 'Integer',
        'SMALLDECIMAL': 'Decimal',
        'REAL': 'hana.REAL',
        'VARCHAR': 'String',
        'CLOB': 'hana.CLOB',
        'BINARY': 'hana.BINARY',
        'ST_POINT': 'hana.ST_POINT',
        'ST_GEOMETRY': 'hana.ST_GEOMETRY',
        'DATETIME': 'UTCDateTime',
        'BIT': 'Boolean',
        'CHAR': 'String'
    }
    return(switcher.get(i_type, "type not found"))


if __name__ == '__main__':
    '''
    Main program takes 2 arguments as input.
    argument 1: the filename of the SQL file that is to be converted
    argument 2: the output directory of the cds file
    '''    
    #Checking at least two arguments are given
    assert len(sys.argv) >= 3
    #Loading the sql file into an array, filtering out all non-relevant data
    l_filename = str(sys.argv[1])
    l_SQLtbl, keys = read_txt(l_filename)
    #Creating objects that are translated to CDS output and written to a file
    outputdir = str(sys.argv[2])
    generate_outputOO(l_SQLtbl, keys, outputdir)