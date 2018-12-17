# CS-250

A Search Engine implementation using xml files as input.
Structure of valid input xml.
```xml
<collection>
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
</collection>
```

1.  <code>xml_parser.py</code> generates inverted index for given xml file.
    On command prompt: <code>python xml_parser.py stopwords.xml sample.xml sample-output.xml</code>
