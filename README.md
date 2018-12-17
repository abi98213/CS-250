# CS-250

A Search Engine implementation using xml files as input.<br />
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
<ol>
<li> <code>xml_parser.py</code> generates inverted index for given xml file.<br />
      On command prompt: <code>python xml_parser.py stopwords.xml sample.xml sample-output.xml</code><br />
      It generates sample-output.xml file as  "word|pageID:occurence1,occurence2...;pageID:occurence1, occurernce2...;..." on each line<br />
  
<ol>
