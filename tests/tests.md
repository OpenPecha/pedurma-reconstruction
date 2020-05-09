
- a.txt is the target of annotation transfer 
- b.txt is the source of annotations
- f.yaml is the file with filter rules # TODO one day

## test1

text body, small amount of text 
- a : clean text with ':' markers and derge pages
- b : raw namsel output
- truth : clean text with '#' tags for footnotes markers

## test2

text body, several pages 
- a : clean text with ':' markers and derge pages
- b : raw namsel output
- truth : clean text with '#' tags for footnotes markers

## test3

footnotes, few pages
- a : google OCR with false positives that need to be filtered out
- b : namsel OCR with good footnote markers
- truth : ...
