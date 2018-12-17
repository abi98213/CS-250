# CS-250

A Search Engine implementation using xml files as input.
the structure of valid input xml
"<collection>
  <page>
    <id>some +ve integer</id>
    <title> title of the page </title>
    <text> contents of the page </text>
  </page>
  <page>....</page>
  <page>....</page>
  <page>....</page>
  .
  .
  . 
</collection>"

xml_parser.py generates inverted index for given xml file
On command prompt: python xml_parser.py stopwords.xml sample.xml sample-output.xml
