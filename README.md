# Pedurma-reconstruction

BODY:

content: 73E-body_transfered.txt
double tseks: 73E-body_transfered.txt
note markers: 73G-body.txt or 73N-body.txt (not sure)


NOTES:

content: 73G-footnotes.txt
note markers: 73N-footnotes.txt

To make the review easier, delimit visually the notes in the text using a regex search : "<.+?>"

corner cases:
 - when a note is located right after a space, before the beginning of a syllable, it has no syllable to attach to and the note location is ignored. By moving the # to the right of the last non-space char, the note location is used, eventhough it is slightly displaced.
 - when a note is after a final ག directly followed by a shad or a space, the note location gets deleted. Workaround : move the # after the shad at the beginning of the next syllable. slightly misplaced...
 - when the base text on which all the markups are transfered(73E-body_transfered.txt) significantly differs from the text in the OCRed versions (73G-body.txt and 73N-body.txt), note location may be skipped or created somewhere there is no note marker at all. the issue is resolved by manually making the three files correspond.