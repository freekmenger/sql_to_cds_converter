# sql_to_cds_converter
Convert SQL to CDS (HANA) Artifacts

This program will allow you to convert SQL code to CDS artifact files (.hdbcds) and the corresponding authorizations (.hdbgrants) and synonym (.hdbsynonym) file for your HANA 2 project.

Instructions:
1. install python
2. export the sql create table statements in one big sql file (SQL Server: Tasks > Generate Scripts)
3. download the SQLtoCDS.py program from github (here)
4. run the following command in command line or powershell (windows): python SQLtoCDS.py [input sql file with directory] [output directory]
5. find the output files in the output directory

All the sql tables will be grouped into one cds (.hdbcds) file and according .hdbgrants and .hdbsynonym file. If you want to change this: 
- either look for the 'context' field in the program and adjust the logic
- export the sql create script files in batches and rename the context or files manually
